# OracleAI — Visual Polish Gauntlet

**Дата:** 27 августа 2026 года
**Ветка:** `master`
**Исходный commit:** `6b8e767f3e01455ef5f0829927f866c4932bb6ae`

## Цель и границы прохода

Этот проход был выполнен как финальная visual-polish итерация, а не как redesign. Архитектура Mini App, существующая token-система, bounded frame, Telegram-first shell и продуктовая иерархия сохранены. Изменения ограничены тремя небольшими визуальными/performance refinements и исправлением воспроизводимости QA evidence.

## Исходное состояние

Репозиторий был клонирован из `astartv1ai-del/oracleAI` в ветке `master`; рабочее дерево на исходном commit было чистым. До изменений проходили frontend build, design contract, visual contrast, cache-busting, frontend static checks, JavaScript syntax checks и `git diff --check`. Для live-render потребовалась локальная dev-конфигурация `APP_ENV=dev DEV_MODE=1`, а также установка зависимостей, объявленных самим проектом. Production guard при отсутствии `BOT_TOKEN`, `ADMIN_ID` и `WEBAPP_URL` намеренно остаётся закрытым.

Первоначальный capture использовал устаревший URL `qa=visual`, ожидал селекторы из прежней навигационной схемы и поэтому фиксировал только recovery/fallback surface. После анализа реального DOM были подтверждены актуальные контракты: домашний экран использует `.hero-orb`, навигация переключает состояния через `data-goto`, а chat открывается из agent card через `data-act="chat"`.

## Наблюдения и решения

| Область | Evidence | Точечное решение | Риск для продукта |
|---|---|---|---|
| Background loading | Browser console показывал, что preload `/static/img/bg-cosmos.jpg?v=103` не совпадал с CSS-запросом `/static/img/bg-cosmos.jpg`. | Версионированный query добавлен в CSS background declarations для mobile и desktop fallback, чтобы preload и фактический request использовали один URL. | Нет изменения artwork или layout; только согласован asset request. |
| Navigation motion | `.main-nav` использовал локальный spring-like overshoot `cubic-bezier(.34, 1.3, .5, 1)` и duration `.38s`, отличавшиеся от token motion language. | Indicator переведён на `var(--motion-base) var(--ease)`. | Нет изменения геометрии; переход стал короче и спокойнее. |
| Visual QA evidence | Capture script не доходил до authenticated hub/chat/profile states из-за устаревших URL и selectors. | Скрипт переведён на `qa=1`, стабильное ожидание `#app-main .screen`, `data-goto` и agent-card chat flow. | Только улучшение тестового harness; runtime product behavior не менялся. |

## Before / after evidence

| Surface | Before | After | Verdict |
|---|---|---|---|
| Home, 375px | Hero, CTA и ritual card уже имели устойчивую иерархию, но baseline capture в основном показывал fallback. | Authenticated home captured with the real hero, daily ritual, seasonal card and bottom navigation. | Ship. |
| Chat, 375px | Существующий shell был визуально resolved, но automated capture не создавал chat evidence. | Composer, send control, agent tabs, tool affordance and bottom nav captured reproducibly. | Ship. |
| Profile, 375px | Profile shell and tabs were already consistent, but only manual browser review confirmed this. | Summary, chart, history and memory states captured for RU/EN across all target breakpoints. | Ship. |
| Home, 1440px | Frame was bounded and centered; preload mismatch remained. | Same frame and atmosphere, with CSS request aligned to the preload URL. | Ship. |

## Final screenshot matrix

The corrected capture script generated **56 PNG evidence files plus `report.json`**: RU and EN at 375, 768, 1440 and 1920px, covering home, hub, chat, profile, chart, history and memory. The generated artifacts remain under `artifacts/visual-qa/` and are intentionally outside the release tree.

The DOM contract passed for all 56 captured states: horizontal overflow was zero, unnamed visible focusable controls were zero, and images without `alt` were zero. Reduced motion was exercised at the 768px viewport. A separate browser request check confirmed that the preload and CSS background request both resolve to `/static/img/bg-cosmos.jpg?v=103`.

## Automated verification

| Check | Result |
|---|---|
| `npm run build:frontend` | PASS; generated CSS bundle `app.57559c9ced4e.min.css` |
| `python3 scripts/check_design_contract.py` | PASS |
| `python3 scripts/check_visual_contrast.py` | PASS; all declared core pairs remain above thresholds |
| `python3 scripts/check_cache_busting.py` | PASS; main asset version remains `v103` |
| `python3 scripts/check_frontend_build.py` | PASS |
| `node --check miniapp/js/*.js` | PASS for all 19 source modules |
| `npm run test:axe` | PASS; zero axe violations across configured scenarios |
| `npm run test:lighthouse` | PASS; no runtime errors, accessibility scores 100 in reported scenarios |
| `python3 scripts/visual_qa_capture.py` | PASS; 56 states, zero overflow, zero unnamed focusables, zero missing image alt |
| `pytest -q --disable-warnings --maxfail=1` | PASS; suite completed at 100% with one expected skip |
| `python3 scripts/check_repository_hygiene.py` | PASS |
| `python3 scripts/check_static_asset_references.py` | PASS |
| `git diff --check` | PASS |

## Fresh critic verdicts

The mobile-only review found no high-impact cramped control, accidental tap target, or hierarchy failure. The 375px home preserves a dominant single CTA, the profile remains symmetrical, and the chat composer stays visually anchored above the bottom navigation. The desktop-only review found the 1440px and 1920px frames intentionally bounded rather than stretched; decorative atmosphere remains behind the content and does not create UI overflow.

