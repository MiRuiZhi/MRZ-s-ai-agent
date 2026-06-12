# 变更记录

本文件按模块整理项目阶段变化，重点记录当前 Python+C++ 主链路的能力、边界和工程化改进。

这里记录的是功能阶段，不伪造开发日期。

## v0.9 文档信息架构与部署说明整理

目标：让读者更快理解项目目录、模块职责、部署方式和验证路径。

repo/docs：

- 新增 `docs/README.md` 作为详细文档导航。
- 新增 `docs/architecture/repository-map.md` 说明仓库结构和推荐阅读顺序。
- 新增 `docs/development/testing.md` 作为主链路验证清单。
- 将详细设计、使用手册、部署说明、项目复盘和面试提纲收进 `docs/` 分区。

modules：

- 新增 `services/README.md` 说明后端服务分工。
- 新增 `services/cpp-worker/README.md` 说明 C++ worker 边界、协议和验证方式。
- 扩充 `services/agent-api/README.md`、`reactor-tool/README.md`、`ui/README.md`，让每个主模块都有独立入口。

deploy：

- 扩充单机 Docker 部署说明，补充服务拓扑、初始化、真实模型配置、部署验证、日志、重启、备份和排障。

## v0.8 运行边界与仓库瘦身

目标：让主链路更稳、更小、更容易理解。

agent-api：

- 工具调用异常会被记录为 failed tool invocation，并把 observation 写回 memory，ReAct 可以继续生成最终回复。
- SSE 客户端断开时会取消后台 Agent task，避免长时间悬挂。
- 生产环境拒绝 wildcard CORS 配置。

tool-runtime：

- 文件预览和下载限制在运行时产物目录内，拒绝越界路径。
- 文件服务测试覆盖嵌套文件名、兼容查询和越界拒绝。

cpp-worker：

- `collectFiles=true` 时只回报本次命令新增或改动的文件。
- 单测覆盖文件产物过滤、hash 和工作目录越界拒绝。

repo/ui：

- 删除展示样例资产。
- 删除重复的 `ui/package-lock.json`，前端依赖锁以 `pnpm-lock.yaml` 为准。
- `.gitignore` 和 `.dockerignore` 改为当前模块口径。

## v0.7 Python+C++ 主线收敛

目标：让仓库结构和运行链路保持一致，降低理解成本。

模块变化：

- `agent-api` 作为唯一 Agent 编排服务。
- `tool-runtime` 作为唯一工具 HTTP 服务。
- `cpp-worker` 作为受控执行边界。
- `ui` 作为前端工作台。
- Docker Compose 服务列表固定为 `mysql/qdrant/tool-runtime/agent-api/ui/nginx`。

保留能力：

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

边界：

- dataAgent/NL2SQL 仍是后续强化方向。
- Admin 使用通用配置表承接前端所需配置流，后续可按资源拆强类型 DTO。

## v0.6 文档与作品集表达

目标：让仓库更适合阅读、复盘和面试讲解。

新增与更新：

- `README.md`：项目入口、模块概览、快速开始、测试命令和文档导航。
- `docs/README.md`：详细文档索引。
- `docs/project/story.md`：工程复盘、模块职责、技术取舍和表达提纲。
- `CHANGELOG.md`：按模块记录阶段变化。
- `docs/architecture/design.md`：服务边界、Agent 循环、数据模型、SSE、工具和部署细节。
- `docs/development/usage.md`：运行、配置、接口、开发和排障说明。
- `docs/development/testing.md`：验证清单。
- `docs/project/interview-notes.md`：面试讲解提纲。

## v0.5 架构、使用与部署说明

目标：让项目不只是能跑，还能被清楚解释和部署。

覆盖内容：

- 本地 Docker Compose 启动。
- OpenAI-compatible 模型配置。
- Agent API 调用示例。
- 文件上传、图片生成、会话和 Admin 通用配置接口。
- tool-runtime 和 C++ worker 本地运行。
- MySQL、Qdrant、tool-output volume 备份。
- 常见失败排查。

## v0.4 单机 Docker 部署方案

目标：提供完整的本地/服务器启动闭环。

新增：

- `docker-compose.yml`
- `.env.example`
- `.dockerignore`
- `deploy/nginx.conf`
- `ui/Dockerfile`

服务组成：

- nginx：统一入口和反向代理。
- ui：React 静态资源。
- agent-api：Python FastAPI 编排服务。
- tool-runtime：工具运行时。
- mysql：关系型数据库。
- qdrant：向量检索服务。

设计特点：

- nginx 提供同源访问，减少前端跨域问题。
- `agent-api` 启动时可以自动执行 Alembic migration 和 seed。
- MySQL、Qdrant、tool-output 使用 Docker volume 持久化。
- `.dockerignore` 排除缓存、文档资产和无关文件，减少构建上下文。

## v0.3 C++ worker 与工具运行时集成

目标：把低层执行边界从 Python 业务编排中分离出来。

新增：

- `services/cpp-worker`
- `reactor-tool/reactor_tool/tool/cpp_worker.py`
- `reactor-tool/reactor_tool/tool/script_runner.py`
- `reactor-tool/reactor_tool/tool/script_runtime.py`
- tool-runtime Dockerfile 和测试。

C++ worker 能力：

- JSON-over-stdin 协议。
- 工作目录 root 限制。
- 命令执行。
- 超时控制。
- 退出码捕获。
- stdout/stderr 捕获。
- 文件产物扫描。
- sha256 计算。

tool-runtime 能力：

- deep search。
- report。
- code interpreter。
- web fetch。
- file service。
- image generation。
- data analysis。
- MRAG。
- table rag。

## v0.2 agent-api 编排服务

目标：建立 Python Agent 主业务链路。

新增：

- `services/agent-api`
- FastAPI app factory。
- 前端 API 和 SSE route。
- Pydantic 请求、响应、SSE schema。
- `ReactAgent`
- `PlanningAgent`
- `ExecutorAgent`
- `SummaryAgent`
- `AgentContext`
- `Memory`
- `ToolCollection`
- `ToolArtifactRegistry`
- `ExecutionLedgerRecorder`
- OpenAI-compatible LLM adapter。
- fake/demo LLM。
- tool-runtime HTTP adapter。
- SQLAlchemy model。
- Alembic migration。
- seed 脚本。
- 单元测试和集成测试。

核心能力：

- `deepThink=0` 路由到 ReAct。
- `deepThink=1` 路由到 PlanSolve。
- SSE 每帧输出 JSON data。
- LLM invocation、tool invocation、artifact、run、session 可落账。
- Admin 通用 CRUD 使用 `config_record` 持久化。
- 文件上传转发到 tool-runtime。
- dataAgent SSE 提供前端兼容入口。

## v0.1 UI 与工具基础

目标：保留可以直接服务主链路的前端、工具和运行素材。

包含：

- React 前端工作台。
- Python 工具运行时。
- runtime skills 示例。
- 基础资产、配置和工程脚手架。

阶段价值：

- 前端可以承载对话、工具事件、文件预览和图片生成。
- 工具运行时可以承接搜索、报告、代码解释器、图片和 MRAG/RAG。
- 后续模块可以围绕可运行主链路迭代。
