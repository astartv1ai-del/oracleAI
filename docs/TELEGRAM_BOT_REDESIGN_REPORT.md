# OracleAI Telegram Bot Redesign Report

## 1. Current state

The Bot was not a separate domain implementation, but it still felt like a reduced channel. The backend already contained canonical chart, Tarot, palm, memory, entitlement, billing, and history capabilities; the Bot presentation did not expose them with the same hierarchy. The main gaps were a mandatory visible age screen, strict date/time formats, no language-first entry, no confirmation or edit checkpoint, menu-first navigation, text-only natal results, incomplete premium discoverability, and long-running actions that left the user staring at a chat.

## 2. Product redesign

The Bot now follows a Telegram-native information architecture. The home surface has one primary conversational action, followed by compact exploration and account rows: Ask Oracle, My chart, Tarot, Mira, My research, Today, Premium, Profile, Settings, and Help. Mini App remains an optional full-surface handoff rather than the only place where the product is usable.

The redesign does not move domain decisions into Telegram handlers. Calculations, entitlement checks, payment prices, report generation, memory storage, and ownership remain server-side. The Bot adds only presentation orchestration, localized copy, state recovery, and contextual next actions.

## 3. Onboarding

Onboarding is now language-first and no longer renders a duplicate 16+ screen. The legacy `age:confirm` and `age:decline` callbacks remain harmless for stale messages and old tests, while the normal `/start` path proceeds to language selection. API and direct shared-service callers still use the fail-closed age policy; the Bot explicitly uses the Telegram surface policy.

The flow stores `onboarding_step`, supports `/start` resume, offers back/edit controls, and shows a compact profile confirmation before chart interpretation. Birth dates accept numeric, ISO, Russian named-month, and English named-month forms. Incomplete or impossible dates receive a specific error rather than a generic failure. Birth time accepts `14:30`, `1430`, AM/PM forms, approximate choices, and unknown-time choices. Unknown or approximate time is persisted honestly and never presented as exact.

After confirmation, the user selects one of the project’s canonical chart-reading choices: astrology or Lenormand. The selected technique and version are persisted. Persona choice remains optional and is followed by a deterministic first insight from the saved chart before the next question is requested.

## 4. Language

RU and EN selection is available at onboarding and from Settings. The main menu, home, settings, premium plan selector, profile, chat starters, progress statuses, and new Bot callbacks use the selected locale. Returning users can change language without being pushed back into onboarding.

The project still has legacy deep-domain copy in Russian inside older Tarot, palm, compatibility, and practice messages. Those surfaces remain functional and safe, but a complete editorial localization pass is a remaining release item rather than something silently claimed as complete.

## 5. Chat

The default Bot interaction is now conversational. A user can write a question directly after onboarding; specialist selection is available as an optional action instead of a mandatory gateway. Three localized starter prompts help a new user begin without forcing a form: a daily focus question, a relationship question, and a decision question.

The Bot uses the shared `services.chat.ask` path, including routing, safety classification, entitlement checks, usage accounting, evidence-grounded agent execution, memory policy, and message persistence. No client-provided price, capability, or agent tool list is trusted.

## 6. Animation / progress

A reusable `BotStage` contract and `Status` editor now represent `thinking`, `using_tool`, `calculating`, `generating_report`, `waiting_for_payment`, `success`, and `recoverable_error`. AI chat and palm analysis use typed status messages. Tarot already had progressive card reveal and remains on that path. Report generation now shows an explicit building state and returns the purchase on failure.

Progress messages are operationally honest. They do not claim a tool or calculation ran unless the shared service reached that stage. Recoverable errors offer a retry or menu path instead of leaving the conversation in a dead end.

## 7. Natal

The Bot natal surface now reuses `app/core/chart_rendering.py` to send a compact visual chart when the renderer is available, followed by the structured chart facts and precision limitation. Unknown or approximate birth time suppresses houses and Ascendant claims in the confirmation and display path.

The Bot’s paid report shelf now offers native report building through the shared `agent.build_report` service. The entitlement is consumed once before generation and restored if generation fails. The report is persisted through the canonical append-only reports repository and delivered in semantically chunked Telegram messages.

## 8. Tarot

Tarot continues to use the canonical draw-first, interpretation-second contract. The Bot shows a progressive reveal, persists the exact cards and positions, then sends the AI interpretation. When the existing renderer is available, it also sends a visual reading card generated from the persisted draw rather than drawing again. Outcome feedback and share-card controls remain attached to the result.

