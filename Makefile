COMPOSE := docker compose -f infra/docker-compose.yml

.PHONY: init up down restart ps logs observability build migrate selfcheck docs-check shell worker-scale up-local-llm backup restore backup-drill p004-audit config

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
	$(COMPOSE) --profile backup up -d --build backup

restore:
	@test -n "$(BACKUP)" || (echo "usage: make restore BACKUP=/path/to/oracle-<timestamp>.dump.enc RESTORE_TARGET_DB=oracle_restore" && exit 2)
	@test -n "$(RESTORE_TARGET_DB)" || (echo "RESTORE_TARGET_DB must name an isolated database" && exit 2)
	RESTORE_TARGET_DB="$(RESTORE_TARGET_DB)" ./infra/restore-postgres.sh "$(BACKUP)"

backup-drill:
	python3 scripts/check_backup_restore_drill.py

p004-audit:
	python3 scripts/check_p004_infrastructure.py
	bash -n infra/backup-postgres.sh infra/restore-postgres.sh

config:
	$(COMPOSE) config
