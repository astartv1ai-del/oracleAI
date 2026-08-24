# OracleAI — Premium UI/UX audit

**Дата:** 2026-08-24  
**Ветка:** `feat/agent-first-harness`  
**Scope:** Mini App, public landing, admin panel, chat/history, tools and responsive states.

## Executive diagnosis

Текущая оболочка уже функциональна и mobile-first, но на desktop она всё ещё воспринимается как увеличенный Telegram Mini App: рабочая область слишком декоративна, часть controls не имеет единой геометрии, а visual language смешивает premium cosmic background с emoji-like quick actions and oversized ritual cards. Главный structural issue — не отдельный дефект одной кнопки, а отсутствие явного desktop composition contract: header, content column, sidebar, toast and modal layers используют разные alignment anchors.

## Screen-by-screen findings

| Surface | Current issue | Priority | Direction |
|---|---|---:|---|
| Global shell/header | Logo/brand alignment depends on mobile canvas; desktop header has excess empty span and inconsistent center anchor | P0 | Introduce one desktop grid: fixed navigation rail + bounded content column + utility rail/header actions |
| Toast/notifications | Mobile-style centered toast is too dominant on desktop and competes with content | P0 | Desktop top-right stack; mobile bottom safe-area stack; same semantic token and motion |
| Home/landing inside Mini App | Hero and daily cards combine too many decorative layers, emoji and copy blocks; content priority is unclear | P0 | One primary action, compact evidence row, secondary details on demand |
| Agent hub | Cards are improved but desktop still inherits mobile card density and narrow text widths | P1 | Desktop 2×2 capability grid; mobile single-column cards with progressive disclosure |
| Chat workspace | Chat header/session affordances and composer alignment differ by viewport; desktop needs reading column discipline | P0 | Desktop conversation workspace with fixed rail, readable max line length, anchored composer |
| Sidebar/history | Search exists but history needs explicit active/archive grouping and stable result geometry | P1 | Search-first history list, archive badge, keyboard/focus states |
| Tarot | Tool card and reveal states work, but desktop should use larger stage and restrained supporting metadata | P1 | Responsive spread stage, card details column on desktop, stacked details on mobile |
| Mira/palm | Upload/guide surface is visually tall for low content and can look like a form rather than a guided capture flow | P1 | Compact capture panel, clear evidence boundary, result sections with progressive disclosure |
| Urania/chart | Forms and placement tables need shared field widths, grid anchors and less repeated explanatory text | P1 | Desktop two-column form/results; mobile stacked sections |
| Compatibility | Result surface has good semantics but inherits generic widget padding and weak desktop max width | P2 | Shared metric/result card primitive |
| Profile/history | Modal and list surfaces use different spacing/radius conventions | P2 | Shared drawer/modal/list tokens and consistent empty states |
| Tool sheet | Bottom-sheet behavior is correct for mobile but should become contextual popover/side panel on desktop | P1 | Breakpoint-specific interaction model |
| Admin | User table needs safe platform context and consistent wrapping; local dev has no seeded ADMIN_ID for visual login | P1 | Add coarse platform/mode/viewport fields to user drawer/table; keep auth strict |
| Public landing | Existing copy is informative but visual hierarchy remains closer to utility page than premium product landing | P0 | Distinct hero, trust/evidence strip, capabilities grid, restrained CTA, bilingual parity |

## Mantra removal dependency map

The feature is present in product code and tests even though some prior UI wording was softened. Removal must cover the catalog, service behavior, API reachability, agent routing copy and regression tests.

- `app/core/practices.py`: mantra category and `mantra_*` practice records.
- `app/core/agents/specs.py` and `app/agents/lilith/SYSTEM.md`: routing instruction mentioning practice/mantra.
- `app/core/skills.py`: practice description includes `mantra` category.
- `app/data/seed.py`: reminder setting mentions practices and mantras.
- `tests/test_api_growth.py` and `tests/test_practices.py`: direct mantra fixtures and assertions.
- Existing practice engine and active-practice persistence: must retain non-mantra practices and remove only mantra records/routes/references.
- Historical docs/changelog may retain factual migration history, but current UI/product documentation must not advertise the feature.

## Responsive audit contract

The redesign will be validated at **320, 375, 390, 768, 1024 and 1280 px**. Each major surface must satisfy: no accidental horizontal overflow; a single primary alignment anchor; text wraps without clipping; controls remain reachable; desktop does not render a centered mobile canvas; mobile does not inherit desktop side-by-side density; all non-essential motion respects `prefers-reduced-motion`.

## Design-system target

