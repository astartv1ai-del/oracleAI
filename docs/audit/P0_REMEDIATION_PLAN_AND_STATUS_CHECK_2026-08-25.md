# OracleAI — P0 remediation plan and current unfinished-requirements status

**Дата проверки:** 25 августа 2026 года  
**Current commit:** `4534c51dd3b7706580be41e11519f1b6d7fd1e3e`  
**Branch:** `master`  
**Release decision:** **NO-GO for public launch** until all applicable P0 gates have evidence and an accountable release owner signs the release record.

## 1. Current verification result

The verification was run against the current checkout using targeted billing/API/PDF/security/scheduler tests, domain evaluations, routing benchmarks, skill routing, backup-script presence, load-harness presence, support/accessibility/payment contract searches, Docker availability and dependency audit.

| Check | Current result | Interpretation |
|---|---|---|
| Targeted regression suite | **PASS** | Billing, API, PDF, security and scheduler tests pass in the current checkout |
| Domain evaluations | **PASS — 54 cases** | Local domain contract remains green |
| Agent routing | **PASS — 24/24** | Local routing benchmark remains green |
| Skill routing | **PASS — 20/20** | Local skill narrowing remains green |
| Backup/restore scripts | **PRESENT** | Existence is confirmed; production off-site backup is not proven |
| Load harness | **PRESENT** | Locust/simulation tooling exists; no approved production-like result is recorded |
| Support/accessibility/payment contracts | **PRESENT LOCALLY** | Code/docs/tests exist; operational/device/provider acceptance is still open |
| Docker engine | **UNAVAILABLE IN SANDBOX** | Compose/deployment execution cannot be verified in this environment |
| Live LLM | **NOT RUN** | `SELF_CHECK_LIVE=1` and approved provider/staging access are required |
| Dependency audit | **7 known vulnerabilities in 4 packages** | New security follow-up required before a production release |

The dependency audit identified: `pypdf 6.14.2` with two findings fixed in `6.15.0`; `setuptools 68.1.2` with findings requiring versions from `70.0.0`, `78.1.1` or `83.0.0` depending on advisory; `wheel 0.42.0` with a fix in `0.46.2`; and `xhtml2pdf 0.2.14` with a published vulnerability and no fix version shown by the current audit. This is not silently reclassified as a pass. It requires dependency-owner review, upgrade testing and an explicit exception or replacement decision where no fix is available.

## 2. P0 closure program

The nine P0 gates must be closed in dependency order. Local code work can proceed in parallel with staging preparation, but no public traffic should be opened until every applicable row has a reproducible evidence artifact, a named owner, a verification date and a rollback/stop condition.

### P0-1 — Production configuration and fail-closed deployment

**Objective.** Prove that production cannot start in developer mode, cannot use dev-user bypasses, and exposes only HTTPS/publicly safe endpoints.

**Steps.** First create a production-like configuration manifest with `APP_ENV=production`, `DEV_MODE=0`, HTTPS `WEBAPP_URL`, externally injected Telegram/admin credentials and no values committed to Git. Next provision a disposable staging secret set through the deployment secret mechanism, start the API and bot under the production profile, and execute health/readiness checks. Then exercise unauthenticated, invalid-init-data, admin and dev-user paths; confirm that all fail closed. Finally capture the deployment environment, config validation output, health response, logs and shutdown/rollback command.

**Acceptance criteria.** `scripts/release_gate.py` passes under the production-like configuration; no dev bypass is available; HTTPS is enforced; no secret appears in logs or artifacts; health reports database integrity and required dependencies; and rollback returns the previous version without data loss.

**Evidence.** Sanitized config manifest, release-gate output, staging startup log, negative-auth test log, health response, secret scan, deployment version and rollback record.

**Owner/dependency.** Operations. Requires an isolated staging domain, secret store and accountable release owner.

### P0-2 — Staging isolation

**Objective.** Prove that staging cannot send messages, read data or charge accounts in production.

