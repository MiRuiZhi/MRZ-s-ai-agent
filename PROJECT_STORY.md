# 项目说明与工程复盘

这份文档用于说明 MRZ's AI Agent 的定位、模块职责、技术取舍和表达方式。它不是虚构开发时间线，而是把当前仓库真实的工程结构整理成更容易阅读、复盘和面试讲解的说明。

## 1. 项目定位

MRZ's AI Agent 是一个 Python + C++ AI Agent 运行时，目标是提供一条可运行、可验证、可继续生产化的主链路：

- Agent 对话。
- ReAct 工具调用循环。
- PlanSolve 规划和并发子任务执行。
- SSE 流式输出。
- 工具运行时。
- 文件产物和图片生成。
- MRAG/RAG。
- SQL 执行账本。
- React 前端工作台。
- Docker Compose 单机部署。

当前仓库的对外讲法应该围绕模块和能力展开：`agent-api` 管编排，`tool-runtime` 管工具，`cpp-worker` 管执行边界，`ui/deploy` 管体验和部署。

## 2. 模块职责

### 2.1 agent-api

`services/agent-api` 是主编排服务。

它负责：

- 提供 FastAPI HTTP API。
- 提供主 Agent SSE。
- 接收 `/web/api/v1/gpt/queryAgentStreamIncr` 和 `/AutoAgent` 请求。
- 根据 `deepThink` 或 `agentType` 路由到 ReAct / PlanSolve。
- 调用 OpenAI-compatible 模型。
- 调用 tool-runtime。
- 写入 run、LLM、tool、artifact、session 账本。
- 转发文件上传和图片生成。
- 提供前端需要的会话、角色、Admin 通用配置和 dataAgent 兼容入口。

工程价值：

- API 层、runtime 层、core 层、storage 层分离。
- SSE 每帧是 JSON，前端可以稳定解析。
- 工具失败会记录为 failed，不直接中断整条 Agent 对话。
- 客户端断开 SSE 后后台任务会被取消，避免悬挂任务。

### 2.2 tool-runtime

`reactor-tool` 是工具运行时。

它负责：

- deep search。
- report。
- code interpreter。
- web fetch。
- image generation。
- MRAG/RAG。
- file service 上传、预览、下载。
- 和 C++ worker 集成。

工程价值：

- Agent 编排和工具实现解耦。
- 工具可以独立测试和部署。
- 文件服务只允许访问运行时产物目录内的文件，减少越界预览风险。
- MRAG、文件、图片、网页抓取、代码解释器等路由都有测试保护。

### 2.3 cpp-worker

`services/cpp-worker` 是低层执行边界。

它负责：

- 从 stdin 接收 JSON 请求。
- 校验 `cwd` 是否在允许 root 内。
- 执行受控命令。
- 控制超时。
- 捕获退出码和输出。
- 只回报本次命令新增或改动的文件。
- 计算文件 sha256。

工程价值：

- Python 主编排层不直接承担系统调用细节。
- 低层执行协议清楚，可用单元测试验证。
- 未来可以继续加强白名单、低权限用户、容器隔离和资源限制。

### 2.4 ui 与 deploy

`ui` 是 React + TypeScript 工作台，`deploy` 和 `docker-compose.yml` 提供单机部署闭环。

当前服务列表固定为：

- `mysql`
- `qdrant`
- `tool-runtime`
- `agent-api`
- `ui`
- `nginx`

nginx 统一代理 `/web/*`、`/api/*`、`/data/*`、`/AutoAgent` 和 `/tool/*`，前端可以按同源方式访问后端。

## 3. 关键技术取舍

### 3.1 为什么 Python 做主编排

Python 更适合承担 Agent 系统里的高频变化部分：

- FastAPI 和 SSE 开发效率高。
- Pydantic 适合描述请求、响应和事件结构。
- SQLAlchemy + Alembic 适合管理业务账本。
- OpenAI-compatible SDK 和 LLM 生态成熟。
- `asyncio` 可以自然表达工具并发和 PlanSolve 子任务并发。

### 3.2 为什么保留 C++ 边界组件

C++ 不负责 Agent 智能逻辑，不负责 HTTP、SSE、ORM 或模型调用。

它只负责低层执行边界。这样做的好处是：

- 进程执行、超时、退出码、文件扫描和 hash 的职责清楚。
- Agent 编排层更干净。
- 未来加强沙箱时有明确落点。
- 面试中可以讲清楚语言分工，而不是为了多语言而多语言。

一句话：

> Python 负责让 Agent 会编排、会调用工具、会对外服务；C++ 负责让工具执行边界更清楚、更容易约束。

### 3.3 为什么工具单独成服务

工具运行时的资源特征和 Agent API 不一样：

- 搜索、报告、图片、代码解释器和 MRAG 可能耗时更长。
- 工具依赖更重，失败模式也更多。
- 独立服务更方便限制资源、查看日志和横向扩展。