This keeps card identity, orientation, position, and ownership in server-side records; Telegram only renders the result.

## 9. Practices

The Bot no longer frames practical work as “mantras”. The entry point is now “Практики и маленькие шаги”, with copy describing short exercises for attention, decisions, and self-care. Existing practice lifecycle logic remains intact: start, daily step, streak, completion, stop, and reminders. The catalog and API contracts are unchanged, so Bot and Mini App continue to consume the same program state.

## 10. Bot/Mini App parity

The following are now aligned through shared services or canonical storage: chat routing and safety, entitlements and monthly AI limits, price-book checkout, annual plan selection, Crystal balance and spending, profile identity, memory toggle, notification toggle, chart evidence, Tarot draw/interpretation, report generation, and purchase state.

The Bot additionally has native Telegram presentation primitives: inline keyboard navigation, message editing, progressive reveal, visual media delivery, and compact recovery paths. The Mini App remains richer for advanced chart exploration and archive browsing, but the Bot can now support the primary journey without requiring the Mini App for first value, chat, Tarot, profile, premium purchase, Crystal usage, or report delivery.

## 11. Security

Security checks were preserved and extended. The Bot does not accept client prices or client entitlement decisions. Direct API/shared-service calls retain the fail-closed age policy, while the Bot exemption is explicit and scoped to `surface="bot"`. Ownership remains enforced through repository queries for reports, readings, threads, memories, and purchases. Payment handling remains idempotent at the existing billing boundary.

Account anonymization now also clears the new onboarding cursor, time precision, and natal technique fields. No personal text is added to analytics by the redesign; new events carry bounded step, locale, technique, and surface dimensions.

## 12. Performance

Existing asynchronous geocoding and chart calculation boundaries remain in place. New visual rendering uses `asyncio.to_thread` so Pillow/chart rendering does not block the event loop. Long AI and report results are split at semantic boundaries, reducing malformed or inaccessible Telegram messages. Status editing keeps the user informed without creating a burst of fake progress messages.

## 13. Tests

Added `tests/test_bot_telegram_native.py` covering natural RU/EN date parsing, impossible-date rejection, exact/approximate/unknown time semantics, age-gate absence from the visible main menu, localized language controls, annual plan callback contracts, and persisted onboarding/technique fields.

The focused Bot FSM, new Telegram-native acceptance tests, and migration tests pass. The complete Python suite also passes with one pre-existing skipped test. Python compilation of the modified application succeeds, and `git diff --check` is clean before release commit.

## 14. Remaining blockers

The real remaining blockers are operational rather than architectural. A live Telegram journey still needs a configured bot token, real provider responses, and a test account for end-to-end verification of media delivery, invoice confirmation, and webhook retries. Deep legacy feature copy is not fully localized to EN yet. The Bot sends native text reports, but a dedicated native PDF document-delivery action and a full reopenable conversation browser remain follow-up work for a stricter parity release.

The implementation is therefore suitable for a controlled staging rollout, not a claim that all visual/editorial parity is finished. Before broad launch, run the RU and EN journey against a staging Bot, verify every configured payment provider, review the chart/Tarot image outputs on Telegram clients, and complete the remaining localization and PDF/archive polish.

## Repository references

The findings above are grounded in the following project files:

[1]: ../app/bot/onboarding.py "Telegram Bot onboarding FSM"
[2]: ../app/bot/chat.py "Telegram Bot chat handlers"
[3]: ../app/bot/features.py "Telegram Bot domain feature handlers"
[4]: ../app/bot/keyboards.py "Telegram Bot keyboard contracts"
[5]: ../app/bot/profile.py "Telegram Bot profile, settings, history, and reports"
[6]: ../app/bot/shop.py "Telegram Bot premium shop and payment handlers"
[7]: ../app/bot/ui.py "Telegram-native progress and presentation primitives"
[8]: ../app/bot/onboarding_parsers.py "Localized tolerant onboarding parsers"
[9]: ../app/services/chat.py "Shared chat service and eligibility boundary"
[10]: ../app/services/eligibility.py "Transport-aware eligibility policy"
[11]: ../app/core/chart_rendering.py "Canonical chart image renderer"
[12]: ../tests/test_bot_telegram_native.py "Telegram-native acceptance tests"
