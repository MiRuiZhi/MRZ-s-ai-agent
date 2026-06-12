# Reactor Agent API

FastAPI service for the Python+C++ Reactor Agent mainline.

`agent-api` provides the public HTTP/SSE contracts used by the React workspace, routes requests to ReAct or PlanSolve agents, records run/LLM/tool/artifact ledger entries, and delegates heavy tools to `reactor-tool`.
