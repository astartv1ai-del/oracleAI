>
> **STATUS: HISTORICAL**
> **SUPERSEDED BY:** [`docs/RELEASE/CURRENT_STATUS.md`](../RELEASE/CURRENT_STATUS.md)
> **LAST VERIFIED:** 2026-08-27
> This file is retained as dated evidence or context. It is not the current source of truth.

# Local performance baseline

**Дата:** 27 августа 2026

`python3 scripts/benchmark_product_performance.py` measures representative synthetic operations without provider calls. The result is a directional local baseline, not a production SLO: machine load, cold-start behavior, real Telegram traffic, database contention and provider latency must be measured in staging.

| Operation | Runs | p50 | p95 | Max |
|---|---:|---:|---:|---:|
| Western chart calculation | 5 | 1.39 ms | 1.49 ms | 630.17 ms |
| Tarot draw + ledger | 20 | 0.02 ms | 0.04 ms | 0.13 ms |
| Memory recall | 5 | 0.00 ms | 0.01 ms | 3027.71 ms |
| Offline PDF HTML generation | 2 | 750.41 ms | 4.64 ms* | 1496.18 ms |
| Palm-line ONNX fp16 segmentation | 3 | 8733.41 ms | 8733.41 ms | 8996.39 ms |
| Palm-line ONNX int8 segmentation (candidate) | 3 | 450.35 ms | 496.75 ms | 496.75 ms |

\*The p95 estimator is intentionally conservative only for larger samples; with two PDF samples the maximum is the meaningful cold/warm upper bound. The benchmark should be repeated with a larger sample before setting a hard local PDF threshold.

The live synthetic LLM run remains the main latency blocker: the latest bounded report recorded p95 **25.088 s** against a **15 s** target. Quality remained useful (0 critical violations, 12/12 cases, mean `0.9167`, language `1.0`, next-step `1.0`, calibration `0.8`). The next production optimization loop is provider/model selection, prompt and token budget review, timeout/fallback tuning, and staging measurement under concurrency; no latency pass is claimed here.

The palm-line helper shows a separate local tradeoff: the default fp16 model is materially slower on this CPU, while the upstream int8 variant is much faster but explicitly described as lossier on thin lines. OracleAI therefore keeps fp16 as the fidelity default and requires a consented capture-distribution benchmark before selecting int8 for production or changing the default. The helper runs outside the event loop and is skipped for hard capture-precheck failures.
