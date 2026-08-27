COMPOSE := docker compose -f infra/docker-compose.yml

.PHONY: init up down restart ps logs observability build migrate selfcheck docs-check shell worker-scale up-local-llm backup config

init:
	@test -f .env || cp .env.example .env
	@echo "Edit .env, then run: make up"

build:
	$(COMPOSE) build --pull

up:
	$(COMPOSE) up -d --build
	$(COMPOSE) ps

up-local-llm:
	$(COMPOSE) --profile local-llm up -d --build ollama
	$(COMPOSE) --profile local-llm run --rm ollama-init
	$(COMPOSE) up -d --build api bot worker beat
	@echo "Local LLM is ready. Ensure CUSTOM_LLM_BASE_URL=http://ollama:11434/v1 and model names are set in .env."

down:
	$(COMPOSE) down

restart:
	$(COMPOSE) up -d --build --force-recreate

ps:
	$(COMPOSE) ps

logs:
	$(COMPOSE) logs -f --tail=100 api bot worker beat redis postgres caddy loki alloy prometheus grafana cadvisor node-exporter

observability:
	$(COMPOSE) ps loki alloy prometheus grafana cadvisor node-exporter

migrate:
	$(COMPOSE) run --rm migrate

selfcheck:
	$(COMPOSE) exec api python -m scripts.selfcheck

docs-check:
	python3 scripts/check_documentation_links.py

shell:
	$(COMPOSE) exec api /bin/bash

worker-scale:
	$(COMPOSE) up -d --scale worker=$(N)

backup:
	$(COMPOSE) --profile backup up -d backup

config:
	$(COMPOSE) config
