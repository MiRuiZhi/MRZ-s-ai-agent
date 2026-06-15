from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Dict, List, Optional


def _now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


@dataclass
class RunRecord:
    request_id: str
    session_id: str
    entry_agent: str
    query_text: str
    status: str = "running"
    final_summary_text: Optional[str] = None
    started_at: datetime = field(default_factory=_now)
    finished_at: Optional[datetime] = None
    error_msg: Optional[str] = None


@dataclass
class LlmInvocationRecord:
    request_id: str
    agent_name: str
    step_no: int
    call_kind: str
    response_text: str
    tool_call_count: int
    status: str = "success"
    started_at: datetime = field(default_factory=_now)
    finished_at: datetime = field(default_factory=_now)


@dataclass
class ToolInvocationRecord:
    request_id: str
    tool_call_id: str
    tool_name: str
    tool_provider: str
    input_json: Dict[str, Any]
    agent_name: str
    step_no: int
    status: str = "running"
    llm_observation: str = ""
    error_msg: Optional[str] = None
    started_at: datetime = field(default_factory=_now)
    finished_at: Optional[datetime] = None


@dataclass
class ArtifactRecord:
    request_id: str
    tool_call_id: str
    file_name: str
    preview_url: str = ""
    download_url: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


class InMemoryLedger:
    """Production storage implements the same semantic methods with SQLAlchemy."""

    def __init__(self) -> None:
        self.runs: List[RunRecord] = []
        self.llm_invocations: List[LlmInvocationRecord] = []
        self.tool_invocations: List[ToolInvocationRecord] = []
        self.artifacts: List[ArtifactRecord] = []
        self.deleted_sessions: set[str] = set()

    def begin_run(self, context: Any, entry_agent: str) -> RunRecord:
        if self.runs and self.runs[-1].request_id == context.request_id:
            return self.runs[-1]
        record = RunRecord(
            request_id=context.request_id,
            session_id=context.session_id,
            entry_agent=entry_agent,
            query_text=context.query,
        )
        self.runs.append(record)
        return record

    def finish_run(
        self,
        context: Any,
        status: str,
        final_summary_text: Optional[str] = None,
        error_msg: Optional[str] = None,
    ) -> None:
        run = self.begin_run(context, context.entry_agent or "unknown")
        run.status = status
        run.final_summary_text = final_summary_text
        run.error_msg = error_msg
        run.finished_at = _now()

    def record_llm(
        self,
        context: Any,
        agent_name: str,
        step_no: int,
        call_kind: str,
        response_text: str,
        tool_call_count: int,
    ) -> None:
        self.llm_invocations.append(
            LlmInvocationRecord(
                request_id=context.request_id,
                agent_name=agent_name,
                step_no=step_no,
                call_kind=call_kind,
                response_text=response_text,
                tool_call_count=tool_call_count,
            )
        )

    def start_tool(
        self,
        context: Any,
        tool_call_id: str,
        tool_name: str,
        provider: str,
        input_json: Dict[str, Any],
        agent_name: str,
        step_no: int,
    ) -> ToolInvocationRecord:
        record = ToolInvocationRecord(
            request_id=context.request_id,
            tool_call_id=tool_call_id,
            tool_name=tool_name,
            tool_provider=provider,
            input_json=dict(input_json),
            agent_name=agent_name,
            step_no=step_no,
        )
        self.tool_invocations.append(record)
        return record

    def finish_tool(
        self,
        record: ToolInvocationRecord,
        status: str,
        observation: str,
        error_msg: Optional[str] = None,
    ) -> None:
        record.status = status
        record.llm_observation = observation
        record.error_msg = error_msg
        record.finished_at = _now()

    def record_artifacts(self, context: Any, tool_call_id: str, files: List[Dict[str, Any]]) -> None:
        for file_item in files:
            self.artifacts.append(
                ArtifactRecord(
                    request_id=context.request_id,
                    tool_call_id=tool_call_id,
                    file_name=str(file_item.get("fileName") or file_item.get("file_name") or ""),
                    preview_url=str(file_item.get("previewUrl") or file_item.get("domainUrl") or ""),
                    download_url=str(file_item.get("downloadUrl") or ""),
                    metadata=dict(file_item),
                )
            )

    def list_session_summaries(self, limit: int = 20) -> List[Dict[str, Any]]:
        sessions: Dict[str, Dict[str, Any]] = {}
        for run in self.runs:
            if run.session_id in self.deleted_sessions:
                continue
            sessions[run.session_id] = {
                "sessionId": run.session_id,
                "title": run.query_text[:30],
                "status": run.status.upper(),
                "latestQueryText": run.query_text,
                "latestSummaryText": run.final_summary_text,
                "runCount": sum(1 for item in self.runs if item.session_id == run.session_id),
                "finishedRunCount": sum(
                    1 for item in self.runs if item.session_id == run.session_id and item.status == "success"
                ),
                "failedRunCount": sum(
                    1 for item in self.runs if item.session_id == run.session_id and item.status == "failed"
                ),
                "startedAt": run.started_at.isoformat(),
                "lastActiveAt": (run.finished_at or run.started_at).isoformat(),
            }
        return list(sessions.values())[-limit:]

    def get_session_runs(self, session_id: str) -> List[Dict[str, Any]]:
        if session_id in self.deleted_sessions:
            return []
        return [
            {
                "requestId": run.request_id,
                "status": run.status.upper(),
                "queryText": run.query_text,
                "finalSummaryText": run.final_summary_text,
                "startedAt": run.started_at.isoformat(),
                "finishedAt": run.finished_at.isoformat() if run.finished_at else None,
                "replayFrames": [],
            }
            for run in self.runs
            if run.session_id == session_id
        ]

    def delete_session(self, session_id: str) -> bool:
        exists = any(run.session_id == session_id for run in self.runs)
        if not exists:
            return False
        self.deleted_sessions.add(session_id)
        return True
