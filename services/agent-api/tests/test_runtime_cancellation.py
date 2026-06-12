import asyncio
import unittest
from unittest.mock import patch

from agent_api.api.schemas import AgentRequest
from agent_api.core.llm import ScriptedLLM, ToolCall, ToolCallResponse
from agent_api.core.tools import ToolResult
from agent_api.runtime import AgentRuntime
from agent_api.settings import Settings


class RuntimeCancellationTest(unittest.IsolatedAsyncioTestCase):
    async def test_stream_close_cancels_background_agent_task(self):
        runtime = AgentRuntime(Settings(fake_llm=True, ledger_backend="memory"))
        tool_started = asyncio.Event()

        async def slow_tool(arguments, context):
            tool_started.set()
            await asyncio.sleep(10)
            return ToolResult(tool_result="slow complete")

        def register_slow_tool(tools, client):
            tools.add_local_tool("slow", "Slow tool", slow_tool)

        scripted_llm = ScriptedLLM(
            [
                ToolCallResponse(
                    content="I should call slow.",
                    tool_calls=[ToolCall(id="call-slow", name="slow", arguments={})],
                ),
                ToolCallResponse(content="done", tool_calls=[]),
            ]
        )

        with patch("agent_api.runtime.register_tool_runtime_tools", register_slow_tool):
            with patch.object(runtime, "_llm", return_value=scripted_llm):
                stream = runtime.stream_agent(
                    AgentRequest(
                        requestId="req-cancel",
                        sessionId="session-cancel",
                        query="cancel me",
                        agentType=1,
                    )
                )
                await stream.__anext__()
                await asyncio.wait_for(tool_started.wait(), timeout=1)
                await asyncio.wait_for(stream.aclose(), timeout=0.2)


if __name__ == "__main__":
    unittest.main()
