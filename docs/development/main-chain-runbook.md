# 完整主链路运行说明

这份文档只回答一个问题：这个项目保留哪些主设计，默认怎么跑，三种模式如何验证，哪些能力需要真实外部配置才能看到完整效果。

## 1. 保留范围

当前仓库的主链路不是“只留一个聊天壳子”。默认设计保留以下部分：

| 部分 | 默认是否保留 | 作用 |
| --- | --- | --- |
| `agent-api` | 是 | FastAPI、SSE、ReAct、PlanSolve、dataAgent 兼容、会话和 SQL 账本 |
| `tool-runtime` | 是 | deep search、report、code interpreter、web fetch、image generation、MRAG/RAG、文件服务、script runner |
| `cpp-worker` | 是 | 受控命令执行、超时、退出码、stdout/stderr、产物扫描和 sha256 |
| `ui` | 是 | React 工作台、对话、工作区、图片生成、MRAG/dataAgent 等前端入口 |
| `mysql` | 是 | run、LLM invocation、tool invocation、artifact、session、Admin 配置持久化 |
| `qdrant` | 是 | MRAG/RAG 向量检索 |
| `runtime/skills` | 是 | 图表、数据分析、PPT、GitHub 深研等脚本和技能素材 |
| `nginx` | 是 | 同源代理 UI、agent-api、tool-runtime |

瘦身只针对这些东西：

- 本地 `.venv`、`__pycache__`、缓存、系统索引等可再生文件。
- 重复或容易误导的说明。
- Docker 构建上下文里的非运行资料，例如 `docs/`、`.git/`、本地 IDE 文件。

不会因为瘦身删除 MRAG、图片生成、DeepSearch、Qdrant、runtime skills、复杂工作区 UI 或 MySQL 默认依赖。

## 2. 默认部署拓扑

默认 Docker Compose 启动完整链路：

```text
浏览器
  |
  v
nginx :8080
  |-- /              -> ui
  |-- /web /api /data -> agent-api :8000
  |-- /tool          -> tool-runtime :1601

agent-api
  |-- MySQL :3306 inside container, localhost:3307 on host
  |-- tool-runtime

tool-runtime
  |-- Qdrant :6333
  |-- cpp-worker binary
  |-- /app/runtime/skills
  |-- tool-output volume
```

默认服务清单：

```bash
docker compose config --services
```

期望包含：

```text
mysql
qdrant
tool-runtime
agent-api
ui
nginx
```

## 3. `.env` 使用规则

默认启动不要求本地必须有 `.env`。

`docker-compose.yml` 已经给本地验证内置了默认值，尤其是：

```bash
REACTOR_FAKE_LLM=true
REACTOR_LEDGER_BACKEND=sql
REACTOR_RUN_MIGRATIONS=true
REACTOR_RUN_SEED=true
MYSQL_HOST_PORT=3307
QDRANT_HOST_PORT=6333
TOOL_RUNTIME_HOST_PORT=1601
AGENT_API_HOST_PORT=8000
NGINX_HOST_PORT=8080
```

所以本地第一次验证应该直接运行：

```bash
docker compose up -d --build
```

只有需要覆盖默认值时，才复制模板：

```bash
cp .env.example .env
```

根目录 `.env` 只给 Docker Compose 的跨服务配置使用，例如模型 Key、宿主端口、DeepSearch 配置。`reactor-tool` 本地单独运行时使用 `reactor-tool/.env`，不要把 `FILE_SAVE_PATH`、`FILE_SERVER_URL` 这类工具运行时本地路径混进根目录 `.env` 里。

端口冲突时可以只临时覆盖，例如：

```bash
NGINX_HOST_PORT=18080 docker compose up -d --no-build
```

## 4. fake LLM 和真实模型的区别

`REACTOR_FAKE_LLM=true` 的作用是验证主流程：

- API 能启动。
- SSE 能返回。
- ReAct 能走完。
- PlanSolve 能拆任务并汇总。
- dataAgent 兼容接口能给前端稳定事件。
- SQL 账本、会话、run 记录能工作。

fake LLM 不等于真实智能效果。下面这些能力要看到真实效果，需要配置外部服务：

