# Visual UX audit baseline

Date: 2026-08-24. Scope: OracleAI Mini App shell, home screen and agent navigation in local dev preview.

The first viewport is a centered narrow mobile-style canvas even on a desktop-sized browser. The cosmic atmosphere is distinctive and the champagne/lilac hierarchy is coherent, but the screen contains several simultaneous attention layers: dense starfield, nebula, silhouette, header, hero orb, onboarding/ritual card, forecast card, agent invitation section and fixed bottom dock. This works as a moodboard, but not yet as a calm product surface.

Observed improvement targets are: shorten persistent explanatory copy; reserve the strongest glow/animation for the active action; keep proof metadata secondary and collapsible; prevent badges and header metadata from competing with the agent name; make long agent/tool descriptions wrap rather than ellipsize critical meaning; and reduce the number of always-visible sections on narrow screens. The existing bottom dock is legible and the hero has a clear CTA, but the desktop screenshot shows unused side space while the app canvas remains phone-width, so a bounded reading column with deliberate desktop framing is preferable to uncontrolled stretching.

The current onboarding can be dismissed and the home screen remains functional. The dev query does not authenticate subsequent API calls automatically, so authenticated agent/tool states must be validated through existing API tests and static rendering checks; this is recorded separately in LOCAL_VISUAL_QA.md.

## Agent hub checkpoint

The agent hub has strong visual identity and consistent avatar treatment. On the narrow viewport, however, every card shows the avatar/header, outcome, last message, evidence badge, online label, CTA, three suggested questions, a section label and multiple tool rows at once. Urania additionally shows a four-tile Vedic block, making the page feel like a feature catalog rather than a calm choice. The screenshot also shows one-line ellipsis in several secondary descriptions; this preserves height but hides useful meaning. The redesign should keep one primary action and one or two compact capability previews visible, with the full tool set revealed on demand.

## Tarot checkpoint

The Tarot picker has a good single-column hierarchy, but it currently shows school selector, provenance sentence, spread selector, hint, three prompt chips, question field, status, CTA, chat composer, suggestions and onboarding overlay in the same viewport. The overlay can obscure the active Tarot surface, which is a major first-use distraction. The school row should become a compact selected-school card with a progressive details disclosure; the provenance note should be a short status line; prompt chips should be reduced or horizontally scrollable; and the card stage should prioritize card image, position and short meaning, with full evidence/combination detail revealed after all cards are opened.

## v95 redesign checkpoint

After the first density pass, the hub renders each agent as a compact card with avatar, role, one-line outcome/description, proof row and a single `Показать возможности` disclosure. The details summary is keyboard-accessible and the browser exposes separate tool buttons only after expansion. Visual annotation boxes are browser QA markers, not page elements; the underlying card geometry remains inside the centered app canvas.

## Chat guide lifecycle diagnostic

The live console showed `pending: null` and `chat-guide: true` after opening the agent's primary `Начать` CTA. This is expected for a normal empty chat and is not the Tarot widget path. The generic guide was shortened; tool-specific flows are guarded so they should not display it after the tool callback creates a pending widget. The next interaction check should close the guide, open the chat's `Инструменты` sheet and launch the Tarot action from there.

## Quantitative Tarot QA

The live v95 Tarot picker reported no horizontal clipping descendants. Its widget measured 378px wide by 587px high inside the reading column; two prompt buttons measured 261px and 237px wide with wrapped copy; the draw button measured 346px wide. The main app surface had no extra scroll beyond its intended internal container, and no `#intro`, `#chat-guide` or modal overlay was present during the active Tarot tool. This confirms the density pass reduced clutter without producing a new overflow layer.

## Mira capture checkpoint

The live Mira capture surface presents the two primary upload actions as balanced side-by-side cards with large touch targets, short labels and file constraints. The guide block is visually distinct, the disclaimer is separated from the actions, and the composer remains outside the capture card. The screenshot showed no overlap between upload cards, bottom composer or dock. The remaining opportunity is to make the later result/evidence surface progressively reveal technical details rather than showing quality, geometry, limitations, prompts and disclaimer at once.

## v96 final hub checkpoint

The v96 hub screenshot shows the four agent cards in a much calmer stack. The repeated online label is gone; each card keeps one evidence badge, optional tool count, compact avatar/header, a short role/outcome and a clear `Начать` CTA. The full capability list is behind a native disclosure row. The fixed bottom navigation remains visually separated from the cards and no element crosses the app canvas boundary.

## Expanded hub metrics

With Lilith details open, the four card widths remained 434px within the 480px app canvas and only one details panel was open. The expanded card measured 413px high and the others 194px. The browser reported no visible horizontal overflow in the page, but intrinsic `scrollWidth` was larger on transformed avatar/sprite and line-clamped text nodes; this is a follow-up QA item to distinguish harmless intrinsic paint overflow from any real visible clipping before commit.

## v97 final browser checkpoint

The final cache-busted v97 home and hub renders preserve the Astral Midnight concept, but reduce the active visual hierarchy to one hero action, one evidence row and one disclosure row per guide. The browser showed balanced cards, readable primary CTAs, clean bottom navigation separation and no visible overlap. The motion layer is intentionally restrained: avatar signatures and tool/card hover feedback are subtle, and all new motion is disabled under `prefers-reduced-motion`.
