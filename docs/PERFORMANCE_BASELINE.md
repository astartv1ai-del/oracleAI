# Local performance baseline

**Дата:** 26 августа 2026

`python3 scripts/benchmark_product_performance.py` measures representative synthetic operations without provider calls. The result is a directional local baseline, not a production SLO: machine load, cold-start behavior, real Telegram traffic, database contention and provider latency must be measured in staging.

| Operation | Runs | p50 | p95 | Max |
|---|---:|---:|---:|---:|
| Western chart calculation | 5 | 1.35 ms | 1.40 ms | 635.40 ms |
| Tarot draw + ledger | 20 | 0.02 ms | 0.04 ms | 0.14 ms |
| Memory recall | 5 | 0.00 ms | 0.00 ms | 0.69 ms |
| Offline PDF HTML generation | 2 | 730.43 ms | 3.88 ms* | 1456.97 ms |

\*The p95 estimator is intentionally conservative only for larger samples; with two PDF samples the maximum is the meaningful cold/warm upper bound. The benchmark should be repeated with a larger sample before setting a hard local PDF threshold.

The live synthetic LLM run remains the main latency blocker: `gpt-5-mini` p95 was **22.14 s** against a **15 s** target. The next production optimization loop is provider/model selection, prompt and token budget review, timeout/fallback tuning, and staging measurement under concurrency; no latency pass is claimed here.
