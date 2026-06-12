# tool-runtime

`reactor-tool` 是 MRZ's AI Agent 的工具运行时。它通过 FastAPI 暴露 `/v1/tool/*`、`/v1/file_tool/*`、`/v1/documents/*` 等接口，供 `agent-api` 在 ReAct 和 PlanSolve 中调用。

## 职责

- deep search：搜索、页面抓取、推理和答案整合。
- report：生成报告类文件产物。
- code interpreter：执行受控代码任务。
- web fetch：抓取单个网页并落盘为 Markdown。
- image generation：图片生成接口。
- MRAG/RAG：知识库、文档处理、向量检索和问答。
- file service：上传、预览、下载工具产物。
- cpp-worker adapter：调用 C++ worker 执行底层命令。

## 目录结构

```text
reactor_tool
├── api/             # 工具 HTTP 路由和文件服务
├── db/              # 文件元数据存储
├── model/           # 请求/响应模型
├── prompt/          # 工具 prompt
├── tool/            # deep search、report、code interpreter、MRAG 等工具
└── util/            # LLM、日志、文件、Qdrant 等工具函数
```

## 关键路由

| 路由 | 作用 |
| --- | --- |
| `POST /v1/tool/deep_search` | deep search |
| `POST /v1/tool/report` | 报告生成 |
| `POST /v1/tool/code_interpreter` | 代码解释器 |
| `POST /v1/tool/web_fetch` | 单网页抓取 |
| `POST /v1/tool/image_generation` | 图片生成 |
| `POST /v1/tool/mragQuery` | MRAG/RAG 查询 |
| `POST /v1/file_tool/upload_file` | 文件上传 |
| `GET /v1/file_tool/preview/{file_id}/{file_name}` | 文件预览 |
| `GET /v1/file_tool/download/{file_id}/{file_name}` | 文件下载 |

## 本地运行

需要 Python 3.11+。

```bash
cd reactor-tool
uv sync
cp .env_template .env
uv run python -m reactor_tool.db.db_engine
uv run python server.py
```

也可以使用启动脚本：

```bash
cd reactor-tool
./start.sh
```

Windows：

```powershell
cd reactor-tool
.\start.ps1
```

## 关键环境变量

| 变量 | 作用 |
| --- | --- |
| `FILE_SAVE_PATH` | 工具产物落盘目录 |
| `FILE_SERVER_URL` | 前端可访问的文件服务 URL |
| `OPENAI_BASE_URL` / `OPENAI_API_KEY` | 通用 OpenAI-compatible 模型配置 |
| `DEEPSEARCH_BASE_URL` / `DEEPSEARCH_API_KEY` | deep search 独立模型配置，留空回退到 `OPENAI_*` |
| `USE_SEARCH_ENGINE` | 搜索提供方，默认 `ddg` |
| `QDRANT_HOST` / `QDRANT_PORT` | Qdrant 地址 |
| `CPP_WORKER_BIN` | C++ worker 可执行文件路径 |
| `CPP_WORKER_ROOT` | C++ worker 允许访问的根目录 |

不要把 `FILE_SERVER_URL` 配置成本地磁盘目录，否则前端拿到的 `domainUrl/downloadUrl` 会变成不可访问路径。

## C++ worker

Dockerfile 会把 `services/cpp-worker/src/main.cpp` 编译到 `/usr/local/bin/reactor-cpp-worker`。本地直接运行 tool-runtime 时，需要手动编译 worker 或配置 `CPP_WORKER_BIN` 指向已有二进制。

## 测试

```bash
cd reactor-tool
uv run python -m unittest discover -s tests -v
```

测试覆盖工具路由、MRAG/RAG、文件服务、图片生成、web fetch、code interpreter、script runner 和权限策略。部分负向测试会打印预期内的错误日志，判断以退出码和 `OK` 为准。

## 相关文档

- [仓库结构地图](../docs/architecture/repository-map.md)
- [详细设计](../docs/architecture/design.md)
- [验证清单](../docs/development/testing.md)
