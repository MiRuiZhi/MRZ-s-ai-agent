# Python+C++ Agent 使用手册

这份文档说明如何把当前仓库里的 Python+C++ 主链路跑起来、如何切换模型、如何调用核心接口、如何做本地开发和排障。

当前系统的定位是：用 Python FastAPI 承担 Agent 编排和 Web 协议，用 `reactor-tool` 承担工具运行时，用 C++ worker 承担受控脚本执行、超时、退出码、产物扫描和哈希计算。

## 当前状态

已经实现并验证的部分：

- `agent-api`：FastAPI 后端，包含 ReAct、PlanSolve、SSE、会话、SQL 账本、Admin 兼容 CRUD、文件上传兼容、dataAgent SSE 兼容。
- `tool-runtime`：`reactor-tool` 工具 HTTP 服务，集成 C++ worker 接口。
- `cpp-worker`：C++ JSON-over-stdin worker，支持超时、退出码、stdout/stderr、产物扫描、sha256、路径限制。
- Docker Compose 配置：`mysql`、`qdrant`、`tool-runtime`、`agent-api`、`ui`、`nginx`。
- 测试覆盖：Agent 核心、SQL 账本、SSE 协议、文件上传、Admin 持久化、C++ worker。

需要注意的边界：

- 这不是把所有业务接口逐字段完全强类型化的最终版，而是一个可继续迭代的 Python+C++ 生产替代基础。
- `/data/chatQuery` 目前是前端兼容 SSE，占位输出 `THINK`、空 `CHART_DATA` 和 `READY`，还没有完整强化 NL2SQL 能力。
- Admin 路由是通用配置实现，落在 `config_record` 表；后续可按高频资源拆强类型 DTO。
- 本机 Docker daemon 未启动时，不能执行 `docker compose up --build` 或 `docker compose build`。代码层面已经通过 `docker compose config` 校验。

## 瘦身说明

本项目按“当前主链路可运行”决定仓库内容，保留运行服务和必要文档，删除展示样例资产、重复锁文件、本地缓存和不参与运行的生成物。

保留的主模块：

- `reactor-tool`：工具运行时。
- `ui`：React 前端工作台。
- `services/agent-api`：Python Agent 编排服务。
- `services/cpp-worker`：C++ 执行边界。
- `deploy` 和 `docker-compose.yml`：单机部署配置。

Docker 构建上下文已经通过 `.dockerignore` 进一步瘦身：

- `assets`、`runtime`、文档、缓存、虚拟环境和非运行资产不进入镜像构建上下文。
- Docker 镜像只需要 `services/agent-api`、`services/cpp-worker`、`reactor-tool`、`ui` 和 `deploy/nginx.conf` 等运行相关内容。

## 目录速览

```text
.
├── docker-compose.yml
├── .env.example
├── deploy/nginx.conf
├── services
│   ├── agent-api
│   │   ├── agent_api
│   │   │   ├── api
│   │   │   ├── core
│   │   │   ├── integrations
│   │   │   └── storage
│   │   ├── alembic
│   │   ├── scripts
│   │   └── tests
│   └── cpp-worker
│       ├── src
│       └── tests
├── reactor-tool
└── ui
```

最常用入口：

- 使用手册：`USAGE.md`
- 设计说明：`DESIGN.md`
- Docker 部署补充：`deployment/single-node-docker.md`
- 架构速览：`architecture/python-cpp-rewrite.md`
- 面试笔记：`architecture/interview-notes.md`

## 一键 Docker 启动

### 1. 准备环境

需要本机安装：

- Docker Desktop 或 Docker Engine
- Docker Compose v2
- 可选：`curl`，用于接口测试

确认 Docker daemon 已启动：

```bash
docker info
```

如果这里报 `Cannot connect to the Docker daemon`，先启动 Docker Desktop。

### 2. 复制环境变量

```bash
cp .env.example .env
```

默认 `.env.example` 使用 fake LLM：

```bash
REACTOR_FAKE_LLM=true
```

fake LLM 不需要模型 Key，可以先验证服务、SSE、数据库、前端和工具调用链路。

### 3. 启动服务

```bash
docker compose up --build
```

后台启动：

```bash
docker compose up -d --build
```

### 4. 访问地址

默认端口：

