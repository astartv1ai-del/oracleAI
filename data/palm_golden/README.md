# Palm Golden Corpus

This directory contains the semantic ground-truth manifest and templates for palm-reading accuracy evaluation.

## Files

- `schema.json`: JSON Schema for a single golden record.
- `manifest.template.jsonl`: Structural template for the adjudicated manifest.
- `predictions.template.jsonl`: Structural template for model predictions.
- `manifest.jsonl`: (Local only) The actual adjudicated manifest with image hashes.

## Security and Privacy

**DO NOT commit real user images or PII to this repository.**

The `manifest.jsonl` file should only contain image hashes and semantic labels. Raw images must be stored in a secure, access-controlled environment (e.g., encrypted S3 bucket or protected local volume) and referenced by their relative path.
