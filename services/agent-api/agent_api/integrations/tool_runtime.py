from __future__ import annotations

from typing import Any, Dict, Optional

import httpx

from agent_api.core.tools import ToolCollection, ToolResult


class ToolRuntimeClient:
    def __init__(self, base_url: str, *, transport: Optional[httpx.AsyncBaseTransport] = None) -> None:
        self.base_url = base_url.rstrip("/")
        self.transport = transport

    async def post_json(self, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        async with self._client() as client:
            response = await client.post(f"{self.base_url}{path}", json=payload)
            response.raise_for_status()
            return response.json()

    async def upload_file_data(
        self,
        *,
        request_id: str,
        filename: str,
        content: bytes,
        content_type: str | None = None,
    ) -> Dict[str, Any]:
        files = {
            "file": (
                filename,
                content,
                content_type or "application/octet-stream",
            )
        }
        async with self._client() as client:
            response = await client.post(
                f"{self.base_url}/v1/file_tool/upload_file_data",
                data={"requestId": request_id},
                files=files,
            )
            response.raise_for_status()
            return response.json()

    def _client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(timeout=300.0, transport=self.transport)


def _normalize_response(response: Dict[str, Any]) -> ToolResult:
    data = response.get("data", "")
    file_info = response.get("fileInfo") or response.get("file_info") or []
    if isinstance(data, (dict, list)):
        observation = str(data)
    else:
        observation = data or response.get("message", "")
    return ToolResult(
        tool_result=str(data),
        llm_observation=str(observation),
        structured_output=response,
        files=file_info,
        failed=response.get("code") not in (None, 0, 200, "200"),
        error_msg=response.get("message") if response.get("code") not in (None, 0, 200, "200") else None,
    )


def register_tool_runtime_tools(tools: ToolCollection, client: ToolRuntimeClient) -> None:
    async def deep_search(arguments: Dict[str, Any], context: Any) -> ToolResult:
        response = await client.post_json(
            "/v1/tool/deepsearch",
            {
                "request_id": context.request_id,
                "query": arguments.get("query") or context.query,
                "maxLoop": arguments.get("maxLoop", 1),
                "stream": False,
            },
        )
        return _normalize_response(response)

    async def web_fetch(arguments: Dict[str, Any], context: Any) -> ToolResult:
        response = await client.post_json(
            "/v1/tool/web_fetch",
            {
                "requestId": context.request_id,
                "url": arguments.get("url", ""),
                "timeoutSeconds": arguments.get("timeoutSeconds", 30),
            },
        )
        return _normalize_response(response)

    async def report_tool(arguments: Dict[str, Any], context: Any) -> ToolResult:
        response = await client.post_json(
            "/v1/tool/report",
            {
                "requestId": context.request_id,
                "task": arguments.get("task") or context.query,
                "fileNames": arguments.get("fileNames", []),
                "fileName": arguments.get("fileName", "report"),
                "fileType": arguments.get("fileType", "html"),
                "stream": False,
            },
        )
        return _normalize_response(response)

    async def code_interpreter(arguments: Dict[str, Any], context: Any) -> ToolResult:
        response = await client.post_json(
            "/v1/tool/code_interpreter",
            {
                "requestId": context.request_id,
                "task": arguments.get("task") or context.query,
                "fileNames": arguments.get("fileNames", []),
                "stream": False,
                "permissionProfile": arguments.get("permissionProfile", "analysis"),
            },
        )
        return _normalize_response(response)

    async def image_generation(arguments: Dict[str, Any], context: Any) -> ToolResult:
        response = await client.post_json(
            "/v1/tool/image_generation",
            {
                "requestId": context.request_id,
                "prompt": arguments.get("prompt") or context.query,
                "fileNames": arguments.get("fileNames", []),
                "stream": False,
            },
        )
        return _normalize_response(response)

    tools.add_local_tool("deep_search", "Deep research search and answer tool", deep_search)
    tools.add_local_tool("web_fetch", "Fetch and extract one web page", web_fetch)
    tools.add_local_tool("report_tool", "Generate markdown/html/ppt report artifacts", report_tool)
    tools.add_local_tool("code_interpreter", "Run code analysis and generate files", code_interpreter)
    tools.add_local_tool("image_generation", "Generate or edit images", image_generation)
