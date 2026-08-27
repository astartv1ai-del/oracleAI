# OracleAI Monetization v2 Implementation Report

## Delivered

The repository now contains an additive, versioned monetization layer. The canonical catalog is seeded under `catalog_versions` and `price_book_items` with monthly and annual plan prices, Crystal packs, named deep operations, expected cost budgets, features, and catalog fingerprints. The initial production hypothesis is `2026-08-v2` / `pb-2026-08-v2`.

The server-side `EntitlementService` is the decision point for capabilities. It reports effective tier, lifecycle status, period end, cancellation/grace fields, AI quota, compute budget, Crystal balance, and contextual denial reasons. Legacy plans continue to resolve through the legacy allowance implementation, while v2 plans use the monthly AI usage counter. The Free tier has no AI chat in production; deterministic previews, Today, basic chart surfaces, history, and paywall previews remain available.

Checkout supports v2 monthly and annual plans through Telegram Stars and configured web checkout, plus v2 Crystal packs through Stars and Crypto Pay. Prices and grants are always read from the server price book. Provider webhooks continue to bind to immutable orders, verify signatures, and use the existing idempotency boundary. New v2 plan grants update `subscription_state`; purchased and subscription-bonus Crystals are also written to `crystal_lots` without deleting the aggregate legacy balance.

Crystal spending now keeps the fast `users.crystals` aggregate and ledger while allocating lots in expiry order. Legacy balances are backfilled into a non-expiring `legacy` lot on first v2-aware spend. Subscription bonus lots expire after 90 days; purchased lots do not expire. v2 deep-operation purchases create and finish an idempotent `monetization_usage` reservation in the same transaction as the Crystal debit, grant, and order settlement.

The Mini App now reads `catalog` from the server, renders the v2 tier ladder and Crystal packs, supports monthly/annual selection, and sends only the selected plan code and billing period. The Bot Shop reads canonical v2 plans and packs. `/api/me` includes canonical entitlement and subscription lifecycle state. `/api/shop/subscription/cancel` supports cancel-at-period-end and resume for v2 state rows. Pricing experiments can be assigned through `/api/experiment-assignment`; assignment is deterministic and sticky per user and experiment.

The admin analytics dashboard now contains `monetization_v2`, including gross Stars, paid/refunded orders, SKU revenue, active tiers, repeat payers, Crystal lots and outstanding balances, funnel events, cost by event kind, and explicit `required_inputs` when net revenue or contribution cannot be determined from repository data.

## Migration safety

Existing rows in `plans`, `products`, `orders`, `payments`, `entitlements`, `crystal_ledger`, reports, and user profiles are not rewritten. Legacy active access remains valid through the recorded expiry. New purchases use v2 catalog codes. A historical `vip` record is not silently converted to `vip_plus`; it retains its legacy allowance semantics and only maps to a comparable capability tier for the entitlement explanation layer. Existing balances and purchased rights are preserved.

The schema is shared by SQLite and PostgreSQL. Additive columns are covered by the existing migration reconciler, and the PostgreSQL adapter registers v2 identity tables for returned IDs. No raw payment payload, question text, chart data, memory fact, or provider secret is added to monetization analytics.

## Production configuration

Set `AUTO_TRIAL=0` or leave it unset. Set `PADDLE_PRICE_IDS` for the v2 plan codes used by web checkout, for example `vip_core:price_id,vip_plus:price_id,pro:price_id,concierge_v2:price_id`; use the real provider price IDs rather than the illustrative strings. Keep provider webhook secrets configured and enable `web_payments` only after a signed provider callback has been tested. Review the 70% net factor and cost budgets in the design document against actual provider settlement, tax, refunds, support, marketing, and infrastructure exports before displaying net revenue or margin as a business KPI.

## Verification

The following checks were executed successfully in the repository:

| Check | Result |
|---|---|
| `python3 -m compileall -q app scripts` | Passed |
| `npm run build:frontend` | Passed; 19 JS and 21 CSS source files bundled into hashed assets |
| `pytest -q tests/test_billing.py tests/test_limits.py` | Passed |
| `pytest -q tests/test_api.py` | Passed |
| `pytest -q tests/test_monetization_v2.py` | Passed |
| `pytest -q` | Passed; 100% of the repository suite passed with one existing skip |
| `git diff --check` | Passed |

## Rollback

The safest rollback is a code rollback to the preceding approved commit while preserving the additive v2 tables. Because legacy data is not rewritten, the application can continue serving legacy plans and orders. To pause v2 sales without deleting history, set the active `price_book_items.is_active` or `is_public` flags to zero through an owner-reviewed migration and leave existing v2 subscriptions active until their paid period ends.

## Follow-up before broad launch

Connect provider-native cancellation, renewal, grace, and chargeback events to `subscription_state` for each enabled provider. Replace planning conversion and cost assumptions with observed cohort data. Add a scheduled monthly grant job with a unique period key if recurring monthly Crystal grants are enabled beyond the initial purchase grant. Add an owner-reviewed reconciliation export for v2 lots and usage reservations. Run browser smoke tests against a staging Telegram environment and verify the annual provider price IDs before opening traffic.
