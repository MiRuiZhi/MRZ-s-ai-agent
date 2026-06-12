# 单机 Docker 部署指南

## 本地启动

```bash
cp .env.example .env
docker compose up --build
```

默认访问：

- UI: http://localhost:8080
- agent-api: http://localhost:8000/web/health
- tool-runtime: http://localhost:1601
- MySQL: localhost:3306
- Qdrant: http://localhost:6333

`agent-api` 容器默认会在启动时自动执行 Alembic migration 和 seed。需要手动重跑时：

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

默认 `.env.example` 使用 `REACTOR_FAKE_LLM=true`，方便无 API Key 先跑通链路。

接入 OpenAI-compatible 网关时修改：

```bash
REACTOR_FAKE_LLM=false
REACTOR_OPENAI_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
REACTOR_OPENAI_API_KEY=你的Key
REACTOR_REACT_MODEL=qwen-plus
REACTOR_PLANNER_MODEL=qwen-plus
REACTOR_EXECUTOR_MODEL=qwen-plus
```

`reactor-tool` 自己的工具模型配置继续使用 `OPENAI_BASE_URL`、`OPENAI_API_KEY`、`DEEPSEARCH_*` 等变量。

## 上线建议

1. 在服务器安装 Docker 和 Docker Compose。
2. 拉取代码，复制 `.env.example` 为 `.env`，填入生产模型 Key。
3. 使用 `docker compose up -d --build` 启动。
4. 用 Nginx/Caddy 在宿主机配置 HTTPS，把域名反代到 `127.0.0.1:8080`。
5. 定期备份 Docker volume：

```bash
docker run --rm -v ai-agent_mysql-data:/data -v "$PWD/backup:/backup" alpine \
  tar czf /backup/mysql-data.tgz /data
```

## 常见问题

- `agent-api` 无模型 Key 仍能回复：这是 fake LLM 模式，用来验证链路。
- 文件预览打不开：确认 `FILE_SERVER_URL=http://localhost/tool/v1/file_tool`。
- DeepSearch 不工作：先确认 `tool-runtime` 日志，再检查 `OPENAI_*`、`DEEPSEARCH_*` 和搜索引擎配置。
- 数据库迁移失败：确认 MySQL healthcheck 已通过，再查看 `docker compose logs agent-api`。
