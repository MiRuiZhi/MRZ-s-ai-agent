# 仓库结构地图

这份文档回答一个问题：打开仓库后，应该先看哪里。

## 顶层目录

```text
.
├── README.md                 # 项目入口和快速开始
├── CHANGELOG.md              # 按模块整理的阶段变更
├── docker-compose.yml        # 本地/单机部署编排
├── deploy/                   # nginx 配置
├── docs/                     # 详细文档
├── services/                 # Python 编排服务与 C++ worker
├── reactor-tool/             # 工具运行时
├── runtime/skills/           # 工具运行时可调用的技能素材
└── ui/                       # React 前端工作台
```

## 主链路目录

| 路径 | 作用 | 先看文件 |
| --- | --- | --- |
| `services/agent-api` | Agent 编排服务，负责 API、SSE、ReAct、PlanSolve、账本和前端协议 | `services/agent-api/README.md` |
| `reactor-tool` | 工具运行时，负责 deep search、report、code interpreter、web fetch、image generation、MRAG/RAG 和文件服务 | `reactor-tool/README.md` |
| `services/cpp-worker` | C++ 执行边界，负责受控命令执行、超时、退出码、文件扫描和 sha256 | `services/cpp-worker/README.md` |
| `ui` | React + TypeScript 前端工作台 | `ui/README.md` |
| `deploy` | nginx 同源代理配置 | `docs/deployment/single-node-docker.md` |

## agent-api 结构

```text
services/agent-api/agent_api
├── api/             # FastAPI app、routes、请求响应 schema
├── core/            # ReAct、PlanSolve、事件、memory、tools、ledger 接口
├── integrations/    # OpenAI-compatible LLM 与 tool-runtime HTTP client
├── storage/         # SQLAlchemy model、ledger、session factory
├── runtime.py       # 请求转换、Agent 路由、SSE async iterator
├── settings.py      # REACTOR_* 环境变量
└── main.py          # ASGI 入口
```

阅读顺序：

1. `api/routes.py`：外部 HTTP/SSE 入口。
2. `runtime.py`：请求如何进入 ReAct 或 PlanSolve。
3. `core/agents.py`：Agent 主循环。
4. `integrations/tool_runtime.py`：如何调用工具运行时。
5. `storage/ledger.py`：run、LLM、tool、artifact 如何落账。

## tool-runtime 结构

```text
reactor-tool/reactor_tool
├── api/             # 工具 HTTP 路由和文件服务
├── db/              # 文件元数据存储
├── model/           # 工具请求/响应模型
├── prompt/          # 工具 prompt
├── tool/            # deep search、report、code interpreter、MRAG 等工具
└── util/            # LLM、日志、文件、Qdrant 等工具函数
```

阅读顺序：

1. `api/tool.py`：工具路由入口。
2. `api/file_manage.py`：上传、预览、下载。
3. `tool/script_runner.py`：脚本/技能执行入口。
4. `tool/cpp_worker.py`：C++ worker 适配。
5. `tool/mrag/`：MRAG/RAG 相关实现。

## cpp-worker 结构

```text
services/cpp-worker
├── src/main.cpp     # worker 完整实现
└── tests/           # JSON 协议、路径边界、文件产物测试
```

它只通过 stdin/stdout 交换 JSON，不提供 HTTP 服务。tool-runtime 负责调用它。

## 文档结构

| 路径 | 内容 |
| --- | --- |
| `docs/architecture/overview.md` | 架构速览 |
| `docs/architecture/design.md` | 详细设计 |
| `docs/development/usage.md` | 使用手册 |
| `docs/development/testing.md` | 验证清单 |
| `docs/deployment/single-node-docker.md` | 单机 Docker 部署 |
| `docs/project/story.md` | 项目复盘 |
| `docs/project/interview-notes.md` | 面试提纲 |
