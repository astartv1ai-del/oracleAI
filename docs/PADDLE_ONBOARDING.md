# Web-оплата Paddle: тест и включение (G33)

Флаг `web_payments` **выключен по умолчанию** (`seed.py`) — оплата Stars уже
работает, а web-оплату включаем только после теста вебхука на боевом домене.
Причина: комиссия 3–5% против ~30–45% Stars — это рычаг маржи, но сломанный
платёжный путь хуже, чем отсутствие пути.

## Что уже в коде

- `app/api/routers/shop.py` — `POST /api/shop/web-checkout`: создаёт заказ с
  `payload` = `{tg_id, plan}`, редиректит на `PADDLE_CHECKOUT_URL` (гейт —
  флаг `web_payments` и непустой `paddle_checkout_url`).
- `app/api/routers/webhooks.py` — `POST /api/webhooks/paddle`: проверяет
  подпись `Paddle-Signature` (HMAC-SHA256, окно 1 ч), кладёт событие в
  `webhook_events` по `event_id` (идемпотентность), на `transaction.subscription.created`
  создаёт заказ и вызывает `billing.apply_payment` → выдаёт тариф.
- Тесты: `tests/test_growth.py` — `verify_paddle` (верная подпись/неверная/
  чужой секрет/просроченное окно), `_already_seen` дубликаты.

## Порядок включения

1. **Аккаунт Paddle**, каталог: продукты = планы (code: guide/vip/vip_year/concierge),
   ценник в долларах как в `docs/UNIT_ECONOMICS.md` §2.
2. **Настроить checkout URL**: `PADDLE_CHECKOUT_URL=https://.../checkout/...` в `.env`.
3. **Webhook**: в Paddle указать `https://домен/api/webhooks/paddle`, события
   `transaction.subscription.created` (и refund при необходимости). Скопировать
   secret в `PADDLE_WEBHOOK_SECRET`.
4. **Проверить подпись**: `python -m pytest tests/test_growth.py -k paddle`.
5. **Тест на staging** (боевой домен): оплатить `guide` тестовой картой Paddle →
   вебхук обработан (в логах без 401), подписка в админке, повторная доставка
   того же события не выдаёт товар дважды (`webhook_events` по event_id).
6. **Включить флаг**: админка → Флаги → `web_payments` → ON.
7. **Регресс**: `/api/shop/web-checkout` без флага — 404 (защита), с флагом —
   редирект на Paddle; Stars-оплата продолжает работать параллельно.

## Откат

Флаг OFF в любой момент возвращает прежний путь (web-кнопки скрываются),
незатронув уже выданные подписки — они живут по своей дате `sub_until`.
