import asyncio
import unittest

from agent_api.core.agents import PlanSolveAgent, ReactAgent
from agent_api.core.context import AgentContext
from agent_api.core.events import EventCollector
from agent_api.core.ledger import InMemoryLedger
from agent_api.core.llm import ScriptedLLM, ToolCall, ToolCallResponse
from agent_api.core.tools import ToolCollection, ToolResult


class AgentCoreTest(unittest.IsolatedAsyncioTestCase):
    async def test_react_agent_executes_tool_and_records_ledger(self):
        events = EventCollector()
        ledger = InMemoryLedger()
        tools = ToolCollection()

        async def echo_tool(arguments, context):
            return ToolResult(
                tool_result=f"echo:{arguments['text']}",
                llm_observation=f"observed:{arguments['text']}",
            )

        tools.add_local_tool("echo", "Echo input text", echo_tool)
        llm = ScriptedLLM(
            [
                ToolCallResponse(
                    content="I should call echo.",
                    tool_calls=[
                        ToolCall(
                            id="call-1",
                            name="echo",
                            arguments={"text": "hello"},
                        )
                    ],
                ),
                ToolCallResponse(content="Final answer from ReAct.", tool_calls=[]),
            ]
        )
        context = AgentContext(
            request_id="req-react",
            session_id="session-1",
            query="say hello",
            events=events,
            ledger=ledger,
            tools=tools,
        )

        result = await ReactAgent(context=context, llm=llm, max_steps=4).run()

        self.assertEqual(result, "Final answer from ReAct.")
        self.assertEqual(context.memory.last.content, "Final answer from ReAct.")
        self.assertEqual(len(ledger.tool_invocations), 1)
        self.assertEqual(ledger.tool_invocations[0].tool_name, "echo")
        self.assertEqual(ledger.tool_invocations[0].status, "success")
        emitted_types = [event.type for event in events.items]
        self.assertIn("tool_thought", emitted_types)
        self.assertIn("tool_call", emitted_types)
        self.assertIn("result", emitted_types)

    async def test_plan_solve_runs_parallel_subtasks_and_summarizes(self):
        events = EventCollector()
        ledger = InMemoryLedger()
        tools = ToolCollection()
        planner = ScriptedLLM(
            [
                ToolCallResponse(content="search web<sep>write report", tool_calls=[]),
                ToolCallResponse(content="finish", tool_calls=[]),
            ]
        )
        executor = ScriptedLLM(
            [
                ToolCallResponse(content="completed search web", tool_calls=[]),
                ToolCallResponse(content="completed write report", tool_calls=[]),
            ]
        )
        context = AgentContext(
            request_id="req-plan",
            session_id="session-1",
            query="research and report",
            events=events,
            ledger=ledger,
            tools=tools,
        )

        result = await PlanSolveAgent(
            context=context,
            planner_llm=planner,
            executor_llm=executor,
            max_steps=3,
            max_parallel_tasks=2,
        ).run()

        self.assertIn("completed search web", result)
        self.assertIn("completed write report", result)
        self.assertIn("research and report", result)
        task_events = [event for event in events.items if event.type == "task"]
        self.assertEqual([event.payload for event in task_events], ["search web", "write report"])
        self.assertEqual(ledger.runs[0].status, "success")


if __name__ == "__main__":
    unittest.main()
