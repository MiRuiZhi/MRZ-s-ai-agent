# Reactor UI

`ui` 是 MRZ's AI Agent 的 React + TypeScript 前端工作台。它负责对话界面、SSE 流式展示、工具过程展示、文件预览、MRAG 工作区和图片生成工作区。

## 职责

- 展示 Agent 对话和流式输出。
- 展示 ReAct / PlanSolve 的计划、任务、工具调用和结果。
- 上传会话附件。
- 预览工具产物文件。
- 使用图片生成和 MRAG 工作区。
- 通过 nginx 同源代理访问 `agent-api` 和 `tool-runtime`。

## 技术栈

- React 19
- TypeScript
- Vite
- Ant Design
- pnpm

前端依赖锁以 `pnpm-lock.yaml` 为准，不维护 `package-lock.json`。

## 本地运行

```bash
cd ui
pnpm install
pnpm dev
```

默认开发地址：

```text
http://localhost:3000
```

## 构建

```bash
cd ui
pnpm run build
```

Docker 构建时会通过 `ui/Dockerfile` 设置：

```text
SERVICE_BASE_URL=""
REACTOR_TOOL_BASE_URL="/tool"
```

这表示浏览器请求走当前 origin，由 nginx 代理到后端，避免 localhost、127.0.0.1 和容器网络之间混用。

## 常用脚本

| 命令 | 作用 |
| --- | --- |
| `pnpm dev` | 启动开发服务器 |
| `pnpm build` | 构建生产静态资源 |
| `pnpm lint` | 运行 ESLint |
| `pnpm fix` | 自动修复 ESLint 问题 |
| `pnpm preview` | 预览生产构建 |
| `pnpm test` | 运行前端测试 |

## 相关文档

- [项目 README](../README.md)
- [使用手册](../docs/development/usage.md)
- [单机 Docker 部署](../docs/deployment/single-node-docker.md)
- [验证清单](../docs/development/testing.md)
