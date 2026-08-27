# OracleAI — Tarot and card reflection

## Document orientation

| Field | Definition |
|---|---|
| **Purpose** | Define the enabled Tarot reading contract and the boundary between a persisted draw and interpretation. |
| **Source of truth** | `app/core/tarot.py`, `app/api/routers/tarot.py`, the reading repositories and `tests/test_tarot_contract.py`. |
| **Scope** | Card draw, positions, orientation, replay, history and safe interpretation. |
| **Do not change** | Do not invent cards, positions, orientation, timing or certainty; do not imply that an upstream Lenormand capability is an enabled product. |
| **Key files** | `app/core/tarot.py`, `app/repo/readings.py`, `app/api/routers/tarot.py`, `tests/test_tarot_contract.py`, `tests/test_report_history.py`. |
| **Validation** | `pytest -q tests/test_tarot_contract.py tests/test_core.py tests/test_report_history.py`. |

## Enabled Tarot contract

A Tarot request first produces and persists a bounded draw ledger. The ledger contains the selected cards, spread positions and orientation/reversal state before an interpretation is generated. History and replay read the stored ledger rather than drawing again, so a user can reopen the same reading without changing its evidence.

The implementation preserves the 78-card invariants and owner scope. Reversed cards are a property of the persisted draw and must not be introduced or removed by the model. Regeneration of an explanation does not silently replace the original draw; immutable report/history semantics are documented in [`../FEATURES/HISTORY.md`](../FEATURES/HISTORY.md).

## Safety boundary

Tarot is a reflection product. The response may offer a bounded interpretation and a manageable next step, but it must not claim deterministic future events, read a third party’s private mind, give medical/legal/financial diagnosis, or present symbolic cards as proof.

Unsupported card systems must be explicit. The current canonical boundary treats Lenormand as disabled unless a separately versioned contract, enabled route, evidence policy, UI, persistence and tests are added. A fallback must not be described as a Lenormand reading.

## Product and API links

The Tarot route and client behavior are described in [`../API.md`](../API.md), while agent tool permissions and output guardrails are canonical in [`../AI_SYSTEM.md`](../AI_SYSTEM.md). Domain-wide evidence policy is in [`CONTRACTS.md`](CONTRACTS.md).

## References

[1]: [app/core/tarot.py](../../app/core/tarot.py) — draw and interpretation primitives.
[2]: [app/api/routers/tarot.py](../../app/api/routers/tarot.py) — Tarot HTTP routes.
[3]: [tests/test_tarot_contract.py](../../tests/test_tarot_contract.py) — Tarot regression contract.
[4]: [FEATURES/HISTORY.md](../FEATURES/HISTORY.md) — immutable history boundary.
