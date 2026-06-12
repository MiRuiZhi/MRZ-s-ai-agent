from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class Message:
    role: str
    content: str
    tool_call_id: Optional[str] = None
    tool_calls: List[Any] = field(default_factory=list)

    @classmethod
    def user(cls, content: str) -> "Message":
        return cls(role="user", content=content)

    @classmethod
    def assistant(cls, content: str, tool_calls: Optional[List[Any]] = None) -> "Message":
        return cls(role="assistant", content=content, tool_calls=list(tool_calls or []))

    @classmethod
    def tool(cls, content: str, tool_call_id: str) -> "Message":
        return cls(role="tool", content=content, tool_call_id=tool_call_id)

    def to_openai_dict(self) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "role": self.role,
            "content": self.content,
        }
        if self.tool_call_id:
            payload["tool_call_id"] = self.tool_call_id
        if self.tool_calls:
            payload["tool_calls"] = [call.to_openai_dict() for call in self.tool_calls]
        return payload


class Memory:
    def __init__(self) -> None:
        self._messages: List[Message] = []

    def add(self, message: Message) -> None:
        self._messages.append(message)

    def extend(self, messages: List[Message]) -> None:
        self._messages.extend(messages)

    def clear(self) -> None:
        self._messages.clear()

    @property
    def messages(self) -> List[Message]:
        return self._messages

    @property
    def last(self) -> Message:
        if not self._messages:
            raise IndexError("memory is empty")
        return self._messages[-1]

    def __len__(self) -> int:
        return len(self._messages)
