# OracleAI — monetization research pack и unit economics

**Дата исследования:** 13.08.2026.  
**Автор:** Manus AI.  
**Статус:** research pack и launch hypothesis; это не reviewed settlement model и не разрешение на публикацию цен без проверки платёжного канала, налоговой юрисдикции и фактической себестоимости.

## Executive conclusion

OracleAI не следует запускать как «безлимитного AI-астролога» и не следует оставлять только дешёвый разовый вопрос. Наиболее сильная стартовая архитектура при отсутствии вложений — **credit-first**: бесплатный законченный первый ритуал, затем три понятных пакета кристаллов с фиксированными действиями, прозрачным количеством кредитов, видимой ценой и отсутствием скрытой срочности. Подписки можно скрыть для новой тестовой когорты feature flag’ом, но нельзя удалять существующие планы, менять условия действующих подписчиков или отзывать уже выданные права [18].

Моя рабочая рекомендация — **1 490 ₽ / 4 990 ₽ / 9 990 ₽**. Точка 4 990 ₽ становится основным пакетом и соответствует цели пользователя по paid ARPPU 3–5 тыс. ₽ за rolling 30 days; 1 490 ₽ снижает барьер первой покупки; 9 990 ₽ работает как high-intent anchor для большой самостоятельной работы. Это не обещание конверсии. При смешанном миксе 25% / 60% / 15% этих пакетов gross ARPPU модели равен **4 865 ₽** до platform deductions, налогов и refunds.

При illustrative net cash factor 80% и сценарной variable COGS модель даёт contribution на платящего пользователя **3 637 ₽** в cash-constrained, **3 348 ₽** в validated-growth и **2 714 ₽** в large-team сценарии. Это derived illustration, а не доказанная маржа: net cash factor пока неизвестен до settlement export, tax review и observed refund data. В validated-growth сценарии с fixed OPEX 1 612 500 ₽ и paid marketing 500 000 ₽ нужен ориентир **632 платящих пользователя** при mixed ARPPU 4 865 ₽, чтобы покрыть фиксированные затраты и маркетинг при 80% net factor. Этот вывод чувствителен к реальному retention, mix, цене привлечения и settlement.

Главный вывод для быстрого роста: **максимальная наценка сама по себе не максимизирует прибыль**. В первые 60–90 дней прибыль максимизируется не высокой ценой в вакууме, а связкой: бесплатная первая ценность → один честный paywall → core pack около 5 тыс. ₽ → прозрачное повторное использование → только затем paid acquisition. Реклама до подтверждения contribution margin создаёт риск купить отрицательную экономику.

> Все цены и payroll figures ниже разделены на verified market anchors, derived model outputs и planning hypotheses. Где нет settlement или tax input, документ намеренно показывает диапазон и `TBD`, а не выдуманную точную ставку.

## 1. Basis, definitions and boundaries

### 1.1. Что считается выручкой

Модель различает четыре слоя:

| Слой | Определение | Статус для OracleAI |
|---|---|---|
| Gross booking | Успешная сумма покупки до platform/provider deductions, налогов и refunds | Можно получить из orders/payments, но требуется reconciliation |
| Net revenue | `gross × effective platform realization × (1 − tax/withholding) × (1 − refund rate)` | `TBD` до settlement export и tax review |
| Variable COGS | LLM + voice/tool/retry + variable support/referral cost на платящего пользователя | LLM пока estimated; остальное planning buffer |
| Contribution | `net revenue − variable COGS` | Не считать achieved, пока inputs не reviewed |

Telegram требует, чтобы digital goods и services в боте продавались через Telegram Stars (`XTR`), а выдача происходила только после `successful_payment`; charge ID нужно сохранять для возможного refund [14]. Telegram также прямо указывает, что payment providers могут применять собственные commissions и conversion rates, а эти условия находятся вне контроля Telegram [15]. Поэтому в документе нет универсальной ставки «комиссия Telegram = X%» и нет универсального коэффициента Stars→₽.

В числовых иллюстрациях ниже используется **net cash factor** 70% / 80% / 90%. Это не утверждение о фактическом Stars или Paddle take rate. Это sensitivity variable, которая агрегирует platform/provider deductions, tax/withholding и refund reserve. Производственная формула должна подставлять channel/region/device/date-specific settlement values.

### 1.2. Reference date and FX

Все external observations привязаны к **13.08.2026**. Официальный курс Банка России на эту дату в research notes — **82.9977 ₽ за USD** [16]. Для cost sensitivity используются 75 / 83 / 95 ₽ за USD. FX не является прогнозом и не заменяет settlement currency.

