# 单机 Docker 部署指南

这份文档说明如何用 Docker Compose 启动完整主链路：`mysql/qdrant/tool-runtime/agent-api/ui/nginx`。

## 服务拓扑

| 服务 | 端口 | 作用 |
| --- | --- | --- |
| `nginx` | `18080 -> 80` | 浏览器统一入口，同源代理 UI、agent-api、tool-runtime；宿主端口可用 `NGINX_HOST_PORT` 覆盖 |
| `ui` | 容器内部 | React 静态资源构建产物 |
| `agent-api` | `8000 -> 8000` | Agent API、SSE、ReAct、PlanSolve、账本；宿主端口可用 `AGENT_API_HOST_PORT` 覆盖 |
| `tool-runtime` | `1601 -> 1601` | 工具 HTTP 服务、文件服务、MRAG/RAG；宿主端口可用 `TOOL_RUNTIME_HOST_PORT` 覆盖 |
| `mysql` | `3307 -> 3306` | 关系型账本和配置数据；宿主端口可用 `MYSQL_HOST_PORT` 覆盖 |
| `qdrant` | `6333 -> 6333` | 向量检索；宿主端口可用 `QDRANT_HOST_PORT` 覆盖 |

## 本地启动

### 1. 准备环境

需要：

- Docker Desktop 或 Docker Engine。
- Docker Compose v2。

确认 Docker daemon 已启动：

```bash
docker info
```

### 2. 配置

默认不需要创建 `.env`。`docker-compose.yml` 已经内置 fake LLM、MySQL、Qdrant、tool-runtime、agent-api、ui 和 nginx 的本地服务默认值：

```bash
REACTOR_FAKE_LLM=true
```

这个模式不需要模型 Key，适合先验证服务、SSE、数据库、前端和三种主流程。deep search、图片生成、MRAG/RAG 的真实效果仍需要对应外部配置。

只有需要覆盖模型、并发、迁移、宿主端口或搜索配置时，才复制模板；它不是启动前置步骤：

```bash
cp .env.example .env
```

### 3. 启动

```bash
docker compose up -d --build
```

这条命令会在后台启动容器，终端回到提示符后服务仍会继续运行。前台模式只适合看实时日志：

```bash
docker compose up --build
```

前台模式下按 `Ctrl+C` 或关闭终端会停止容器。若镜像已经构建过，但 Docker Hub metadata 或 oauth token 请求临时超时，可以跳过构建直接启动已有镜像：

```bash
docker compose up -d --no-build
```

### 4. 访问

- UI：http://localhost:18080
- agent-api 健康检查：http://localhost:8000/web/health
- tool-runtime：http://localhost:1601
- Qdrant：http://localhost:6333
- MySQL：localhost:3307（容器内仍为 3306，可用 `MYSQL_HOST_PORT` 覆盖宿主端口）

日志里的 `0.0.0.0:8000`、`0.0.0.0:1601` 只表示服务监听所有网卡，不是浏览器访问地址。浏览器请访问 `localhost` 或 `127.0.0.1`。如果打开 `0.0.0.0`，部分浏览器会直接卡住或拒绝连接。

端口冲突时，在 `.env` 中覆盖：

```bash
NGINX_HOST_PORT=18080
AGENT_API_HOST_PORT=18000
TOOL_RUNTIME_HOST_PORT=11601
QDRANT_HOST_PORT=16333
MYSQL_HOST_PORT=13307
```

完整保留范围、三种模式验证和 runtime skills 路径见 [完整主链路运行说明](../development/main-chain-runbook.md)。

如果浏览器访问不到，先看容器是否仍在运行：

```bash
docker compose ps
```

`Exited` 表示容器已经停了，需要重新执行 `docker compose up -d --no-build` 或 `docker compose up -d --build`。

## 初始化

`agent-api` 容器默认会在启动时自动执行 Alembic version update 和 seed：

```bash
alembic -c alembic.ini upgrade head
python scripts/seed.py
```

需要手动重跑时：

```bash
docker compose exec agent-api alembic -c alembic.ini upgrade head
docker compose exec agent-api python scripts/seed.py
```

