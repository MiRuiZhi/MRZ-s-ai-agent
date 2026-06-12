# cpp-worker

`cpp-worker` 是工具运行层的低层执行边界。它不负责 Agent、HTTP、SSE、数据库或模型调用，只负责把一次命令执行包装成稳定 JSON 协议。

## 职责

- 从 stdin 读取 JSON 请求。
- 校验 `cwd` 是否在允许的 root 内。
- 执行命令并控制超时。
- 捕获退出码和输出。
- 在 `collectFiles=true` 时只回报本次命令新增或改动的文件。
- 计算文件 sha256。
- 向 stdout 写出 JSON 响应。

## 请求示例

```json
{
  "command": "python3 -c \"from pathlib import Path; Path('result.txt').write_text('hello')\"",
  "cwd": "/tmp/reactor-worker-demo",
  "timeoutSeconds": 10,
  "collectFiles": true
}
```

## 编译

```bash
g++ -std=c++17 -Wall -Wextra -Wpedantic \
  services/cpp-worker/src/main.cpp \
  -o /tmp/reactor_cpp_worker_verify
```

## 测试

```bash
python3 -m unittest discover -s services/cpp-worker/tests -v
```

测试覆盖：

- 命令执行和文件产物回报。
- 已存在文件不会被误报为本次产物。
- `CPP_WORKER_ROOT` 外的工作目录会被拒绝。

## 调用关系

```text
agent-api -> tool-runtime -> cpp-worker
```

`agent-api` 不直接调用这个 worker；它通过 `tool-runtime` 的 code interpreter / script runner 链路间接使用。
