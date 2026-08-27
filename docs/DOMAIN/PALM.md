# OracleAI — palm and visual evidence

## Document orientation

| Field | Definition |
|---|---|
| **Purpose** | Define what the palm surface can observe, retain and explain. |
| **Source of truth** | `app/core/palm.py`, `app/core/palm_vision.py`, `app/core/palm_lines.py`, `app/core/palm_full_scope.py` and `app/api/routers/placements.py`. |
| **Scope** | Upload validation, capture quality, geometry/vision evidence, normalization, persistence and user-facing limitations. |
| **Do not change** | Do not retain raw uploads or raw masks as product evidence, accept unbounded file input, or present palm observations as diagnosis or guaranteed prediction. |
| **Key files** | `app/core/palm.py`, `app/core/palm_vision.py`, `app/core/palm_lines.py`, `app/core/palm_full_scope.py`, `tests/test_palm_vision.py`, `tests/test_palm_integration.py`. |
| **Validation** | `pytest -q tests/test_palm_vision.py tests/test_palm_integration.py tests/test_placements_palm.py`, plus the configured palm benchmark when model assets are available. |

## Evidence pipeline

The current path is deliberately layered: upload MIME/size validation and image normalization, capture/hand-pose quality checks, MediaPipe geometry where configured, ONNX line evidence, bounded full-scope candidate search, optional vision adjudication, strict JSON normalization and a final LLM explanation only over normalized observations. The public result is structured evidence with quality/confidence metadata rather than a raw segmentation artifact.

The supported view matters. Some zones require a folded-edge or other explicitly requested view; an open-palm image must not be silently treated as evidence for a view it cannot show. Low-quality or incomplete captures produce a bounded recovery state rather than invented observations.

## Privacy and retention

Raw image, raw mask and raw edge-map data are not part of the retained product artifact. The persisted result is owner-scoped and deletion removes the analysis and image fingerprints according to the implementation contract. Upload size, MIME and malformed-image defenses remain server-side.

## Interpretation boundary

Palmistry output is reflective and bounded. The agent may explain normalized observations and uncertainty, but it must not diagnose disease, assert a fixed future, infer sensitive traits as fact or make high-stakes recommendations. Model confidence is not a truth guarantee.

The AI handoff is documented in [`../AI_SYSTEM.md`](../AI_SYSTEM.md); upload and endpoint behavior is documented in [`../API.md`](../API.md); open performance and real-capture gates are tracked in [`../RELEASE/CURRENT_STATUS.md`](../RELEASE/CURRENT_STATUS.md).

## References

[1]: [app/core/palm.py](../../app/core/palm.py) — palm orchestration and retention boundary.
[2]: [app/core/palm_vision.py](../../app/core/palm_vision.py) — visual evidence and quality handling.
[3]: [app/core/palm_lines.py](../../app/core/palm_lines.py) — model-backed line evidence.
[4]: [app/api/routers/placements.py](../../app/api/routers/placements.py) — authenticated upload endpoint.
[5]: [tests/test_palm_vision.py](../../tests/test_palm_vision.py) — visual evidence regression tests.
