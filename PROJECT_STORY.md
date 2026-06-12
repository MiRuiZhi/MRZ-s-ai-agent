# 项目演进说明

这份文档用于说明这个仓库为什么要重构、重构时做了哪些技术取舍、每个部分承担什么职责，以及在面试中应该如何讲清楚。

它的定位不是伪造开发时间线，而是把真实的工程思路整理成容易阅读、容易复盘、容易表达的作品集说明。

## 1. 项目背景

原始项目是一个 Java 技术栈的 Agent 后端，里面包含了很多值得学习的业务设计：

- ReAct：模型在推理过程中选择工具、调用工具、观察结果，再继续推理。
- PlanSolve：先规划任务，再把复杂任务拆成可执行子任务，最后汇总结果。
- SSE：通过流式事件把 Agent 的中间过程和最终结果返回给前端。
- 工具系统：包含 deep search、report、code interpreter、web fetch、image generation、data analysis、MRAG 等能力。
- 执行账本：记录 run、LLM invocation、tool invocation、artifact 等运行过程。
- 前端工作台：已有 React UI，可以承载对话、工具结果和文件产物展示。

这个项目的问题不在业务想法，而在学习门槛。对于主要使用 Python 和 C++ 的学习者来说，Java 多模块工程、Spring 风格分层、DTO/PO/DAO、配置和依赖链路会拉高理解成本。

所以这次重构的目标是：保留原项目有价值的 Agent 业务语义，同时把主链路改造成 Python + C++ 技术栈，让它更适合学习、调试、部署和面试讲解。

## 2. 重构目标

这次重构不是逐行翻译旧后端，而是做生产替代版的技术重建。

核心目标：

- 保留 `ReAct` 和 `PlanSolve` 两个核心 Agent 模式。
- 保留原有 React 前端，不重写 UI。
- 保留并整理原有 `reactor-tool`，最大化复用工具能力。
- 用 FastAPI 替代历史 Controller，提供兼容的 API 和 SSE 输出。
- 用 SQLAlchemy + Alembic 重建数据库 schema 和迁移。
- 用 `asyncio` 实现工具调用、PlanSolve 子任务和 `<sep>` 子任务的并发。
- 用 C++ worker 承担受控执行边界，避免 Python 主后端直接做低层命令执行。
- 用 Docker Compose 提供单机启动方案，方便本地学习和后续上线。
- 补充中文设计文档、使用手册、架构图、面试材料和变更记录。

## 3. 总体技术路线

最终形成的是“两服务内聚 + 一个边缘执行组件”的架构。

### 3.1 agent-api

`services/agent-api` 是主后端，使用 Python 技术栈：

- FastAPI：提供 HTTP API、SSE 和兼容路由。
- Pydantic：定义请求、响应、SSE 事件和工具调用 schema。
- SQLAlchemy：定义会话、run、LLM 调用、工具调用、artifact、配置记录等数据模型。
- Alembic：管理数据库迁移。
- asyncio：实现 Agent 主循环、并发工具调用和并发子任务执行。

它负责“业务编排”：

- 接收前端请求。
- 判断 `deepThink=0` 还是 `deepThink=1`。
- 路由到 ReAct 或 PlanSolve。
- 调用 LLM。
- 调用工具运行时。
- 生成 SSE 事件。
- 记录执行账本。
- 返回最终结果。

### 3.2 tool-runtime

`reactor-tool` 是工具运行时，保留并整理原有 Python 工具能力：

- deep search
- report
- code interpreter
- web fetch
- file service
- image generation
- data analysis
- MRAG

它负责“工具能力”，不负责 Agent 主循环。

这样做的好处是：

- Agent 编排和工具实现解耦。
- 工具可以独立扩展和测试。
- 原有工具资产可以继续复用。
- 后续如果要把工具服务部署到单独机器，也不需要大改 agent-api。

### 3.3 cpp-worker

`services/cpp-worker` 是 C++ JSON-over-stdin worker。

它不承担 LLM、HTTP、SSE、ORM 或 Agent 业务逻辑，只做低层执行边界：

- 接收 JSON 请求。
- 校验工作目录是否在允许的 root 下。
- 执行受控命令。
- 控制超时时间。
- 捕获退出码。
- 捕获 stdout/stderr。
- 扫描执行目录下的文件产物。
- 计算文件 sha256。
- 输出统一 JSON 结果。

这个设计体现的是职责分离：

- Python 负责可读性、业务表达、异步编排和生态适配。
- C++ 负责更靠近系统层的执行边界。

## 4. 为什么不是全部用 Python

全部用 Python 也能实现，但是这次故意保留一个 C++ 边缘组件，原因是：

