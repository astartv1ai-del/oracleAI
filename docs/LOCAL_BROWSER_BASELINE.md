# Local browser baseline

**Date:** 2026-08-27
**URL:** `http://127.0.0.1:8080/?dev_user=10001` (RU), `http://127.0.0.1:8080/?dev_user=10002` (EN)
**Environment:** `APP_ENV=dev`, `DEV_MODE=1`, `LLM_PROVIDER=off`, disposable SQLite DB.

The Mini App loaded with HTTP 200 and rendered the first-use surface without a visible browser extraction error. The page title is `OracleAI — твой мягкий ритуал дня`. The initial surface exposes profile, notifications, today, diary, four guide entry points (Lilith, Urania, Madame Lenormand, Mira), bottom navigation (Today, Dialogues, Profile), and an onboarding prompt with Start/Skip actions.

The extracted content confirmed explicit empty/loading-friendly copy for the daily ritual and personalized sign area. The interactive browser session did not provide a stable uploadable screenshot, so manual pixel-level approval is not claimed; deterministic Playwright captures below provide the reproducible mobile baseline, while broader desktop and state coverage remain open in `docs/TASKS.md`.

## Interaction follow-up

The first attempted indexed click could not be replayed because the browser reported a stale DOM snapshot; a subsequent snapshot was `about:blank`. This is an environment/browser-session issue rather than proof of a product defect. No sensitive or irreversible browser action was taken. The local HTTP smoke test remains the authoritative transport evidence, while a stable browser session or real Telegram WebView is still required for full E2E visual QA.

## Post-change browser check

A fresh navigation to the local source again returned the OracleAI first-use surface with the same interactive controls and localized copy. The extracted page title and four guide entry points remained intact after the report-history changes. Screenshot upload remained unavailable in this browser environment; deterministic Playwright evidence is therefore the reproducible visual baseline for the covered mobile states.

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

## Expanded visual baseline — deterministic Playwright capture

The harness `scripts/capture_visual_baseline.py` captures distinct server-side RU/EN synthetic identities at 360×800, 390×844 and 430×932. Covered states are age-gate, home, chat, payment, profile, chart/history/memory tabs and modals, and Tarot picker. The latest aggregate DOM report passed for every state: no horizontal overflow, zero unnamed focusable controls, zero images without `alt` attributes, and explicit expected-locale markers with the opposite hero marker absent.

Visual inspection of the locally generated RU home and chat captures shows clear hero hierarchy, a single primary CTA above the safe-area dock, a readable daily-ritual card, a stable bottom navigation, a focused current-agent card, proof badges and distinct tool chips. The EN Tarot capture now shows English picker prompts, question placeholder, draw CTA, agent labels, composer presence, tools label and suggestion chips. No obvious clipping or decorative layer obscures the primary action in these inspected states. Generated captures are kept outside the source tree.

Visual inspection of the locally generated EN home and Tarot captures confirms that the English hero, helper copy, navigation labels, agent labels and Tarot picker copy fit cleanly. The prior Russian helper-copy fallback was corrected in `HOME_I18N`; the later mixed-language Tarot/chat-shell findings are now covered by explicit locale dictionaries and static regressions. Generated captures are kept outside the source tree.

## Unified archive profile capture

The latest profile screenshots at 390×844 remain visually stable: the existing hero, tab bar, stats grid and bottom dock preserve the established visual system and the new history section is loaded below the selected History tab without competing with the primary profile surface. Focus-visible styling, full-width card tap targets and ellipsis handling were added for the archive cards. The EN profile labels visible in the inspected viewport are localized; the history section is below the first fold and will be checked through the automated DOM/state harness rather than overstating visual content not present in this viewport.

## Browser runtime check — latest source

The local Mini App loaded at both server-side locale identities and exposed labeled controls for profile, notifications, daily ritual, four agents and the four-item dock (Today/Guides/Pay/Mine). The deterministic harness confirms expected RU/EN copy for home, chat, Tarot and payment surfaces; it does not claim that all generated AI/user-authored message text is translated. The first-use overlay and chat guide were dismissed through explicit state setup for reproducible capture. Browser screenshot upload was unavailable in the interactive session; the Playwright artifacts and report are the reproducible local evidence.

The browser reached the profile screen and exposed the expected tab controls (`Сводка`, `Карта`, `История`, `Память`). A subsequent click snapshot became stale and the browser session then returned to `about:blank`; this is recorded as a browser-session instability, not a product failure. The deterministic Playwright harness remains the authoritative visual/accessibility check and reports no overflow, unnamed focusable controls or missing image alt attributes.
