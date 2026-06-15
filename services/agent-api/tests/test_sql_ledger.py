import unittest

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from agent_api.core.context import AgentContext
from agent_api.core.events import EventCollector
from agent_api.core.tools import ToolCollection
from agent_api.storage.ledger import SqlAlchemyLedger
from agent_api.storage.models import ArtifactLedger, Base, DialogueRun, DialogueSession, LlmInvocation, ToolInvocation


class SqlAlchemyLedgerTest(unittest.TestCase):
    def test_ledger_persists_run_invocations_and_artifacts(self):
        engine = create_engine("sqlite+pysqlite:///:memory:")
        Base.metadata.create_all(bind=engine)
        session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
        ledger = SqlAlchemyLedger(session_factory)
        context = AgentContext(
            request_id="req-sql",
            session_id="session-sql",
            query="build a report",
            events=EventCollector(),
            ledger=ledger,
            tools=ToolCollection(),
        )

        ledger.begin_run(context, "react")
        ledger.record_llm(
            context,
            agent_name="react",
            step_no=1,
            call_kind="askTool",
            response_text="I need a report tool",
            tool_call_count=1,
        )
        tool_record = ledger.start_tool(
            context,
            tool_call_id="call-report",
            tool_name="report",
            provider="tool-runtime",
            input_json={"topic": "agents"},
            agent_name="react",
            step_no=1,
        )
        ledger.finish_tool(tool_record, "success", "report generated")
        ledger.record_artifacts(
            context,
            "call-report",
            [
                {
                    "fileName": "agent-report.md",
                    "previewUrl": "/tool/v1/file_tool/preview/agent-report.md",
                    "downloadUrl": "/tool/v1/file_tool/download/agent-report.md",
                    "sha256": "abc123",
                    "fileSize": 42,
                }
            ],
        )
        ledger.finish_run(context, "success", "done")

        with session_factory() as session:
            stored_session = session.scalar(select(DialogueSession).where(DialogueSession.session_id == "session-sql"))
            stored_run = session.scalar(select(DialogueRun).where(DialogueRun.request_id == "req-sql"))
            llm_count = len(session.scalars(select(LlmInvocation)).all())
            tool = session.scalar(select(ToolInvocation).where(ToolInvocation.tool_call_id == "call-report"))
            artifact = session.scalar(select(ArtifactLedger).where(ArtifactLedger.file_name == "agent-report.md"))

        self.assertIsNotNone(stored_session)
        self.assertEqual(stored_session.run_count, 1)
        self.assertEqual(stored_session.finished_run_count, 1)
        self.assertEqual(stored_session.latest_summary_text, "done")
        self.assertIsNotNone(stored_run)
        self.assertEqual(stored_run.status, 1)
        self.assertEqual(stored_run.llm_call_count, 1)
        self.assertEqual(stored_run.tool_call_count, 1)
        self.assertEqual(stored_run.artifact_count, 1)
        self.assertEqual(llm_count, 1)
        self.assertEqual(tool.status, 1)
        self.assertEqual(tool.llm_observation, "report generated")
        self.assertEqual(artifact.file_hash, "abc123")
        self.assertEqual(artifact.file_size, 42)

        sessions = ledger.list_session_summaries(limit=10)
        runs = ledger.get_session_runs("session-sql")

        self.assertEqual(len(sessions), 1)
        self.assertEqual(sessions[0]["sessionId"], "session-sql")
        self.assertEqual(sessions[0]["runCount"], 1)
        self.assertEqual(len(runs), 1)
        self.assertEqual(runs[0]["requestId"], "req-sql")
        self.assertEqual(runs[0]["finalSummaryText"], "done")

    def test_delete_session_soft_deletes_summary_and_runs(self):
        engine = create_engine("sqlite+pysqlite:///:memory:")
        Base.metadata.create_all(bind=engine)
        session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
        ledger = SqlAlchemyLedger(session_factory)
        context = AgentContext(
            request_id="req-delete",
            session_id="session-delete",
            query="delete this conversation",
            events=EventCollector(),
            ledger=ledger,
            tools=ToolCollection(),
        )

        ledger.begin_run(context, "react")
        ledger.finish_run(context, "success", "done")

        self.assertTrue(ledger.delete_session("session-delete"))
        self.assertEqual(ledger.list_session_summaries(limit=10), [])
        self.assertEqual(ledger.get_session_runs("session-delete"), [])

        with session_factory() as session:
            stored_session = session.scalar(
                select(DialogueSession).where(DialogueSession.session_id == "session-delete")
            )
            stored_run = session.scalar(
                select(DialogueRun).where(DialogueRun.request_id == "req-delete")
            )

        self.assertEqual(stored_session.deleted, 1)
        self.assertEqual(stored_run.deleted, 1)


if __name__ == "__main__":
    unittest.main()
