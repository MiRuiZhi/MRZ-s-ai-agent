import unittest

from fastapi.testclient import TestClient

from agent_api.api.app import create_app


class VisitorRouteTest(unittest.TestCase):
    def test_visitor_naming_accepts_frontend_username_payload(self):
        client = TestClient(create_app())

        response = client.post(
            "/api/agent/visitor/naming",
            json={"username": "测试用户", "visitorId": "visitor-existing"},
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()["data"]
        self.assertEqual(data["visitorId"], "visitor-existing")
        self.assertEqual(data["username"], "测试用户")
        self.assertEqual(data["visitorName"], "测试用户")
        self.assertTrue(data["named"])


if __name__ == "__main__":
    unittest.main()
