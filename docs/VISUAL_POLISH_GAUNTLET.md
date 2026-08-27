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
| Background loading | Browser console показывал, что preload `/static/img/bg-cosmos.jpg?v=102` не совпадал с CSS-запросом `/static/img/bg-cosmos.jpg`. | Версионированный query добавлен в CSS background declarations для mobile и desktop fallback, чтобы preload и фактический request использовали один URL. | Нет изменения artwork или layout; только согласован asset request. |
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

The DOM contract passed for all 56 captured states: horizontal overflow was zero, unnamed visible focusable controls were zero, and images without `alt` were zero. Reduced motion was exercised at the 768px viewport. A separate browser request check confirmed that the preload and CSS background request both resolve to `/static/img/bg-cosmos.jpg?v=102`.

## Automated verification

| Check | Result |
|---|---|
| `npm run build:frontend` | PASS; generated CSS bundle `app.eba1f8ac8f0c.min.css` |
| `python3 scripts/check_design_contract.py` | PASS |
| `python3 scripts/check_visual_contrast.py` | PASS; all declared core pairs remain above thresholds |
| `python3 scripts/check_cache_busting.py` | PASS; main asset version remains `v102` |
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

> **SHIP IT**

The product was not made louder or more decorative. The final change set removes two concrete visual/performance inconsistencies and restores trustworthy screenshot evidence for the important authenticated surfaces. OracleAI remains a bounded, quiet cosmic interface whose pixels, transitions and visual states are intentional.

## References

[1]: [`docs/DESIGN_SYSTEM.md`](DESIGN_SYSTEM.md) — token, geometry, motion and responsive contracts.
[2]: [`docs/VISUAL_QA.md`](VISUAL_QA.md) — existing visual QA methodology and acceptance surface.
[3]: [`scripts/visual_qa_capture.py`](../scripts/visual_qa_capture.py) — reproducible RU/EN breakpoint capture.
[4]: [`scripts/check_visual_contrast.py`](../scripts/check_visual_contrast.py) — numerical contrast check.
