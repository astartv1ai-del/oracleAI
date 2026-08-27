# Мониторинг платежей и админ-панель

## Что проверяется автоматически

Активный bot process запускает lease-защищённый scheduler tick каждые десять минут. Внутри этого тика payment monitor выполняет bounded read-only проверки и сохраняет в `settings` только агрегированный snapshot. Второй bot process остаётся standby благодаря существующему SQLite lease, поэтому один и тот же alert не должен отправляться двумя владельцами одновременно.

Мониторинг проверяет зависшие `pending`-заказы старше двух часов, неуспешные заказы за последние 24 часа, обработанные webhook events по provider, безопасный failure journal webhook за 24 часа, orphan payments, paid orders без succeeded payment, дубликаты succeeded payments по заказу и расхождение последнего `crystal_ledger.balance` с быстрым балансом пользователя. Raw webhook payload, invoice IDs, Telegram IDs и произвольный текст в snapshot не попадают.

При наличии `CRYPTOBOT_API_TOKEN` monitor выполняет read-only `getBalance`. В snapshot сохраняются только asset и ограниченные строки available/onhold, без token и пользовательских данных. Stars помечены как `bot_polling`, потому что успешная оплата приходит через Telegram `successful_payment`, а Crypto Pay и Paddle — через HTTP webhook. Повторное DEGRADED/CRITICAL уведомление не отправляется чаще одного раза в шесть часов; новое уведомление приходит при переходе состояния или после cooldown. Восстановление до OK отправляет отдельное сообщение владельцу.

Состояния интерпретируются так:

| Состояние | Условие | Реакция |
|---|---|---|
| `OK` | Нет stale pending, ошибок заказов, failure journal и reconciliation anomalies; provider checks не degraded | Ничего не отправляется |
| `DEGRADED` | Есть stale pending/failed orders или provider balance check недоступен | Owner alert с cooldown |
| `CRITICAL` | Есть reconciliation anomaly: orphan payment, paid order без payment, duplicate succeeded payment или ledger mismatch | Owner alert с cooldown; ручная сверка обязательна |

## Как войти в админ-панель через Telegram

Владелец задаётся переменной `ADMIN_ID`. В Telegram нужно открыть чат с ботом и отправить `/admin`. Бот проверяет роль и присылает меню. В production при корректно заданном HTTPS `WEBAPP_URL` кнопка `📊 Панель управления` открывает `WEBAPP_URL/admin` как Telegram Mini App. Веб-панель передаёт Telegram `initData` в `X-Init-Data`; API проверяет подпись HMAC, срок `auth_date`, Telegram user id и роль. Пароль в панели не используется.

Если `WEBAPP_URL` пуст или не начинается с HTTPS, production-кнопка Mini App не показывается; остаётся только callback `📊 Статистика`. Это намеренное fail-closed поведение, а не полноценный вход в панель. Команда `/stats` даёт короткую сводку администратору.

Для локальной проверки используется только `DEV_MODE=1` и query-параметр `?dev_user=<ADMIN_ID>`. Этот режим не должен включаться в production. В браузерном smoke test необходимо открыть `/admin?dev_user=1`, убедиться в успешном gate, загрузке dashboard и `Платёжный контур`, затем выключить DEV_MODE перед деплоем.

## Демо-режим

Кнопка `ДЕМО: выкл.` отображается только owner после успешного `/api/admin/me`. После нажатия она меняет только состояние текущей страницы и запрашивает owner-only `/api/admin/dashboard/demo`. Synthetic response содержит ровно 451 уникального пользователя, 130 повторных плательщиков, 17 дней работы и 17 056 Stars, которые UI показывает ориентировочно как `$328` по своей reference rate `1/52`.

> Демо-режим — это презентационный срез, а не фиктивная запись в product database.

На экране всегда видны маркировка `ДЕМО-РЕЖИМ · тестовые данные` и пояснение, что данные не являются реальными пользователями, заказами, платежами или балансом. Операционный payment-health card остаётся реальным даже при включённом demo, поэтому состояние provider и сверки нельзя случайно принять за demo KPI. Демо endpoint не создаёт users, orders, payments, events, entitlements, balances или webhook rows. Выключение кнопки возвращает обычный `/api/admin/dashboard`.

## Production activation checklist

Перед публикацией необходимо задать `BOT_TOKEN`, `ADMIN_ID`, HTTPS `WEBAPP_URL`, а для web/crypto flows — соответствующие `PADDLE_WEBHOOK_SECRET`, `PADDLE_API_KEY`/price mapping и `CRYPTOBOT_API_TOKEN`. Crypto Pay webhook URL должен быть зарегистрирован в Crypto Pay App; секретный URL path и signature header остаются provider boundary. Paddle webhook destination должен быть настроен на `/api/webhooks/paddle` и доставлять `transaction.completed` с проверяемой подписью.

Для Telegram Stars необходимо пройти реальный pre-checkout → `successful_payment` flow. Для Crypto Pay нужно подтвердить реальный `invoice_paid` flow, баланс и повторную доставку webhook. Для Paddle нужно проверить signed completed transaction и retry behaviour. Эти проверки требуют тестовых или production credentials и не выполняются локальными unit tests. Прямой TON Connect здесь не заявляется как реализованный payment rail: для него отдельно нужны transaction monitor, masterchain finality и reconciliation.

Источники provider facts: [Telegram Bot API][1], [Crypto Pay API][2] и [Paddle Webhooks][3].

[1]: https://core.telegram.org/bots/api "Telegram Bot API"
[2]: https://help.send.tg/en/articles/10279948-crypto-pay-api "Crypto Pay API"
[3]: https://developer.paddle.com/webhooks/overview "Paddle Webhooks"