### 1.3. Unit of sale

Кристалл — это не случайная внутренняя валюта и не лутбокс. Это заранее описанный доступ к конкретному действию. До оплаты пользовательница должна видеть: что откроется, сколько кредитов будет списано, какие данные потребуются, что останется бесплатным, какой будет формат результата, как восстановить покупку и куда обратиться по support/refund.

Рабочая карта действий из утверждённого плана [18]:

| Действие | Рабочий расход | Коммерческое правило |
|---|---:|---|
| Углублённый разбор вопроса | 6–10 ✦ | Бесплатный короткий ориентир остаётся до paywall |
| Таро 1 / 3 / 5–10 карт | 12 / 28 / 55–80 ✦ | Вопрос и позиции видны до оплаты; без обещания точного будущего |
| Полная натальная интерпретация | 100–140 ✦ | Базовые доступные факты и date-only режим не блокируются |
| Совместимость | 120–160 ✦ | Нужен explicit consent; данные партнёра не сохраняются без opt-in |
| Большой годовой/карьерный отчёт | 160–240 ✦ | Показываются разделы, формат и ограничения результата |
| Аудио или повторный формат | Низкий отдельный SKU | Не может быть обязательным для safety или доступа к уже купленному результату |

Эти credit costs — продуктовые гипотезы. Перед включением они должны быть сверены с фактическими токенами, latency, retries, support load и observed refund rate.

## 2. Competitive pricing matrix

Ниже приведены verified public anchors из official websites, App Store listings и официальных product pages. USD→₽ пересчитан только для ориентира по курсу 82.9977 ₽/USD; это не локальная цена, не net receipt и не утверждение о доступности продукта в России.

| Продукт и поверхность | Public price | Derived ₽ at 82.9977 | Что именно сравнимо с OracleAI |
|---|---:|---:|---|
| CHANI monthly | $11.99/mo | 995 ₽/mo | Astrology depth, editorial authority, recurring use [1] |
| CHANI annual | $107.99/yr | 8 963 ₽/yr | Annual commitment and discounted recurring value [1] |
| Nebula entry monthly | $7.99/mo | 663 ₽/mo | Low/mid astrology subscription anchor [2] |
| Nebula premium monthly | $29.99/mo | 2 489 ₽/mo | Higher-intent premium tier [2] |
| Nebula high monthly | $49.99/mo | 4 149 ₽/mo | High recurring spend and premium anchor [2] |
| Nebula chat balance | $9.99 | 829 ₽ | Direct evidence for balance/credit-like monetization [2] |
| The Pattern Go Deeper+ | $14.99/mo | 1 244 ₽/mo | Reflective, relationship and psychological interpretation [3] |
| Sanctuary first 5 minutes | $4.99 | 414 ₽ | Human-reader acquisition offer; not an AI cost benchmark [4] |
| Sanctuary reader range | $4.99–$19.99/min | 414–1 659 ₽/min | Upper human-service ceiling, with human supply and trust costs [4] |
| Prophesy first week | $4.49 | 373 ₽ | Low-friction astrology/Tarot entry; weekly model risk [5] |
| Prophesy monthly | $9.99/mo | 829 ₽/mo | Lower recurring benchmark [5] |
| Prophesy annual | $19.99/yr | 1 659 ₽/yr | Discounted annual benchmark [5] |
| Labyrinthos | Free; optional AI/deck purchases | Public exact price not exposed | Free/ad-free Tarot funnel with optional depth [6] |
| Reflection annual billing | $5.75/mo equivalent | 477 ₽/mo equivalent | AI journaling/self-reflection anchor [7] |
| Day One Silver | $49.99/yr | 4 149 ₽/yr | Premium journal utility [8] |
| Day One Gold | $74.99/yr | 6 224 ₽/yr | Journal + Daily Chat + Reflective AI [8] |
| Russian natal-chart listing | from 5 000 ₽ per 75–90 min | 5 000 ₽ | Human-service anchor in the target market [11] |

The comparison supports a key positioning decision. OracleAI is not priced against the marginal cost of an LLM reply. It sits between low-cost recurring self-reflection products and high-intent human astrology services. The defensible differentiation is the combination of Telegram-native access, structured reflection, evidence-first interpretation, opt-in memory, Tarot and astrology in one calm workflow, and explicit privacy/safety controls. The market is not analogue-free: adjacent competitors exist, but the combined product proposition remains differentiated [1] [2] [3] [4] [6] [7] [8] [10].

