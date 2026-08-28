# OracleAI Telegram Bot — Capability and UX Audit

## Executive finding

The current Bot already reaches most domain engines through shared services, but its presentation layer is still **menu-first, text-heavy, and state-fragmented**. The Mini App has a richer home, session, recovery, history, visual chart, and capability-discovery model. The redesign therefore keeps the Bot as a native conversational surface rather than copying Mini App screens into inline keyboards.

## Capability matrix

| Capability | Mini App | Bot before redesign | Backend source | Gap / target |
|---|---|---|---|---|
| Onboarding | Structured, resumable bootstrap | FSM with mandatory 16+ gate, strict formats, no back/edit/confirm | `users`, `astro`, `geo`, `/api/me` | Remove visible gate; add locale suggestion, tolerant parsers, back/resume/confirm |
| Profile | Full editable profile, privacy, memory, notifications | Status card plus a few toggles | `/api/profile`, `users`, `dialog` | Make Bot profile a settings hub |
| Language | RU/EN state and UI | Mixed hardcoded Russian with partial English copy | `users.lang`, Mini App i18n | Centralize Bot copy and language selector |
| AI chat | Routing, starters, sessions, recovery, tool widgets | Agent picker first, free text after selection | `services.chat`, `core.agents`, `dialog` | Default Oracle routing, starters, staged progress, contextual next actions |
| Agents | Agent cards and capability chips | Agent list hidden behind Ask | `core.agents` | Keep shared agent registry; expose change-guide action contextually |
| Memory | Explicit opt-in and management | Brief profile preview | `dialog`, `/api/memories` | Add explain/pause/view/delete controls |
| Diary | Daily ritual and archive | Write-only flow with short preview | `dialog`, `practices` | Reframe as reflective journal with meaningful archive |
| Today | Home ritual, sky/card modules, next action | Subscription-gated forecast plus text | `services.chat`, `astro`, `agent_core` | Add practical “small step” and contextual CTA |
| Astrology / natal | Visual chart and evidence/provenance | Long text list | `astro`, chart APIs, `cards` | Reuse canonical chart and send visual artifact/PDF path |
| Natal techniques | Selector and product contracts | No Bot selector | `chart_products`, domain contracts | Persist and surface canonical technique choices |
| Tarot | Visual cards, reveal, share | Textual card names with text reveal | `core.cards`, `core.tarot`, `readings` | Send canonical card image and progressive reveal |
| Palm / Mira | Image upload and visual evidence widgets | Quality/result text only | `core.palm`, `palm_readings` | Show image/evidence status and limitations |
| Compatibility | Rich widget flow | Date-only FSM and text result | `skills`, `readings` | Add tolerant date parsing and next actions |
| Matrix | Dedicated visual/structured surface | Text list | `core.matrix` | Preserve backend calculation, improve hierarchy |
| Reports | History, generation state, PDF | Ready reports only; Mini App handoff for pending | `readings`, PDF pipeline | Add Bot-native request/progress/document delivery |
| History | Unified archive | Profile list of reports only | `/api/history`, `readings`, `dialog` | Create research-library view with source categories |
| Sharing | Deep links, share cards | Tarot/card sharing only | `cards`, referral links | Add result-aware share actions |
| Payments | Canonical v2 catalog and lifecycle | Shared billing but simple offer → invoice | `services.billing`, `entitlements` | Add offer/benefit/price/status/unlocked states |
| Crystals | Canonical balance/lots/usage | Legacy balance text | `billing`, `monetization`, `entitlements` | Show pre-spend confirmation and remaining balance |
| Subscription | Canonical tier/quota/lifecycle | Legacy `users.sub_active` copy | `entitlements`, `subscription_state` | Consume same snapshot and explain premium value |
| Notifications | Settings and localized UI | Morning push toggle | scheduler, `users` | Add localized notification preferences and dedupe |
| Error recovery | Inline recovery components | Generic text and menu | shared services | Every state gets retry/back/cancel/continue |

## Current architecture risks

The largest risk is not domain correctness; it is **duplicate interaction logic**. Hardcoded copy, menu composition, progress messages, payment phrasing, and language decisions are spread across handlers. The new Bot layer will introduce reusable Telegram presentation primitives while leaving access, calculation, pricing, and entitlement decisions in shared backend services.

The second risk is FSM fragility. The current onboarding has an `age` state that is only a product gate, no persisted step cursor, and no compact confirmation checkpoint. The replacement will preserve the existing deterministic chart calculation and geocoding boundaries, but make the presentation resumable and forgiving.

The third risk is result degradation. Chart and Tarot domain assets already exist, but the Bot often renders only text. The implementation will reuse those renderers rather than create a second calculation or visual system.

## Design direction

The Bot will have five primary native actions: **Ask**, **My chart**, **Tarot**, **Mira**, and **My research**, with Profile/Settings as a secondary hub. `/start` for a returning user becomes a short home message with one clear primary action and contextual resume choices. Within a conversation, the default is Oracle routing; choosing a specialist remains available but is not mandatory.

The Bot will use one status message that is edited through typed states (`thinking`, `using_tool`, `calculating`, `generating_report`, `waiting_for_payment`, `success`, `recoverable_error`). It will not emit a stream of fake dots or claim calculations that did not run. Long output will be chunked at semantic boundaries and end with context-specific actions.
