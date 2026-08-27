# Notification inbox browser smoke

**Date:** 2026-08-27
**Environment:** local FastAPI, `APP_ENV=dev`, synthetic QA user `10001` (RU)
**Route:** `/?dev_user=10001&qa=1&qa_view=home&cache=notification-v107`

## Interactive evidence

1. The Mini App home loaded with a bell button exposing the hint `Уведомления · есть новое`.
2. Clicking the bell opened the notification modal. The modal showed the current daily forecast, the Telegram morning forecast preference, `Входящие · 1`, a `Прогноз дня` item and `Отметить всё прочитанным`.
3. Clicking `Отметить всё прочитанным` reloaded the modal through `POST /api/notifications/read-all`; the inbox changed to `Входящие · 0` and the read button disappeared.
4. Clicking the morning forecast preference changed the button from `вкл` to `выкл`; the UI was refreshed from the server response rather than relying on an optimistic-only state.
5. The notification body was rendered as escaped text in the browser. The modal copy explicitly states that private chat text and provider payloads are excluded.

## Automated contract evidence

`tests/test_notifications.py` covers owner isolation, daily forecast deduplication, formatting-tag redaction, bounded response shape, preference persistence and idempotent mark-all-read. The API applies the existing authenticated-user and read/write rate-limit dependencies. The inbox does not invoke an LLM or accept user-supplied notification content.

## Limitation

This is local browser evidence with synthetic identity. Real Telegram delivery, signed `initData` across iOS/Android/Desktop WebView and provider credentials remain external deployment gates.