## 3. Recommended price architecture

### 3.1. Price ladder

| SKU role | Customer price hypothesis | Credits | Price per total credit | Purpose |
|---|---:|---:|---:|---|
| Первый глубокий шаг | **1 490 ₽** | 120 ✦ | 12.42 ₽ | First successful payment after completed free value |
| Личный месяц | **4 990 ₽** | 450 paid + 50 transparent bonus = 500 ✦ | 9.98 ₽ | Recommended core pack and target paid ARPPU anchor |
| Большой период | **9 990 ₽** | 1 000 paid + 200 transparent bonus = 1 200 ✦ | 8.33 ₽ | High-intent bundle; 16.6% lower price/credit than core |

The 4 990 ₽ point is intentionally closer to the user’s requested 5 000 ₽ than the earlier 3 990 ₽ hypothesis. It increases the probability of reaching a 3–5k paid ARPPU with one core purchase, while 1 490 ₽ preserves an affordable first step and 9 990 ₽ gives an anchor for users who already received value. The high pack should not be the only visible offer: fast growth needs a credible first purchase, not only maximum nominal margin.

The bonus must be written as an exact number, not as «подарок до» or a fake countdown. The interface should show both paid and bonus credits, action prices and an example of what the bundle can actually cover. It should not suggest that a larger balance improves mystical accuracy or guarantees a relationship, career or financial outcome.

### 3.2. Why not 1 500 / 5 000 / 10 000 exactly

Round numbers are easy to remember, but 1 490 / 4 990 / 9 990 are conventional test points that preserve the same psychological bands while allowing a clear price-variant identifier. This is not a reason to keep them forever. If a Russian payment surface or Stars price table makes 1 500 / 5 000 / 10 000 cleaner, use channel-specific pricing and keep the economic comparison on net receipt, not on visual parity.

The architecture should not promise that the same number of Stars equals the same number of rubles across regions or platforms. The server price book must version `channel`, `currency`, `price_stars`, `display_price`, `credit_qty`, `bonus_qty`, `effective_from` and `catalog_version`; historic orders and entitlements must remain unchanged.

### 3.3. Suggested catalog sequencing

The rollout sequence should be:

1. Keep the free first ritual, one safe short answer and a transparent preview of the next deep result.
2. Offer 1 490 ₽ only after the user has completed first value and explicitly requested depth.
3. Show 4 990 ₽ as the recommended option only when its lower unit price and concrete use cases are visible.
4. Show 9 990 ₽ as an anchor for a large report and follow-up credits, never as a forced upsell.
5. Hide the purchase entry point for existing subscription customers only through a reversible cohort flag; do not change their current access.

## 4. AI COGS model

### 4.1. Public model anchors

The official OpenAI pricing page reports, among the referenced models, GPT-5.6 Luna at $0.20/M input and $1.20/M output, GPT-5.6 Terra at $2/M input and $12/M output, and GPT-5.6 Sol at $5/M input and $30/M output [12]. Anthropic’s official pricing docs list Claude Haiku 4.5 at $1/M input and $5/M output, Claude Sonnet 5 at $2/M input and $10/M output, and Claude Opus 5 at $5/M input and $25/M output; they also document cache-hit pricing at 0.1× base input price [13].

OracleAI’s actual provider chain is custom OpenAI-compatible → Anthropic → OpenAI → offline fallback. Therefore public list prices are only a benchmark. The production cost source must be the existing `llm_usage` records, joined by provider, model, purpose, input tokens, output tokens, retries and USD estimate. Provider fallback cannot silently exceed a SKU budget.

### 4.2. Token budget scenarios

The following are **30-day planning budgets per paying user**, not production observations. The cost equation is:

`LLM COGS USD = input_Mtokens × input_price_USD_per_Mtoken + output_Mtokens × output_price_USD_per_Mtoken`  
`LLM COGS ₽ = LLM COGS USD × USD/RUB`

| Routing scenario | Planning token budget | Planning rate | LLM cost USD | LLM cost ₽ at 82.9977 |
|---|---:|---:|---:|---:|
| Haiku/Luna economy | 0.40M input + 0.10M output | $1 / $5 | $0.90 | **75 ₽** |
| Mixed routing | 0.90M input + 0.18M output | weighted $1.30 / $6.50 | $2.34 | **194 ₽** |
| Sonnet premium | 1.50M input + 0.30M output | $2 / $10 | $6.00 | **498 ₽** |