- 前端 UI：http://localhost:8080
- agent-api 健康检查：http://localhost:8000/web/health
- tool-runtime：http://localhost:1601
- Qdrant：http://localhost:6333
- MySQL：localhost:3306

### 5. 数据库初始化

`agent-api` 容器启动时默认自动执行：

```bash
alembic -c alembic.ini upgrade head
python scripts/seed.py
```

对应开关在 `.env`：

```bash
REACTOR_RUN_MIGRATIONS=true
REACTOR_RUN_SEED=true
```

如果你想手动执行：

```bash
docker compose exec agent-api alembic -c alembic.ini upgrade head
docker compose exec agent-api python scripts/seed.py
```

### 6. 停止服务

停止容器但保留数据：

```bash
docker compose down
```

停止并删除 volume 数据：

```bash
docker compose down -v
```

删除 volume 会清空 MySQL、Qdrant、tool output 文件产物。

## 使用真实模型

默认 fake LLM 只用于验证链路。要接入真实模型，把 `.env` 改成：

```bash
REACTOR_FAKE_LLM=false
REACTOR_OPENAI_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
REACTOR_OPENAI_API_KEY=你的Key
REACTOR_REACT_MODEL=qwen-plus
REACTOR_PLANNER_MODEL=qwen-plus
REACTOR_EXECUTOR_MODEL=qwen-plus
REACTOR_SUMMARY_MODEL=qwen-plus
```

如果使用 OpenAI：

```bash
REACTOR_FAKE_LLM=false
REACTOR_OPENAI_BASE_URL=https://api.openai.com/v1
REACTOR_OPENAI_API_KEY=你的OpenAIKey
REACTOR_REACT_MODEL=gpt-4o-mini
REACTOR_PLANNER_MODEL=gpt-4o-mini
REACTOR_EXECUTOR_MODEL=gpt-4o-mini
```

如果使用 Ollama OpenAI-compatible 网关：

```bash
REACTOR_FAKE_LLM=false
REACTOR_OPENAI_BASE_URL=http://host.docker.internal:11434/v1
REACTOR_OPENAI_API_KEY=ollama
REACTOR_REACT_MODEL=qwen2.5
REACTOR_PLANNER_MODEL=qwen2.5
REACTOR_EXECUTOR_MODEL=qwen2.5
```

`agent-api` 和 `tool-runtime` 是两套模型配置：

- `REACTOR_OPENAI_*`：给 `agent-api` 的 ReAct、PlanSolve 编排层使用。
- `OPENAI_*`：给 `reactor-tool` 内部工具使用，例如 report、code interpreter、image generation。
- `DEEPSEARCH_*`：给 deep search 工具使用。

## 前端使用

启动 Docker Compose 后，打开：

```text
http://localhost:8080
```

前端通过 nginx 同源访问：

- `/web/api/v1/gpt/queryAgentStreamIncr` 进入 `agent-api`
- `/api/agent/*` 进入 `agent-api`
- `/data/*` 进入 `agent-api`
- `/tool/*` 被 nginx rewrite 到 `tool-runtime`

前端构建时 `SERVICE_BASE_URL=""`，所以浏览器会用当前域名访问后端，避免 localhost 和 127.0.0.1 混用导致 Cookie 或 CORS 问题。

## 核心接口使用

### 健康检查

```bash
curl http://localhost:8000/web/health
```

预期返回：

```text
ok
```

### ReAct 对话

`deepThink=0` 或 `agentType=1` 走 ReAct。

```bash
curl -N \
  -H 'Content-Type: application/json' \
  -X POST http://localhost:8000/web/api/v1/gpt/queryAgentStreamIncr \
  -d '{
    "query": "请介绍一下这个系统",
    "sessionId": "session-react-001",
    "deepThink": 0
  }'
```

SSE 每一帧都是 JSON：

```text
data: {"messageType":"tool_thought","data":"...","isFinal":false}

data: {"messageType":"result","data":{"taskSummary":"..."},"isFinal":true}
```

注意：这里不会输出 `data: [DONE]`，因为前端会直接 `JSON.parse(event.data)`。

### PlanSolve 对话

`deepThink=1` 或 `agentType=2` 走 PlanSolve。