- 面试中可以讲清楚“语言分工”，不是为了用 C++ 而用 C++。
- C++ 更适合表达低层执行、进程退出码、文件扫描、hash 等边界能力。
- Python 主后端不需要直接接触太多系统调用细节，业务层更干净。
- 后续如果要加强沙箱、资源限制、隔离策略，C++ worker 是一个更自然的扩展点。

需要强调的是，C++ 在这里不是 Agent 大脑，而是工具运行层的一段执行边界。

一句话：

> Python 负责让 Agent 会思考、会编排、会对外服务；C++ 负责让工具执行更可控、更清楚、更容易约束。

## 5. 为什么删除 Java 源码

重构早期曾保留 `Reactor-agent-*` Java 模块，主要用于迁移对照：

- 对照 Controller 到 FastAPI route 的迁移方式。
- 对照 domain/case/infrastructure 分层到 Python api/core/storage 分层。
- 对照 DTO/PO/DAO 到 Pydantic/SQLAlchemy 的表达方式。
- 说明这个项目不是凭空写 demo，而是基于已有复杂系统抽取业务语义后重建。

当前阶段已经不再需要把 Java 源码留在工作树里。保留大量 Java 会让仓库语言结构、学习入口和作品集表达变得混乱，也会让不熟悉 Java 的维护者误以为运行链路仍依赖 Spring Boot。

因此仓库主线改成：

- 工作树只保留 Python + C++ + React UI 的可运行代码。
- Java/Maven 后端源码从当前分支删除。
- 历史对照依据保存在 Git 历史中。
- 本仓库目标是主链路能力完整：Agent 对话、ReAct、PlanSolve、SSE、工具调用、文件产物、图片生成、MRAG/RAG、前端工作台和 Docker 部署。
- 旧 Java Admin/DataAgent 全量接口不再作为逐项等价迁移目标；当前只保留前端实际需要的兼容入口和可运行主链路。

## 6. 关键业务链路

### 6.1 ReAct 链路

ReAct 适合短链路、工具驱动型任务。

执行过程：

1. 前端调用 `/web/api/v1/gpt/queryAgentStreamIncr`。
2. 请求进入 `agent-api`。
3. `runtime.py` 根据 `deepThink=0` 路由到 `ReactAgent`。
4. `ReactAgent` 把用户问题、会话记忆和工具描述发给 LLM。
5. LLM 如果返回 tool call，Agent 并发调用 `ToolCollection`。
6. 工具结果写入 memory、ledger 和 artifact registry。
7. Agent 再次调用 LLM，让模型基于观察结果继续推理。
8. 如果模型返回最终答案，SSE 输出 `result`。
9. 如果超过最大步数，输出受控的终止结果。

这个链路体现的是：模型不是一次性回答，而是在工具观察中逐步逼近答案。

### 6.2 PlanSolve 链路

PlanSolve 适合复杂任务，例如报告、分析、方案规划。

执行过程：

1. 请求进入 `agent-api`。
2. `runtime.py` 根据 `deepThink=1` 路由到 `PlanningAgent`。
3. planner LLM 先生成计划。
4. 如果计划里有多个子任务，用 `<sep>` 或结构化任务拆分。
5. `ExecutorAgent` 并发执行子任务。
6. 每个子任务可以继续调用工具。
7. 子任务结果返回给 planner memory。
8. planner 判断是否继续规划。
9. 完成后由 summary/result 事件输出最终答案。

这个链路体现的是：复杂任务先拆解，再并发执行，再汇总。

## 7. SSE 协议设计

SSE 统一使用 JSON data。

事件类型包括：

- `plan_thought`
- `tool_thought`
- `tool_call`
- `tool_result`
- `task`
- `plan`
- `task_summary`
- `result`
- `heartbeat`

这样设计的原因：

- 前端只需要统一 `JSON.parse`。
- ReAct 和 PlanSolve 都可以复用同一套事件通道。
- 调试时可以直接看每一帧事件。
- 后续可以把事件直接落入运行账本或可观测系统。

## 8. 数据层设计

数据层使用 MySQL 8，迁移使用 Alembic。

核心表语义：

- session：会话。
- run：一次 Agent 运行。
- llm_invocation：一次 LLM 调用。
- tool_invocation：一次工具调用。
- artifact：一次文件、图片、报告等产物。
- config_record：Admin 通用配置记录。
- visitor/admin_user/ai_agent/ai_client/model/system_prompt/mcp/rag_order/draw_config/chat_model_info：保留原项目语义的配置类数据。

执行账本的价值：

