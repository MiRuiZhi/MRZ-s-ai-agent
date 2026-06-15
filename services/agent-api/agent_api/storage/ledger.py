from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Callable, Dict, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from agent_api.storage.models import ArtifactLedger, DialogueRun, DialogueSession, LlmInvocation, ToolInvocation


STATUS_CODE: Dict[str, int] = {
    "running": 0,
    "success": 1,
    "failed": 2,
    "stopped": 3,
}
STATUS_LABEL = {value: key.upper() for key, value in STATUS_CODE.items()}


def _now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


@dataclass(frozen=True)
class SqlToolInvocationHandle:
    id: int
    request_id: str
    tool_call_id: str


class SqlAlchemyLedger:
    """SQLAlchemy-backed ledger with the same methods as InMemoryLedger."""

    def __init__(self, session_factory: Callable[[], Session]) -> None:
        self.session_factory = session_factory

    def begin_run(self, context: Any, entry_agent: str) -> DialogueRun:
        with self.session_factory() as session:
            run = self._get_run(session, context.request_id)
            if run is None:
                run = self._create_run(session, context, entry_agent)
            session.commit()
            return run

    def finish_run(
        self,
        context: Any,
        status: str,
        final_summary_text: Optional[str] = None,
        error_msg: Optional[str] = None,
    ) -> None:
        now = _now()
        status_code = STATUS_CODE.get(status, STATUS_CODE["failed"])
        with self.session_factory() as session:
            run = self._get_run(session, context.request_id)
            if run is None:
                run = self._create_run(session, context, context.entry_agent or "unknown")
            old_status = run.status
            run.status = status_code
            run.final_summary_text = final_summary_text
            run.error_msg = error_msg
            run.finished_at = now
            if run.started_at:
                run.duration_ms = int((now - run.started_at).total_seconds() * 1000)

            dialogue_session = self._get_or_create_dialogue_session(session, context, now)
            dialogue_session.status = status_code
            dialogue_session.latest_request_id = context.request_id
            dialogue_session.latest_query_text = context.query
            dialogue_session.latest_summary_text = final_summary_text
            dialogue_session.last_active_at = now
            if old_status != STATUS_CODE["success"] and status_code == STATUS_CODE["success"]:
                dialogue_session.finished_run_count += 1
            if old_status != STATUS_CODE["failed"] and status_code == STATUS_CODE["failed"]:
                dialogue_session.failed_run_count += 1
            session.commit()

    def record_llm(
        self,
        context: Any,
        agent_name: str,
        step_no: int,
        call_kind: str,
        response_text: str,
        tool_call_count: int,
    ) -> None:
        now = _now()
        with self.session_factory() as session:
            run = self._get_run(session, context.request_id)
            if run is None:
                run = self._create_run(session, context, context.entry_agent or agent_name)
            run.llm_call_count += 1
            session.add(
                LlmInvocation(
                    run_id=run.id,
                    invocation_seq=run.llm_call_count,
                    agent_name=agent_name,
                    step_no=step_no,
                    call_kind=call_kind,
                    response_text=response_text,
                    tool_call_count=tool_call_count,
                    status=STATUS_CODE["success"],
                    started_at=now,
                    finished_at=now,
                    duration_ms=0,
                )
            )
            session.commit()

    def start_tool(
        self,
        context: Any,
        tool_call_id: str,
        tool_name: str,
        provider: str,
        input_json: Dict[str, Any],
        agent_name: str,
        step_no: int,
    ) -> SqlToolInvocationHandle:
        now = _now()
        with self.session_factory() as session:
            run = self._get_run(session, context.request_id)
            if run is None:
                run = self._create_run(session, context, context.entry_agent or agent_name)
            run.tool_call_count += 1
            invocation = ToolInvocation(
                run_id=run.id,
                tool_call_id=tool_call_id,
                dispatch_index=run.tool_call_count,
                agent_name=agent_name,
                step_no=step_no,
                tool_name=tool_name,
                tool_provider=provider,
                input_json=dict(input_json),
                status=STATUS_CODE["running"],
                started_at=now,
            )
            session.add(invocation)
            session.flush()
            handle = SqlToolInvocationHandle(
                id=int(invocation.id),
                request_id=context.request_id,
                tool_call_id=tool_call_id,
            )
            session.commit()
            return handle

    def finish_tool(
        self,
        record: SqlToolInvocationHandle,
        status: str,
        observation: str,
        error_msg: Optional[str] = None,
    ) -> None:
        now = _now()
        with self.session_factory() as session:
            invocation = session.get(ToolInvocation, record.id)
            if invocation is None:
                return
            invocation.status = STATUS_CODE.get(status, STATUS_CODE["failed"])
            invocation.llm_observation = observation
            invocation.error_msg = error_msg
            invocation.finished_at = now
            if invocation.started_at:
                invocation.duration_ms = int((now - invocation.started_at).total_seconds() * 1000)
            session.commit()

    def record_artifacts(self, context: Any, tool_call_id: str, files: list[dict[str, Any]]) -> None:
        if not files:
            return
        with self.session_factory() as session:
            run = self._get_run(session, context.request_id)
            if run is None:
                run = self._create_run(session, context, context.entry_agent or "unknown")
            tool_invocation = session.scalar(
                select(ToolInvocation).where(
                    ToolInvocation.run_id == run.id,
                    ToolInvocation.tool_call_id == tool_call_id,
                )
            )
            for file_item in files:
                session.add(
                    ArtifactLedger(
                        run_id=run.id,
                        request_id=context.request_id,
                        tool_invocation_id=tool_invocation.id if tool_invocation else None,
                        tool_call_id=tool_call_id,
                        artifact_role="tool_output",
                        source_type="tool",
                        source_name=tool_invocation.tool_name if tool_invocation else None,
                        file_name=str(
                            file_item.get("fileName")
                            or file_item.get("file_name")
                            or file_item.get("name")
                            or ""
                        ),
                        storage_key=str(file_item.get("storageKey") or file_item.get("path") or ""),
                        download_url=str(file_item.get("downloadUrl") or ""),
                        preview_url=str(file_item.get("previewUrl") or file_item.get("domainUrl") or ""),
                        mime_type=file_item.get("mimeType") or file_item.get("contentType"),
                        file_size=file_item.get("fileSize") or file_item.get("size"),
                        file_hash=file_item.get("sha256") or file_item.get("fileHash"),
                        metadata_json=dict(file_item),
                    )
                )
                run.artifact_count += 1
            session.commit()

    def list_session_summaries(self, limit: int = 20) -> list[dict[str, Any]]:
        with self.session_factory() as session:
            rows = session.scalars(
                select(DialogueSession)
                .where(DialogueSession.deleted == 0)
                .order_by(DialogueSession.last_active_at.desc(), DialogueSession.id.desc())
                .limit(limit)
            ).all()
            return [
                {
                    "sessionId": row.session_id,
                    "title": row.title or row.session_id,
                    "status": STATUS_LABEL.get(row.status, "UNKNOWN"),
                    "latestRequestId": row.latest_request_id,
                    "latestQueryText": row.latest_query_text,
                    "latestSummaryText": row.latest_summary_text,
                    "runCount": row.run_count,
                    "finishedRunCount": row.finished_run_count,
                    "failedRunCount": row.failed_run_count,
                    "startedAt": row.started_at.isoformat() if row.started_at else None,
                    "lastActiveAt": row.last_active_at.isoformat() if row.last_active_at else None,
                }
                for row in rows
            ]

    def get_session_runs(self, session_id: str) -> list[dict[str, Any]]:
        with self.session_factory() as session:
            rows = session.scalars(
                select(DialogueRun)
                .where(DialogueRun.session_id == session_id, DialogueRun.deleted == 0)
                .order_by(DialogueRun.started_at.asc(), DialogueRun.id.asc())
            ).all()
            return [
                {
                    "requestId": row.request_id,
                    "status": STATUS_LABEL.get(row.status, "UNKNOWN"),
                    "queryText": row.query_text,
                    "finalSummaryText": row.final_summary_text,
                    "startedAt": row.started_at.isoformat() if row.started_at else None,
                    "finishedAt": row.finished_at.isoformat() if row.finished_at else None,
                    "replayFrames": [],
                }
                for row in rows
            ]

    def delete_session(self, session_id: str) -> bool:
        now = _now()
        with self.session_factory() as session:
            dialogue_session = session.scalar(
                select(DialogueSession).where(
                    DialogueSession.session_id == session_id,
                    DialogueSession.deleted == 0,
                )
            )
            if dialogue_session is None:
                return False

            dialogue_session.deleted = 1
            dialogue_session.update_time = now
            runs = session.scalars(
                select(DialogueRun).where(
                    DialogueRun.session_id == session_id,
                    DialogueRun.deleted == 0,
                )
            ).all()
            for run in runs:
                run.deleted = 1
                run.update_time = now
            session.commit()
            return True

    def _get_run(self, session: Session, request_id: str) -> Optional[DialogueRun]:
        return session.scalar(select(DialogueRun).where(DialogueRun.request_id == request_id))

    def _create_run(self, session: Session, context: Any, entry_agent: str) -> DialogueRun:
        now = _now()
        dialogue_session = self._get_or_create_dialogue_session(session, context, now)
        dialogue_session.run_count += 1
        dialogue_session.latest_request_id = context.request_id
        dialogue_session.latest_query_text = context.query
        dialogue_session.last_active_at = now
        run = DialogueRun(
            run_uid=context.request_id,
            request_id=context.request_id,
            session_id=context.session_id,
            visitor_id=getattr(context, "visitor_id", None),
            entry_agent=entry_agent,
            status=STATUS_CODE["running"],
            query_text=context.query,
            started_at=now,
        )
        session.add(run)
        session.flush()
        return run

    def _get_or_create_dialogue_session(self, session: Session, context: Any, now: datetime) -> DialogueSession:
        dialogue_session = session.scalar(
            select(DialogueSession).where(DialogueSession.session_id == context.session_id)
        )
        if dialogue_session is not None:
            return dialogue_session
        title = context.query[:30] if context.query else context.session_id
        dialogue_session = DialogueSession(
            session_id=context.session_id,
            visitor_id=getattr(context, "visitor_id", None),
            title=title,
            status=STATUS_CODE["running"],
            latest_request_id=context.request_id,
            latest_query_text=context.query,
            run_count=0,
            started_at=now,
            last_active_at=now,
        )
        session.add(dialogue_session)
        session.flush()
        return dialogue_session
