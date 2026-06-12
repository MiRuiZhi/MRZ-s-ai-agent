# 变更记录

本文件按功能阶段整理项目演进，便于快速了解仓库从原始基线到 Python+C++ 重构版的变化。

这里记录的是功能阶段，不伪造开发日期。

## v0.6 作品集展示与项目复盘

目标：让 GitHub 展示更清楚，也让面试讲解更顺畅。

新增：

- 新增 `PROJECT_STORY.md`，说明项目背景、重构目标、技术取舍、核心链路和面试表达。
- 新增 `CHANGELOG.md`，按版本阶段整理功能演进。
- README 增加“项目定位”和“作品集导航”。
- README 文档入口补充项目故事和变更记录。

价值：

- HR 可以快速看懂项目亮点。
- 面试官可以顺着文档深入看架构。
- 自己复盘时有完整讲稿和技术脉络。

## v0.5 中文架构、使用与面试材料

目标：让项目不只是能跑，还能被清楚解释。

新增：

- `USAGE.md`：完整中文使用手册。
- `DESIGN.md`：细粒度中文设计说明。
- `architecture/python-cpp-rewrite.md`：Python+C++ 重构架构速览。
- `architecture/interview-notes.md`：面试讲解稿和常见追问。
- `deployment/single-node-docker.md`：单机 Docker 部署说明。

覆盖内容：

- 本地部署。
- 服务器部署。
- 环境变量解释。
- 模型配置。
- 日志查看。
- 数据备份。
- 常见失败排查。
- Java 到 Python/C++ 的映射。
- ReAct 和 PlanSolve 的执行时序。

## v0.4 单机 Docker 部署方案

目标：让项目可以一键启动，而不是只停留在代码层。

新增：

- `docker-compose.yml`
- `.env.example`
- `.dockerignore`
- `deploy/nginx.conf`
- `ui/Dockerfile`

服务组成：

- nginx：统一入口和反向代理。
- ui：React 静态资源。
- agent-api：Python FastAPI 后端。
- tool-runtime：工具运行时。
- mysql：关系型数据库。
- qdrant：向量检索服务。

设计特点：

- nginx 提供同源访问，减少前端跨域问题。
- `agent-api` 启动时可以自动执行 Alembic migration 和 seed。
- MySQL、Qdrant、tool-output 使用 Docker volume 持久化。
- `.dockerignore` 排除旧 Java 模块、缓存、文档资产和无关二进制，减少构建上下文。

## v0.3 C++ worker 与工具运行时集成

目标：整理原有工具服务，并把低层执行边界从 Python 业务编排中分离出来。

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

保留和整理的工具能力：

- deep search
- report
- code interpreter
- web fetch
- file service
- image generation
- data analysis
- MRAG
- table rag

## v0.2 Python agent-api 编排服务

目标：用 Python 重建 Java Agent 后端的主业务链路。

新增：

- `services/agent-api`
- FastAPI app factory。
- 兼容 Java Controller 的 route。
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

## v0.1 原始工程基线

目标：保留原始工程作为迁移来源和学习对照。

包含：

- `Reactor-agent-*` Java 源码。
- 原 React UI。
- 原 assets/runtime/pom 等工程文件。
- 原始业务分层和模块结构。

保留原因：

- 方便对照 Java 到 Python/C++ 的映射。
- 方便理解原项目的业务语义。
- 方便面试中说明迁移依据，而不是凭空写一个 demo。

当前处理方式：

- Java 源码保留在仓库。
- Java 源码不参与 Docker 构建。
- 运行链路以 Python+C++ 重构版为主。
