from __future__ import annotations

import inspect
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Dict, List, Optional, Union


@dataclass
class ToolResult:
    tool_result: str
    llm_observation: Optional[str] = None
    structured_output: Optional[Dict[str, Any]] = None
    files: List[Dict[str, Any]] = field(default_factory=list)
    failed: bool = False
    error_msg: Optional[str] = None

    @property
    def observation(self) -> str:
        return self.llm_observation if self.llm_observation is not None else self.tool_result


ToolHandler = Callable[[Dict[str, Any], Any], Union[Awaitable[ToolResult], ToolResult]]


@dataclass
class ToolDefinition:
    name: str
    description: str
    handler: ToolHandler
    provider: str = "local"


class ToolCollection:
    def __init__(self) -> None:
        self._tools: Dict[str, ToolDefinition] = {}

    def add_local_tool(self, name: str, description: str, handler: ToolHandler) -> None:
        self._tools[name] = ToolDefinition(
            name=name,
            description=description,
            handler=handler,
            provider="local",
        )

    def describe_for_llm(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "provider": tool.provider,
            }
            for tool in self._tools.values()
        ]

    def provider_for(self, name: str) -> str:
        tool = self._tools.get(name)
        return tool.provider if tool else "unknown"

    async def execute(self, name: str, arguments: Dict[str, Any], context: Any) -> ToolResult:
        if name not in self._tools:
            return ToolResult(
                tool_result=f"Tool {name} Error.",
                llm_observation=f"Tool {name} Error.",
                failed=True,
                error_msg=f"Unknown tool: {name}",
            )
        result = self._tools[name].handler(arguments, context)
        if inspect.isawaitable(result):
            result = await result
        return result
