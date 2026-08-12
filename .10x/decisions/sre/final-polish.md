# SRE — final-polish

## SLO (существующие, не менялись)
- `/health` 200 от API; liveness бота по хартбиту планировщика (`scripts/healthcheck.py`)
- Rate-limiter in-process → ровно 1 api-воркер (docker-compose закрепляет)

## Мониторинг
- Docker healthcheck: `interval 60s`, `start_period 120s`
- Логи: json-file, max-size 10m, max-file 5 (ротация в compose)

## Runbook: если после деплоя сломалось
1. `docker compose -f infra/docker-compose.yml ps` — контейнеры up?
2. `docker compose logs api --tail 100` — ищем 500/трейс
3. Совместимость (`/api/compat/full`) → 500? Это был фикс `cached["created_at"]`;
   если регресс — проверь, что app/core/agent.py задеплоен (старый контейнер)
4. Визуальные проблемы miniapp → проверить cache-busting `?v=` на сервере
   (браузер клиентки мог закешировать старую статику; поднять версию)
5. Пользователь «видит старый чат» → жёсткое обновление / поднять `?v=`

## Escalation
- Ошибки LLM-провайдеров: fallback «Все провайдеры недоступны» уже в `app/core/llm.py`
  (проверено тестами) — деградация, не падение. Следить за долей таких ответов в логах.