**Steps.** Create a separate bot token, database, domain, LLM credentials, payment sandbox credentials and analytics namespace. Seed only synthetic users and synthetic content. Add an explicit environment identity to logs and health output. Run cross-environment connection checks and attempt to access production-like resource names using staging credentials. Verify that backup paths, webhook URLs and scheduled jobs point only to staging. Destroy and recreate staging to prove reproducibility.

**Acceptance criteria.** Staging has no production data, no production credentials and no production webhook/payment destination; all external calls use sandbox endpoints; and a reviewer can reproduce the isolation check from a documented runbook.

**Evidence.** Sanitized environment matrix, secret/resource mapping, synthetic DB checksum, webhook/payment endpoint report, isolation test log and teardown/recreate log.

**Owner/dependency.** Operations/Security. Must precede live provider, payment and device QA.

### P0-3 — Live LLM safety and reliability

**Objective.** Prove that live providers produce grounded, schema-valid, safe and economically bounded responses under normal, adversarial and degraded conditions.

**Steps.** Freeze a versioned RU/EN evaluation set covering natal, Tarot, palm, memory, crisis, medical/legal/financial boundaries, prompt injection, unsupported placements and code-switching. Run it against the approved provider chain in staging with synthetic profiles. Measure strict-JSON success, invalid-output retry rate, grounding violations, critical safety failures, provider timeout rate, fallback rate, circuit-open behavior, p50/p95/p99 latency, token cost and per-workflow budget. Repeat with provider failure, malformed JSON, slow response and rate-limit fixtures. Review all critical failures manually and block release on any unresolved critical safety issue.

**Acceptance criteria.** Versioned live report shows zero critical safety failures; schema success and grounding thresholds are approved; p95 latency and cost are within budget; retry/fallback/circuit-breaker behavior is observed; and the report names the exact provider/model/configuration and date.

**Evidence.** Evaluation dataset hash, provider/model manifest, raw sanitized result summary, red-team report, latency/cost table, circuit-breaker log and sign-off by AI/Safety owner.

**Owner/dependency.** AI/Safety and Operations. Requires P0-2 and approved provider access; do not use live credentials in the repository or report.

### P0-4 — Palm quality gate

**Objective.** Prove that Palm produces useful, bounded observations and reliable fallbacks without medical, longevity or unsupported event claims.

**Steps.** Assemble an approved synthetic/licensed benchmark spanning clear, blurred, dark, cropped, rotated, low-resolution and non-palm images. Run the live vision provider using the production schema. Measure valid enum/schema rate, `needs_photo` precision, p50/p95/p99 latency, retry and timeout behavior, and output safety. Manually review a stratified sample for image-grounded observations, no diagnosis, no lifespan claims, no fabricated features and correct localization. Verify original images are not retained beyond the documented policy.

**Acceptance criteria.** At least 99% valid schema rate on the approved benchmark; p95 latency within the product budget; quality fallback works on poor images; zero critical medical/longevity/unsupported-event failures; and retention/deletion behavior is evidenced.

**Evidence.** Benchmark manifest/hash, sanitized image metadata, schema/latency report, manual QA rubric, retention/deletion log and AI/Product sign-off.

**Owner/dependency.** AI/Product. Requires P0-2 and live multimodal provider access.

### P0-5 — Real Telegram device UX

**Objective.** Prove the mandatory user journey in Telegram on iOS, Android and Desktop for RU and EN.

**Steps.** Create a device matrix and test accounts isolated from production. Execute first launch, 16+ gate, onboarding, birth-data entry, chart, chat, Stop/retry, offline/slow-provider state, Palm upload, PDF generation, share/revoke, checkout return, deletion and re-login. Capture small viewport, safe-area, keyboard, permission, loading, empty, error and long-content states. Record severity, screenshot/video, device/OS/Telegram version and reproduction steps.

**Acceptance criteria.** All P0 journey cases pass; no blocker/critical UX defects; no private data leaks in share or analytics; loading/error/slow-provider states remain actionable; and accessibility checks cover touch targets, focus, contrast, reduced motion and screen-reader critical paths.

**Evidence.** Signed device matrix, fresh screenshots/videos, defect register, accessibility checklist and QA sign-off.

