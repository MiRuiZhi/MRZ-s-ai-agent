import unittest
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from agent_api.api.app import create_app


class FileUploadRouteTest(unittest.TestCase):
    def test_upload_conversation_file_forwards_to_tool_runtime(self):
        app = create_app()
        client = TestClient(app)
        upload_mock = AsyncMock(
            return_value={
                "downloadUrl": "/tool/v1/file_tool/download/session-1/notes.txt",
                "domainUrl": "/tool/v1/file_tool/preview/session-1/notes.txt",
                "fileSize": 5,
            }
        )

        with patch("agent_api.integrations.tool_runtime.ToolRuntimeClient.upload_file_data", upload_mock):
            response = client.post(
                "/api/agent/file/upload",
                data={"sessionId": "session-1"},
                files={"file": ("notes.txt", b"hello", "text/plain")},
            )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["code"], "0000")
        self.assertEqual(payload["data"]["name"], "notes.txt")
        self.assertEqual(payload["data"]["url"], "/tool/v1/file_tool/preview/session-1/notes.txt")
        self.assertEqual(payload["data"]["downloadUrl"], "/tool/v1/file_tool/download/session-1/notes.txt")
        self.assertEqual(payload["data"]["size"], 5)
        upload_mock.assert_awaited_once()


if __name__ == "__main__":
    unittest.main()