```bash
curl -N \
  -H 'Content-Type: application/json' \
  -X POST http://localhost:8000/web/api/v1/gpt/queryAgentStreamIncr \
  -d '{
    "query": "帮我规划并完成一份学习路线",
    "sessionId": "session-plan-001",
    "deepThink": 1
  }'
```

典型 SSE 事件：

- `plan_thought`：规划模型的思考或规划文本。
- `plan`：当前计划、步骤列表、步骤状态。
- `task`：被拆出来的子任务。
- `tool_thought`：执行子任务时的模型输出。
- `task_summary`：子任务总结。
- `result`：最终总结。

### `/AutoAgent`

`/AutoAgent` 使用新的 Python `AgentRequest` 结构。

```bash
curl -N \
  -H 'Content-Type: application/json' \
  -X POST http://localhost:8000/AutoAgent \
  -d '{
    "requestId": "req-auto-001",
    "sessionId": "session-auto-001",
    "query": "用 ReAct 回答一个问题",
    "agentType": 1,
    "isStream": true
  }'
```

`agentType`：

- `1`：ReAct
- `2`：PlanSolve

### 文件上传

前端使用这个接口上传会话文件：

```bash
curl \
  -X POST http://localhost:8000/api/agent/file/upload \
  -F 'sessionId=session-file-001' \
  -F 'file=@README.md'
```

`agent-api` 会转发到：

```text
tool-runtime /v1/file_tool/upload_file_data
```

返回给前端的数据类似：

```json
{
  "code": "0000",
  "info": "success",
  "data": {
    "name": "README.md",
    "url": "/tool/v1/file_tool/preview/session-file-001/README.md",
    "type": "text/markdown",
    "size": 1234,
    "previewUrl": "/tool/v1/file_tool/preview/session-file-001/README.md",
    "downloadUrl": "/tool/v1/file_tool/download/session-file-001/README.md",
    "resourceKey": "session-file-001/README.md",
    "mimeType": "text/markdown",
    "originFileName": "README.md"
  }
}
```

### 图片生成

```bash
curl \
  -H 'Content-Type: application/json' \
  -X POST http://localhost:8000/api/agent/image-generation/generate \
  -d '{
    "requestId": "req-image-001",
    "prompt": "一张科技感城市夜景",
    "mode": "text-to-image",
    "fileNames": []
  }'
```

`agent-api` 会转发到 `tool-runtime` 的 `/v1/tool/image_generation`。

### dataAgent 问数兼容接口

```bash
curl -N \
  -H 'Content-Type: application/json' \
  -X POST http://localhost:8000/data/chatQuery \
  -d '{
    "content": "查看最近一个月销售额"
  }'
```

当前兼容版输出：

```text
data: {"eventType":"THINK","data":"正在分析问题：查看最近一个月销售额"}

data: {"eventType":"CHART_DATA","data":[]}

data: {"eventType":"READY"}
```

这是为了让前端 dataAgent 工作流先能运行。完整 NL2SQL、表结构召回、SQL 执行和图表数据生成还需要继续增强。

### 会话历史

列出会话：

```bash
curl http://localhost:8000/api/agent/conversation/sessions
```

查看会话详情：

```bash
curl http://localhost:8000/api/agent/conversation/sessions/session-react-001
```

默认 `REACTOR_LEDGER_BACKEND=sql` 时，从 SQL 账本读取。

如果设置：

```bash
REACTOR_LEDGER_BACKEND=memory
```

则从进程内内存读取，服务重启后历史会丢失。

### Admin 兼容 CRUD

创建配置：

```bash
curl \
  -H 'Content-Type: application/json' \
  -X POST http://localhost:8000/api/v1/admin/ai_agent/create \
  -d '{
    "agentId": "sales-agent",
    "agentName": "Sales Agent",
    "enabled": true
  }'
```

分页列表：

```bash
curl http://localhost:8000/api/v1/admin/ai_agent/query-list
```

查询全部：

```bash
curl http://localhost:8000/api/v1/admin/ai_agent/query-all
```

查询启用：

```bash
curl http://localhost:8000/api/v1/admin/ai_agent/query-enabled
```

删除：

```bash
curl \
  -H 'Content-Type: application/json' \
  -X POST http://localhost:8000/api/v1/admin/ai_agent/delete/sales-agent \
  -d '{}'
```