The mixed rate is a planning inference, not a provider quote: it represents a routed product where simple prompts use Haiku/Luna-class economics and premium reports use Sonnet/Terra-class economics. Caching can reduce repeat stable-context input cost, but it must be implemented without violating privacy boundaries and must be measured in actual usage.

### 4.3. Full variable COGS scenarios

To avoid the false conclusion that «LLM is cheap, therefore margin is infinite», the model adds voice/tool/retry and variable support/referral reserves. The latter include human handling, creator reward or referral cost, and delivery overhead; they are estimated buffers and not payroll.

| Scenario | LLM COGS | Voice/tool/retry buffer | Support/referral buffer | Total variable COGS / payer / 30d | Status |
|---|---:|---:|---:|---:|---|
| Cash-constrained | 75 ₽ | 60 ₽ | 120 ₽ | **255 ₽** | Estimated planning model |
| Validated growth | 194 ₽ | 100 ₽ | 250 ₽ | **544 ₽** | Estimated planning model |
| Large team | 498 ₽ | 180 ₽ | 500 ₽ | **1 178 ₽** | Estimated stress-test model |

These numbers are intentionally not presented as verified production COGS. A product SKU is launchable only when its actual purpose-level cost, worst-case retry path and refund/support rate fit its cost budget.

## 5. Platform fees, Stars and net-revenue sensitivity

### 5.1. The non-negotiable unknowns

Telegram’s public terms do not provide a universal merchant net-realization percentage. Telegram states that third-party payment providers may apply their own commissions and conversion rates [15]. The exact effective realization must therefore be measured from settlement exports by provider, device, region, currency, date and refund outcome. Taxes and withholding are also jurisdiction/entity-specific and remain `REQUIRED_INPUT`.

The model uses the following illustrative factor table. It is a decision tool, not a fee claim.

| Gross customer price | 70% illustrative net cash | 80% illustrative net cash | 90% illustrative net cash |
|---:|---:|---:|---:|
| 1 490 ₽ | 1 043 ₽ | 1 192 ₽ | 1 341 ₽ |
| 4 990 ₽ | 3 493 ₽ | 3 992 ₽ | 4 491 ₽ |
| 9 990 ₽ | 6 993 ₽ | 7 992 ₽ | 8 991 ₽ |

The production formula must replace the illustrative factor with `effective platform realization × (1−tax/withholding) × (1−refund rate)`. Net revenue and contribution in admin KPI must stay `null` or explicitly estimated until those inputs are reviewed. This preserves the existing repository boundary [18] [19].

### 5.2. Payment implementation implications

The payment system must create an order before invoice, bind the server-owned SKU and price variant, accept only a valid `successful_payment`, grant credits idempotently, store the charge ID and expose purchase recovery. A duplicate webhook cannot create duplicate credits. A delivered result remains accessible after the balance reaches zero. Refund and reversal must not create a negative balance or silently revoke unrelated purchased entitlements [14] [18].

## 6. Staffing and operating cost scenarios

Habr Career’s H1 2026 survey reports a median Russian IT salary of **191 000 ₽/month**, with medians of 235 000 ₽ in Moscow, 200 000 ₽ in Saint Petersburg and 160 000 ₽ in other regions. It also reports 243 000 ₽ median for Python developers and identifies higher growth in support, marketing and content roles [17]. These are employee-reported salary observations, not guaranteed offers. The OracleAI figures below are **full-loaded planning scenarios** that add role mix, contractors, employer costs, infrastructure, legal, accounting and admin; they must be replaced by actual payroll/contractor quotes before hiring.

| Scenario | Operating design | Fixed OPEX / month | Paid marketing / month | Total fixed + marketing | Average full-loaded person cost where meaningful |
|---|---|---:|---:|---:|---:|
| Cash-constrained | Founder + critical contractors, organic/referral only | **360 000 ₽** | **0 ₽** | **360 000 ₽** | Planning cost for critical capacity: 360 000 ₽ |
| Validated growth | Five-person core team, capped acquisition tests | **1 612 500 ₽** | **500 000 ₽** | **2 112 500 ₽** | 322 500 ₽ across five people |
| Large team | Fifteen-person team, support/safety/content/growth and redundancy | **4 550 000 ₽** | **3 000 000 ₽** | **7 550 000 ₽** | 303 333 ₽ across fifteen people |

