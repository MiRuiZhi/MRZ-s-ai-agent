# Reactor Agent Python+C++ 重构架构说明

## 目标

这个重构版把原 Java Spring Boot 后端拆成两个内聚服务：

- `agent-api`：Python FastAPI 服务，负责 HTTP/SSE、Agent 编排、会话、账本、管理接口兼容。
- `tool-runtime`：复用原有 `reactor-tool` Python 工具服务，负责 deep search、report、code interpreter、image generation、MRAG 等工具。

C++ 不负责 LLM、SSE、ORM 这些 Python 生态更成熟的部分，只负责低层边界能力，例如进程执行、超时控制、stdout/stderr 捕获、产物扫描和文件哈希。

## Java 到 Python/C++ 映射

| Java 模块 | 新位置 | 说明 |
| --- | --- | --- |
| `Reactor-agent-trigger` | `services/agent-api/agent_api/api` | FastAPI 路由兼容原 Controller |
| `Reactor-agent-case` | `services/agent-api/agent_api/runtime.py` | 请求转换、策略路由、SSE 编排 |
| `Reactor-agent-domain/runtime` | `services/agent-api/agent_api/core` | ReAct、PlanSolve、Memory、ToolCollection |
| `Reactor-agent-infrastructure` | `services/agent-api/agent_api/storage` | SQLAlchemy 模型与 Alembic migration |
| `reactor-tool` | `reactor-tool` | 原 Python 工具服务继续保留 |
| Java `CompletableFuture` 工具并发 | `asyncio.gather` | 工具调用和 PlanSolve 子任务并发 |
| Java `SseEmitter` | FastAPI `StreamingResponse` | 输出 `data: JSON` SSE |
| Java 执行账本 | `dialogue_*_ledger` 等表 | 保留 run、LLM、tool、artifact 事实 |

## 两个 Agent 模式

### ReAct

```mermaid
flowchart TD
    A["AgentContext"] --> B["ReactAgent.run"]
    B --> C["LLM askTool"]
    C --> D{"tool_calls?"}
    D -->|yes| E["ToolCollection execute concurrently"]
    E --> F["ledger + tool_call events + memory observation"]
    F --> C
    D -->|no| G["result event + finish run"]
```

### PlanSolve

```mermaid
flowchart TD
    A["AgentContext"] --> B["Planning LLM"]
    B --> C{"finish?"}
    C -->|no| D["split by <sep>"]
    D --> E["Executor subtasks via asyncio.gather"]
    E --> F["merge results into planner memory"]
    F --> B
    C -->|yes| G["summary + result event"]
```

## 面试讲法

1. 先讲边界：Python 管编排，C++ 管低层执行，tool-runtime 管重工具。
2. 再讲可观测性：每次 run、LLM 调用、tool 调用、artifact 都落账，历史回放不靠日志。
3. 再讲稳定性：ReAct 适合短链路，PlanSolve 适合复杂任务；PlanSolve 子任务可并发，工具调用也可并发。
4. 最后讲迁移策略：不是逐行翻译 Java，而是保留业务协议和核心运行时语义，用目标技术栈重建边界。

