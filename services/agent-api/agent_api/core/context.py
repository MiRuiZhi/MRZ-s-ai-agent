from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from agent_api.core.events import EventCollector
from agent_api.core.ledger import InMemoryLedger
from agent_api.core.memory import Memory, Message
from agent_api.core.tools import ToolCollection


@dataclass
class AgentContext:
    request_id: str
    session_id: str
    query: str
    events: EventCollector
    ledger: InMemoryLedger
    tools: ToolCollection
    memory: Memory = field(default_factory=Memory)
    entry_agent: Optional[str] = None

    def ensure_user_query_in_memory(self) -> None:
        if len(self.memory) == 0:
            self.memory.add(Message.user(self.query))

    def fork_for_task(self, task: str) -> "AgentContext":
        child_memory = Memory()
        child_memory.extend(list(self.memory.messages))
        child = AgentContext(
            request_id=self.request_id,
            session_id=self.session_id,
            query=task,
            events=self.events,
            ledger=self.ledger,
            tools=self.tools,
            memory=child_memory,
            entry_agent=self.entry_agent,
        )
        child.memory.add(Message.user(task))
        return child
