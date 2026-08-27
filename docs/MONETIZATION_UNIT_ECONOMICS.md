# OracleAI — unit economics contract

**Version:** `2026-08-13.v1`  
**Status:** assumptions template; not a forecast and not a basis for external spending until required inputs are populated and reviewed.

## Purpose

This model answers one commercial question: **how many paying users and which mix of purchases are required for OracleAI to cover variable cost, fixed operating cost, marketing and a full-loaded team while preserving a positive contribution margin?** The target paid ARPPU is a working hypothesis of 3,000–5,000 ₽ per rolling 30 days. It is not observed revenue and must not be reported as achieved until settlement-reconciled cohorts confirm it.

The companion input file is [`MONETIZATION_ASSUMPTIONS.csv`](MONETIZATION_ASSUMPTIONS.csv). Every output is driven from that file or from reconciled operational tables; downstream formulas must not contain hidden prices, fees or payroll constants.

## Scenario structure

| Scenario | Purpose | Commercial posture |
|---|---|---|
| `cash_constrained` | Survive with no new investment. | Organic/referral testing only, founder/critical contractors, zero assumed paid marketing until contribution gate. |
| `validated_growth` | Reinvest only after positive evidence. | Capped acquisition, small team, provider redundancy and controlled creative tests. |
| `large_team` | Stress-test the requested “large team and advertising” case. | Full-loaded payroll, support/safety/content, growth budget, legal/admin and downside sensitivity. |

The model must show required payers at 3,000 ₽, 4,000 ₽ and 5,000 ₽ paid ARPPU, but must not assume that a higher price automatically increases demand. Conversion, repeat purchase and refund/support guardrails are separate assumptions.

## Definitions and formulas

| Output | Formula | Required inputs |
|---|---|---|
| Net paid revenue | `gross successful payments × effective platform realization × (1 − tax/withholding rate) × (1 − refund rate)` | Settlement exports by channel/region, tax review, refunds. |
| Variable COGS per payer | `LLM COGS + voice/tool COGS + support/referral COGS` | `llm_usage` cost map, provider statements, support/referral ledger. |
| Contribution per payer | `net paid revenue per payer − variable COGS per payer` | Net revenue and variable COGS. |
| Contribution margin % | `contribution per payer / net paid revenue per payer` | Net revenue and contribution. |
| Monthly contribution | `unique paying users × contribution per payer` | Cohort payer count, contribution per payer. |
| Break-even payers | `ceil((fixed OPEX + paid marketing) / contribution per payer)` | Fixed OPEX, marketing, contribution. |
| Hire gate | `trailing 3-month contribution / full-loaded hire cost >= 1.5` | Contribution history, role-specific full-loaded cost. |
| CAC | `attributed acquisition spend / first successful payer` | Approved channel spend and privacy-safe paid conversion. |
| CAC payback months | `CAC / contribution per payer` | CAC and contribution. |
| LTV contribution | `sum(cohort net revenue − cohort variable COGS) over observed repeat window` | Cohort settlements, repeat purchase, COGS. |
| LTV/CAC | `LTV contribution / CAC` | Cohort contribution and CAC. |

### Example break-even interpretation

If a future reviewed model reports `fixed OPEX = 1,000,000 ₽`, `marketing = 0 ₽`, and `contribution per payer = 2,500 ₽`, the required payer count is `ceil(1,000,000 / 2,500) = 400`. That is a formula illustration only; it is not a claim about OracleAI’s current costs or expected demand. The same formula must be recomputed for the 3,000/4,000/5,000 ₽ ARPPU rows and downside assumptions.

## Price and credit allocation

The credit-first price book should separate four numbers that are currently mixed in the catalog:

1. **Customer price** by permitted channel (`price_stars`, permitted web currency, region and effective date).
2. **Credit quantity** granted, with exact bonus shown separately from paid quantity.
3. **Expected variable cost budget** for the purchased purpose: LLM/tool/voice, retries and delivery overhead.
4. **Economic result** after settlement, refund and cost allocation.

A SKU is not launchable when its expected contribution is negative, when the worst-case provider path exceeds its budget, or when the result depends on a hidden forced upsell. The catalog should mark the assumption status as `hypothesis`, `observed_input`, or `reviewed_input`; only `reviewed_input` values can drive a public price experiment.

## Required data reconciliation

| Data | Current source | Review status |
|---|---|---|
| Successful Stars payment | `payments` and `orders` | Reconcile against Telegram settlement/export by date and currency. |
| Paddle payment | `payments`, `orders`, webhook/provider metadata | Reconcile against Paddle transaction/settlement report before web price use. |
| LLM cost | `llm_usage.cost_usd` by provider/model/purpose | Validate model price table and exchange-rate conversion. |
| Voice/tool cost | Provider usage/settlement data | Add purpose-level allocation; no guess from token cost. |
| Refunds | `orders.status`, `payments.status` and provider refund result | Track requested, approved, completed and net value. |
| Payroll | Finance/payroll source | Include employer overhead, contractor fees and role-specific support/safety coverage. |
| Marketing | Approved channel budget and attribution | Do not put arbitrary URL/referrer or user text into product events. |

## Decision gates

A SKU can enter an organic soft launch only when its contribution margin is positive in the base case and remains positive with 20% higher variable cost plus a documented refund rate. Paid acquisition is blocked until 50–100 successful payers validate delivery, support/refund and contribution events. Budget expansion is blocked until cohort LTV/CAC is at least 3.0x in base case, at least 1.5x in downside, and CAC payback is no longer than 90 days in the cash-constrained scenario.

A large-team hiring decision is not justified by gross revenue or the 3,990 ₽ core-pack hypothesis. It requires three consecutive months of contribution that cover the role’s full-loaded monthly cost with a 1.5x buffer, plus a downside case with 30% lower conversion and 20% higher variable cost. Unlimited usage is prohibited unless an explicit per-purpose budget ceiling, provider circuit breaker and abuse limits exist.

## Privacy and accounting boundaries

Product events contain only allowlisted categorical fields: SKU/price variant/credit band/channel/result category. They never contain message text, diary text, memory, birth data, partner data, model answer, raw Telegram initData, IP, payment identifiers or arbitrary client event names. Detailed event and LLM usage retention follows the existing privacy contract; deletion must remove or anonymize associated records as approved by legal policy.

The model distinguishes gross booking, net revenue and contribution. Stars are not treated as rubles by a fixed universal rate; effective realization is channel/region/date specific and must be sourced from settlement data. Taxes and withholding are not inferred from payment processor marketing pages. All material model values carry source, as-of date and status.

## References

[1]: [OracleAI monetization baseline](FEATURES/BILLING.md) — current catalog, payment paths and known gaps.
[2]: [OracleAI privacy-safe event dictionary](ANALYTICS_EVENT_DICTIONARY.md) — permitted analytics fields and retention boundaries.
[3]: [OracleAI scale and migration contract](SCALE_AND_MIGRATION.md) — operational triggers and cost-related measurement discipline.
[4]: [Telegram Stars developer documentation](https://core.telegram.org/bots/payments-stars) — platform payment flow; verify applicable current terms and settlement rules before launch.
[5]: [Paddle pricing](https://www.paddle.com/pricing) — provider reference only; use contract/settlement data for actual effective rates.

This is product and operating analysis, not guaranteed financial advice. Confirm consequential pricing, tax, payment and hiring decisions with the relevant finance, tax, legal and platform professionals.