**Owner/dependency.** Product/QA. Requires staging, P0-1/P0-2 and provider/device access.

### P0-6 — Privacy and legal review

**Objective.** Obtain qualified approval for the first-wave countries and the actual data/claims/payment model.

**Steps.** Freeze the product data map: Telegram identifiers, birth data, images, memory/diary content, generated reports, analytics events, provider transfers, retention and deletion. Review Privacy, Terms, 16+ gate, safety wording, cross-border processing, processor contracts, user deletion and support paths. Define the first-wave country scope and record jurisdiction-specific constraints. Resolve every legal review comment before launch; do not change age threshold, claims or policy text autonomously.

**Acceptance criteria.** Written legal/privacy sign-off covers intended countries, data categories, retention/deletion, subprocessors, cross-border processing, user rights, age/payment eligibility and product claims. Public pages match the approved version and the release record names the reviewer/date.

**Evidence.** Data map, policy version hashes, review memo, processor/subprocessor list, deletion/retention test, country-scope decision and release-owner approval.

**Owner/dependency.** Product/Legal. External dependency; cannot be closed by unit tests.

### P0-7 — Production backup and restore

**Objective.** Prove recoverability, confidentiality and known RPO/RTO for production data.

**Steps.** Configure encrypted off-site backup with key custody separate from the backup destination. Add checksum, retention and backup-age monitoring. Run a scheduled backup in staging, restore into an isolated database, run `PRAGMA integrity_check`, migrations, schema checks, anonymized health/selfcheck and representative read-only journeys. Record elapsed time, data-loss window and failure/rollback handling. Repeat on the documented cadence before launch.

**Acceptance criteria.** Latest encrypted backup is retrievable; checksum verifies; isolated restore succeeds; post-restore selfcheck and migration checks pass; RPO/RTO are measured and within the approved thresholds; and no production data is exposed in evidence.

**Evidence.** Backup manifest/checksum, key-custody record, restore log, integrity/selfcheck output, RPO/RTO result, retention configuration and scheduled-run alert.

**Owner/dependency.** Operations. Local disposable plaintext/encrypted fixture already passes; off-site and scheduled production proof remain open.

### P0-8 — Incident response

**Objective.** Prove that the team can detect, contain, communicate and recover from safety, data, provider and payment incidents.

**Steps.** Assign named primary and backup on-call owners. Define severity levels, escalation times, contact tree, incident channel, evidence-preservation rules and user/support templates. Run a tabletop for a critical safety failure, data exposure, provider outage and payment/webhook inconsistency. Execute at least one rollback or feature-flag disable path and measure acknowledgement/recovery times. Store no secrets or user content in the report.

**Acceptance criteria.** Every scenario has an owner, stop action, communication path, rollback/recovery command and post-incident checklist; tabletop participants can execute the runbook; and the release record contains contacts and SLA.

**Evidence.** Incident runbook, contact tree, tabletop minutes, alert-to-acknowledgement timeline, rollback output and postmortem template.

**Owner/dependency.** Operations/Support. Requires monitoring and staging; legal/privacy input is needed for user communication.

### P0-9 — Production monitoring and test alerts

**Objective.** Prove that critical failures are visible to the right operator before users report them.

**Steps.** Create dashboards for health, HTTP 5xx, webhook failures, LLM/provider success/fallback/cost, scheduler freshness, backup age, payment state and privacy-safe funnel signals. Connect test-alert destinations and verify acknowledgement. Define thresholds, SLO placeholders, escalation and feature-flag actions. Generate synthetic failures for scheduler stale, provider timeout, webhook failure, backup age and high 5xx. Confirm alerts contain no raw chat, diary, memory, palm or birth-data payloads.

**Acceptance criteria.** Every P0 failure mode generates a test alert; the correct owner receives and acknowledges it; dashboard queries are reproducible; alert payloads are privacy-safe; and the incident runbook references each alert.

**Evidence.** Dashboard links/export, alert-rule version, synthetic alert log, acknowledgement record, privacy review and runbook cross-links.

