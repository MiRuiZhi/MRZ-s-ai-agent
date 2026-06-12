import unittest

import httpx

from agent_api.integrations.tool_runtime import ToolRuntimeClient


class ToolRuntimeClientTest(unittest.IsolatedAsyncioTestCase):
    async def test_upload_file_data_posts_multipart_payload(self):
        captured = {}

        async def handler(request: httpx.Request) -> httpx.Response:
            captured["url"] = str(request.url)
            captured["content_type"] = request.headers["content-type"]
            captured["body"] = await request.aread()
            return httpx.Response(
                200,
                json={
                    "downloadUrl": "/v1/file_tool/download/session-1/notes.txt",
                    "domainUrl": "/v1/file_tool/preview/session-1/notes.txt",
                    "fileSize": 5,
                },
            )

        client = ToolRuntimeClient("http://tool-runtime", transport=httpx.MockTransport(handler))

        response = await client.upload_file_data(
            request_id="session-1",
            filename="notes.txt",
            content=b"hello",
            content_type="text/plain",
        )

        self.assertEqual(captured["url"], "http://tool-runtime/v1/file_tool/upload_file_data")
        self.assertIn("multipart/form-data", captured["content_type"])
        self.assertIn(b'name="requestId"', captured["body"])
        self.assertIn(b"session-1", captured["body"])
        self.assertIn(b'filename="notes.txt"', captured["body"])
        self.assertEqual(response["fileSize"], 5)


if __name__ == "__main__":
    unittest.main()