SQL 模式下，数据写入 `config_record`：

- `record_type`：路由里的资源名，例如 `ai_agent`
- `record_id`：`agentId`、`modelCode`、`id` 等推导出来的主键
- `name`：`agentName`、`modelName`、`name` 等推导出来的展示名
- `status`：启用状态
- `payload`：原始 JSON

## 本地开发

### agent-api 本地运行

进入仓库根目录：

```bash
cd /Users/miruizhi/workspace/codex_workspace/ai-agent
```

创建虚拟环境并安装依赖：

```bash
uv venv services/agent-api/.venv
uv pip install -p services/agent-api/.venv/bin/python -e 'services/agent-api[dev]'
```

使用 SQLite 本地跑：

```bash
cd services/agent-api
export REACTOR_DATABASE_URL="sqlite+pysqlite:///./agent-api.local.db"
export REACTOR_TOOL_RUNTIME_BASE_URL="http://localhost:1601"
export REACTOR_FAKE_LLM=true
export REACTOR_LEDGER_BACKEND=sql
.venv/bin/alembic -c alembic.ini upgrade head
.venv/bin/python scripts/seed.py
.venv/bin/uvicorn agent_api.main:app --host 0.0.0.0 --port 8000 --reload
```

如果只是跑 Agent 核心，不想准备数据库：

```bash
export REACTOR_LEDGER_BACKEND=memory
```

### tool-runtime 本地运行

`reactor-tool` 是当前工具 HTTP 服务。它的 Dockerfile 已经会把 C++ worker 编译到 `/usr/local/bin/reactor-cpp-worker`。

本地直接跑时，需要参考 `reactor-tool/README.md` 和 `reactor-tool/pyproject.toml` 安装依赖。

关键环境变量：

```bash
FILE_SAVE_PATH=/tmp/reactor-tool-output
FILE_SERVER_URL=http://localhost:1601/v1/file_tool
CPP_WORKER_BIN=/path/to/reactor-cpp-worker
CPP_WORKER_ROOT=/tmp/reactor-tool-output
```

### C++ worker 本地编译

直接用 g++：

```bash
g++ -std=c++17 -Wall -Wextra -Wpedantic \
  services/cpp-worker/src/main.cpp \
  -o /tmp/reactor_cpp_worker
```

用 stdin 传 JSON：

```bash
mkdir -p /tmp/cpp-worker-demo
printf '%s' '{
  "command": "python3 -c \"from pathlib import Path; Path('\'result.txt\'').write_text('\'hello\'')\"",
  "cwd": "/tmp/cpp-worker-demo",
  "timeoutSeconds": 10,
  "collectFiles": true
}' | /tmp/reactor_cpp_worker
```

限制工作目录：

```bash
export CPP_WORKER_ROOT=/tmp/cpp-worker-demo
```

如果传入的 `cwd` 不在 `CPP_WORKER_ROOT` 下面，worker 会拒绝执行。

### 前端本地运行

进入 `ui`：

```bash
cd ui
pnpm install
pnpm dev
```

前端构建变量在 `ui/Dockerfile` 中：

```text
SERVICE_BASE_URL=""
REACTOR_TOOL_BASE_URL="/tool"
```

开发时如果不走 nginx，可以设置前端运行环境，让 API 指向 `http://localhost:8000`。

## 测试

### agent-api 测试

```bash
services/agent-api/.venv/bin/python \
  -W error::DeprecationWarning \
  -m unittest discover \
  -s services/agent-api/tests \
  -t services/agent-api \
  -v
```

当前覆盖：

- ReAct 工具调用和 ledger 记录
- PlanSolve 子任务并发和汇总
- SQL ledger 持久化
- runtime 使用 SQL ledger
- SSE 主入口每帧都是 JSON
- dataAgent SSE 兼容
- 文件上传转发 tool-runtime
- tool-runtime multipart client
- Admin CRUD 写入 `config_record`

### C++ worker 测试

```bash
python3 -m unittest discover -s services/cpp-worker/tests -v
```

当前覆盖：

- 命令执行
- stdout 捕获
- 退出码
- 文件产物发现
- sha256 计算
- `CPP_WORKER_ROOT` 越界拒绝

### Alembic migration 验证

SQLite 临时库：

