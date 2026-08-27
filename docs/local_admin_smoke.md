# Local admin smoke evidence

**Date:** 2026-08-27

Opening `http://127.0.0.1:8080/admin` without Telegram `initData` renders only the auth gate:

> Открой панель кнопкой из бота — нужна подпись Telegram.

The dashboard shell is not visible and no operational data is rendered. This confirms the direct-URL client gate for an unauthenticated local request. Server-side API denial is covered separately by `tests/test_api.py` and `tests/test_security_regressions.py`.
