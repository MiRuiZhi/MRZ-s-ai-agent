import json
import unittest

from fastapi.testclient import TestClient

from agent_api.api.app import create_app
from agent_api.api.routes import get_runtime
from agent_api.runtime import AgentRuntime
from agent_api.settings import Settings


class DataChatRouteTest(unittest.TestCase):
    def create_memory_client(self):
        runtime = AgentRuntime(Settings(fake_llm=True, ledger_backend="memory"))
        app = create_app()
        app.dependency_overrides[get_runtime] = lambda: runtime
        return TestClient(app)

    def test_data_chat_query_streams_frontend_compatible_events(self):
        client = self.create_memory_client()

        response = client.post("/data/chatQuery", json={"content": "show sales"})

        self.assertEqual(response.status_code, 200)
        self.assertIn("text/event-stream", response.headers["content-type"])
        events = [
            json.loads(line.removeprefix("data: "))
            for line in response.text.splitlines()
            if line.startswith("data: ")
        ]
        self.assertEqual([event["eventType"] for event in events], ["THINK", "CHART_DATA", "READY"])
        self.assertIn("show sales", events[0]["data"])
        self.assertEqual(events[1]["data"], [])

    def test_data_chat_query_records_recent_session(self):
        client = self.create_memory_client()

        response = client.post(
            "/data/chatQuery",
            json={
                "content": "show sales",
                "sessionId": "session-data-chat",
                "requestId": "req-data-chat",
            },
        )

        self.assertEqual(response.status_code, 200)
        sessions = client.get("/api/agent/conversation/sessions").json()["data"]
        self.assertEqual(sessions[0]["sessionId"], "session-data-chat")
        self.assertEqual(sessions[0]["latestQueryText"], "show sales")
        self.assertEqual(sessions[0]["status"], "SUCCESS")


if __name__ == "__main__":
    unittest.main()
