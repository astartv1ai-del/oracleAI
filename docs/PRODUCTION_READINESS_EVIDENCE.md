# OracleAI Production Readiness Evidence

**Дата evidence pass:** 13 августа 2026 года  
**Контур:** локальный repository QA, production-like configuration checks без реальных production secrets  
**Назначение:** зафиксировать, что проверено кодом и CI, а что остаётся обязательным внешним launch gate.

## Automated evidence

| Проверка | Команда / artifact | Результат |
|---|---|---|
| Python syntax/import | `python3 -m compileall -q app scripts tests` | PASS |
| JavaScript syntax | `find miniapp/js admin -name '*.js' ... node --check` | PASS |
| Static release gate | `python scripts/release_gate.py` | PASS |
| LLM golden set | `scripts/generate_eval_set.py` | 140 cases generated |
| Deterministic LLM evaluator | `scripts/evaluate_llm.py --min-score 0.75` | 140/140 evaluated; critical violations 0; mean score 1.0; language/safety/latency pass rate 1.0 |
| Targeted Palm/LLM regression | `pytest -q tests/test_release_gate.py tests/test_llm_evaluation.py tests/test_placements_palm.py tests/test_openai_compat.py tests/test_palm_integration.py` | PASS |
| Full project suite | `pytest -q -p no:cacheprovider --timeout=120` | PASS; current repository collects 381 tests |
| Selfcheck | `python scripts/selfcheck.py` | PASS; two expected skips: live LLM disabled and production config values absent in local QA |
| Diff hygiene | `git diff --check` | PASS |

The CI workflow now runs the static production-readiness gate and uploads the deterministic, privacy-safe LLM evaluation report as a GitHub Actions artifact. The report stores scores, lengths, latency and categorical hits, not user-like response text.

## Changes covered by this evidence

The product source of truth now documents Мира as an independent palm/evidence guide, adds the Palm surface and defines the limits of photo interpretation. `LAUNCH_GOVERNANCE.md` records the controlled-beta default, P0/P1 gates, owners, SLO placeholders and no-go rules. `PRODUCTION_READINESS_AND_LAUNCH_PLAN.md` contains the complete route from beta to public launch.

The Palm vision path now passes a strict JSON Schema response contract to compatible providers. The schema closes unexpected object fields, constrains status, hand-side, topic and visibility enums, and keeps the existing server-side normalization and safety sanitization. GPT-5 token compatibility remains covered by the OpenAI regression test. The 140-case synthetic evaluation set now contains Palm quality, evidence reading, image prompt-injection and Palm safety cases in addition to the existing agent scenarios.

## Evidence interpretation

> A green deterministic suite proves that code contracts, safety boundaries and fallback behavior are reproducible. It does not prove that a live provider, real Telegram device, payment account or production host is ready for public traffic.

The local selfcheck intentionally does not claim live LLM readiness because `SELF_CHECK_LIVE=1` was not enabled and the development environment does not contain production bot, admin and HTTPS URL settings. Previous live Palm QA also showed that the external multimodal proxy can time out after retries; therefore the Palm feature must remain behind a feature flag until the selected production provider passes the approved vision benchmark and latency budget.

## Remaining launch blockers

| Blocker | Required evidence before public launch |
|---|---|
| Legal and privacy | External legal review for first-wave countries, privacy/terms/16+ wording, retention, deletion and cross-border provider processing. |
| Real-device UX | Telegram iOS, Android and Desktop matrix covering onboarding, permissions, Palm upload, offline/slow provider and checkout return. |
| Live LLM quality | Provider benchmark with approved synthetic/licensed image set, strict JSON success, p95 latency, fallback and circuit-breaker evidence. |
| Production infrastructure | Isolated staging, production secrets, HTTPS domain, off-site encrypted backup, restore drill, load test and rollback rehearsal. |
| Payments | Paddle sandbox certification for signed webhook, idempotency, entitlement, cancellation, failed payment and refund reconciliation. |
| Operations | Named release/support/on-call owners, alert routing, incident tabletop and 72-hour post-launch rota. |
| Growth | Privacy-safe funnel, beta cohort retention/support/cost evidence and two successful invite waves before public acquisition. |

Until these blockers are signed off, the correct status is **code and CI readiness improved; public launch not yet approved**.

## References

[1]: [Launch governance](LAUNCH_GOVERNANCE.md)
[2]: [Production readiness and launch plan](PRODUCTION_READINESS_AND_LAUNCH_PLAN.md)
[3]: [Security checklist](SECURITY.md)
[4]: [Deployment runbook](DEPLOYMENT.md)
[5]: [LLM evaluation contract](LLM_EVALUATION.md)