| 能力 | 需要配置 |
| --- | --- |
| ReAct/PlanSolve 真实推理 | `REACTOR_FAKE_LLM=false`、`REACTOR_OPENAI_BASE_URL`、`REACTOR_OPENAI_API_KEY` |
| deep search | `OPENAI_*` 或 `DEEPSEARCH_*`，以及可用搜索引擎 |
| report/code interpreter 中的模型能力 | `OPENAI_BASE_URL`、`OPENAI_API_KEY` |
| image generation | `OPENAI_*` 指向支持图片生成的网关或实现 |
| MRAG/RAG | Qdrant 已默认启动，还需要知识库数据、embedding/rerank/LLM 配置 |
| script runner 技能 | 对应 skill 需要的 Python/Node/Shell 依赖和输入文件 |

## 5. 三种模式验证

### 5.1 ReAct

`deepThink=0` 或 `agentType=1` 进入 ReAct。

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

预期能看到 JSON SSE 帧，最后有 `messageType=result` 且 `isFinal=true`。

### 5.2 PlanSolve

`deepThink=1` 或 `agentType=2` 进入 PlanSolve。

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

预期能看到 `plan_thought`、`plan`、`task`、`task_summary`、`result` 等事件。

### 5.3 dataAgent 兼容流

`/data/chatQuery` 目前用于保持前端 dataAgent 流程可运行。

```bash
curl -N \
  -H 'Content-Type: application/json' \
  -X POST http://localhost:8000/data/chatQuery \
  -d '{
    "content": "查看最近一个月销售额"
  }'
```

当前兼容事件：

```text
data: {"eventType":"THINK","data":"正在分析问题：查看最近一个月销售额"}

data: {"eventType":"CHART_DATA","data":[]}

data: {"eventType":"READY"}
```

完整 NL2SQL、表结构召回、SQL 执行和图表生成属于后续增强，不应该在文档里写成已经完整生产化。

## 6. 工具链路验证

### 文件服务

```bash
curl \
  -X POST http://localhost:8000/api/agent/file/upload \
  -F 'sessionId=session-file-001' \
  -F 'file=@README.md'
```

这条链路会走：

```text
agent-api -> tool-runtime /v1/file_tool/upload_file_data -> tool-output volume
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

这条链路会走：

```text
agent-api -> tool-runtime /v1/tool/image_generation
```

如果没有图片模型配置，链路可能返回工具错误；这不是部署缺失，而是外部模型能力未配置。

### runtime skills

Docker 镜像内固定保留技能素材目录：

```text
/app/runtime/skills
```

例如 script runner 可以用稳定路径指向技能：

```json
{
  "requestId": "req-skill-001",
  "skillName": "data-analysis",
  "skillBasePath": "/app/runtime/skills/data-analysis",
  "scriptName": "analyze",
  "scriptPath": "scripts/analyze.py",
  "runtime": "python",
  "arguments": {},
  "argv": ["--help"],
  "timeoutSeconds": 30
}
```

调用入口：

```text
POST http://localhost:1601/v1/tool/script_runner
```

技能脚本是否能完成业务结果，取决于该技能自己的依赖、输入文件和外部服务配置；默认部署保证的是素材和执行入口存在。

## 7. 文档分工

文档按层级维护：

| 文档 | 负责内容 |
| --- | --- |
| `README.md` | 项目是什么、默认怎么启动、三模式最短验证 |
| `docs/README.md` | 文档导航和阅读顺序 |
| `docs/development/main-chain-runbook.md` | 完整主链路运行说明，也就是本文 |
| `docs/development/usage.md` | 日常使用、本地开发、接口示例和排障 |
| `docs/deployment/single-node-docker.md` | Docker Compose 单机部署和运维 |
| `docs/architecture/overview.md` | 架构速览 |
| `docs/architecture/design.md` | 详细设计、数据模型、Agent 循环、SSE 协议 |
| `docs/development/testing.md` | 修改后如何验证 |

维护原则：

- README 不写长篇实现细节，只给最短可跑路径。
- 真实运行步骤放在 `docs/development/main-chain-runbook.md` 和 `docs/deployment/single-node-docker.md`。
- 架构解释放在 `docs/architecture/`，不要和启动命令混在一起。
- 文档不要承诺尚未完成的能力，例如完整 NL2SQL。
- 文档不要写必须复制 `.env`，除非确实需要覆盖默认值。
