# 验证清单

这份清单用于回答：改完项目后，如何证明主链路没有坏。

## 必跑检查

### agent-api

验证 FastAPI API、SSE、ReAct、PlanSolve、账本、文件上传和前端兼容入口。

```bash
uv run --project services/agent-api \
  python -W error::DeprecationWarning \
  -m unittest discover \
  -s services/agent-api/tests \
  -t services/agent-api \
  -v
```

期望：

- `Ran 12 tests`
- `OK`

### tool-runtime

验证工具路由、MRAG/RAG、文件服务、图片生成、web fetch、code interpreter、script runner 和权限策略。

```bash
cd reactor-tool
uv run python -m unittest discover -s tests -v
```

期望：

- `Ran 99 tests`
- `OK`

说明：部分负向测试会打印错误日志，例如越界脚本、embedding provider error、web fetch 拒绝二进制内容。这些日志是测试输入的一部分，判断以退出码和 `OK` 为准。

### cpp-worker

验证 C++ worker 的 JSON 协议、工作目录限制、文件产物扫描和 hash。

```bash
python3 -m unittest discover -s services/cpp-worker/tests -v
```

期望：

- `Ran 3 tests`
- `OK`

### C++ 编译检查

验证 `main.cpp` 可以用 C++17 编译。

```bash
g++ -std=c++17 -Wall -Wextra -Wpedantic \
  services/cpp-worker/src/main.cpp \
  -o /tmp/reactor_cpp_worker_verify
```

期望：命令退出码为 `0`。

### Docker Compose 配置

验证部署配置能被 Compose 正常解析。

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

## 结构扫描

确认仓库仍然只保留当前主链路源码：

```bash
rg --files -g '*.java'
rg --files | rg '(^pom\.xml$|/pom\.xml$|Reactor-agent-)'
```

期望：两条命令都没有输出。

确认文档和提交说明没有回到旧技术栈叙事：

```bash
git log --oneline --all \
  --grep='Java\|Maven\|Spring\|基于java\|基于 Java' \
  --regexp-ignore-case

rg -n 'Java|Maven|Spring|Reactor-agent|pom\.xml|fill-payload|CompletableFuture|基于 Java|基于java' \
  README.md CHANGELOG.md docs services/agent-api/README.md reactor-tool/README.md ui/README.md
```

期望：两条命令都没有输出。

## 前端检查

前端使用 pnpm，依赖锁以 `ui/pnpm-lock.yaml` 为准。

```bash
cd ui
pnpm test
pnpm run build
```

如果本机没有 `pnpm`、`npm`、`corepack` 或 `yarn`，记录为环境缺失，不要把它写成测试通过。Docker 构建时会在 `ui/Dockerfile` 内安装 pnpm。

## 提交前最小清单

- `git diff --check`
- `git status --short`
- agent-api 测试通过。
- tool-runtime 测试通过。
- cpp-worker 测试和 C++ 编译通过。
- `docker compose config` 通过。
- `.java`、`pom.xml`、`Reactor-agent-*` 扫描为空。