**Owner/dependency.** Operations. Local scheduler lease/status and alert parsing pass; real dashboards and alert routing remain open.

## 3. Recommended sequencing and exit criteria

### Wave A — foundation

Create the accountable release owner, isolated staging, production-like configuration, environment/resource matrix, dependency inventory and security exception process. Before any live provider test, resolve or formally accept the seven pip-audit findings; upgrade `pypdf`, `setuptools` and `wheel`, and decide whether `xhtml2pdf` is upgraded, replaced or isolated with a documented risk acceptance.

### Wave B — live quality and platform proof

Run the live LLM and Palm benchmarks, the real-device Telegram matrix, and the backup/restore rehearsal. In parallel, implement monitoring dashboards, test alerts and incident response tabletop. Do not open external traffic if any P0 produces a critical defect or has no evidence owner.

### Wave C — legal and operational approval

Complete privacy/legal review for the intended first-wave countries, close all P0 comments, certify support ownership and verify that public policy pages match the approved version. Only then prepare controlled-beta traffic caps and stop conditions.

### Wave D — launch decision

Produce a release record containing all P0 evidence, dependency audit result/exception, backup checksum and restore log, device matrix, live LLM/Palm reports, legal sign-off, dashboard links, incident tabletop, rollback command and named owner. The release owner may approve controlled beta only when all P0 rows are closed. Public launch additionally requires all P1 gates, two successful invite waves and a documented go/no-go decision.

## 4. Remaining non-P0 requirements — current status

| Area | Current status | Current verification | Next action |
|---|---|---|---|
| Product moat / memory value | **PARTIAL** | Runtime paths and local isolation tests exist | Run privacy-safe cohort test for relevance, opt-in comprehension and deletion |
| Full E2E journey | **PARTIAL** | Targeted API/billing/PDF/security tests pass | Execute real Telegram share, checkout return, restore, deletion and re-login matrix |
| Domain source registry | **PARTIAL** | Deterministic domain evaluations pass 54 cases | Expand source/license/settings/tolerance registry and sign off dates |
| PDF regression | **PASS locally / follow-up** | Existing RU/EN profile QA and targeted tests pass | Add malicious markup, long-name, font fallback, print/device cases |
| Competitive analysis | **PARTIAL** | Existing research and ADRs retained | Refresh dated RU/EN matrix with confirmed feature/pricing URLs |
| Monetization | **PARTIAL / sandbox only** | Local billing, entitlement, idempotency and refund contracts pass | Certify provider sandbox, server-owned price book, tax/fees and unit economics |
| Dubai/UAE GTM | **BLOCKED** | No approved legal/payment/market pack | Obtain external legal/payment review, research and go/no-go approval |
| Tone/localization/safety | **PASS locally / PARTIAL release** | RU/EN prompts, safety, crisis, age and privacy contracts pass | Human/device language review and legal approval |
| Security/privacy/abuse | **PARTIAL release** | Secret scan and local security regressions pass; dependency audit finds 7 vulnerabilities | Remediate/accept dependency findings, run production threat/DAST review and webhook sandbox |
| Infrastructure/observability | **PARTIAL** | Scripts, load harness and local scheduler/ops checks present | Run Docker/staging, off-site restore, dashboards, alerts, SLO and on-call rehearsal |
| Capacity | **OPEN** | Load harness exists; no approved measured result | Run representative load and decide SQLite vs migration |
| Support/analytics/beta | **OPEN** | Supporting docs/contracts exist | Assign owner/SLA, implement privacy-safe funnel, run two invite waves |
| Runtime line audit | **PARTIAL** | Scheduler high-risk path audited | Continue file-by-file review of remaining legacy/runtime paths |
| Documentation consistency | **PARTIAL** | Current reports are present | Reconcile older architecture/competitor claims with the current completed implementation and mark historical statements clearly |

## 5. Current blockers that require external access or owner decision

The sandbox cannot close production configuration, staging isolation, live LLM/Palm, device UX, legal/privacy, off-site backup, incident ownership, production monitoring, capacity or payment-provider evidence. Docker is unavailable in the current sandbox. Live LLM was not run. The dependency audit is not a sandbox limitation: it found seven known package vulnerabilities and requires a real remediation decision before production approval.

