# OracleAI — evidence index

## Document orientation

| Field | Definition |
|---|---|
| **Purpose** | Explain what dated audits, QA records and benchmark summaries prove and what they do not prove. |
| **Source of truth** | The dated artifact itself plus the current code and [`../RELEASE/CURRENT_STATUS.md`](../RELEASE/CURRENT_STATUS.md). |
| **Scope** | Historical audits, local baselines, traceability, visual/benchmark records and curated audit notes. |
| **Do not change** | Do not use an old commit snapshot as current behavior without revalidation. Do not include secrets, PII or raw generated dumps. |
| **Key files** | [`../REPOSITORY_INVENTORY.md`](../REPOSITORY_INVENTORY.md), [`TRACEABILITY_MATRIX_2026-08-26.md`](TRACEABILITY_MATRIX_2026-08-26.md), dated audit files. |
| **Validation** | Re-run the relevant command and update `RELEASE/CURRENT_STATUS.md` before closing a gate. |

## Evidence policy

Every file in this directory is dated or explicitly labeled as historical. Evidence records a bounded observation: local, synthetic, staging, production or external. It does not override current code, configuration or the release status document. Raw screenshots, logs, browser traces, local databases and secret-bearing outputs stay outside the repository.

| Evidence group | Contents |
|---|---|
| Repository and implementation audits | Dated review, baseline and continuation reports. |
| QA and visual records | Browser, accessibility, PDF, performance and P2 evidence summaries. |
| Traceability | Requirement-to-code-to-test mapping from the dated audit baseline. |
| Curated audit notes | [`AUDIT/`](AUDIT/) contains two retained scaling/index reviews. |

The only current status is [`../RELEASE/CURRENT_STATUS.md`](../RELEASE/CURRENT_STATUS.md); the only current backlog is [`../RELEASE/TASKS.md`](../RELEASE/TASKS.md).
