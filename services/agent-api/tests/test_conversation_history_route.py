import unittest
from urllib.parse import quote

from fastapi.testclient import TestClient

from agent_api.api.app import create_app
from agent_api.api.routes import get_runtime
from agent_api.runtime import AgentRuntime
from agent_api.settings import Settings


class ConversationHistoryRouteTest(unittest.TestCase):
    def test_delete_session_hides_it_from_recent_sessions(self):
        runtime = AgentRuntime(Settings(fake_llm=True, ledger_backend="memory"))
        app = create_app()
        app.dependency_overrides[get_runtime] = lambda: runtime
        client = TestClient(app)

        client.post(
            "/web/api/v1/gpt/queryAgentStreamIncr",
            json={"query": "delete me", "sessionId": "session-delete-route", "deepThink": 0},
        )

        before_delete = client.get("/api/agent/conversation/sessions").json()["data"]
        self.assertEqual(before_delete[0]["sessionId"], "session-delete-route")

        response = client.delete("/api/agent/conversation/sessions/session-delete-route")

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["data"]["deleted"])
        after_delete = client.get("/api/agent/conversation/sessions").json()["data"]
        self.assertEqual(after_delete, [])
        detail = client.get("/api/agent/conversation/sessions/session-delete-route").json()["data"]
        self.assertEqual(detail["runs"], [])

    def test_encoded_session_id_with_slash_can_be_loaded_and_deleted(self):
        runtime = AgentRuntime(Settings(fake_llm=True, ledger_backend="memory"))
        app = create_app()
        app.dependency_overrides[get_runtime] = lambda: runtime
        client = TestClient(app)
        session_id = "session/special 中文"
        encoded_session_id = quote(session_id, safe="")

        client.post(
            "/web/api/v1/gpt/queryAgentStreamIncr",
            json={"query": "special session", "sessionId": session_id, "deepThink": 0},
        )

        detail = client.get(f"/api/agent/conversation/sessions/{encoded_session_id}")
        self.assertEqual(detail.status_code, 200)
        self.assertEqual(detail.json()["data"]["sessionId"], session_id)

        delete_response = client.delete(f"/api/agent/conversation/sessions/{encoded_session_id}")
        self.assertEqual(delete_response.status_code, 200)
        self.assertTrue(delete_response.json()["data"]["deleted"])


if __name__ == "__main__":
    unittest.main()
