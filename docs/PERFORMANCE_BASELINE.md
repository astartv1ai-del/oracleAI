# Local performance baseline

**Дата:** 26 августа 2026

`python3 scripts/benchmark_product_performance.py` measures representative synthetic operations without provider calls. The result is a directional local baseline, not a production SLO: machine load, cold-start behavior, real Telegram traffic, database contention and provider latency must be measured in staging.

| Operation | Runs | p50 | p95 | Max |
|---|---:|---:|---:|---:|
| Western chart calculation | 5 | 1.32 ms | 1.42 ms | 640.35 ms |
| Tarot draw + ledger | 20 | 0.02 ms | 0.04 ms | 0.14 ms |
| Memory recall | 5 | 0.00 ms | 0.00 ms | 0.70 ms |
| Offline PDF HTML generation | 2 | 794.03 ms | 3.79 ms* | 1584.27 ms |
| Palm-line ONNX fp16 segmentation | 3 | 8355.97 ms | 8355.97 ms | 8597.62 ms |
| Palm-line ONNX int8 segmentation (candidate) | 3 | 450.35 ms | 496.75 ms | 496.75 ms |

\*The p95 estimator is intentionally conservative only for larger samples; with two PDF samples the maximum is the meaningful cold/warm upper bound. The benchmark should be repeated with a larger sample before setting a hard local PDF threshold.

The live synthetic LLM run remains the main latency blocker: after the context/prompt hardening pass, `gpt-5-mini` p95 was **23.899 s** against a **15 s** target. Quality remained strong (0 critical violations, mean `0.9583`, language `1.0`, next-step `1.0`, calibration `0.9`). The next production optimization loop is provider/model selection, prompt and token budget review, timeout/fallback tuning, and staging measurement under concurrency; no latency pass is claimed here.

The palm-line helper shows a separate local tradeoff: the default fp16 model is materially slower on this CPU, while the upstream int8 variant is much faster but explicitly described as lossier on thin lines. OracleAI therefore keeps fp16 as the fidelity default and requires a consented capture-distribution benchmark before selecting int8 for production or changing the default. The helper runs outside the event loop and is skipped for hard capture-precheck failures.
