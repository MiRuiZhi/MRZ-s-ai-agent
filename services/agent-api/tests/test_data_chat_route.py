import json
import unittest

from fastapi.testclient import TestClient

from agent_api.api.app import create_app


class DataChatRouteTest(unittest.TestCase):
    def test_data_chat_query_streams_frontend_compatible_events(self):
        client = TestClient(create_app())

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


if __name__ == "__main__":
    unittest.main()
