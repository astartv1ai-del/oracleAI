# OracleAI — Visual Final Specification

Дата: 2026-08-27
Статус: **SHIP IT для проверенного web Mini App surface**

Этот документ фиксирует фактическую geometry baseline после pixel-precision pass. Он является источником истины для новых визуальных изменений; новые значения нельзя добавлять в отдельные screen-specific overrides без измерения и обновления этого файла.

## Composition

OracleAI использует mobile-first app shell с controlled floating frame на широких экранах. На мобильных устройствах контент занимает доступную ширину, а на tablet/desktop центрируется в самостоятельном frame, чтобы desktop не превращался в растянутую mobile-страницу.

| Breakpoint | Viewport matrix | Frame rule | Content gutter |
|---|---|---|---|
| Mobile | 320×720, 360×800, 375×812, 390×844, 430×932 | `width: min(100%, 520px)` | 16px; 14px legacy rule only at ≤360px where required by existing mobile contract |
| Tablet | 768×1024 | max-width 520px, floating frame | 22px |
| Desktop | 1024×768, 1440×900 | max-width 540px, controlled frame | 24px |
| Wide | 1920×1080 | max-width 540px, centered frame with restrained atmosphere | 24px |

The production QA matrix covers all nine required viewport sizes in both Russian and English. The main static frame has no horizontal overflow in the tested states.

## Global tokens

The base spacing unit is 4px. The primary rhythm uses 8px, 12px, 16px, 20px and 24px increments. Section gaps use 20px; card gaps use 12px. The primary touch target is 44px. Standard control radius is 14px, card radius is 20px, and modal/sheet radius is 24px or larger when the surface needs a stronger boundary.

| Primitive | Final value |
|---|---:|
| `--precision-mobile-gutter` | 16px |
| `--precision-desktop-gutter` | 24px |
| Section gap | 20px |
| Card gap | 12px |
| Control height | 44px minimum |
| Navigation visual height | 70px capsule / 82px allocated area |
| Frame radius | 30px desktop, 26px hero |
| Card radius | 20px |
| Focus outline | 2px solid accent, 3px offset |

## Typography

Display headings use Cinzel/Georgia and body text uses Plus Jakarta Sans/Arial. Headings follow the shared scale rather than screen-specific arbitrary sizes: H1 32px, H2 24px, H3 20px, body 14px, body-large 16px, caption 12px and labels 11px. Long Russian and English strings use `overflow-wrap: anywhere` only as a last-resort containment rule; the preferred behavior is readable wrapping inside the controlled content frame.

## Header and navigation

The header is a three-column grid: user identity at the start, brand lockup centered, and notification control at the end. It has a 64px minimum mobile geometry and a 44px notification/user touch target. The bottom navigation uses four equal segments inside one 20px-radius capsule. The active segment is represented by one restrained gold indicator rather than multiple competing dots or glows. Reduced-motion mode disables indicator transitions, ambient animations and hero motion without hiding content.

## Home screen

The Home screen follows this vertical order: hero ritual, seasonal moment, daily rhythm, moon calendar, personal forecast, card of the day, next action, and guide invitations. The hero has a bounded 360px height on mobile/tablet and desktop QA surfaces, with a 24px top content inset, 72px bottom reserve for CTA, and a full-width CTA with symmetric 16px insets. The title/date/lunar copy are contained inside the hero; the previous fixed-flex alignment clipping defect was removed.

| Home primitive | Final measured value at desktop QA |
|---|---:|
| App frame | 480×920px at 1280×1100 browser viewport |
| Header | 478×75px |
| Main content | 478×737px |
| Hero | 428×360px after final containment fix |
| Hero CTA | 426px wide, 44px high, 16px side inset |
| Daily rhythm card | content-driven; no fixed empty height |
| Bottom nav capsule | max-width 456px on wide frame |

## Chat, profile and result surfaces

Chat and Hub use the same frame as Home but place the primary task closer to the top of the screen. Agent cards use a 58px avatar, 20px card radius and 12px internal spacing. Chat tools remain at least 44px high and stack vertically on mobile to avoid tiny tap targets. Profile uses a stable hero, four-tab control and compact stat cards; history, memory and chart are progressive panes inside the same scroll model. Payment and tarot are validated through the baseline harness as dedicated states rather than inferred from Home styling.

## QA coverage

The corrected visual harness captures Home, Chat/Hub, Profile, Chart, History and Memory across Russian and English at 320, 360, 375, 390, 430, 768, 1024, 1440 and 1920 widths. The separate baseline harness also covers age gate, Payment, Tarot, profile chart modal and memory modal. In the final aggregate run: horizontal overflow was 0, unnamed focusable controls were 0, and images without an `alt` attribute were 0.

## Known boundaries

The desktop shell intentionally remains app-like and centered rather than becoming a full-width dashboard. Telegram-specific keyboard and safe-area behavior still requires manual device QA inside Telegram WebView; local browser runs validate the deterministic CSS/DOM contract, not every Telegram client implementation. Decorative overflow from the starfield is excluded from content overflow checks by design and does not receive pointer events.

## Change control

The final geometry layer lives in `miniapp/css/18-pixel-precision.css`. The visual QA harnesses accept environment-configured URLs through `ORACLEAI_QA_BASE_URL`, `ORACLEAI_QA_VISUAL_URL` and `ORACLEAI_QA_DESKTOP_URL`, so future CI or preview environments do not depend on a hard-coded port. The design contract checker explicitly validates the final import order including `18-pixel-precision.css`.