所以 `agent-api` 只关心工具名、参数、结果和 artifact，不把工具内部细节揉进 Agent 核心。

## 4. 主链路执行过程

### 4.1 ReAct

1. 前端调用 `/web/api/v1/gpt/queryAgentStreamIncr`。
2. `agent-api` 把请求转换成内部 `AgentRequest`。
3. `runtime.py` 根据 `deepThink=0` 路由到 `ReactAgent`。
4. LLM 根据上下文决定是否调用工具。
5. 工具调用并发执行。
6. 工具结果写入 memory、ledger 和 artifact registry。
7. LLM 基于 observation 继续推理。
8. 无工具调用时输出最终 `result` SSE。

### 4.2 PlanSolve

1. `runtime.py` 根据 `deepThink=1` 路由到 `PlanningAgent`。
2. planner 生成计划或子任务。
3. executor 并发执行子任务。
4. 子任务可以继续调用工具。
5. 子任务结果回写 planner memory。
6. planner 判断继续规划或完成。
7. 完成后输出 summary/result SSE。

### 4.3 文件和 artifact

1. 工具产物写入 tool-output volume。
2. tool-runtime 记录文件元数据。
3. agent-api 将 artifact 写入账本。
4. 前端通过文件服务预览或下载。
5. 文件服务会拒绝产物目录外的路径。

## 5. 数据和可观测性

核心账本表语义：

- `dialogue_session_ledger`：会话聚合。
- `dialogue_run_ledger`：一次 Agent 运行。
- `llm_invocation_ledger`：一次模型调用。
- `tool_invocation_ledger`：一次工具调用。
- `artifact_ledger`：一次文件、图片、报告等产物。
- `config_record`：Admin 通用配置持久化。

账本的价值：

- 可以复盘 Agent 为什么这么回答。
- 可以统计模型和工具调用。
- 可以追踪 artifact 来自哪个 run、哪个 tool。
- 可以作为审计、监控和计费的基础。

## 6. 当前边界

已经作为主链路目标保留并验证：

- Agent 对话。
- ReAct。
- PlanSolve。
- SSE JSON。
- 工具调用。
- 文件产物。
- 图片生成。
- MRAG/RAG。
- 前端工作台。
- Docker Compose 部署。

当前不把以下内容作为已完成的生产级能力：

- 完整 NL2SQL/dataAgent。
- Admin 全资源强类型 DTO。
- 正式用户鉴权和权限系统。
- 生产级工具沙箱。
- 完整监控、指标和 tracing。

## 7. 瘦身原则

本仓库按“当前主链路可运行”来决定保留内容：

- 保留 `services/agent-api`、`reactor-tool`、`services/cpp-worker`、`ui`、`deploy`。
- 删除展示样例资产、重复前端锁文件和不参与运行的生成物。
- 前端依赖锁以 `pnpm-lock.yaml` 为准。
- Docker build context 排除文档、缓存、本地工作流目录和非运行资产。

这样仓库入口更清楚，也减少了维护者误判运行依赖的概率。

## 8. 面试表达

一句话：

> 我做的是一个 Python + C++ AI Agent 运行时：`agent-api` 负责 ReAct/PlanSolve 编排、SSE 和执行账本，`tool-runtime` 负责搜索、报告、代码解释器、图片生成和 MRAG/RAG，`cpp-worker` 负责受控执行边界，最后用 React 工作台和 Docker Compose 串成可运行系统。

稍微展开：

> 这个项目的重点不是堆功能名，而是把 Agent 主链路拆清楚。FastAPI 层负责协议和流式输出，core 层负责 Agent 循环，storage 层负责可观测账本，tool-runtime 负责重工具，C++ worker 负责执行边界。ReAct 处理短链路工具任务，PlanSolve 处理复杂任务拆解和并发执行。每次模型调用、工具调用和文件产物都会落账，所以可以复盘一次回答是怎么产生的。

可以重点讲：

- ReAct 和 PlanSolve 的适用场景。
- 工具调用并发与 PlanSolve 子任务并发的区别。
- SSE 为什么坚持 JSON `data:`。
- 账本如何支持回放、审计和排障。
- C++ worker 为什么只做边界，不进入业务编排。
- tool-runtime 为什么独立成服务。

## 9. 简历描述

Python+C++ AI Agent 运行时：使用 FastAPI、Pydantic、SQLAlchemy、Alembic、asyncio 实现 ReAct/PlanSolve 编排、SSE 流式输出、工具调用、执行账本和前端兼容 API；通过 tool-runtime 集成 deep search、report、code interpreter、web fetch、image generation、MRAG/RAG 和文件服务；使用 C++ worker 处理受控命令执行、超时、退出码、stdout/stderr、文件产物扫描和 sha256；使用 Docker Compose 集成 MySQL、Qdrant、agent-api、tool-runtime、React UI 和 nginx，并补充测试、架构文档和部署说明。
