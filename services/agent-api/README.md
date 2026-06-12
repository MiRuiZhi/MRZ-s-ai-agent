# agent-api

`agent-api` 是 Python + C++ 主链路里的 Agent 编排服务。它负责对外 HTTP/SSE 协议、ReAct/PlanSolve 路由、模型调用、工具调用适配、执行账本和前端工作台所需的兼容 API。

## 目录结构

```text
agent_api
├── api/             # FastAPI app、routes、Pydantic schema
├── core/            # Agent、Memory、Events、Tools、Ledger 接口
├── integrations/    # OpenAI-compatible LLM 和 tool-runtime HTTP client
├── storage/         # SQLAlchemy model、SQL ledger、session factory
├── runtime.py       # 请求转换、Agent 选择、SSE async iterator
├── settings.py      # REACTOR_* 环境变量
└── main.py          # ASGI app 入口
```

## 主要入口

| 路由 | 作用 |
| --- | --- |
| `GET /web/health` | 健康检查 |
| `POST /web/api/v1/gpt/queryAgentStreamIncr` | 前端主 Agent SSE 入口 |
| `POST /AutoAgent` | 内部 AgentRequest 结构入口 |
| `GET /api/agent/conversation/sessions` | 会话列表 |
| `GET /api/agent/conversation/sessions/{session_id}` | 会话详情 |
| `POST /api/agent/file/upload` | 文件上传转发到 tool-runtime |
| `POST /api/agent/image-generation/generate` | 图片生成转发到 tool-runtime |
| `POST /data/chatQuery` | dataAgent SSE 兼容入口 |
| `/api/v1/admin/{resource}/{action:path}` | Admin 通用配置入口 |

## Agent 路由

- `deepThink=0` 或 `agentType=1`：进入 ReAct。
- `deepThink=1` 或 `agentType=2`：进入 PlanSolve。
- SSE 每帧都是 JSON `data:`，结束时关闭连接，不发送非 JSON 哨兵值。

## 关键配置

所有环境变量使用 `REACTOR_` 前缀：

| 变量 | 作用 |
| --- | --- |
| `REACTOR_DATABASE_URL` | SQLAlchemy 数据库连接 |
| `REACTOR_TOOL_RUNTIME_BASE_URL` | tool-runtime 地址 |
| `REACTOR_FAKE_LLM` | 是否使用 fake LLM |
| `REACTOR_OPENAI_BASE_URL` | OpenAI-compatible base URL |
| `REACTOR_OPENAI_API_KEY` | 模型 key |
| `REACTOR_REACT_MODEL` | ReAct 模型 |
| `REACTOR_PLANNER_MODEL` | PlanSolve planner 模型 |
| `REACTOR_EXECUTOR_MODEL` | PlanSolve executor 模型 |
| `REACTOR_LEDGER_BACKEND` | `sql` 或 `memory` |

## 本地测试

```bash
uv run --project services/agent-api \
  python -W error::DeprecationWarning \
  -m unittest discover \
  -s services/agent-api/tests \
  -t services/agent-api \
  -v
```

## 相关文档

- [架构速览](../../docs/architecture/overview.md)
- [详细设计](../../docs/architecture/design.md)
- [使用手册](../../docs/development/usage.md)
- [验证清单](../../docs/development/testing.md)
