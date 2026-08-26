# Local browser baseline

**Date:** 2026-08-26  
**URL:** `http://127.0.0.1:8080/?dev_user=10001`  
**Environment:** `APP_ENV=dev`, `DEV_MODE=1`, `LLM_PROVIDER=off`, disposable SQLite DB.

The Mini App loaded with HTTP 200 and rendered the first-use surface without a visible browser extraction error. The page title is `OracleAI — твой мягкий ритуал дня`. The initial surface exposes profile, notifications, today, diary, four guide entry points (Lilith, Urania, Madame Lenormand, Mira), bottom navigation (Today, Dialogues, Profile), and an onboarding prompt with Start/Skip actions.

The extracted content confirmed explicit empty/loading-friendly copy for the daily ritual and personalized sign area. A screenshot was not available from the browser environment, so no visual pixel-level claim is made; a real screenshot-based desktop/mobile pass remains an open QA item in `docs/TASKS.md`.

## Interaction follow-up

The first attempted indexed click could not be replayed because the browser reported a stale DOM snapshot; a subsequent snapshot was `about:blank`. This is an environment/browser-session issue rather than proof of a product defect. No sensitive or irreversible browser action was taken. The local HTTP smoke test remains the authoritative transport evidence, while a stable browser session or real Telegram WebView is still required for full E2E visual QA.