- 可以复盘一次 Agent 为什么这么回答。
- 可以统计 LLM 调用和工具调用。
- 可以追踪 artifact 从哪个 run、哪个 tool 来。
- 可以为后续计费、审计、监控和调试做基础。

## 9. 工具系统设计

工具系统分为三层：

1. `ToolCollection`：Agent 层看到的工具集合。
2. `ToolRuntimeClient`：agent-api 调用 tool-runtime 的 HTTP adapter。
3. `reactor-tool`：真实工具实现。

这样设计后，Agent 不关心工具内部是搜索、代码解释器、文件服务还是 MRAG。

Agent 只关心：

- 工具叫什么。
- 参数是什么。
- 返回结果是什么。
- 有没有 artifact。
- 是否需要写 ledger。

## 10. 部署设计

单机 Docker Compose 包含：

- nginx
- ui
- agent-api
- tool-runtime
- mysql
- qdrant

nginx 统一入口：

- `/` 到 React UI。
- `/web/*` 到 agent-api。
- `/api/*` 到 agent-api。
- `/tool/*` 到 tool-runtime。

好处：

- 前端不用处理复杂跨域。
- 本地和服务器部署路径一致。
- 后续上 HTTPS 只需要收敛在 nginx。

## 11. 项目瘦身

瘦身原则是：删除生成物、无关二进制和不再参与主线的旧后端源码，保留运行价值和讲解价值。

已删除：

- Python 虚拟环境 `.venv`。
- Python 编译缓存。
- `.DS_Store`。
- `.codegraph`。
- Windows-only 小红书 MCP `.exe`。
- 旧 Java/Maven 后端源码与根 `pom.xml`。
- 依赖旧 Java jar 打包方式的 `fill-payload.ps1`。

保留：

- React UI：实际前端。
- reactor-tool：工具运行时。
- agent-api：Python 主后端。
- cpp-worker：C++ 执行边界。

## 12. 面试表达方式

### 12.1 一句话版本

我把一个 Java 多智能体项目重构成 Python+C++ 技术栈，保留 ReAct、PlanSolve、工具调用、SSE、执行账本和前端工作台，用 FastAPI 承担 Agent 编排，用 C++ worker 承担受控执行边界，并补齐了 Docker Compose、数据库迁移、文档和测试。

### 12.2 两分钟版本

这个项目最开始是 Java 技术栈，业务设计很好，但学习和调试成本比较高。我做的事情不是简单翻译代码，而是先抽取核心业务语义：ReAct、PlanSolve、SSE、工具系统、执行账本和 artifact 管理。

然后我把主后端拆成 Python FastAPI 的 `agent-api`，把 Agent 编排、SSE、SQLAlchemy 账本、Alembic 迁移和 Admin 兼容接口都集中在这里。原有 `reactor-tool` 没有丢掉，而是作为工具运行时继续提供 deep search、report、code interpreter、web fetch、image generation 和 MRAG。对于脚本执行这种更底层的能力，我没有放在 Python 业务层里，而是做了一个 C++ JSON worker，用来处理超时、退出码、stdout/stderr、文件产物扫描和 sha256。

最后我保留 React 前端，通过 nginx 做同源代理，用 Docker Compose 把 mysql、qdrant、agent-api、tool-runtime、ui 串起来。这个项目可以用 fake LLM 先跑通全链路，也可以接 OpenAI-compatible 模型。

### 12.3 简历写法

可以写成：

```text
AI Agent 后端重构项目：将 Java 多智能体项目迁移为 Python+C++ 技术栈，使用 FastAPI、Pydantic、SQLAlchemy、Alembic、asyncio 实现 ReAct/PlanSolve 编排、SSE 流式输出、工具调用、执行账本和 Admin 兼容接口；复用 reactor-tool 工具运行时，并新增 C++ worker 处理受控命令执行、超时、stdout/stderr、文件产物扫描和 sha256；使用 Docker Compose 集成 MySQL、Qdrant、agent-api、tool-runtime 和 React UI，补充中文架构文档、使用手册和测试。
```

## 13. 可以继续迭代的方向

这个项目后续可以继续增强：

- 强化 dataAgent/NL2SQL。
- Admin DTO 做成强类型 schema。
- 增加正式登录、鉴权和权限控制。
- 给 tool-runtime 增加更强的沙箱隔离。
- 增加 OpenTelemetry tracing。
- 增加 Prometheus metrics。
- 增加 GitHub Actions CI。
- 增加更完整的 E2E 测试。
- 把文件产物从本地 volume 替换成 S3/OSS。

这些方向可以在面试中作为“我知道当前边界，也知道下一步怎么生产化”的补充说明。
