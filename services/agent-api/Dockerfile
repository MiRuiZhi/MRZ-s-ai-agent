FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

RUN pip install --no-cache-dir --upgrade pip

COPY services/agent-api /app
RUN pip install --no-cache-dir . \
    && chmod +x scripts/docker-entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["scripts/docker-entrypoint.sh"]
CMD ["uvicorn", "agent_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
