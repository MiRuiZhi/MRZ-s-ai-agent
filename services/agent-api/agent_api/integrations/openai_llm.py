from __future__ import annotations

import json
from typing import Any, Dict, List

from agent_api.core.llm import ToolCall, ToolCallResponse


class DemoLLM:
    def __init__(self, agent_name: str, query: str) -> None:
        self.agent_name = agent_name
        self.query = query
        self.planning_turn = 0

    async def ask_tool(self, context: Any, agent_name: str) -> ToolCallResponse:
        role = agent_name or self.agent_name
        if role == "planning":
            if self.planning_turn == 0:
                self.planning_turn += 1
                return ToolCallResponse(content="检索资料<sep>整理报告")
            return ToolCallResponse(content="finish")
        if role == "executor":
            return ToolCallResponse(content=f"已完成：{context.query}")
        return ToolCallResponse(content=f"已收到：{context.query}")


def demo_llm_for(agent_name: str, query: str) -> DemoLLM:
    return DemoLLM(agent_name, query)


class OpenAICompatibleLLM:
    def __init__(self, *, model: str, api_key: str, base_url: str, system_prompt: str = "") -> None:
        self.model = model
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.system_prompt = system_prompt

    async def ask_tool(self, context: Any, agent_name: str) -> ToolCallResponse:
        if not self.api_key:
            return (await demo_llm_for(agent_name, context.query).ask_tool(context, agent_name))

        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=self.api_key, base_url=self.base_url)
        messages: List[Dict[str, Any]] = []
        prompt = self.system_prompt or self._default_system_prompt(agent_name, context)
        messages.append({"role": "system", "content": prompt})
        messages.extend(message.to_openai_dict() for message in context.memory.messages)
        tools = [
            {
                "type": "function",
                "function": {
                    "name": item["name"],
                    "description": item["description"],
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "additionalProperties": True,
                    },
                },
            }
            for item in context.tools.describe_for_llm()
        ]
        response = await client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=tools or None,
            tool_choice="auto" if tools else None,
        )
        choice = response.choices[0]
        message = choice.message
        tool_calls: List[ToolCall] = []
        for raw_call in message.tool_calls or []:
            arguments = raw_call.function.arguments or "{}"
            try:
                parsed_arguments = json.loads(arguments)
            except Exception:
                parsed_arguments = {"raw": arguments}
            tool_calls.append(
                ToolCall(
                    id=raw_call.id,
                    name=raw_call.function.name,
                    arguments=parsed_arguments,
                )
            )
        usage = response.usage
        return ToolCallResponse(
            content=message.content or "",
            tool_calls=tool_calls,
            finish_reason=choice.finish_reason,
            prompt_tokens=getattr(usage, "prompt_tokens", 0) if usage else 0,
            completion_tokens=getattr(usage, "completion_tokens", 0) if usage else 0,
            total_tokens=getattr(usage, "total_tokens", 0) if usage else 0,
        )

    def _default_system_prompt(self, agent_name: str, context: Any) -> str:
        if agent_name == "planning":
            return (
                "你是规划 Agent。把复杂任务拆成可执行步骤；多个可并发步骤用 <sep> 分隔。"
                "当执行结果已经足够完成任务时，只回复 finish。"
            )
        if agent_name == "executor":
            return "你是执行 Agent。围绕当前子任务选择工具，若无需工具则直接给出完成摘要。"
        return "你是 ReAct Agent。根据用户问题选择工具，若无需工具则直接给出最终答案。"
