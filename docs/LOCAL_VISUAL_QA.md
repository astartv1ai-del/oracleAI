# Local visual QA — 2026-08-24

The FastAPI preview started successfully with `APP_ENV=dev DEV_MODE=1 HOST=0.0.0.0 PORT=8080`. The root Mini App rendered with the existing dark OracleAI shell, agent cards, onboarding controls, fonts, background and all versioned JS/CSS assets returning HTTP 200. A clean screenshot was captured at `/home/ubuntu/screenshots/127_0_0_1_2026-08-24_16-30-10_7336.webp`.

The browser root request with `?dev_user=1` still produced 401 responses for `/api/me`, `/api/agents` and `/api/tarot/decks` because the frontend's subsequent API requests do not propagate the query parameter. Direct `/api/tarot/decks?dev_user=1` returned the application's expected “open bot/start” identity error, confirming that a real Telegram initData/session is required for authenticated interactive QA. This is not evidence of a deck catalog failure; API, persistence and deck behavior are covered by the authenticated test fixtures in `tests/test_api.py`.

No production credentials, user data or raw palm image were used. The preview process should be stopped after QA.
