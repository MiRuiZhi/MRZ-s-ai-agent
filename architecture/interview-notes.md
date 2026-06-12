# 面试讲解提纲

## 一句话介绍

我做的是一个 Python + C++ AI Agent 运行时：`agent-api` 负责 ReAct/PlanSolve 编排、SSE 和执行账本，`tool-runtime` 负责搜索、报告、代码解释器、图片生成和 MRAG/RAG，`cpp-worker` 负责受控命令执行边界，最后用 React 工作台和 Docker Compose 串成可运行系统。

## 可以重点展开的点

1. **Agent 模式选择**
   - ReAct：适合工具调用链较短、边想边做的任务。
   - PlanSolve：先规划，再对子任务执行，适合长任务和复杂交付。

2. **并发设计**
   - 工具调用并发和 PlanSolve 子任务并发是两个不同层级。
   - Python 侧用 `asyncio.gather` 和 `Semaphore` 控制并发。
   - 工具失败会记录状态和错误，不直接让整条对话流崩掉。

3. **可观测性**
   - run 表记录一次用户请求。
   - LLM invocation 表记录每次模型调用。
   - tool invocation 表记录每次工具调用。
   - artifact 表记录输入/输出文件。
   - 这样可以从事实表复盘执行过程，而不是只翻日志。

4. **语言分工**
   - Python 生态适合 LLM、FastAPI、SSE、HTTP 工具编排。
   - C++ 适合稳定、可控、低层执行边界。
   - C++ 不进入 Agent 业务编排层，避免复杂度扩散。

5. **部署闭环**
   - Docker Compose 启动 `mysql/qdrant/tool-runtime/agent-api/ui/nginx`。
   - nginx 做同源代理，前端请求不需要处理复杂跨域。
   - MySQL、Qdrant、tool-output 用 volume 持久化。

## 常见追问

**为什么不是单体服务？**

Agent 编排和工具执行的资源特征不同。Agent API 更关注低延迟 SSE 和状态一致性；tool-runtime 可能跑代码、生成报告、做检索，耗时长且依赖重。拆成两个服务能隔离故障，也方便独立扩展。

**为什么不是拆更多服务？**

这是单机可运行的工程主线。拆太细会增加部署和调试成本。`agent-api + tool-runtime + cpp-worker` 是学习、演示和继续上线之间比较平衡的方案。

**PlanSolve 如何防止无限循环？**

planner 和 executor 都有最大步数；超过阈值会以 stopped 状态结束 run，并通过 SSE 发最终结果。

**如何保证工具并发后状态不乱？**

每个 tool call 都有稳定 `toolCallId`，执行前先记录 running 状态，结束时按同一 ID 回写 success/failed，并把 observation 写回 Memory。

**为什么 SSE 每帧必须是 JSON？**

前端会直接 `JSON.parse(event.data)`，所以后端不发送 `[DONE]` 这类非 JSON 哨兵值，而是通过连接关闭表示流结束。

**C++ worker 的边界是什么？**

它接收 JSON，校验工作目录，执行命令，控制超时，回传退出码和输出，只扫描本次新增或改动的文件，并计算 sha256。它不接触模型、HTTP、SSE 和数据库。
