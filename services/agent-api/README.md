# Reactor Agent API

FastAPI service that replaces the Java agent orchestration layer with a Python
implementation. It keeps the legacy SSE/API contracts while routing requests to
ReAct or PlanSolve agents and delegating tools to `reactor-tool`.