The validated-growth planning mix is approximately product/ops 300 000 ₽, two backend/AI roles 700 000 ₽ in total, frontend/design 250 000 ₽, content/safety/support 180 000 ₽ and shared cloud/legal/admin 182 500 ₽. The large-team stress test is approximately product/ops 600 000 ₽, five backend/AI roles 1 600 000 ₽, two frontend/design roles 560 000 ₽, three content/safety/editorial roles 600 000 ₽, two support/QA roles 360 000 ₽, one growth role 250 000 ₽ and shared infrastructure/legal/admin 580 000 ₽. These allocations are scenario estimates, not observed payroll.

The large-team case is a stress test, not a hiring plan. OracleAI has no investment reserve in the current brief, so the only responsible sequence is to earn contribution first, then fund contractors and hires from measured cash flow. A new hire should be approved only after three consecutive months of contribution cover its full-loaded monthly cost by at least 1.5× and the downside case still has a positive operating path [18].

## 7. Break-even and contribution model

### 7.1. Mixed-pack base case

The model uses the following illustrative purchase mix: 25% first deep step, 60% personal month and 15% big period. The resulting gross ARPPU is:

`0.25 × 1 490 + 0.60 × 4 990 + 0.15 × 9 990 = 4 865 ₽`

At 80% illustrative net cash factor, net revenue per payer is 3 892 ₽. The table below subtracts the scenario-specific variable COGS and divides fixed OPEX plus paid marketing by contribution per payer.

| Scenario | Net revenue / payer | Variable COGS / payer | Contribution / payer | Contribution margin | Fixed + marketing | Break-even payers |
|---|---:|---:|---:|---:|---:|---:|
| Cash-constrained | 3 892 ₽ | 255 ₽ | **3 637 ₽** | 93.46% | 360 000 ₽ | **99** |
| Validated growth | 3 892 ₽ | 544 ₽ | **3 348 ₽** | 86.02% | 2 112 500 ₽ | **632** |
| Large team | 3 892 ₽ | 1 178 ₽ | **2 714 ₽** | 69.73% | 7 550 000 ₽ | **2 782** |

The 80% factor is not a claim that Telegram will deliver 80% net. If net cash factor is 70% or 90%, the same mix changes as follows:

| Scenario | 70% contribution / BE payers | 80% contribution / BE payers | 90% contribution / BE payers |
|---|---:|---:|---:|
| Cash-constrained | 3 151 ₽ / 115 | 3 637 ₽ / 99 | 4 124 ₽ / 88 |
| Validated growth | 2 861 ₽ / 739 | 3 348 ₽ / 632 | 3 834 ₽ / 551 |
| Large team | 2 228 ₽ / 3 390 | 2 714 ₽ / 2 782 | 3 201 ₽ / 2 359 |

### 7.2. Break-even at target paid ARPPU

The user’s target of 3 000–5 000 ₽ is useful only if it is defined as **paid ARPPU after a stable mix**, not as a one-time gross checkout. At the illustrative 80% net factor, the break-even table is:

| Scenario | 3 000 ₽ paid ARPPU | 4 000 ₽ paid ARPPU | 5 000 ₽ paid ARPPU |
|---|---:|---:|---:|
| Cash-constrained | 168 payers | 123 payers | 97 payers |
| Validated growth | 1 139 payers | 796 payers | 612 payers |
| Large team | 6 179 payers | 3 734 payers | 2 676 payers |

This table demonstrates why hiring a large team before product-market evidence is dangerous. At 5 000 ₽ paid ARPPU, the large-team stress test still needs about 2 676 active payers per rolling 30 days under the illustrative assumptions. A lower price may improve conversion but increase the required payer count; a higher price may increase contribution per payer but reduce conversion and repeat purchase. Those demand effects must be measured rather than assumed.

### 7.3. Unit economics by individual pack

At 80% illustrative net factor and scenario-specific variable COGS, the personal-month pack is the most balanced economic unit:

| Scenario | 1 490 ₽ pack: contribution / BE | 4 990 ₽ pack: contribution / BE | 9 990 ₽ pack: contribution / BE |
|---|---:|---:|---:|
| Cash-constrained | 937 ₽ / 385 | 3 737 ₽ / 97 | 7 737 ₽ / 47 |
| Validated growth | 648 ₽ / 3 262 | 3 448 ₽ / 613 | 7 448 ₽ / 284 |
| Large team | 14 ₽ / 538 755 | 2 814 ₽ / 2 684 | 6 814 ₽ / 1 109 |

The large-team 1 490 ₽ result is a warning: after high variable cost, the first pack is almost contribution-neutral in that stress test. It is therefore a customer-acquisition and activation product, not the product that should fund a large organization. If actual support/voice costs rise above this planning buffer, the entry pack must either be scoped down, priced up, or limited to a bounded first report.