Use a restrained **Astral Midnight / Editorial Observatory** system rather than a full rebrand: deep ink background, warm ivory text, muted lilac secondary text, one champagne accent and one mint status accent. Standardize spacing on 4/8 px increments, radii into three levels, shadows into two levels, and type into display/body/meta scales. Cosmic avatars remain identity anchors; decorative stars, emoji and glow effects become secondary and must never compete with labels or CTAs.


## v103 implementation checkpoint

В v103 добавлен отдельный premium foundation layer поверх существующих модулей. Он вводит 4/8 spacing tokens, control/card/panel radii, two elevation levels, muted ink/champagne/lilac/mint semantic aliases, общий focus ring и reduced-motion contract. Старые CSS aliases оставлены совместимыми, поэтому перестройка не требует рискованного одномоментного переписывания всех исторических модулей.

Desktop shell теперь использует фиксированный левый rail, bounded reading canvas и симметричную utility-зону header. Бренд привязан к началу workspace, а не к псевдоцентру мобильного canvas. Toast на desktop закреплён справа сверху внутри viewport; на mobile он возвращается вниз с учётом safe-area. Home получил явные `home-primary`/`home-secondary` зоны: hero и daily rhythm находятся в основном столбце, lunar/forecast/card/next-action — в редакционной вторичной колонке. Hub на desktop использует 2×2 grid, а mobile сохраняет одну колонку и progressive disclosure.

Визуальная проверка live v103 на широком экране подтвердила: sidebar остаётся самостоятельной навигацией, логотип и notification control имеют единый header anchor, home не выходит за viewport, а в daily practice block больше не появляется legacy mantra entry. После перезапуска preview API логировал отфильтрованные legacy codes `mantra_gayatri`, `mantra_lakshmi`, `mantra_moon` и `mantra_shiva`; они не были возвращены Mini App.

## Удаление mantra functionality

Удалены встроенная категория и четыре catalog records из `app/core/practices.py`. Обновлены routing copy Lilith, practice tool schema, Telegram growth/menu copy, seed setting, diary topic keywords, Mini App quick prompt и ritual widget. Practice service дополнительно отбрасывает legacy DB overrides с `mantra_` code или `mantra` category, чтобы старые admin content rows не могли вернуть feature после деплоя. API regression проверяет, что поддерживаемая карточка открывается, список не содержит category `mantra`, а удалённый code возвращает 404.

## Validation snapshot

| Check | Result | Note |
|---|---:|---|
| `node --check` for Mini App/admin JS | PASS | All files parsed successfully |
| `py_compile` for changed Python modules | PASS | Chat archive guard and practice service included |
| Targeted practice + growth API tests | PASS | 53 tests passed |
| Cache-busting checker | PASS | Mini App assets synchronized at v103 |
| Mobile overflow runner | PASS | 8 surfaces × 3 widths; document horizontal overflow remained false |
| Desktop live visual check | PASS | Wide home/sidebar/header composition rendered without page overflow |
| Admin visual login | BLOCKED HONESTLY | Local dev DB has no authorized seeded owner; strict auth was not bypassed |

The current checkpoint covers the critical shell/home/header/toast and mantra-removal P0 work. Tarot, palm, chart, compatibility, profile, public landing and admin still require a dedicated visual pass before claiming the redesign complete.


## Final visual pass notes

Live проверка hub показала, что desktop breakpoint сохраняет отдельный rail и bounded content canvas; при ширине ниже 900 px интерфейс корректно возвращается к mobile/tablet single-column режиму, а drawer/sidebar остаётся доступным. Chat проверен из persistent sidebar: header агента, reading area, session row и composer имеют общий горизонтальный rhythm, textarea не расширяет viewport, а быстрые подсказки остаются отдельным нижним слоем.

Public landing переписан в RU/EN parity: hero теперь строится вокруг спокойного value proposition, одной primary CTA и secondary exploration CTA; справа используется существующий Oracle mark в CSS orbital composition без новых внешних изображений. Добавлен factual principles strip (`16+`, consent-based memory, no verdicts), capability grid, three-step workflow и safety block. На desktop это asymmetric editorial grid, на mobile — последовательный stack с full-width controls и без accidental horizontal overflow.

Admin stylesheet получил тот же ink/champagne/muted foundation, более устойчивые table/drawer widths, focus states и mobile collapse at 860/480 px. Визуальный admin login locally не заявляется как пройденный: dev database не содержит авторизованного owner context, поэтому strict auth не обходился.

## Remaining product-quality caveat

Некоторые старые component modules всё ещё содержат emoji как content-level symbols (например, lunar phase or Tarot metadata); они не используются как role/navigation icons и не нарушают новую alignment system. Meaningful agent avatars сохранены. Final scope утверждается как completed only for the audited surfaces above; backend/API behavior, Tarot assets, palm/photo capture, chart/placements, compatibility and history remain covered by automated or mobile QA, while any future visual iteration should use this report as the baseline.
