# 面试讲解提纲

## 一句话介绍

我把一个 Java Spring Boot 多智能体平台重构成 Python+C++ 两服务架构：Python 负责 Agent 编排和 Web 协议，C++负责低层执行隔离，保留 ReAct、PlanSolve、工具并发、执行账本和 artifact 回放这些核心能力。

## 可以重点展开的点

1. **Agent 模式选择**
   - ReAct：适合工具调用链较短、边想边做的任务。
   - PlanSolve：先规划，再对子任务执行，适合长任务和复杂交付。

2. **并发设计**
   - Java 版用 `CompletableFuture`。
   - Python 版用 `asyncio.gather` 和 `Semaphore`。
   - 工具调用并发和 PlanSolve 子任务并发是两个不同层级。

3. **可观测性**
   - run 表记录一次用户请求。
   - LLM invocation 表记录每次模型调用。
   - tool invocation 表记录每次工具调用。
   - artifact 表记录输入/输出文件。
   - 这样历史回放可以从事实表恢复，而不是翻日志。

4. **语言选型**
   - Python 生态适合 LLM、FastAPI、SSE、HTTP 工具编排。
   - C++适合稳定、可控、低层执行边界。
   - 不把 C++强行塞到 LLM 编排层，是为了降低复杂度和提升可维护性。

5. **迁移策略**
   - 不逐行翻译 Java。
   - 先冻结外部协议，再迁核心运行时，再迁基础设施。
   - 保留业务语义，替换实现方式。

## 常见追问

**为什么不是单体服务？**

Agent 编排和工具执行的资源特征不同。Agent API 更关注低延迟 SSE 和状态一致性；tool-runtime 可能跑代码、生成报告、做检索，耗时长且依赖重。拆成两个服务能隔离故障，也方便独立扩展。

**为什么不是微服务拆更多？**

这是单机生产替代版。拆太细会增加部署和调试成本。两服务是学习、演示和上线之间比较平衡的方案。

**PlanSolve 如何防止无限循环？**

每轮 planner 都有最大步数，executor 也有最大步数；超过阈值会以 stopped 状态结束 run，并通过 SSE 发最终结果。

**如何保证工具并发后状态不乱？**

每个 tool call 都有稳定 `toolCallId`，执行前先记录 running 状态，结束时按同一 ID 回写 success/failed，并把 observation 写回 Memory。

