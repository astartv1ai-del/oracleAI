# Monetization external source notes

**Research date:** 2026-08-13. Search results were used only to identify primary sources; no secondary snippet is treated as a final fee assumption.

| Topic | Primary source | Modeling rule |
|---|---|---|
| Telegram Stars for bot digital goods | [Bot Payments API for Digital Goods and Services](https://core.telegram.org/bots/payments-stars) | Use the current official payment flow and settlement/account data. Do not hard-code a universal Stars→RUB or fee percentage. |
| Telegram Stars API/account mechanics | [Telegram Stars API](https://core.telegram.org/api/stars) | Verify balances, withdrawals, refunds and reporting behavior against the current account/API documentation before launch. |
| Telegram Stars terms | [Terms of Service for Telegram Stars](https://telegram.org/tos/stars) | Legal/platform review is required for current merchant, refund, withdrawal and regional terms. |
| Paddle merchant-of-record pricing | [Paddle Pricing](https://www.paddle.com/pricing) | Treat public pricing as reference only; the contract/settlement export is the source for effective fee, tax and refund treatment. |

Search snippets and third-party articles surfaced conflicting Stars fee/realization figures. They are intentionally not copied into the unit-economics CSV. The model remains `required_input` until settlement exports, contracts, tax review and region/device channel splits are supplied.