可通过 `.env` 关闭自动初始化：

```bash
REACTOR_RUN_MIGRATIONS=false
REACTOR_RUN_SEED=false
```

## 使用真实模型

接入 OpenAI-compatible 网关时修改 `.env`：

```bash
REACTOR_FAKE_LLM=false
REACTOR_OPENAI_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
REACTOR_OPENAI_API_KEY=你的Key
REACTOR_REACT_MODEL=qwen-plus
REACTOR_PLANNER_MODEL=qwen-plus
REACTOR_EXECUTOR_MODEL=qwen-plus
```

`tool-runtime` 自己的工具模型配置继续使用：

```bash
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_API_KEY=你的Key
DEEPSEARCH_BASE_URL=
DEEPSEARCH_API_KEY=
```

如果 `DEEPSEARCH_*` 留空，deep search 会回退到 `OPENAI_*`。

## 验证部署配置

不用真正启动容器，也可以先验证 Compose 配置：

```bash
docker compose config
docker compose config --services
```

期望包含以下服务，输出顺序不作为判断依据：

```text
mysql
qdrant
tool-runtime
agent-api
ui
nginx
```

启动后可以检查：

```bash
curl http://localhost:8000/web/health
curl -N \
  -H 'Content-Type: application/json' \
  -X POST http://localhost:8000/web/api/v1/gpt/queryAgentStreamIncr \
  -d '{"query":"请介绍一下这个系统","sessionId":"deploy-check","deepThink":0}'
```

## 常用运维命令

查看日志：

```bash
docker compose logs -f agent-api
docker compose logs -f tool-runtime
docker compose logs -f nginx
```

重启服务：

```bash
docker compose restart agent-api
docker compose restart tool-runtime
```

停止但保留数据：

```bash
docker compose down
```

停止并删除 volume 数据：

```bash
docker compose down -v
```

## 数据备份

MySQL volume：

```bash
mkdir -p backup
docker run --rm \
  -v ai-agent_mysql-data:/data \
  -v "$PWD/backup:/backup" \
  alpine tar czf /backup/mysql-data.tgz /data
```

Qdrant volume：

```bash
mkdir -p backup
docker run --rm \
  -v ai-agent_qdrant-data:/data \
  -v "$PWD/backup:/backup" \
  alpine tar czf /backup/qdrant-data.tgz /data
```

工具产物 volume：

```bash
mkdir -p backup
docker run --rm \
  -v ai-agent_tool-output:/data \
  -v "$PWD/backup:/backup" \
  alpine tar czf /backup/tool-output.tgz /data
```

## 上线建议

1. 在服务器安装 Docker 和 Docker Compose。
2. 拉取代码；如果要接真实模型，复制 `.env.example` 为 `.env`。
3. 改 `REACTOR_FAKE_LLM=false`，填入模型 Key。
4. 修改 MySQL root/user 密码。
5. 使用 `docker compose up -d --build` 启动。
6. 用 Nginx、Caddy 或云厂商负载均衡配置 HTTPS，反代到 `127.0.0.1:18080`。
7. 只暴露 80/443，不直接暴露 MySQL、Qdrant、agent-api、tool-runtime 管理端口。
8. 定期备份 MySQL、Qdrant 和 `tool-output` volume。

## 常见问题

- `agent-api` 无模型 Key 仍能回复：这是 fake LLM 模式，用来验证链路。
- 文件预览打不开：Docker Compose 默认在容器内使用 `FILE_SAVE_PATH=/app/skilloutput`，浏览器侧通过 nginx 访问 `/tool/v1/file_tool`；先看 `docker compose logs tool-runtime nginx`。
- DeepSearch 不工作：先看 `docker compose logs tool-runtime`，再检查 `OPENAI_*`、`DEEPSEARCH_*` 和搜索引擎配置。
- 数据库版本更新失败：确认 MySQL healthcheck 已通过，再查看 `docker compose logs agent-api`。
- 浏览器访问 UI 正常但接口失败：优先看 `deploy/nginx.conf` 和 nginx 日志，确认 `/web/`、`/api/`、`/data/`、`/tool/` 代理是否正常。
