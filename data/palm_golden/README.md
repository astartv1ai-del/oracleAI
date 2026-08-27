# Palm golden-corpus templates

This directory contains **structural templates only**. It is not a semantic accuracy dataset and it does not contain raw photographs, masks, provider responses, or production user data.

## Required workflow

Store consented images outside Git in protected review storage. For each record, keep an immutable SHA-256, provenance and consent status, two independent annotator references, capture/view labels, region-level visibility and evidence states, and domain-reviewer adjudication for `test` and `challenge` records. Prefer `unknown` or `not_supported` when anatomy or visibility is uncertain. Never promote an uncertain or not-visible region to `observed` or `inferred`.

Copy `manifest.template.jsonl` and `predictions.template.jsonl` into a protected review workspace and replace every template value before evaluation. Validate the manifest structurally with:

```bash
python scripts/validate_palm_corpus.py \
  --manifest data/palm_golden/manifest.template.jsonl \
  --schema-only
```

For a real review, use `--image-root` pointing to the protected image store. Run predictions through `scripts/run_palm_human_review.py` and provide its output to `scripts/palm_independent_critic.py`. A local contract pass does not establish semantic palmistry accuracy; semantic signoff remains blocked until an adjudicated, consented or synthetic labelled corpus and exact prediction coverage are supplied.

## Privacy boundary

Do not commit raw images or derived raw masks/edge maps. Do not put `raw_image`, `image_bytes`, `data_url`, `provider_response`, or `raw_provider_output` in manifests, predictions, reports, or logs. Do not include diagnoses, age claims, dates of life events, number of children, financial outcomes, or other prohibited claims in labels.
