# Services

`services/` 放当前主链路里的后端执行组件。

| 服务 | 路径 | 运行形态 | 职责 |
| --- | --- | --- | --- |
| `agent-api` | `services/agent-api` | FastAPI HTTP/SSE 服务 | Agent 编排、ReAct、PlanSolve、会话、账本、前端 API |
| `cpp-worker` | `services/cpp-worker` | JSON-over-stdin C++ worker | 受控命令执行、超时、退出码、文件产物扫描、sha256 |

`agent-api` 是用户请求入口，`cpp-worker` 不是独立 HTTP 服务。tool-runtime 在需要执行脚本或命令时，通过本地进程调用 `cpp-worker`。

## 阅读顺序

1. [agent-api README](agent-api/README.md)
2. [cpp-worker README](cpp-worker/README.md)
3. [仓库结构地图](../docs/architecture/repository-map.md)
4. [详细设计](../docs/architecture/design.md)

## 验证

```bash
uv run --project services/agent-api \
  python -W error::DeprecationWarning \
  -m unittest discover \
  -s services/agent-api/tests \
  -t services/agent-api \
  -v

python3 -m unittest discover -s services/cpp-worker/tests -v

g++ -std=c++17 -Wall -Wextra -Wpedantic \
  services/cpp-worker/src/main.cpp \
  -o /tmp/reactor_cpp_worker_verify
```
