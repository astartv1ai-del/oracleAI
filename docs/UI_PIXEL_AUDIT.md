# OracleAI — UI Pixel Audit

Дата baseline: 2026-08-27.

## Baseline environment

Проверена `miniapp/index.html` через локальный static server на viewport примерно 893×766. Страница загружается, но основной экран не отображается: видны белый фон, чёрные декоративные частицы и вертикальный scrollbar; интерактивные элементы не обнаружены. Console показывает вызовы Telegram WebView theme/viewport/safe-area APIs. Это означает, что локальный static-server baseline не воспроизводит production static mount полностью либо приложение ожидает Telegram runtime/API bootstrap. До оценки пиксельной геометрии необходимо обеспечить deterministic preview mode.

## Initial visual defects

| Area | Baseline observation | Severity |
|---|---|---|
| App bootstrap | Main UI is absent in local preview; only decorative particle layer is visible | blocker |
| Preview environment | Assets/scripts use `/static/...` paths while the raw miniapp directory is served at `/` | high |
| Layout measurement | Content frame, cards, header and bottom navigation cannot be measured until bootstrap succeeds | blocker |
| Accessibility/interaction | No visible interactive elements in baseline viewport | high |
| Responsive behavior | Not measurable before deterministic app bootstrap | high |

## Required next step

Add a development/preview bootstrap that does not require Telegram-only runtime state and supports root-relative local assets, then rerender at mobile and desktop viewports. Do not approve visual reconstruction based on the blank baseline.

## QA Home baseline capture

После создания dev QA пользователя real FastAPI preview rendered the Home screen at approximately 893×766 viewport. The application frame is centered at roughly 334px wide with large desktop side margins and a strong decorative starfield. The visible frame includes a compact header, large Today hero card, seasonal card, rhythm card, a mood/check-in row and four-item bottom navigation. The viewport captures only the upper portion of the scrollable Home screen; the frame has an internal vertical scrollbar.

Initial visual observations: the central app shell is legible and coherent, but the desktop presentation is phone-width rather than a responsive desktop composition; navigation labels are very small; the hero CTA is visually dominant; and the decorative background competes with the narrow shell. The yellow QA overlay markers are browser annotations, not product UI. This baseline is sufficient to measure Home, but other screens still require separate QA captures.

## Post-precision Home geometry

The final precision layer was rendered through the real FastAPI preview. At the desktop QA viewport (1280×1100), the application frame measured 480×920px, the header 478×75px, the content area 478×737px, the hero 428×375px, the CTA 384×46px, and the bottom navigation capsule 420×82px. The hero title was fully contained within the hero bounds (`contained: true`), and the document had no horizontal overflow.

The reference-390 capture shows a more intentional mobile hierarchy: the header stays compact, the hero CTA spans the content frame with symmetric 16px insets, cards share a 12px rhythm, and the bottom navigation remains large enough for touch while using less visual mass. The source modules remain visually stable and the updated CSS is isolated in `18-pixel-precision.css` as a final controlled layer.

## Visual critic findings after precision layer

The mobile screenshot reveals a critical hierarchy defect: the hero title begins above the visible hero content area and is visibly clipped at the top on the 375px capture. The desktop screenshot shows the same issue in a subtler form, with the first line of the Russian hero heading clipped behind the hero boundary. This is a real layout regression caused by the fixed hero height combined with content positioning, not a screenshot artifact.

The CTA, seasonal card, rhythm card and navigation have strong alignment and the frame reads as premium. The next fix must preserve those alignments while giving the hero body a safe top inset and ensuring title/date/ritual label/mood copy remain within the hero's vertical content box at 320px, 375px and 430px widths. Decorative starfield is acceptable as atmosphere but should remain visually subordinate to text contrast.

## Post-fix critic checkpoint

The 390px Home screenshot now keeps the full hero date, ritual label, greeting, lunar copy and CTA inside the hero bounds. The previous clipped heading defect is resolved. The 375px Chat screenshot shows a usable agent hub with readable hierarchy, visible Start CTA, 44px-class controls and no horizontal overflow; the agent card/tool list remains vertically scrollable rather than forcing a dense desktop grid onto mobile.

## Profile and desktop Chat critic checkpoint

The profile capture is structurally coherent: the subscription surface is clear, payment choice is visible, and the primary payment action is large enough. Its main remaining concern is information density below the fold; this is acceptable for a scrollable profile surface and should not be solved by shrinking typography.

The desktop Chat/hub capture scales the same shell to a controlled 520px-class frame, keeps the agent card centered, and avoids excessive line length. The frame is intentionally app-like rather than a stretched SaaS dashboard. The main residual issue is that the decorative desktop background is stronger than the content frame on the right side; this is a polish concern, not a geometry blocker.

## Corrected Profile/History capture

After replacing the stale navigation selectors, the visual QA harness captured the actual Profile screen and its History tab rather than the Payment screen. The 375px Profile state has a clear profile hero, four-tab control, two-column stat cards and persistent bottom navigation. The History state preserves the same tab geometry and presents conversations, readings and diary entries as compact rows with visible chevrons. Both states are readable, contained and suitable for the existing scroll model.

The corrected harness now captures six states per locale/viewport: Home, Chat/Hub, Profile, Chart, History and Memory. Across eight locale/viewport runs it reports zero horizontal overflow, zero unnamed focusable controls and zero images without alt attributes.

## Final acceptance verdict

The final visual matrix covered 18 locale/viewport runs: Russian and English at 320, 360, 375, 390, 430, 768, 1024, 1440 and 1920 widths. Each run covered Home, Chat/Hub, Profile, Chart, History and Memory; the separate baseline harness covered Age Gate, Payment, Tarot, chart modal and memory modal.

The final aggregate reported zero horizontal-overflow states, zero unnamed focusable controls and zero images without an `alt` attribute. The geometry probe confirmed hero title containment at 375, 390 and 1440 widths after the flex-alignment clipping fix. Design tokens, import order, contrast, static asset references, cache busting, frontend bundle generation and desktop layout audit all pass. A stale visual QA selector and a missing payment locale contract were also corrected before the final run.

The verified scope is marked **SHIP IT** for the deterministic web Mini App surface. Manual Telegram WebView keyboard/safe-area QA and production deployment QA remain operational checks outside this sandbox acceptance run.
