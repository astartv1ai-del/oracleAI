>
> **STATUS: HISTORICAL**
> **SUPERSEDED BY:** [`docs/RELEASE/CURRENT_STATUS.md`](../RELEASE/CURRENT_STATUS.md)
> **LAST VERIFIED:** 2026-08-27
> This file is retained as dated evidence or context. It is not the current source of truth.

# P2 release checklist

**Дата обновления:** 27 августа 2026 года
**Область:** остаточные P2-риски из аудита OracleAI.

Этот реестр является частью release evidence. Статус **PASS** означает, что локальный автоматический контракт проверен в disposable/offline окружении. Статус **OPEN** означает проверку, которую нельзя честно выполнить без реального Telegram WebView, физических устройств, staging-провайдера, production storage или решения владельца продукта. Synthetic-тест не переводит внешний gate в PASS.

## Сводный статус

| ID | Направление | Автоматический результат | Внешний или ручной gate | Статус релиза |
|---|---|---|---|---|
| P2-001 | Visual QA / responsive UI | Capture contract, CSS design contract и desktop audit definitions tracked | Проверить landing, loading, empty/error, Telegram iOS/Android/desktop и четыре ширины с реальными WebView | OPEN — manual |
| P2-002 | Accessibility | Contrast, semantic-label, focus-ring, reduced-motion и touch-target contracts pass locally | Полный keyboard/Shift+Tab, screen reader, focus return, zoom, orientation и touch review | OPEN — manual |
| P2-003 | Localization | RU/EN key parity, glossary, plural-count cases и PDF localization checks pass locally | Носитель языка проверяет длинные labels, typography, glyph fallback и product terminology | OPEN — manual |
| P2-004 | Account lifecycle | Confirm-gated, idempotent anonymization and privacy regressions pass | Владелец/юрист подтверждает retention exceptions, support workflow и deletion SLA | OPEN — external |
| P2-005 | Avatar / uploads | MIME, size, malformed-image, normalization, no-raw-image persistence and deletion scrub pass | Проверить object-storage lifecycle, retention expiry, deletion drill и avatar-specific UI in staging | OPEN — external/manual |
| P2-006 | Report templates | Natal golden cases, localization, truth-state and template catalog contracts pass | Проверить print/mobile pixels, font licensing, synastry/Tarot product approval and rollback | OPEN — product/external |
| P2-007 | Performance | Offline representative benchmark reports p50/p95 and reproducible pass | Run staging SLO with live provider chain, representative conversations and alert thresholds | OPEN — staging |
| P2-008 | Growth / monetization UX | Price/entitlement/invoice copy, retry/history states and payment safety contracts pass | Provider sandbox for Stars/Crypto, trial/cancellation/refund copy review and settlement drill | OPEN — external/manual |

## Reproducible local gate

Run from the repository root with providers disabled:

```bash
LLM_PROVIDER=off SELF_CHECK_LIVE=0 OPENAI_API_KEY= OPENAI_API_BASE= EMBED_MODEL='' \
  /tmp/oracleai-venv/bin/python scripts/check_p2_quality.py
```

The gate is read-only. It verifies tracked evidence, Markdown links, locale parity and glossary coverage, accessibility/design contracts, report golden cases, backup/restore isolation, palm-retention scrubbing, payment UX safety markers, benchmark reproducibility and the explicit manual-gate register.

## Manual evidence packet

For P2-001 and P2-002, the owner must attach screenshots and a short screen recording for 375px, 768px, 1440px and 1920px surfaces, then record keyboard traversal, focus return after modal close, screen-reader names, contrast on actual surfaces, touch targets and Telegram viewport/keyboard transitions. The packet must identify client, operating system, Telegram version, locale and commit SHA.

For P2-005, staging evidence must show that an uploaded image is normalized in memory, that no raw bytes or reversible URL are persisted, that a deleted reading has no analysis or image fingerprint, and that object-storage lifecycle rules remove any temporary object. The test must include malformed, oversized, unsupported, low-quality and duplicate uploads.

For P2-008, the provider sandbox packet must include successful, failed, expired, duplicated and refunded events for each enabled provider. The product owner must approve copy for pricing, trial, cancellation, refund and entitlement failure states; the copy must not use false scarcity, fear, guaranteed outcomes or an obstructive cancellation path.

## Evidence ownership and closure rule

A P2 row may be marked **Done** only after both its local automated checks and its listed external/manual gate have evidence links. Until then, `docs/RELEASE/TASKS.md` and this register intentionally retain the `partial`, `manual`, `staging` or `external` qualifier.

## References

[1]: https://www.w3.org/WAI/WCAG22/ "W3C Web Content Accessibility Guidelines 2.2"

[2]: https://core.telegram.org/bots/webapps "Telegram Mini Apps documentation"

[3]: https://core.telegram.org/bots/payments-stars "Telegram Stars payments documentation"
