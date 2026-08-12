# DevOps — final-polish

## Что деплоится
Miniapp статикой, API FastAPI. Изменения пасса — только статика+один backend-фикс
(не схема, не инфраструктура). Процесс деплоя не меняется.

## CI/CD (существующее)
- `.github/workflows/ci.yml` — прогон тестов на push
- Деплой: `docker compose -f infra/docker-compose.yml up -d --build` на VPS
- Только 2 процесса: `bot` (планировщик+рассылки — НЕ дублировать!) и `api`
  (1 воркер обязателен из-за in-process rate-limiter G22)

## Rollback
- Стадия: изменить `?v=49→50` при откате? Нет. Rollback = `git revert` пасса → rebuild
  контейнеров. API-фикс (`cached["created_at"]`) обратим (без миграций).
- Cache-busting: `/static` TTL 1ч. Для форсированной инвалидации поднять `?v=`.
  Пасс поднял 47→49.

## Шаги запуска
1. `DEV_MODE=0` в прод-`../.env` (иначе вход по `?dev_user` открыт)
2. Включить строгий CSP (без CDN-inline), см. security-review
3. `docker compose -f infra/docker-compose.yml up -d --build`
4. Smoke: `/health` 200, открыть WEBAPP_URL, проверить композер с tool-btn
5. Проверить, что новые статические файлы `.js`/`.css` прокинуты (объём не вырос на гигабайты)