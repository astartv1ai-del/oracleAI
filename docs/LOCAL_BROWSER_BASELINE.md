# Local browser baseline

**Date:** 2026-08-26  
**URL:** `http://127.0.0.1:8080/?dev_user=10001`  
**Environment:** `APP_ENV=dev`, `DEV_MODE=1`, `LLM_PROVIDER=off`, disposable SQLite DB.

The Mini App loaded with HTTP 200 and rendered the first-use surface without a visible browser extraction error. The page title is `OracleAI — твой мягкий ритуал дня`. The initial surface exposes profile, notifications, today, diary, four guide entry points (Lilith, Urania, Madame Lenormand, Mira), bottom navigation (Today, Dialogues, Profile), and an onboarding prompt with Start/Skip actions.

The extracted content confirmed explicit empty/loading-friendly copy for the daily ritual and personalized sign area. A screenshot was not available from the browser environment, so no visual pixel-level claim is made; a real screenshot-based desktop/mobile pass remains an open QA item in `docs/TASKS.md`.

## Interaction follow-up

The first attempted indexed click could not be replayed because the browser reported a stale DOM snapshot; a subsequent snapshot was `about:blank`. This is an environment/browser-session issue rather than proof of a product defect. No sensitive or irreversible browser action was taken. The local HTTP smoke test remains the authoritative transport evidence, while a stable browser session or real Telegram WebView is still required for full E2E visual QA.

## Post-change browser check

A fresh navigation to the committed server again returned the OracleAI first-use surface with the same interactive controls and localized copy. The extracted page title and four guide entry points remained intact after the report-history changes. Screenshot upload remained unavailable in this browser environment, so visual pixel-level approval is intentionally not claimed.

## PDF visual QA — RU exact-time sample

Rendered sample: `/tmp/oracleai-pdf-audit/ru_exact/anna-1990-06-21.pdf`.

Observed on pages 1–5: the cover renders cleanly with premium dark palette, centered hierarchy and no obvious clipping; the second page keeps the chart summary and Matrix blocks legible with balanced spacing; the wheel page renders with readable aspect lines and no visible overlap severe enough to hide the main placements; the technical tables for planets, nodes, additional points and house cusps are readable and keep consistent typography; no broken glyphs, blank pages or obvious overflow were observed in the inspected pages. Remaining pages still require inspection for full visual sign-off.

The remaining pages 6–9 of the same RU exact-time sample also rendered without obvious clipping or broken glyphs. The aspects table stayed legible, two-column interpretation pages preserved headings and paragraph flow, and the closing page maintained card borders, spacing and footer consistency. Based on this inspected sample, the exact-time RU PDF path is visually acceptable for this baseline, while EN/date-only variants still remain metadata-verified rather than fully screenshot-reviewed.

## PDF visual QA — RU date-only sample after fix

Rendered sample: `/tmp/oracleai-pdf-audit-v2/ru_date_only/anna-1990-06-21.pdf`.

Pages 1–5 confirm the intended truth state after the fix: the summary card shows unknown birth time explicitly, the natal page renders a precision notice instead of a wheel, all placement tables show `—` for houses, and the narrative page now states that the Ascendant is not calculated and that only sign placements are used. No reintroduced house-wheel visuals or placeholder angle claims were observed in the inspected pages. Text extraction for both RU and EN date-only samples also confirmed the removal of the previous unsupported strings.

## PDF visual QA — EN date-only sample after fix

Rendered sample: `/tmp/oracleai-pdf-audit-v2/en_date_only/anna-1990-06-21.pdf`.

Pages 1–5 preserve the localized premium layout and the same corrected truth state: unknown birth time is explicit, the wheel is replaced by a precision notice, house columns remain blank, and the narrative states that the Ascendant is not calculated because birth time is unconfirmed. Typography, spacing and localization remained readable in the inspected pages.
