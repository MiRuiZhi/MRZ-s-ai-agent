from __future__ import annotations

import asyncio
import uuid
from typing import AsyncIterator, Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from agent_api.api.schemas import AgentRequest, GptQueryRequest
from agent_api.core.agents import PlanSolveAgent, ReactAgent
from agent_api.core.context import AgentContext
from agent_api.core.events import Event, QueueEventSink
from agent_api.core.ledger import InMemoryLedger
from agent_api.core.tools import ToolCollection
from agent_api.integrations.openai_llm import OpenAICompatibleLLM, demo_llm_for
from agent_api.integrations.tool_runtime import ToolRuntimeClient, register_tool_runtime_tools
from agent_api.settings import Settings
from agent_api.storage.ledger import SqlAlchemyLedger


class AgentRuntime:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.sql_engine = None
        self.ledger = self._create_ledger()

    def convert_gpt_query(self, request: GptQueryRequest) -> AgentRequest:
        request_id = request.trace_id or request.request_id or str(uuid.uuid4())
        agent_type = 2 if request.deep_think else 1
        return AgentRequest(
            requestId=request_id,
            sessionId=request.session_id,
            visitorId=None,
            erp=request.user or "reactor",
            query=request.query,
            agentType=agent_type,
            isStream=True,
            sessionFiles=request.session_files,
            outputStyle=request.output_style,
            aiAgentId=request.ai_agent_id,
        )

    async def stream_agent(self, request: AgentRequest) -> AsyncIterator[Event]:
        queue: asyncio.Queue[Optional[Event]] = asyncio.Queue()
        events = QueueEventSink(queue)
        tools = ToolCollection()
        register_tool_runtime_tools(tools, ToolRuntimeClient(self.settings.tool_runtime_base_url))
        context = AgentContext(
            request_id=request.request_id,
            session_id=request.session_id,
            query=request.query,
            events=events,
            ledger=self.ledger,
            tools=tools,
        )

        async def run_agent() -> None:
            try:
                if request.agent_type == 2:
                    planner_llm = self._llm("planning", request.query, self.settings.planner_model)
                    executor_llm = self._llm("executor", request.query, self.settings.executor_model)
                    await PlanSolveAgent(
                        context=context,
                        planner_llm=planner_llm,
                        executor_llm=executor_llm,
                        max_steps=self.settings.max_steps,
                        max_parallel_tasks=self.settings.max_parallel_tasks,
                    ).run()
                else:
                    await ReactAgent(
                        context=context,
                        llm=self._llm("react", request.query, self.settings.react_model),
                        max_steps=self.settings.max_steps,
                    ).run()
            except Exception as exc:
                await events.emit("result", {"taskSummary": "", "errorMsg": str(exc)}, is_final=True)
            finally:
                await queue.put(None)

        task = asyncio.create_task(run_agent())
        try:
            while True:
                item = await queue.get()
                if item is None:
                    break
                yield item
        finally:
            if not task.done():
                task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

    def _llm(self, agent_name: str, query: str, model: str):
        if self.settings.fake_llm or not self.settings.openai_api_key:
            return demo_llm_for(agent_name, query)
        return OpenAICompatibleLLM(
            model=model,
            api_key=self.settings.openai_api_key,
            base_url=self.settings.openai_base_url,
        )

    def _create_ledger(self):
        if self.settings.ledger_backend.lower() != "sql":
            return InMemoryLedger()
        connect_args = {}
        if self.settings.database_url.startswith("sqlite"):
            connect_args["check_same_thread"] = False
        self.sql_engine = create_engine(
            self.settings.database_url,
            pool_pre_ping=True,
            connect_args=connect_args,
        )
        session_factory = sessionmaker(
            bind=self.sql_engine,
            autoflush=False,
            autocommit=False,
            expire_on_commit=False,
        )
        return SqlAlchemyLedger(session_factory)