The pixel-precision review identified the preload mismatch and motion-curve inconsistency as the most concrete remaining polish issues. Both were resolved without introducing new colors, radii, layout sections, or framework changes. The final pass did not identify a remaining defect with sufficient impact to justify further redesign.

## Acceptance summary

| Category | Status |
|---|---|
| Typography, spacing and alignment | PASS; existing token contract preserved and live screens reviewed |
| Icons, colors, borders, shadows and radii | PASS; no new one-off visual language introduced |
| Navigation and chat | PASS; real hub/chat/profile flows are now covered by evidence |
| Loading and layout stability | PASS; background preload contract is aligned; no observed layout shift in capture |
| Responsive behavior | PASS at 375, 768, 1440 and 1920px in RU/EN |
| Accessibility | PASS; axe zero violations, focus contract and reduced motion preserved |
| Performance | PASS; Lighthouse completed without runtime errors; no asset growth beyond the regenerated CSS bundle |
| Design-system cleanup | PASS; motion now uses shared tokens, and no new arbitrary UI token was added |

## Final verdict

The follow-up implementation also made the payment locale contract version-safe, so future cache-busting increments no longer fail API tests that previously hard-coded `v102`.

> **SHIP IT**

The product was not made louder or more decorative. The final change set removes two concrete visual/performance inconsistencies and restores trustworthy screenshot evidence for the important authenticated surfaces. OracleAI remains a bounded, quiet cosmic interface whose pixels, transitions and visual states are intentional.

## References

[1]: [`docs/DESIGN_SYSTEM.md`](DESIGN_SYSTEM.md) — token, geometry, motion and responsive contracts.
[2]: [`docs/VISUAL_QA.md`](VISUAL_QA.md) — existing visual QA methodology and acceptance surface.
[3]: [`scripts/visual_qa_capture.py`](../scripts/visual_qa_capture.py) — reproducible RU/EN breakpoint capture.
[4]: [`scripts/check_visual_contrast.py`](../scripts/check_visual_contrast.py) — numerical contrast check.

## Follow-up audit after remote sync

The latest `report.json` exposed two real evidence-level issues that are also visible in screenshots:

| Surface | Finding | Impact |
|---|---|---|
| Hub, 375px | The first row of quick-question chips is clipped at the right edge; the report lists `.ask-chip` as overflow nodes. The clipping is not a deliberate carousel affordance because no complete chip or scroll cue is visible. | Medium: the first agent card reads as unfinished and one action is hard to tap. |
| Chat, 375px | The composer’s suggestion chip is clipped horizontally at the right edge. The report lists `.chip.tpl` as overflow nodes. | Medium: the high-frequency composer action is visually truncated. |
| QA contract | Chat states report `visible.screen: null` because the contract only queries `.screen`, while the chat surface uses `.chat-shell`. | Low but important: visual evidence is incomplete and can hide layout defects. |
| Start page | The authenticated home is functional but presents a dense hero before the first task. The first fold should communicate the ritual and primary action more clearly, with less competing copy and stronger breathing room. | Medium: first impression is less calm and deliberate than the rest of the product. |

The decorative overflow nodes remain intentional atmosphere bleed. The interactive overflow nodes above are not accepted as intentional and will be fixed with bounded chip rows and a chat-aware QA contract.

## Start-page review

The current authenticated home at 375px is visually polished but too information-dense in the first fold: the hero contains date, ritual label, large greeting, lunar advice, decorative orbit lines and a full-width CTA, then immediately introduces a seasonal card and a partly visible rhythm card. The hierarchy is technically correct, but the first impression does not feel as calm as the rest of the app because several messages compete before the user has taken the first action.

The follow-up pass will keep the same hero artwork, type scale and single primary CTA, but reduce the hero’s copy density, give the CTA more optical separation, and make the first fold read as one clear invitation. The pre-auth age-gate screenshot is not present in the current capture output because the corrected evidence intentionally focuses on authenticated product states; the age gate remains covered by the existing application flow and axe/Lighthouse scenarios.

## Follow-up polish result

| Surface | Result after fix |
|---|---|
| Start page, 375px | Hero reduced from 382px to 353px, with tighter support copy and a clearer, better-separated CTA. The seasonal card and ritual card now enter the first fold without the hero feeling overstuffed. |
| Hub, 375px | Quick-question chips now wrap to full-width rows inside the agent card. No interactive chip is clipped or extends beyond the bounded frame. |
| Chat, 375px | Composer suggestions use the same bounded wrapping rule, preserving readable labels and tap targets. |
| QA contract | Chat is measured through `.chat-shell`; the report now records a real screen rectangle instead of `null`. |

Visual review confirms the refreshed start page is calmer and more intentional while preserving the existing OracleAI artwork, type hierarchy, single primary CTA, and overall navigation architecture.

## Remote CI follow-up

Push of the previous commit succeeded after rebasing onto the newer remote `master`; remote SHA became `3ba8179`. GitHub Actions run [CI #33088703611](https://github.com/astartv1ai-del/oracleAI/actions/runs/33088703611) started for that SHA. Frontend quality, browser QA setup, JS syntax, repository hygiene, documentation links, design contract, LLM evaluator and migration tests passed. The run was blocked by an existing contract in `tests/test_api.py::test_admin_demo_and_payment_health_ui_contract`, which still asserted `/static/styles.css?v=102` after the earlier cache-busting version had been raised to `v103`. This was a stale test expectation, not a visual runtime regression; the follow-up patch makes the contract version-aware while preserving cache-busting validation.