## 8. Sensitivity analysis

### 8.1. FX × LLM routing sensitivity

This table holds validated-growth non-LLM variable cost at 350 ₽ per payer, uses gross mixed ARPPU 4 865 ₽ and 80% illustrative net cash factor, then varies only FX and routing scenario. It answers the question: «Will AI COGS alone break the model?» Under these assumptions, FX is not the dominant risk; conversion, repeat purchase, settlement realization and payroll are larger risks. The table still matters because premium routing and retries can compound at scale.

| Routing | FX 75 ₽ | FX 83 ₽ | FX 95 ₽ |
|---|---:|---:|---:|
| Haiku/Luna economy: total COGS / contribution / BE | 418 / 3 475 / 609 | 425 / 3 467 / 610 | 436 / 3 457 / 612 |
| Mixed routing: total COGS / contribution / BE | 526 / 3 367 / 628 | 544 / 3 348 / 632 | 572 / 3 320 / 637 |
| Sonnet premium: total COGS / contribution / BE | 800 / 3 092 / 684 | 848 / 3 044 / 694 | 920 / 2 972 / 711 |

Values are ₽ per payer except BE payers. The Sonnet route at FX 95 increases total variable cost by 376 ₽ versus the Haiku route at FX 75 in this table. The product should therefore route simple work to cheaper models and reserve stronger models for high-value, budgeted outputs; it should never sell unlimited premium generation without a circuit breaker.

### 8.2. Conversion sensitivity

The next table holds 10 000 activated users, validated-growth fixed plus marketing cost of 2 112 500 ₽, gross ARPPU 4 865 ₽, 80% illustrative net factor and mixed-routing variable COGS. It shows the difference between gross top-line and operating cash contribution.

| Activated users | Paid conversion | Payers | Gross booking | Contribution before fixed | After fixed + marketing |
|---:|---:|---:|---:|---:|---:|
| 10 000 | 3% | 300 | 1 459 500 ₽ | 1 004 336 ₽ | **−1 108 164 ₽** |
| 10 000 | 6% | 600 | 2 919 000 ₽ | 2 008 671 ₽ | **−103 829 ₽** |
| 10 000 | 10% | 1 000 | 4 865 000 ₽ | 3 347 785 ₽ | **+1 235 285 ₽** |

The practical conclusion is not «force conversion to 10%». It is that 3–6% paid conversion is insufficient to finance a five-person team plus 500 000 ₽ acquisition budget at this particular mix. The product should first improve first-value completion, result delivery, repeat purchase and trust; only then should it spend on traffic.

### 8.3. Platform/net factor sensitivity

For the mixed pack, net revenue per payer is 3 406 ₽ at 70%, 3 892 ₽ at 80% and 4 378 ₽ at 90%. At 80% the break-even payer counts are 99 / 632 / 2 782 for cash-constrained / validated-growth / large-team. If reviewed settlement produces a net factor below 70%, the price book or channel mix must be re-evaluated before paid traffic. If it produces a factor above 90%, do not immediately lower prices; first test whether the extra contribution can fund reliable delivery, support and reserve.

## 9. LTV/CAC gates and paid acquisition

Paid acquisition must be governed by contribution, not gross booking. The unit-economics contract defines CAC as attributed spend divided by first successful payer, CAC payback as CAC divided by monthly contribution per payer, and LTV contribution as observed cohort contribution over the repeat window [18].

The following is an **illustrative** LTV table. Repeat multipliers 1.25× / 1.80× / 2.50× are planning hypotheses for the three scenarios, not observed retention.

| Scenario | Monthly contribution | Illustrative repeat multiplier | Illustrative LTV contribution | Max CAC at 3× LTV/CAC | Max CAC at 90-day payback |
|---|---:|---:|---:|---:|---:|
| Cash-constrained | 3 637 ₽ | 1.25× | 4 547 ₽ | **1 516 ₽** | 10 912 ₽ |
| Validated growth | 3 348 ₽ | 1.80× | 6 026 ₽ | **2 009 ₽** | 10 043 ₽ |
| Large team | 2 714 ₽ | 2.50× | 6 785 ₽ | **2 262 ₽** | 8 142 ₽ |

For actual growth decisions, use the stricter gate: `CAC ≤ min(3× LTV contribution threshold, 90-day payback threshold)` in the base case, and require at least 1.5× LTV/CAC in downside. For validated growth, that makes an initial **CAC ceiling of 2 009 ₽** under the illustrative model, not 10 043 ₽. This ceiling is deliberately conservative because a 90-day payback test alone can approve a poor long-term business if repeat purchase is weak.