```bash
cd services/agent-api
tmpdir=$(mktemp -d)
REACTOR_DATABASE_URL="sqlite+pysqlite:///$tmpdir/alembic.db" \
  .venv/bin/alembic -c alembic.ini upgrade head
```

### Docker Compose 配置验证

```bash
docker compose config
```

这只验证配置能被 Compose 正确解析，不等于镜像 build 成功。

## 日志

查看所有服务日志：

```bash
docker compose logs -f
```

只看 agent-api：

```bash
docker compose logs -f agent-api
```

只看 tool-runtime：

```bash
docker compose logs -f tool-runtime
```

只看 MySQL：

```bash
docker compose logs -f mysql
```

## 数据备份和恢复

### 备份 MySQL volume

```bash
mkdir -p backup
docker run --rm \
  -v ai-agent_mysql-data:/data \
  -v "$PWD/backup:/backup" \
  alpine \
  tar czf /backup/mysql-data.tgz /data
```

### 备份 Qdrant volume

```bash
docker run --rm \
  -v ai-agent_qdrant-data:/data \
  -v "$PWD/backup:/backup" \
  alpine \
  tar czf /backup/qdrant-data.tgz /data
```

### 备份工具产物

```bash
docker run --rm \
  -v ai-agent_tool-output:/data \
  -v "$PWD/backup:/backup" \
  alpine \
  tar czf /backup/tool-output.tgz /data
```

## 常见问题

### Docker daemon 未启动

现象：

```text
failed to connect to the docker API
```

处理：

```bash
docker info
```

如果失败，启动 Docker Desktop。

### agent-api 启动时报数据库连接失败

检查 MySQL 是否健康：

```bash
docker compose ps
docker compose logs mysql
```

确认 `agent-api` 依赖的是：

```text
mysql:
  condition: service_healthy
```

### Alembic migration 失败

查看：

```bash
docker compose logs agent-api
```

手动执行：

```bash
docker compose exec agent-api alembic -c alembic.ini upgrade head
```

### 前端可以打开，但聊天没有响应

检查：

```bash
curl http://localhost:8000/web/health
docker compose logs agent-api
```

如果 `REACTOR_FAKE_LLM=false`，确认模型 Key：

```bash
REACTOR_OPENAI_API_KEY=...
REACTOR_OPENAI_BASE_URL=...
```

### deep_search/report/code_interpreter 不工作

这些工具在 `tool-runtime`，不是 `agent-api` 内部实现。检查：

```bash
docker compose logs tool-runtime
curl http://localhost:1601
```

再检查：

```bash
OPENAI_API_KEY=...
DEEPSEARCH_API_KEY=...
FILE_SAVE_PATH=...
FILE_SERVER_URL=...
```

### 文件预览打不开

检查 nginx `/tool/` 代理和 `FILE_SERVER_URL`：

```bash
FILE_SERVER_URL=http://localhost/tool/v1/file_tool
```

通过 nginx 访问时，浏览器里的预览链接一般应该走：

```text
/tool/v1/file_tool/preview/{request_id}/{file_name}
```

### Admin 默认账号

seed 会写入：

```text
username: admin
password: admin123
```

当前 seed 存的是 sha256 hash。生产环境必须改掉默认密码，并补正式认证鉴权。

## 生产上线建议

最小生产部署：

1. 服务器安装 Docker 和 Docker Compose。
2. 拉代码，复制 `.env.example` 为 `.env`。
3. 改 `REACTOR_FAKE_LLM=false`。
4. 填真实模型 Key。
5. 改 MySQL root/user 密码。
6. 启动：

```bash
docker compose up -d --build
```

7. 用 Caddy、Nginx 或云厂商负载均衡配置 HTTPS。
8. 只暴露 80/443，不直接暴露 MySQL、Qdrant、agent-api、tool-runtime 管理端口。
9. 定期备份 MySQL、Qdrant 和 `tool-output` volume。

生产前建议补齐：

- 正式用户认证和 Admin 权限控制。
- Admin DTO 强类型化。
- 完整 NL2SQL/dataAgent 能力。
- tool-runtime 的资源限制、沙箱和安全策略。
- C++ worker 更严格的命令白名单或隔离运行用户。
- 全链路 tracing、指标和告警。
