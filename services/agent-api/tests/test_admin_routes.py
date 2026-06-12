import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from agent_api.api.app import create_app
from agent_api.api.routes import get_runtime
from agent_api.runtime import AgentRuntime
from agent_api.settings import Settings
from agent_api.storage.models import Base, ConfigRecord


class AdminRouteTest(unittest.TestCase):
    def test_admin_create_and_query_list_persist_to_config_record(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "admin.db"
            database_url = f"sqlite+pysqlite:///{db_path}"
            engine = create_engine(database_url)
            Base.metadata.create_all(bind=engine)
            runtime = AgentRuntime(
                Settings(
                    database_url=database_url,
                    ledger_backend="sql",
                    fake_llm=True,
                )
            )
            app = create_app()
            app.dependency_overrides[get_runtime] = lambda: runtime
            client = TestClient(app)

            created = client.post(
                "/api/v1/admin/ai_agent/create",
                json={"agentId": "sales-agent", "agentName": "Sales Agent", "enabled": True},
            )
            listed = client.get("/api/v1/admin/ai_agent/query-list")

            SessionLocal = sessionmaker(bind=engine)
            with SessionLocal() as session:
                record = session.scalar(
                    select(ConfigRecord).where(
                        ConfigRecord.record_type == "ai_agent",
                        ConfigRecord.record_id == "sales-agent",
                    )
                )

        self.assertEqual(created.status_code, 200)
        self.assertEqual(created.json()["data"]["agentId"], "sales-agent")
        self.assertEqual(listed.status_code, 200)
        self.assertEqual(listed.json()["data"]["total"], 1)
        self.assertEqual(listed.json()["data"]["records"][0]["agentName"], "Sales Agent")
        self.assertIsNotNone(record)
        self.assertEqual(record.name, "Sales Agent")
        self.assertTrue(record.payload["enabled"])


if __name__ == "__main__":
    unittest.main()
