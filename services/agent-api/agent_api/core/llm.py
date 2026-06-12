from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional, Protocol


@dataclass
class ToolCall:
    id: str
    name: str
    arguments: Dict[str, Any] = field(default_factory=dict)

    def to_openai_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": "function",
            "function": {
                "name": self.name,
                "arguments": json.dumps(self.arguments, ensure_ascii=False),
            },
        }


@dataclass
class ToolCallResponse:
    content: str
    tool_calls: List[ToolCall] = field(default_factory=list)
    finish_reason: Optional[str] = None
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class ToolCapableLLM(Protocol):
    async def ask_tool(self, context: Any, agent_name: str) -> ToolCallResponse:
        ...


class ScriptedLLM:
    """Deterministic LLM used by tests and local demos."""

    def __init__(self, responses: Iterable[ToolCallResponse]) -> None:
        self._responses: List[ToolCallResponse] = list(responses)
        self._index = 0
        self._lock = asyncio.Lock()

    async def ask_tool(self, context: Any, agent_name: str) -> ToolCallResponse:
        async with self._lock:
            if self._index >= len(self._responses):
                return ToolCallResponse(content="", tool_calls=[])
            response = self._responses[self._index]
            self._index += 1
            return response