No paid media should start until at least 50–100 successful payers have validated: payment success, idempotent credit grant, result delivery, support/refund flow, actual LLM cost allocation and privacy-safe cohort reporting. Initial acquisition should be organic, founder-led, creator/recommendation experiments and small capped referral tests. Referral rewards must be recorded as variable COGS and issued only after verified payment; no multilevel scheme is appropriate.

## 10. Product and operational guardrails

A credit-first model can become manipulative if it hides the exchange rate, uses random rewards or blocks safety guidance. The product should therefore preserve these rules:

| Risk | Required guardrail |
|---|---|
| Credits feel opaque | Show exact price, paid credits, bonus credits, action cost and example result before payment |
| Paywall interrupts a crisis | Crisis-safe guidance remains available; do not sell safety access |
| High price implies certainty | State that astrology/Tarot is a reflective interpretation, not a guaranteed outcome |
| LLM cost runaway | Purpose-level budget, max tokens, retry budget, provider circuit breaker and low-balance state |
| Refund confusion | Purchase history, receipt recovery, delivered-result access and visible support/refund route |
| Hidden personalization | Memory remains opt-in; price never depends on diary/birth/partner-data volume |
| Existing customer harm | Preserve existing subscriptions and entitlements; version price book; no retroactive change |
| Analytics leakage | Keep server-owned categorical events only: SKU, channel, price variant, credit band, result category and reason |

## 11. Implementation roadmap

### Phase B — Reversible credit catalog and entitlements

Add a versioned price book and catalog rows for the three packs. Store customer price by channel, credit quantity, bonus quantity, expiry, estimated cost budget, safety classification and effective date. Debit and grant in one server-side transaction. Add idempotent refund/reversal and duplicate webhook tests. Do not delete current `plans`, historic orders or existing entitlements.

The launch blocker for Phase B is not visual polish. It is the ability to prove: paid order → exactly one grant → eligible spend → delivered result → recoverable receipt → correct refund/reversal → reconciled dashboard.

### Phase C — Honest paywall and Mini App UX

Place one conversion surface after first completed value, at an explicit deep-report choice or when included credits are exhausted. The paywall must name the result, credits required, what remains free, price, restore path and support/refund route. Display all three offers but make the core pack recommended only because its unit economics and concrete use cases are objectively better. Do not use countdowns, fear, relationship promises or technical urgency.

### Phase D — Pricing experiment and rollout

Use the following sequence:

| Window | Action | Stop criteria |
|---|---|---|
| Days 0–14 | Reconcile Stars/Paddle settlements, tax/legal inputs, actual `llm_usage`, refund and support taxonomy | Any unknown net-realization or paid-without-credit incident blocks launch |
| Days 15–30 | Internal/staging purchase replay and 10–20 friendly testers | Duplicate grant, missing delivery, negative balance or safety complaint blocks cohort |
| Days 31–60 | Organic soft launch with 1 490 / 4 990 / 9 990 ₽ hypothesis | Negative contribution, unclear value or high refund/support rate rolls back price flag |
| Days 61–90 | 50–100 successful payer validation and one-variable price experiment | Do not add paid media without reviewed contribution and delivery data |
| After Day 90 | Small creator/referral and capped paid tests | CAC > gate, LTV/CAC < 3× base or payback >90 days pauses spend |

Run one independent experiment variable at a time: price, credit quantity or value framing. Pre-register owner, cohort, duration, sample threshold and rollback rule. The primary decision metric is **net contribution per payer**, with conversion, repeat purchase, refund rate, support rate, LLM cost and safety complaints as guardrails. CTR alone is not a success metric.

## 12. Required inputs before public price launch

| Input | Current status | Owner/source required |
|---|---|---|
| Effective Stars realization by channel/region/device/date | `REQUIRED_INPUT` | Telegram settlement/export and finance reconciliation |
| Paddle effective net realization if web flow is permitted | `REQUIRED_INPUT` | Paddle contract and settlement report |
| Tax/withholding rate and legal sales channel | `REQUIRED_INPUT` | Tax/legal review for actual entity and jurisdiction |
| Refund/chargeback rate | `REQUIRED_INPUT` | Observed provider and order data by SKU |
| Actual LLM input/output cost | `ESTIMATED` until reviewed | `llm_usage` plus provider invoices/rate cards |
| Voice/tool/retry cost | `ESTIMATED` until reviewed | Provider usage statements |
| Payroll and employer overhead | `ESTIMATED` until reviewed | Actual offers/contracts and finance ledger |
| Paid CAC and repeat purchase | Not observed | Privacy-safe attributed cohorts after soft launch |
| Large-team definition and timeline | Planning stress test only | Product owner and finance approval |

