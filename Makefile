.PHONY: up start stop down ps logs health react plan data

up:
	docker compose up -d --build

start:
	docker compose up -d --no-build

stop:
	docker compose down

down: stop

ps:
	docker compose ps

logs:
	docker compose logs -f

health:
	@printf 'agent-api: '
	@curl -fsS http://localhost:8000/web/health
	@printf '\nui: '
	@curl -fsS -o /dev/null http://localhost:18080
	@printf 'ok http://localhost:18080\n'

react:
	@curl -sS -N \
		-H 'Content-Type: application/json' \
		-X POST http://localhost:8000/web/api/v1/gpt/queryAgentStreamIncr \
		-d '{"query":"请介绍一下这个系统","sessionId":"make-react","deepThink":0}'

plan:
	@curl -sS -N \
		-H 'Content-Type: application/json' \
		-X POST http://localhost:8000/web/api/v1/gpt/queryAgentStreamIncr \
		-d '{"query":"帮我规划并完成一份学习路线","sessionId":"make-plan","deepThink":1}'

data:
	@curl -sS -N \
		-H 'Content-Type: application/json' \
		-X POST http://localhost:8000/data/chatQuery \
		-d '{"content":"查看最近一个月销售额"}'
