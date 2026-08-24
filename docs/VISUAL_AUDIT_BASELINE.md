# Финальный visual UX/UI audit OracleAI

**Дата:** 24 августа 2026 года

**Ветка:** `feat/agent-first-harness`

**Область:** Mini App shell, home/agent hub, Tarot, Mira, natal chart, compatibility, placements, profile/history and public bilingual landing.

## Итог

Второй UX/UI проход сохранил концепцию **Astral Midnight** и существующие avatar signatures, но сделал интерфейс более последовательным: сначала одно действие и один результат, затем доказательства и дополнительные инструменты через disclosure. Основная постоянная информация теперь ограничена именем агента, ожидаемым результатом, CTA и коротким evidence label. Остальные quick tools and question ideas are progressive rather than wall-of-text.

## Live Tarot flip

Tarot was tested through the local FastAPI preview with an authenticated QA profile and a real API round trip. The question was `Что мне важно увидеть в ближайшем шаге?`; the draw returned three cards; the first card was opened by an actual click, not by DOM injection. Post-click DOM verification recorded `.tcard.open`, a populated card title/meaning, and the opened-card progress state `1 из 3`.

Evidence files:

- Full post-click viewport: `docs/assets/ux-qa/tarot-opened-live.webp`.
- v98 card-face crop: `docs/assets/ux-qa/tarot-card-opened-v98.webp`.
- PNG crop: `docs/assets/ux-qa/tarot-card-opened-v98.png`.

The Tarot interaction keeps the face image and meaning hidden until reveal, uses a short tactile flip/tilt, and disables non-essential motion under `prefers-reduced-motion`. No generic onboarding overlay remained above the active picker during the final interaction.

## Mobile horizontal-scroll QA

A reproducible CDP runner checked real viewport widths **320, 375 and 390 CSS px** with cache disabled. It measured `documentElement.scrollWidth`, `body.scrollWidth`, the app shell, agent cards, details panels, Tarot picker, Mira picker, compatibility form, placements and chart form/result containers. The final semantic rule counts page-level overflow or an actual `overflow-x:auto/scroll` container with excess width; harmless intrinsic overflow from transformed icons or line-clamp text is not reported as user-visible scrolling.

| Surface | 320 px | 375 px | 390 px | Result |
|---|---:|---:|---:|---|
| Page/app shell | 320 / 320 | 375 / 375 | 390 / 390 | No horizontal scroll |
| Agent hub/cards | 320 / 320 | 375 / 375 | 390 / 390 | No horizontal scroll |
| Tarot picker | 320 / 320 | 375 / 375 | 390 / 390 | No horizontal scroll |
| Mira picker | 320 / 320 | 375 / 375 | 390 / 390 | No horizontal scroll |
| Compatibility form | 320 / 320 | 375 / 375 | 390 / 390 | No horizontal scroll |
| Placements surface | 320 / 320 | 375 / 375 | 390 / 390 | No horizontal scroll |
| Chart form | 320 / 320 | 375 / 375 | 390 / 390 | No horizontal scroll |

The only confirmed issue was an inner horizontal suggestion-chip rail in the agent hub at narrow width. It was changed to a wrapping layout. The final report contains `horizontalOverflow: false` for all tested stages and widths in `docs/assets/ux-qa/mobile-overflow-metrics.json`.

## Agent and tool hierarchy

The agent hub now presents each guide as a compact article card with avatar, role/outcome, primary `Начать` action and a short evidence row. Capabilities, quick tools and question ideas appear in one native disclosure; a global `toggle` handler keeps only one disclosure open at a time. Count labels now use correct Russian and English singular/plural forms, so labels such as `1 инструмент`, `2 инструмента`, `5 инструментов`, `1 quick tool` and `2 quick tools` remain natural.

Mira's picker was tightened without weakening its evidence-first framing. The photo guide keeps the three practical capture conditions but removes the repeated phrase about filters, glare and relaxed fingers from the main sentence. The result continues to show visible observations first, while the map of zones and techniques stays behind a details disclosure. MediaPipe is described honestly as hand geometry/capture support; the UI does not claim line segmentation, diagnosis, fate prediction or medical inference.

Chart, compatibility, placements and profile/history surfaces already use the same general hierarchy: calculation or fact first, interpretation second, and deeper details in disclosure/modal surfaces. Their existing progress, error, precision and empty states were checked for safe wording. No new oversized or horizontally clipping container was introduced in the final pass.

## LLM-facing state audit

The UI is aligned with the actual backend contract. The backend can use an ordered provider chain, fall back when a provider or tool is unavailable, and ultimately return an offline reflective response. Tool failures are converted into neutral user-safe wording; reasoning content is intentionally discarded. The frontend exposes `Факты → интерпретация` / `Evidence → reflection` and tool names, but does not expose provider keys, internal retries, raw errors or chain-of-thought.

In the local visual preview, `LLM_PROVIDER=off` is intentionally used, so the preview is an offline/degraded environment rather than proof of production provider availability. Strict Telegram authentication remains unchanged outside `DEV_MODE`; the QA query path was used only by the local preview. User-facing error normalization continues to hide authentication/provider details and guide the user toward a safe next step.

## Public SEO copy audit

The Russian and English landing pages now describe the actual product surface more precisely: natal charts, Rahu and Ketu, Tarot and Lenormand, palm-photo observations, journaling and personal rituals. The structured data adds a concise `featureList` matching those claims, and the guide copy names all four current agents. The existing `__PUBLIC_BASE_URL__` tokens remain intentionally deploy-safe because the FastAPI public-template route replaces them from the request host; the runtime robots and sitemap routes also generate the public base URL dynamically.

No Similarweb traffic, Ahrefs/Semrush keyword, or stock-analysis claims were fabricated. A competitor SEO report would require an accessible target dataset and a defined competitor scope; the current work therefore improves first-party public copy and metadata only.

## Validation checklist

- `node --check` for every Mini App JavaScript file.
- `ruff check app tests scripts`.
- Full `pytest` suite with `LLM_PROVIDER=off`.
- Cache-busting consistency check after the v98 bump.
- Agent quality/routing check.
- `git diff --check`.
- Live Tarot draw, click-to-open state and screenshot evidence.
- Mobile widths 320/375/390 with page and component overflow measurements.
- Reduced-motion rules retained for the newly added interactions.
