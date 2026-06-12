import json
import unittest

from fastapi.testclient import TestClient

from agent_api.api.app import create_app
from agent_api.api.routes import get_runtime
from agent_api.runtime import AgentRuntime
from agent_api.settings import Settings


class AgentSseRouteTest(unittest.TestCase):
    def test_query_agent_stream_emits_only_json_sse_data(self):
        app = create_app()
        app.dependency_overrides[get_runtime] = lambda: AgentRuntime(
            Settings(fake_llm=True, ledger_backend="memory")
        )
        client = TestClient(app)

        response = client.post(
            "/web/api/v1/gpt/queryAgentStreamIncr",
            json={"query": "hello", "sessionId": "session-sse", "deepThink": 0},
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("text/event-stream", response.headers["content-type"])
        events = [
            json.loads(line.removeprefix("data: "))
            for line in response.text.splitlines()
            if line.startswith("data: ")
        ]
        self.assertTrue(events)
        self.assertNotIn("[DONE]", response.text)
        self.assertEqual(events[-1]["messageType"], "result")
        self.assertTrue(events[-1]["isFinal"])


if __name__ == "__main__":
    unittest.main()
