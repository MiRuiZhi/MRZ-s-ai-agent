from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class Event:
    type: str
    payload: Any
    message_id: Optional[str] = None
    is_final: bool = False
    result_map: Dict[str, Any] = field(default_factory=dict)

    def to_sse_data(self) -> str:
        body: Dict[str, Any] = {
            "messageType": self.type,
            "data": self.payload,
            "isFinal": self.is_final,
        }
        if self.message_id:
            body["messageId"] = self.message_id
        if self.result_map:
            body["resultMap"] = self.result_map
        return json.dumps(body, ensure_ascii=False)


class EventCollector:
    """In-memory event sink used by tests and API streaming adapters."""

    def __init__(self) -> None:
        self.items: List[Event] = []

    async def emit(
        self,
        event_type: str,
        payload: Any,
        *,
        message_id: Optional[str] = None,
        is_final: bool = False,
        result_map: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.items.append(
            Event(
                type=event_type,
                payload=payload,
                message_id=message_id,
                is_final=is_final,
                result_map=dict(result_map or {}),
            )
        )


class QueueEventSink(EventCollector):
    """Event sink backed by an asyncio queue for SSE routes."""

    def __init__(self, queue: Any) -> None:
        super().__init__()
        self._queue = queue

    async def emit(
        self,
        event_type: str,
        payload: Any,
        *,
        message_id: Optional[str] = None,
        is_final: bool = False,
        result_map: Optional[Dict[str, Any]] = None,
    ) -> None:
        await super().emit(
            event_type,
            payload,
            message_id=message_id,
            is_final=is_final,
            result_map=result_map,
        )
        await self._queue.put(self.items[-1])