The updated [`MONETIZATION_ASSUMPTIONS.csv`](MONETIZATION_ASSUMPTIONS.csv) records these boundaries. `required_input` values remain blank rather than pretending that public terms reveal OracleAI’s net cash. The `estimated` rows are scenario planning values and must not be presented in the UI or admin as reviewed economic truth.

## 13. Final recommendation

Launch the **1490 / 4990 / 9990 ₽** credit-first ladder as a reversible hypothesis, with the 4 990 ₽ pack visually central, 1 490 ₽ pack as the first paid step and 9 990 ₽ pack as an optional high-intent anchor. Keep the free first ritual generous enough to demonstrate the product’s value. Do not use subscriptions for the new test cohort until credit-first retention and cost-to-serve are understood; preserve current subscriber rights.

For a no-investment business, the financially correct order is: **measure settlement → validate one delivered paid result → prove positive contribution → reach 50–100 payers → validate repeat purchase and CAC → only then hire or buy traffic**. The large-team scenario is useful as a warning line, not a budget to spend now.

## References

[1]: https://apps.apple.com/us/app/chani-your-astrology-guide/id1532791252 "CHANI — Apple App Store US listing"

[2]: https://apps.apple.com/us/app/nebula-spiritual-guidance/id1459969523 "Nebula — Apple App Store US listing"

[3]: https://apps.apple.com/us/app/the-pattern/id1071085727 "The Pattern — Apple App Store US listing"

[4]: https://www.sanctuaryworld.co/faq/ "Sanctuary — official FAQ and reader pricing"

[5]: https://apps.apple.com/us/app/prophesy-horoscope-tarot/id1469028948 "Prophesy — Apple App Store US listing"

[6]: https://apps.apple.com/us/app/labyrinthos-tarot-reading/id1155180220 "Labyrinthos Tarot Reading — Apple App Store US listing"

[7]: https://www.reflection.app/premium "Reflection — official Premium pricing"

[8]: https://dayoneapp.com/plans/ "Day One — official plans"

[9]: https://apps.apple.com/us/app/wysa-mental-wellbeing-ai/id1166585565 "Wysa — Apple App Store US listing"

[10]: https://help.replika.com/hc/en-us/articles/39551043419149-Choosing-a-Subscription "Replika — official subscription tiers"

[11]: https://moskva.skidkom.ru/partner/individualnye-uslugi-astrologa-rafaelya/uslugi-i-ceny/208867-uslugi/1382691-sostavlenie-natalnoy-karty---goroskop-dushi-i-sudby/ "Russian natal chart service listing"

[12]: https://developers.openai.com/api/docs/pricing "OpenAI API pricing"

[13]: https://platform.claude.com/docs/en/about-claude/pricing "Anthropic Claude Platform pricing"

[14]: https://core.telegram.org/bots/payments-stars "Telegram Bot Payments API for digital goods and services"

[15]: https://telegram.org/tos/stars "Telegram Terms of Service for Stars"

[16]: https://www.cbr.ru/currency_base/daily/ "Bank of Russia official daily exchange rates"

[17]: https://habr.com/ru/specials/1060148/ "Habr Career — IT salaries in the first half of 2026"

[18]: https://github.com/astartv1ai-del/oracleAI/blob/master/oracleAI_monetization_plan.md "OracleAI approved credit-first monetization plan"

[19]: https://github.com/astartv1ai-del/oracleAI/blob/master/docs/MONETIZATION_UNIT_ECONOMICS.md "OracleAI unit-economics contract"

**Disclosure.** Basis: gross package prices, illustrative net cash factors and scenario variable costs are separated; contribution is net revenue less variable COGS. Time: all external observations are dated 13.08.2026 and FX uses the Bank of Russia 13.08.2026 rate. Assumptions: 25%/60%/15% pack mix, 70%/80%/90% net-factor sensitivity, planning token budgets, repeat multipliers and full-loaded staffing are hypotheses until reviewed. Sources & confidence: public official pricing, Telegram terms, Bank of Russia FX and Habr salary survey are source-backed; effective settlements, taxes, refunds, payroll offers, CAC and retention remain unknown or estimated. Compliance: this is research and operating analysis only, not personalized financial advice.
