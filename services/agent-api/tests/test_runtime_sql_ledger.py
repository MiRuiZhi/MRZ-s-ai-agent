import tempfile
import unittest
from pathlib import Path

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from agent_api.api.schemas import AgentRequest
from agent_api.runtime import AgentRuntime
from agent_api.settings import Settings
from agent_api.storage.models import Base, DialogueRun


class AgentRuntimeSqlLedgerTest(unittest.IsolatedAsyncioTestCase):
    async def test_runtime_persists_react_run_when_sql_ledger_enabled(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "agent-api.db"
            database_url = f"sqlite+pysqlite:///{db_path}"
            engine = create_engine(database_url)
            Base.metadata.create_all(bind=engine)
            settings = Settings(
                database_url=database_url,
                ledger_backend="sql",
                fake_llm=True,
                tool_runtime_base_url="http://tool-runtime.invalid",
            )
            runtime = AgentRuntime(settings)

            events = [
                event
                async for event in runtime.stream_agent(
                    AgentRequest(
                        requestId="req-runtime-sql",
                        sessionId="session-runtime-sql",
                        query="hello runtime",
                        agentType=1,
                    )
                )
            ]

            SessionLocal = sessionmaker(bind=engine)
            with SessionLocal() as session:
                run = session.scalar(select(DialogueRun).where(DialogueRun.request_id == "req-runtime-sql"))

        self.assertEqual(events[-1].type, "result")
        self.assertIsNotNone(run)
        self.assertEqual(run.status, 1)
        self.assertIn("hello runtime", run.final_summary_text)


if __name__ == "__main__":
    unittest.main()
