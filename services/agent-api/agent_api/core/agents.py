from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import List

from agent_api.core.context import AgentContext
from agent_api.core.llm import ToolCall, ToolCapableLLM, ToolCallResponse
from agent_api.core.memory import Message
from agent_api.core.tools import ToolResult


@dataclass
class BaseAgent:
    context: AgentContext
    llm: ToolCapableLLM
    name: str
    max_steps: int = 10

    async def _ask_tool(self, step_no: int) -> ToolCallResponse:
        response = await self.llm.ask_tool(self.context, self.name)
        self.context.ledger.record_llm(
            self.context,
            agent_name=self.name,
            step_no=step_no,
            call_kind="askTool",
            response_text=response.content,
            tool_call_count=len(response.tool_calls),
        )
        return response

    async def _execute_tool_call(self, tool_call: ToolCall, step_no: int) -> ToolResult:
        provider = self.context.tools.provider_for(tool_call.name)
        ledger_record = self.context.ledger.start_tool(
            self.context,
            tool_call_id=tool_call.id,
            tool_name=tool_call.name,
            provider=provider,
            input_json=tool_call.arguments,
            agent_name=self.name,
            step_no=step_no,
        )
        await self.context.events.emit(
            "tool_call",
            {
                "messageType": "tool_call",
                "status": "running",
                "toolName": tool_call.name,
                "toolCallId": tool_call.id,
                "toolProvider": provider,
                "input": tool_call.arguments,
                "summary": f"正在调用 {tool_call.name}",
                "isFinal": False,
            },
            message_id=tool_call.id,
            is_final=False,
        )
        try:
            result = await self.context.tools.execute(tool_call.name, tool_call.arguments, self.context)
        except Exception as exc:
            result = ToolResult(
                tool_result=f"Tool {tool_call.name} Error.",
                llm_observation=f"Tool {tool_call.name} Error: {exc}",
                failed=True,
                error_msg=str(exc),
            )
        status = "failed" if result.failed else "success"
        self.context.ledger.finish_tool(
            ledger_record,
            status=status,
            observation=result.observation,
            error_msg=result.error_msg,
        )
        self.context.ledger.record_artifacts(self.context, tool_call.id, result.files)
        await self.context.events.emit(
            "tool_call",
            {
                "messageType": "tool_call",
                "status": status,
                "toolName": tool_call.name,
                "toolCallId": tool_call.id,
                "toolProvider": provider,
                "input": tool_call.arguments,
                "summary": f"{tool_call.name} 调用完成" if status == "success" else f"{tool_call.name} 调用失败",
                "errorMsg": result.error_msg,
                "isFinal": True,
            },
            message_id=tool_call.id,
            is_final=True,
        )
        return result


class ReactAgent(BaseAgent):
    def __init__(self, context: AgentContext, llm: ToolCapableLLM, max_steps: int = 10) -> None:
        super().__init__(context=context, llm=llm, name="react", max_steps=max_steps)

    async def run(self) -> str:
        self.context.entry_agent = "react"
        self.context.ledger.begin_run(self.context, "react")
        self.context.ensure_user_query_in_memory()
        try:
            for step_no in range(1, self.max_steps + 1):
                response = await self._ask_tool(step_no)
                if response.tool_calls and response.content:
                    await self.context.events.emit("tool_thought", response.content)

                self.context.memory.add(Message.assistant(response.content, response.tool_calls))
                if not response.tool_calls:
                    await self.context.events.emit("result", {"taskSummary": response.content}, is_final=True)
                    self.context.ledger.finish_run(self.context, "success", response.content)
                    return response.content

                results = await asyncio.gather(
                    *[self._execute_tool_call(call, step_no) for call in response.tool_calls]
                )
                for call, result in zip(response.tool_calls, results):
                    self.context.memory.add(Message.tool(result.observation, call.id))
                    await self.context.events.emit(
                        "tool_result",
                        {
                            "toolName": call.name,
                            "toolParam": call.arguments,
                            "toolResult": result.tool_result,
                            "toolCallId": call.id,
                        },
                    )
            summary = f"Terminated: Reached max steps ({self.max_steps})"
            await self.context.events.emit("result", {"taskSummary": summary}, is_final=True)
            self.context.ledger.finish_run(self.context, "stopped", summary)
            return summary
        except asyncio.CancelledError:
            self.context.ledger.finish_run(self.context, "stopped", "请求已取消")
            raise
        except Exception as exc:
            self.context.ledger.finish_run(self.context, "failed", error_msg=str(exc))
            raise