## References

[1]: [Master requirements status](MASTER_REQUIREMENTS_STATUS_2026-08-25.md)  
[2]: [Launch governance](../LAUNCH_GOVERNANCE.md)  
[3]: [Remaining public-launch tasks](REMAINING_TASKS_PUBLIC_LAUNCH_2026-08-25.md)  
[4]: [Traceability matrix](../TRACEABILITY_MATRIX.md)  
[5]: [Current unfinished-requirements check](unfinished_requirements_check_2026-08-25.txt)


## 6. Execution results from the ordered cycle

| Workstream | Execution result | Gate impact |
|---|---|---|
| Dependency scope | `pip-audit -r requirements-dev.txt` reported **No known vulnerabilities found** for declared project requirements. Ambient sandbox audit separately reported seven findings in four installed packages; those are not accepted as product-image proof and require a clean image audit. | Local dependency scope clarified; production dependency gate remains pending clean Docker/image verification |
| P0-1 production-like config | `APP_ENV=production DEV_MODE=0 WEBAPP_URL=https://staging.example.invalid` with synthetic credentials passed `scripts/release_gate.py --production`. | Static/config contract PASS; real production secrets/domain/deploy remain OPEN |
| P0-2 staging isolation | Disposable database/API smoke returned `{"ok":true}` with a synthetic bot token and temporary data directory. | Isolated local smoke PASS; real staging resource separation remains OPEN |
| P0-3 live LLM | `scripts/live_llm_probe.py` attempted the configured provider; two attempts returned an empty model response and the probe ended with `RuntimeError: Все LLM-провайдеры недоступны: openai: пустой ответ модели`. | **OPEN**; live provider quality is not green |
| P0-4 Palm | Local schema/safety/ownership contracts remain covered by targeted tests. No new live multimodal pass was claimed because the configured live provider did not return usable output in P0-3. | **OPEN** |
| P0-5 devices | No real iOS/Android/Desktop Telegram devices are available in the sandbox. | **OPEN** |
| P0-6 legal/privacy | No qualified legal review or country-scope approval can be performed by the sandbox. | **EXTERNAL** |
| P0-7 backup/restore | Disposable plaintext and AES-256 encrypted backup/restore passed with checksum and SQLite integrity verification; fixture value restored correctly. | Local fixture PASS; off-site key custody/schedule/RPO/RTO remain OPEN |
| P0-8 incident response | `docs/INCIDENT_RESPONSE_RUNBOOK.md` created with severity, containment, escalation and scenario playbooks. Named owners and tabletop acknowledgement remain open. | Runbook prepared; gate remains OPEN |
| P0-9 monitoring | Synthetic `ops_alerts.py` dry-run detected HTTP 5xx, webhook failure, stale backup and scheduler error signals without user content. | Local alert parser PASS; real dashboards, recipients and acknowledgement remain OPEN |
| P1 capacity follow-up | Disposable local load simulation passed: start flood 200/200, forecast 150/150, questions 60/60, payment 20/20, all with zero errors; question p95 44.2 ms in the offline stub. | Mechanism smoke PASS; production-like capacity remains OPEN |
| Payment follow-up | Local billing/API/security targeted tests pass; provider sandbox signed webhook/reconciliation was not run. | **PARTIAL** |

## 7. Evidence generated in this cycle

`docs/audit/live_llm_probe_2026-08-25.txt`, `docs/audit/declared_requirements_audit_2026-08-25.txt`, `docs/audit/monitoring_incident_dry_run_2026-08-25.txt`, `docs/audit/unfinished_requirements_check_2026-08-25.txt`, `docs/INCIDENT_RESPONSE_RUNBOOK.md` and this report record the current execution result. No live credential, payment, production database or user data was stored.

The cycle closes all locally actionable preparation and fixture checks that were available in the sandbox. It does not close external P0 gates whose required evidence depends on real providers, Telegram devices, production-like infrastructure, qualified legal review, off-site storage or named operational owners.
