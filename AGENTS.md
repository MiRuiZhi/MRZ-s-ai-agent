# AGENTS.md

## Git 工作偏好

- 默认在完成代码或文档修改后，主动帮助整理真实、清晰、可解释的 Git 提交，并在验证通过后尝试推送到用户指定的远端仓库。
- 提交信息优先使用中文语义化风格，例如 `feat(agent-api): 重建 Python Agent 编排服务`、`docs: 补充中文架构说明`。
- 不伪造提交日期、不制造虚假的长期开发历史、不改写事实来误导他人；可以通过 README、CHANGELOG、PROJECT_STORY、tag 和清晰 commit message 做真实的作品集润色。
- 推送遇到 GitHub 认证时，不要求用户在聊天中提供密码或 token；应提示用户在本机终端使用 GitHub Personal Access Token、SSH key、credential helper 或 `gh auth login` 完成授权。

## 终端代理说明

- 开发、测试、构建或推送过程中，如果遇到需要网络访问的命令，并且出现 Docker Hub、GitHub、npm、pnpm、uv、pip、模型网关等连接超时、TLS 握手失败、认证 token 获取超时或下载失败，可以先在终端运行：

```bash
proxy_on
```

- `proxy_on` 用于打开本机终端代理。代理开启后，可以复用同一个终端会话继续执行原命令，例如 `docker compose build`、`docker compose up -d --build`、`git push`、`uv sync`、`pnpm install` 等。
- 如果当前非交互 shell 找不到 `proxy_on`，不要要求用户在聊天中提供代理账号、密码或 token；应说明该命令在当前 shell 不可用，并提示用户可在本机交互终端启用代理后重试。
- 不要把代理地址、token、密钥或临时凭据写入仓库文件、提交信息或公开文档。