class _ExecutorAgent(BaseAgent):
    def __init__(self, context: AgentContext, llm: ToolCapableLLM, max_steps: int = 5) -> None:
        super().__init__(context=context, llm=llm, name="executor", max_steps=max_steps)

    async def run(self) -> str:
        for step_no in range(1, self.max_steps + 1):
            response = await self._ask_tool(step_no)
            if response.tool_calls and response.content:
                await self.context.events.emit("tool_thought", response.content)
            self.context.memory.add(Message.assistant(response.content, response.tool_calls))
            if not response.tool_calls:
                await self.context.events.emit("task_summary", {"taskSummary": response.content})
                return response.content
            results = await asyncio.gather(
                *[self._execute_tool_call(call, step_no) for call in response.tool_calls]
            )
            for call, result in zip(response.tool_calls, results):
                self.context.memory.add(Message.tool(result.observation, call.id))
        return f"Terminated: Reached max steps ({self.max_steps})"


class PlanSolveAgent:
    def __init__(
        self,
        context: AgentContext,
        planner_llm: ToolCapableLLM,
        executor_llm: ToolCapableLLM,
        max_steps: int = 10,
        max_parallel_tasks: int = 2,
    ) -> None:
        self.context = context
        self.planner = BaseAgent(context=context, llm=planner_llm, name="planning", max_steps=max_steps)
        self.executor_llm = executor_llm
        self.max_steps = max_steps
        self.max_parallel_tasks = max_parallel_tasks

    async def run(self) -> str:
        self.context.entry_agent = "plan_solve"
        self.context.ledger.begin_run(self.context, "plan_solve")
        self.context.ensure_user_query_in_memory()
        accumulated_results: List[str] = []
        try:
            for step_no in range(1, self.max_steps + 1):
                plan = await self.planner._ask_tool(step_no)
                await self.context.events.emit("plan_thought", plan.content)
                if plan.content.strip().lower() == "finish":
                    summary = self._build_summary(accumulated_results)
                    await self.context.events.emit("result", {"taskSummary": summary}, is_final=True)
                    self.context.ledger.finish_run(self.context, "success", summary)
                    return summary

                tasks = self._split_tasks(plan.content)
                await self.context.events.emit(
                    "plan",
                    {
                        "currentStep": plan.content,
                        "steps": tasks,
                        "stepStatus": ["pending" for _ in tasks],
                    },
                )
                for task in tasks:
                    await self.context.events.emit("task", task)
                task_results = await self._run_tasks(tasks)
                accumulated_results.extend(task_results)
                self.context.memory.add(Message.tool("\n".join(task_results), f"planner-step-{step_no}"))

            summary = f"Terminated: Reached max steps ({self.max_steps})"
            await self.context.events.emit("result", {"taskSummary": summary}, is_final=True)
            self.context.ledger.finish_run(self.context, "stopped", summary)
            return summary
        except asyncio.CancelledError:
            self.context.ledger.finish_run(self.context, "stopped", "请求已取消")
            raise
        except Exception as exc:
            self.context.ledger.finish_run(self.context, "failed", error_msg=str(exc))
            raise

    async def _run_tasks(self, tasks: List[str]) -> List[str]:
        semaphore = asyncio.Semaphore(self.max_parallel_tasks)

        async def run_one(task: str) -> str:
            async with semaphore:
                child_context = self.context.fork_for_task(f"你的任务是：{task}")
                return await _ExecutorAgent(child_context, self.executor_llm, max_steps=self.max_steps).run()

        return await asyncio.gather(*[run_one(task) for task in tasks])

    @staticmethod
    def _split_tasks(value: str) -> List[str]:
        return [item.strip() for item in value.split("<sep>") if item.strip()]

    def _build_summary(self, results: List[str]) -> str:
        joined = "\n".join(results)
        return f"Query: {self.context.query}\n{joined}".strip()
