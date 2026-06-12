FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    REACTOR_TOOL_WORKERS=1 \
    CPP_WORKER_BIN=/usr/local/bin/reactor-cpp-worker \
    CPP_WORKER_ROOT=/app/skilloutput

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential curl \
    && rm -rf /var/lib/apt/lists/*

COPY services/cpp-worker/src/main.cpp /tmp/reactor-cpp-worker.cpp
RUN g++ -std=c++17 -O2 /tmp/reactor-cpp-worker.cpp -o /usr/local/bin/reactor-cpp-worker \
    && rm /tmp/reactor-cpp-worker.cpp

COPY reactor-tool /app
RUN pip install --no-cache-dir uv \
    && uv sync --frozen

EXPOSE 1601

CMD ["./start.sh"]
