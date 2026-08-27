# OracleAI — repository inventory

> **Status:** working inventory generated from the current repository tree checked out from `master`. This document is an audit aid, not a source of truth for runtime behavior.
>
> **Method:** paths and file modes come from Git; references are conservative literal path matches in tracked text files; generated/stale/canonical flags are review signals and require human confirmation. No deletion is implied by a heuristic flag.

## Legend

| Field | Meaning |
|---|---|
| Type | Detected file family. |
| References | Number of other repository text files containing the exact path. |
| Imported/referenced | `yes` only when at least one literal path reference was found; code imports may be indirect. |
| Executable | Git file mode contains an execute bit. |
| Generated? | Heuristic signal from path/name; verify before moving or deleting. |
| Stale candidate? | Name-based review signal only. |
| Canonical? | Reserved for the small current documentation core. |
| Decision | Initial inventory action; `REVIEW` is not an automatic delete. |

## Summary

- Repository files inventoried: **995**.
- Markdown/text files: **261**.
- Source/config/test files: **309**.
- Assets/models/PDFs: **109**.

## File-by-file inventory

| Path | Type | Approximate purpose | Size, bytes | References | Referenced? | Executable? | Generated? | Stale candidate? | Canonical? | Decision |
|---|---|---|---:|---:|:---:|:---:|:---:|:---:|:---:|---|
| `.dockerignore` | Other | Other repository file. | 466 | 1 | yes | no | no | no | no | KEEP |
| `.env.example` | Other | Environment variable template. | 5617 | 9 | yes | no | no | no | no | KEEP |
| `.env.production.example` | Other | Environment variable template. | 6934 | 3 | yes | no | no | no | no | KEEP |
| `.github/workflows/ci.yml` | YAML | Continuous integration configuration. | 2716 | 7 | yes | no | no | no | no | KEEP |
| `.gitignore` | Other | Other repository file. | 800 | 3 | yes | no | no | no | no | KEEP |
| `.pytest_cache/.gitignore` | Other | Other repository file. | 37 | 1 | yes | no | no | no | no | KEEP |
| `.pytest_cache/CACHEDIR.TAG` | Other | Other repository file. | 191 | 1 | yes | no | no | no | no | KEEP |
| `.pytest_cache/README.md` | Markdown | Markdown repository file. | 302 | 1 | yes | no | no | no | no | KEEP |
| `.pytest_cache/v/cache/nodeids` | Other | Other repository file. | 48547 | 1 | yes | no | no | no | no | KEEP |
| `.ruff_cache/.gitignore` | Other | Other repository file. | 35 | 1 | yes | no | no | no | no | KEEP |
| `.ruff_cache/0.6.9/10220782102293000912` | Other | Other repository file. | 3630 | 1 | yes | no | no | no | no | KEEP |
| `.ruff_cache/0.6.9/16472115779547811747` | Other | Other repository file. | 7701 | 1 | yes | no | no | no | no | KEEP |
| `.ruff_cache/0.6.9/9456835563799503800` | Other | Other repository file. | 3375 | 1 | yes | no | no | no | no | KEEP |
| `.ruff_cache/CACHEDIR.TAG` | Other | Other repository file. | 43 | 1 | yes | no | no | no | no | KEEP |
| `Makefile` | Other | Operator/developer command entry points. | 1042 | 6 | yes | no | no | no | no | KEEP |
| `README.md` | Markdown | Корневая точка входа для продукта, запуска и документации. | 2300 | 13 | yes | no | no | no | yes | KEEP |
| `admin/admin.css` | CSS | Admin panel client. | 18464 | 3 | yes | no | no | no | no | KEEP |
| `admin/admin.js` | JavaScript/TypeScript | Admin panel client. | 70580 | 4 | yes | no | no | no | no | KEEP |
| `admin/index.html` | HTML | Admin panel client. | 18088 | 4 | yes | no | no | no | no | KEEP |
| `alembic.ini` | Other | Other repository file. | 623 | 2 | yes | no | no | no | no | KEEP |
| `alembic/env.py` | Python | Persistence, schema or database migration. | 1712 | 1 | yes | no | no | no | no | KEEP |
| `alembic/versions/0001_pg_baseline.py` | Python | Persistence, schema or database migration. | 997 | 2 | yes | no | yes | no | no | KEEP |
| `alembic/versions/0002_task_jobs.py` | Python | Persistence, schema or database migration. | 1250 | 2 | yes | no | no | no | no | KEEP |
| `app/__init__.py` | Python | Python repository file. | 0 | 2 | yes | no | no | no | no | KEEP |
| `app/__pycache__/__init__.cpython-312.pyc` | Other | Other repository file. | 134 | 1 | yes | no | no | no | no | KEEP |
| `app/__pycache__/config.cpython-312.pyc` | Other | Other repository file. | 13215 | 1 | yes | no | no | no | no | KEEP |
| `app/__pycache__/db.cpython-312.pyc` | Other | Other repository file. | 6246 | 1 | yes | no | no | no | no | KEEP |
| `app/agents/README.md` | Markdown | Agent runtime, persona, skill or domain knowledge. | 2627 | 1 | yes | no | no | no | no | KEEP |
| `app/agents/SKILL_AUTHORING.md` | Markdown | Agent runtime, persona, skill or domain knowledge. | 3151 | 1 | yes | no | no | no | no | KEEP |
| `app/agents/lenormand/SYSTEM.md` | Markdown | Agent runtime, persona, skill or domain knowledge. | 2720 | 2 | yes | no | no | no | no | KEEP |
| `app/agents/lenormand/agent.yaml` | YAML | Agent runtime, persona, skill or domain knowledge. | 848 | 1 | yes | no | no | no | no | KEEP |
| `app/agents/lenormand/evals/README.md` | Markdown | Agent runtime, persona, skill or domain knowledge. | 157 | 1 | yes | no | no | no | no | KEEP |
| `app/agents/lenormand/evals/cases.yaml` | YAML | Agent runtime, persona, skill or domain knowledge. | 3662 | 1 | yes | no | no | no | no | KEEP |
| `app/agents/lenormand/knowledge/DOMAIN.md` | Markdown | Agent runtime, persona, skill or domain knowledge. | 349 | 1 | yes | no | no | no | no | KEEP |
| `app/agents/lenormand/knowledge/DOMAIN_PLAYBOOK.md` | Markdown | Agent runtime, persona, skill or domain knowledge. | 5486 | 1 | yes | no | no | no | no | KEEP |
| `app/agents/lenormand/skills.manifest.yaml` | YAML | Agent runtime, persona, skill or domain knowledge. | 6148 | 1 | yes | no | no | no | no | KEEP |
| `app/agents/lenormand/skills/anti-barnum-protocol/SKILL.md` | Markdown | Agent runtime, persona, skill or domain knowledge. | 2154 | 2 | yes | no | no | no | no | KEEP |
| `app/agents/lenormand/skills/anti-barnum/SKILL.md` | Markdown | Agent runtime, persona, skill or domain knowledge. | 2415 | 2 | yes | no | no | no | no | KEEP |
| `app/agents/lenormand/skills/card-combinations/SKILL.md` | Markdown | Agent runtime, persona, skill or domain knowledge. | 2427 | 2 | yes | no | no | no | no | KEEP |
| `app/agents/lenormand/skills/card-ledger-evidence/SKILL.md` | Markdown | Agent runtime, persona, skill or domain knowledge. | 1724 | 2 | yes | no | no | no | no | KEEP |
| `app/agents/lenormand/skills/card-position-semantics/SKILL.md` | Markdown | Agent runtime, persona, skill or domain knowledge. | 2455 | 2 | yes | no | no | no | no | KEEP |
| `app/agents/lenormand/skills/career-spread/SKILL.md` | Markdown | Agent runtime, persona, skill or domain knowledge. | 2449 | 2 | yes | no | no | no | no | KEEP |
| `app/agents/lenormand/skills/choice-spread/SKILL.md` | Markdown | Agent runtime, persona, skill or domain knowledge. | 2439 | 2 | yes | no | no | no | no | KEEP |
| `app/agents/lenormand/skills/combination-synthesis/SKILL.md` | Markdown | Agent runtime, persona, skill or domain knowledge. | 1812 | 2 | yes | no | no | no | no | KEEP |
| `app/agents/lenormand/skills/court-cards/SKILL.md` | Markdown | Agent runtime, persona, skill or domain knowledge. | 2435 | 2 | yes | no | no | no | no | KEEP |
| `app/agents/lenormand/skills/cross-agent-routing/SKILL.md` | Markdown | Agent runtime, persona, skill or domain knowledge. | 2445 | 2 | yes | no | no | no | no | KEEP |
| `app/agents/lenormand/skills/daily-draw/SKILL.md` | Markdown | Agent runtime, persona, skill or domain knowledge. | 2087 | 2 | yes | no | no | no | no | KEEP |
| `app/agents/lenormand/skills/decision-matrix/SKILL.md` | Markdown | Agent runtime, persona, skill or domain knowledge. | 2083 | 2 | yes | no | no | no | no | KEEP |
| `app/agents/lenormand/skills/deck-variation/SKILL.md` | Markdown | Agent runtime, persona, skill or domain knowledge. | 2085 | 2 | yes | no | no | no | no | KEEP |
| `app/agents/lenormand/skills/elemental-dignities/SKILL.md` | Markdown | Agent runtime, persona, skill or domain knowledge. | 2104 | 2 | yes | no | no | no | no | KEEP |
| `app/agents/lenormand/skills/major-arcana-journey/SKILL.md` | Markdown | Agent runtime, persona, skill or domain knowledge. | 2457 | 2 | yes | no | no | no | no | KEEP |
| `app/agents/lenormand/skills/major-arcana/SKILL.md` | Markdown | Agent runtime, persona, skill or domain knowledge. | 2070 | 2 | yes | no | no | no | no | KEEP |
| `app/agents/lenormand/skills/minor-arcana-numerology/SKILL.md` | Markdown | Agent runtime, persona, skill or domain knowledge. | 2110 | 2 | yes | no | no | no | no | KEEP |
| `app/agents/lenormand/skills/minor-arcana-suits/SKILL.md` | Markdown | Agent runtime, persona, skill or domain knowledge. | 2461 | 2 | yes | no | no | no | no | KEEP |
| `app/agents/lenormand/skills/narrative-three-act/SKILL.md` | Markdown | Agent runtime, persona, skill or domain knowledge. | 2081 | 2 | yes | no | no | no | no | KEEP |
| `app/agents/lenormand/skills/question-clarity/SKILL.md` | Markdown | Agent runtime, persona, skill or domain knowledge. | 2433 | 2 | yes | no | no | no | no | KEEP |
| `app/agents/lenormand/skills/question-to-spread/SKILL.md` | Markdown | Agent runtime, persona, skill or domain knowledge. | 1497 | 2 | yes | no | no | no | no | KEEP |
| `app/agents/lenormand/skills/reading-review/SKILL.md` | Markdown | Agent runtime, persona, skill or domain knowledge. | 2093 | 2 | yes | no | no | no | no | KEEP |
| `app/agents/lenormand/skills/relationship-spread/SKILL.md` | Markdown | Agent runtime, persona, skill or domain knowledge. | 2467 | 2 | yes | no | no | no | no | KEEP |
| `app/agents/lenormand/skills/reversed-cards/SKILL.md` | Markdown | Agent runtime, persona, skill or domain knowledge. | 3011 | 2 | yes | no | no | no | no | KEEP |
| `app/agents/lenormand/skills/rws-deck-structure/SKILL.md` | Markdown | Agent runtime, persona, skill or domain knowledge. | 2463 | 2 | yes | no | no | no | no | KEEP |
| `app/agents/lenormand/skills/rws-school/SKILL.md` | Markdown | Agent runtime, persona, skill or domain knowledge. | 2445 | 2 | yes | no | no | no | no | KEEP |
| `app/agents/lenormand/skills/shadow-card/SKILL.md` | Markdown | Agent runtime, persona, skill or domain knowledge. | 2121 | 2 | yes | no | no | no | no | KEEP |
| `app/agents/lenormand/skills/suit-dynamics/SKILL.md` | Markdown | Agent runtime, persona, skill or domain knowledge. | 2080 | 2 | yes | no | no | no | no | KEEP |
| `app/agents/lenormand/skills/tarot-history/SKILL.md` | Markdown | Agent runtime, persona, skill or domain knowledge. | 2445 | 2 | yes | no | no | no | no | KEEP |
| `app/agents/lenormand/skills/tarot-journaling/SKILL.md` | Markdown | Agent runtime, persona, skill or domain knowledge. | 2435 | 2 | yes | no | no | no | no | KEEP |
| `app/agents/lenormand/skills/tarot-proof-safety/SKILL.md` | Markdown | Agent runtime, persona, skill or domain knowledge. | 1470 | 2 | yes | no | no | no | no | KEEP |
| `app/agents/lenormand/skills/tarot-safety/SKILL.md` | Markdown | Agent runtime, persona, skill or domain knowledge. | 2453 | 2 | yes | no | no | no | no | KEEP |
| `app/agents/lenormand/skills/three-card-spread/SKILL.md` | Markdown | Agent runtime, persona, skill or domain knowledge. | 2467 | 2 | yes | no | no | no | no | KEEP |
| `app/agents/lenormand/skills/uncertainty-language/SKILL.md` | Markdown | Agent runtime, persona, skill or domain knowledge. | 2457 | 2 | yes | no | no | no | no | KEEP |
| `app/agents/lenormand/skills/visual-symbol-reading/SKILL.md` | Markdown | Agent runtime, persona, skill or domain knowledge. | 3007 | 2 | yes | no | no | no | no | KEEP |
| `app/agents/lilith/SYSTEM.md` | Markdown | Agent runtime, persona, skill or domain knowledge. | 3941 | 2 | yes | no | no | no | no | KEEP |
| `app/agents/lilith/agent.yaml` | YAML | Agent runtime, persona, skill or domain knowledge. | 1031 | 1 | yes | no | no | no | no | KEEP |
| `app/agents/lilith/evals/README.md` | Markdown | Agent runtime, persona, skill or domain knowledge. | 168 | 1 | yes | no | no | no | no | KEEP |
| `app/agents/lilith/evals/cases.yaml` | YAML | Agent runtime, persona, skill or domain knowledge. | 3294 | 1 | yes | no | no | no | no | KEEP |
| `app/agents/lilith/knowledge/DOMAIN.md` | Markdown | Agent runtime, persona, skill or domain knowledge. | 358 | 1 | yes | no | no | no | no | KEEP |
| `app/agents/lilith/knowledge/DOMAIN_PLAYBOOK.md` | Markdown | Agent runtime, persona, skill or domain knowledge. | 5584 | 1 | yes | no | no | no | no | KEEP |
| `app/agents/lilith/skills.manifest.yaml` | YAML | Agent runtime, persona, skill or domain knowledge. | 5894 | 1 | yes | no | no | no | no | KEEP |
| `app/agents/lilith/skills/answer-structure/SKILL.md` | Markdown | Agent runtime, persona, skill or domain knowledge. | 2455 | 2 | yes | no | no | no | no | KEEP |
| `app/agents/lilith/skills/anti-barnum-protocol/SKILL.md` | Markdown | Agent runtime, persona, skill or domain knowledge. | 2309 | 2 | yes | no | no | no | no | KEEP |
| `app/agents/lilith/skills/boundary-design/SKILL.md` | Markdown | Agent runtime, persona, skill or domain knowledge. | 2132 | 2 | yes | no | no | no | no | KEEP |
| `app/agents/lilith/skills/career-reflection/SKILL.md` | Markdown | Agent runtime, persona, skill or domain knowledge. | 2465 | 2 | yes | no | no | no | no | KEEP |
| `app/agents/lilith/skills/chart-overview/SKILL.md` | Markdown | Agent runtime, persona, skill or domain knowledge. | 2451 | 2 | yes | no | no | no | no | KEEP |
| `app/agents/lilith/skills/cognitive-reframe/SKILL.md` | Markdown | Agent runtime, persona, skill or domain knowledge. | 2092 | 2 | yes | no | no | no | no | KEEP |
| `app/agents/lilith/skills/conversation-rehearsal/SKILL.md` | Markdown | Agent runtime, persona, skill or domain knowledge. | 2122 | 2 | yes | no | no | no | no | KEEP |
| `app/agents/lilith/skills/cross-agent-routing/SKILL.md` | Markdown | Agent runtime, persona, skill or domain knowledge. | 2461 | 2 | yes | no | no | no | no | KEEP |
| `app/agents/lilith/skills/daily-ritual/SKILL.md` | Markdown | Agent runtime, persona, skill or domain knowledge. | 2411 | 2 | yes | no | no | no | no | KEEP |
| `app/agents/lilith/skills/decision-journal/SKILL.md` | Markdown | Agent runtime, persona, skill or domain knowledge. | 2098 | 2 | yes | no | no | no | no | KEEP |
| `app/agents/lilith/skills/decision-journaling/SKILL.md` | Markdown | Agent runtime, persona, skill or domain knowledge. | 2453 | 2 | yes | no | no | no | no | KEEP |
| `app/agents/lilith/skills/diary-dynamics/SKILL.md` | Markdown | Agent runtime, persona, skill or domain knowledge. | 2413 | 2 | yes | no | no | no | no | KEEP |
| `app/agents/lilith/skills/emotion-naming/SKILL.md` | Markdown | Agent runtime, persona, skill or domain knowledge. | 3214 | 2 | yes | no | no | no | no | KEEP |
| `app/agents/lilith/skills/emotional-reflection/SKILL.md` | Markdown | Agent runtime, persona, skill or domain knowledge. | 2449 | 2 | yes | no | no | no | no | KEEP |
| `app/agents/lilith/skills/grief-reflection/SKILL.md` | Markdown | Agent runtime, persona, skill or domain knowledge. | 2106 | 2 | yes | no | no | no | no | KEEP |
| `app/agents/lilith/skills/habit-loop/SKILL.md` | Markdown | Agent runtime, persona, skill or domain knowledge. | 2057 | 2 | yes | no | no | no | no | KEEP |
| `app/agents/lilith/skills/matrix-compatibility/SKILL.md` | Markdown | Agent runtime, persona, skill or domain knowledge. | 2457 | 2 | yes | no | no | no | no | KEEP |
| `app/agents/lilith/skills/matrix-lines/SKILL.md` | Markdown | Agent runtime, persona, skill or domain knowledge. | 2477 | 2 | yes | no | no | no | no | KEEP |
| `app/agents/lilith/skills/matrix-reading/SKILL.md` | Markdown | Agent runtime, persona, skill or domain knowledge. | 3860 | 2 | yes | no | no | no | no | KEEP |
| `app/agents/lilith/skills/memory-recall/SKILL.md` | Markdown | Agent runtime, persona, skill or domain knowledge. | 2451 | 2 | yes | no | no | no | no | KEEP |
| `app/agents/lilith/skills/memory-save-decision/SKILL.md` | Markdown | Agent runtime, persona, skill or domain knowledge. | 2457 | 2 | yes | no | no | no | no | KEEP |
| `app/agents/lilith/skills/monthly-review/SKILL.md` | Markdown | Agent runtime, persona, skill or domain knowledge. | 2118 | 2 | yes | no | no | no | no | KEEP |
| `app/agents/lilith/skills/oracle-safety/SKILL.md` | Markdown | Agent runtime, persona, skill or domain knowledge. | 2453 | 2 | yes | no | no | no | no | KEEP |
| `app/agents/lilith/skills/pattern-mapping/SKILL.md` | Markdown | Agent runtime, persona, skill or domain knowledge. | 3216 | 2 | yes | no | no | no | no | KEEP |
| `app/agents/lilith/skills/placement-translation/SKILL.md` | Markdown | Agent runtime, persona, skill or domain knowledge. | 2445 | 2 | yes | no | no | no | no | KEEP |
| `app/agents/lilith/skills/practice-follow-through/SKILL.md` | Markdown | Agent runtime, persona, skill or domain knowledge. | 2455 | 2 | yes | no | no | no | no | KEEP |
| `app/agents/lilith/skills/practice-selection/SKILL.md` | Markdown | Agent runtime, persona, skill or domain knowledge. | 2451 | 2 | yes | no | no | no | no | KEEP |
| `app/agents/lilith/skills/question-framing/SKILL.md` | Markdown | Agent runtime, persona, skill or domain knowledge. | 2461 | 2 | yes | no | no | no | no | KEEP |
| `app/agents/lilith/skills/relationship-reflection/SKILL.md` | Markdown | Agent runtime, persona, skill or domain knowledge. | 2467 | 2 | yes | no | no | no | no | KEEP |
| `app/agents/lilith/skills/self-compassion/SKILL.md` | Markdown | Agent runtime, persona, skill or domain knowledge. | 2101 | 2 | yes | no | no | no | no | KEEP |
| `app/agents/lilith/skills/values-conflict/SKILL.md` | Markdown | Agent runtime, persona, skill or domain knowledge. | 2546 | 2 | yes | no | no | no | no | KEEP |
| `app/agents/mira/SYSTEM.md` | Markdown | Agent runtime, persona, skill or domain knowledge. | 5559 | 2 | yes | no | no | no | no | KEEP |
| `app/agents/mira/agent.yaml` | YAML | Agent runtime, persona, skill or domain knowledge. | 1030 | 1 | yes | no | no | no | no | KEEP |
| `app/agents/mira/evals/README.md` | Markdown | Agent runtime, persona, skill or domain knowledge. | 174 | 1 | yes | no | no | no | no | KEEP |
| `app/agents/mira/evals/cases.yaml` | YAML | Agent runtime, persona, skill or domain knowledge. | 3451 | 1 | yes | no | no | no | no | KEEP |
| `app/agents/mira/knowledge/DOMAIN.md` | Markdown | Agent runtime, persona, skill or domain knowledge. | 371 | 1 | yes | no | no | no | no | KEEP |
| `app/agents/mira/knowledge/DOMAIN_PLAYBOOK.md` | Markdown | Agent runtime, persona, skill or domain knowledge. | 5651 | 1 | yes | no | no | no | no | KEEP |
| `app/agents/mira/skills.manifest.yaml` | YAML | Agent runtime, persona, skill or domain knowledge. | 6045 | 1 | yes | no | no | no | no | KEEP |
| `app/agents/mira/skills/anti-barnum-protocol/SKILL.md` | Markdown | Agent runtime, persona, skill or domain knowledge. | 2135 | 2 | yes | no | no | no | no | KEEP |
| `app/agents/mira/skills/bracelets-and-wrist/SKILL.md` | Markdown | Agent runtime, persona, skill or domain knowledge. | 2456 | 2 | yes | no | no | no | no | KEEP |
| `app/agents/mira/skills/capture-rectification/SKILL.md` | Markdown | Agent runtime, persona, skill or domain knowledge. | 1740 | 2 | yes | no | no | no | no | KEEP |
| `app/agents/mira/skills/comparative-reading/SKILL.md` | Markdown | Agent runtime, persona, skill or domain knowledge. | 2466 | 2 | yes | no | no | no | no | KEEP |
| `app/agents/mira/skills/evidence-confidence/SKILL.md` | Markdown | Agent runtime, persona, skill or domain knowledge. | 2462 | 2 | yes | no | no | no | no | KEEP |
| `app/agents/mira/skills/fate-line-context/SKILL.md` | Markdown | Agent runtime, persona, skill or domain knowledge. | 2100 | 2 | yes | no | no | no | no | KEEP |
| `app/agents/mira/skills/fate-line/SKILL.md` | Markdown | Agent runtime, persona, skill or domain knowledge. | 2456 | 2 | yes | no | no | no | no | KEEP |
| `app/agents/mira/skills/finger-proportions/SKILL.md` | Markdown | Agent runtime, persona, skill or domain knowledge. | 2462 | 2 | yes | no | no | no | no | KEEP |
| `app/agents/mira/skills/hand-shape-elements/SKILL.md` | Markdown | Agent runtime, persona, skill or domain knowledge. | 2450 | 2 | yes | no | no | no | no | KEEP |
| `app/agents/mira/skills/hand-side-context/SKILL.md` | Markdown | Agent runtime, persona, skill or domain knowledge. | 2460 | 2 | yes | no | no | no | no | KEEP |
| `app/agents/mira/skills/head-line-depth/SKILL.md` | Markdown | Agent runtime, persona, skill or domain knowledge. | 2111 | 2 | yes | no | no | no | no | KEEP |
| `app/agents/mira/skills/head-line/SKILL.md` | Markdown | Agent runtime, persona, skill or domain knowledge. | 2452 | 2 | yes | no | no | no | no | KEEP |
| `app/agents/mira/skills/heart-line-depth/SKILL.md` | Markdown | Agent runtime, persona, skill or domain knowledge. | 2088 | 2 | yes | no | no | no | no | KEEP |
| `app/agents/mira/skills/heart-line/SKILL.md` | Markdown | Agent runtime, persona, skill or domain knowledge. | 2456 | 2 | yes | no | no | no | no | KEEP |
| `app/agents/mira/skills/image-quality-protocol/SKILL.md` | Markdown | Agent runtime, persona, skill or domain knowledge. | 2099 | 2 | yes | no | no | no | no | KEEP |
| `app/agents/mira/skills/life-line-continuity/SKILL.md` | Markdown | Agent runtime, persona, skill or domain knowledge. | 2094 | 2 | yes | no | no | no | no | KEEP |
| `app/agents/mira/skills/life-line/SKILL.md` | Markdown | Agent runtime, persona, skill or domain knowledge. | 2450 | 2 | yes | no | no | no | no | KEEP |
| `app/agents/mira/skills/markings-and-signs/SKILL.md` | Markdown | Agent runtime, persona, skill or domain knowledge. | 2444 | 2 | yes | no | no | no | no | KEEP |
| `app/agents/mira/skills/mercury-line/SKILL.md` | Markdown | Agent runtime, persona, skill or domain knowledge. | 2450 | 2 | yes | no | no | no | no | KEEP |
| `app/agents/mira/skills/mounts-topography/SKILL.md` | Markdown | Agent runtime, persona, skill or domain knowledge. | 2098 | 2 | yes | no | no | no | no | KEEP |
| `app/agents/mira/skills/mounts/SKILL.md` | Markdown | Agent runtime, persona, skill or domain knowledge. | 2466 | 2 | yes | no | no | no | no | KEEP |
| `app/agents/mira/skills/palm-angle-classification/SKILL.md` | Markdown | Agent runtime, persona, skill or domain knowledge. | 2470 | 2 | yes | no | no | no | no | KEEP |
| `app/agents/mira/skills/palm-evidence-reading/SKILL.md` | Markdown | Agent runtime, persona, skill or domain knowledge. | 3339 | 2 | yes | no | no | no | no | KEEP |
| `app/agents/mira/skills/palm-line-topology/SKILL.md` | Markdown | Agent runtime, persona, skill or domain knowledge. | 2241 | 2 | yes | no | no | no | no | KEEP |
| `app/agents/mira/skills/palm-photo-quality/SKILL.md` | Markdown | Agent runtime, persona, skill or domain knowledge. | 3600 | 2 | yes | no | no | no | no | KEEP |
| `app/agents/mira/skills/palm-safety/SKILL.md` | Markdown | Agent runtime, persona, skill or domain knowledge. | 2458 | 2 | yes | no | no | no | no | KEEP |
| `app/agents/mira/skills/palm-technique-triangulation/SKILL.md` | Markdown | Agent runtime, persona, skill or domain knowledge. | 1841 | 2 | yes | no | no | no | no | KEEP |
| `app/agents/mira/skills/photo-comparison/SKILL.md` | Markdown | Agent runtime, persona, skill or domain knowledge. | 2126 | 2 | yes | no | no | no | no | KEEP |
| `app/agents/mira/skills/relationship-lines/SKILL.md` | Markdown | Agent runtime, persona, skill or domain knowledge. | 2438 | 2 | yes | no | no | no | no | KEEP |
| `app/agents/mira/skills/sun-line/SKILL.md` | Markdown | Agent runtime, persona, skill or domain knowledge. | 2458 | 2 | yes | no | no | no | no | KEEP |
| `app/agents/mira/skills/thumb-analysis/SKILL.md` | Markdown | Agent runtime, persona, skill or domain knowledge. | 2460 | 2 | yes | no | no | no | no | KEEP |
| `app/agents/mira/skills/thumb-mechanics/SKILL.md` | Markdown | Agent runtime, persona, skill or domain knowledge. | 2077 | 2 | yes | no | no | no | no | KEEP |
| `app/agents/mira/skills/travel-lines/SKILL.md` | Markdown | Agent runtime, persona, skill or domain knowledge. | 2422 | 2 | yes | no | no | no | no | KEEP |
| `app/agents/mira/skills/visual-evidence-protocol/SKILL.md` | Markdown | Agent runtime, persona, skill or domain knowledge. | 2539 | 2 | yes | no | no | no | no | KEEP |
| `app/agents/urania/SYSTEM.md` | Markdown | Agent runtime, persona, skill or domain knowledge. | 4285 | 2 | yes | no | no | no | no | KEEP |
| `app/agents/urania/agent.yaml` | YAML | Agent runtime, persona, skill or domain knowledge. | 1190 | 1 | yes | no | no | no | no | KEEP |
| `app/agents/urania/evals/README.md` | Markdown | Agent runtime, persona, skill or domain knowledge. | 159 | 1 | yes | no | no | no | no | KEEP |
| `app/agents/urania/evals/cases.yaml` | YAML | Agent runtime, persona, skill or domain knowledge. | 4501 | 1 | yes | no | no | no | no | KEEP |
| `app/agents/urania/knowledge/DOMAIN.md` | Markdown | Agent runtime, persona, skill or domain knowledge. | 353 | 1 | yes | no | no | no | no | KEEP |
| `app/agents/urania/knowledge/DOMAIN_PLAYBOOK.md` | Markdown | Agent runtime, persona, skill or domain knowledge. | 5769 | 1 | yes | no | no | no | no | KEEP |
| `app/agents/urania/skills.manifest.yaml` | YAML | Agent runtime, persona, skill or domain knowledge. | 8340 | 1 | yes | no | no | no | no | KEEP |
| `app/agents/urania/skills/anti-barnum-protocol/SKILL.md` | Markdown | Agent runtime, persona, skill or domain knowledge. | 2226 | 2 | yes | no | no | no | no | KEEP |
| `app/agents/urania/skills/aspect-patterns/SKILL.md` | Markdown | Agent runtime, persona, skill or domain knowledge. | 2102 | 2 | yes | no | no | no | no | KEEP |
| `app/agents/urania/skills/aspects/SKILL.md` | Markdown | Agent runtime, persona, skill or domain knowledge. | 2449 | 2 | yes | no | no | no | no | KEEP |
| `app/agents/urania/skills/astro-journaling/SKILL.md` | Markdown | Agent runtime, persona, skill or domain knowledge. | 2089 | 2 | yes | no | no | no | no | KEEP |
| `app/agents/urania/skills/astrology-history/SKILL.md` | Markdown | Agent runtime, persona, skill or domain knowledge. | 2453 | 2 | yes | no | no | no | no | KEEP |
| `app/agents/urania/skills/astrology-safety/SKILL.md` | Markdown | Agent runtime, persona, skill or domain knowledge. | 2463 | 2 | yes | no | no | no | no | KEEP |
| `app/agents/urania/skills/career-symbolism/SKILL.md` | Markdown | Agent runtime, persona, skill or domain knowledge. | 2467 | 2 | yes | no | no | no | no | KEEP |
| `app/agents/urania/skills/chart-data-quality/SKILL.md` | Markdown | Agent runtime, persona, skill or domain knowledge. | 2457 | 2 | yes | no | no | no | no | KEEP |
| `app/agents/urania/skills/chart-synthesis/SKILL.md` | Markdown | Agent runtime, persona, skill or domain knowledge. | 3900 | 2 | yes | no | no | no | no | KEEP |
| `app/agents/urania/skills/compatibility-synastry/SKILL.md` | Markdown | Agent runtime, persona, skill or domain knowledge. | 2475 | 2 | yes | no | no | no | no | KEEP |
| `app/agents/urania/skills/date-only-mode/SKILL.md` | Markdown | Agent runtime, persona, skill or domain knowledge. | 3127 | 2 | yes | no | no | no | no | KEEP |
| `app/agents/urania/skills/dignities-traditions/SKILL.md` | Markdown | Agent runtime, persona, skill or domain knowledge. | 2093 | 2 | yes | no | no | no | no | KEEP |
| `app/agents/urania/skills/electional-framework/SKILL.md` | Markdown | Agent runtime, persona, skill or domain knowledge. | 2465 | 2 | yes | no | no | no | no | KEEP |
| `app/agents/urania/skills/electional-reflection/SKILL.md` | Markdown | Agent runtime, persona, skill or domain knowledge. | 2134 | 2 | yes | no | no | no | no | KEEP |
| `app/agents/urania/skills/graha-strengths/SKILL.md` | Markdown | Agent runtime, persona, skill or domain knowledge. | 1138 | 2 | yes | no | no | no | no | KEEP |
| `app/agents/urania/skills/guna-milan/SKILL.md` | Markdown | Agent runtime, persona, skill or domain knowledge. | 1373 | 2 | yes | no | no | no | no | KEEP |
| `app/agents/urania/skills/houses-and-angles/SKILL.md` | Markdown | Agent runtime, persona, skill or domain knowledge. | 2461 | 2 | yes | no | no | no | no | KEEP |
| `app/agents/urania/skills/luminaries/SKILL.md` | Markdown | Agent runtime, persona, skill or domain knowledge. | 2457 | 2 | yes | no | no | no | no | KEEP |
| `app/agents/urania/skills/lunar-nodes/SKILL.md` | Markdown | Agent runtime, persona, skill or domain knowledge. | 3727 | 2 | yes | no | no | no | no | KEEP |
| `app/agents/urania/skills/lunar-phases/SKILL.md` | Markdown | Agent runtime, persona, skill or domain knowledge. | 2822 | 2 | yes | no | no | no | no | KEEP |
| `app/agents/urania/skills/mercury-and-mars/SKILL.md` | Markdown | Agent runtime, persona, skill or domain knowledge. | 2463 | 2 | yes | no | no | no | no | KEEP |
| `app/agents/urania/skills/moon-cycles/SKILL.md` | Markdown | Agent runtime, persona, skill or domain knowledge. | 2453 | 2 | yes | no | no | no | no | KEEP |
| `app/agents/urania/skills/nakshatra-pada/SKILL.md` | Markdown | Agent runtime, persona, skill or domain knowledge. | 1440 | 2 | yes | no | no | no | no | KEEP |
| `app/agents/urania/skills/natal-chart-foundations/SKILL.md` | Markdown | Agent runtime, persona, skill or domain knowledge. | 2489 | 2 | yes | no | no | no | no | KEEP |
| `app/agents/urania/skills/outer-planets/SKILL.md` | Markdown | Agent runtime, persona, skill or domain knowledge. | 2471 | 2 | yes | no | no | no | no | KEEP |
| `app/agents/urania/skills/panchang-muhurta/SKILL.md` | Markdown | Agent runtime, persona, skill or domain knowledge. | 1370 | 2 | yes | no | no | no | no | KEEP |
| `app/agents/urania/skills/planets-in-signs/SKILL.md` | Markdown | Agent runtime, persona, skill or domain knowledge. | 2461 | 2 | yes | no | no | no | no | KEEP |
| `app/agents/urania/skills/retrogrades/SKILL.md` | Markdown | Agent runtime, persona, skill or domain knowledge. | 2109 | 2 | yes | no | no | no | no | KEEP |
| `app/agents/urania/skills/saturn-and-boundaries/SKILL.md` | Markdown | Agent runtime, persona, skill or domain knowledge. | 2447 | 2 | yes | no | no | no | no | KEEP |
| `app/agents/urania/skills/solar-return/SKILL.md` | Markdown | Agent runtime, persona, skill or domain knowledge. | 2117 | 2 | yes | no | no | no | no | KEEP |
| `app/agents/urania/skills/synastry-boundaries/SKILL.md` | Markdown | Agent runtime, persona, skill or domain knowledge. | 2120 | 2 | yes | no | no | no | no | KEEP |
| `app/agents/urania/skills/traditional-modern-bridge/SKILL.md` | Markdown | Agent runtime, persona, skill or domain knowledge. | 2143 | 2 | yes | no | no | no | no | KEEP |
| `app/agents/urania/skills/transits/SKILL.md` | Markdown | Agent runtime, persona, skill or domain knowledge. | 2443 | 2 | yes | no | no | no | no | KEEP |
| `app/agents/urania/skills/varga-charts/SKILL.md` | Markdown | Agent runtime, persona, skill or domain knowledge. | 1171 | 2 | yes | no | no | no | no | KEEP |
| `app/agents/urania/skills/vedic-evidence-safety/SKILL.md` | Markdown | Agent runtime, persona, skill or domain knowledge. | 1435 | 2 | yes | no | no | no | no | KEEP |
| `app/agents/urania/skills/vedic-foundations/SKILL.md` | Markdown | Agent runtime, persona, skill or domain knowledge. | 1560 | 2 | yes | no | no | no | no | KEEP |
| `app/agents/urania/skills/vedic-transits/SKILL.md` | Markdown | Agent runtime, persona, skill or domain knowledge. | 1077 | 2 | yes | no | no | no | no | KEEP |
| `app/agents/urania/skills/venus-and-relationships/SKILL.md` | Markdown | Agent runtime, persona, skill or domain knowledge. | 2471 | 2 | yes | no | no | no | no | KEEP |
| `app/agents/urania/skills/vimshottari-dasha/SKILL.md` | Markdown | Agent runtime, persona, skill or domain knowledge. | 1320 | 2 | yes | no | no | no | no | KEEP |
| `app/api/__init__.py` | Python | FastAPI application, dependencies or security. | 0 | 2 | yes | no | no | no | no | KEEP |
| `app/api/__pycache__/__init__.cpython-312.pyc` | Other | FastAPI application, dependencies or security. | 138 | 1 | yes | no | no | no | no | KEEP |
| `app/api/__pycache__/auth.cpython-312.pyc` | Other | FastAPI application, dependencies or security. | 378 | 1 | yes | no | no | no | no | KEEP |
| `app/api/__pycache__/deps.cpython-312.pyc` | Other | FastAPI application, dependencies or security. | 8963 | 1 | yes | no | no | no | no | KEEP |
| `app/api/__pycache__/main.cpython-312.pyc` | Other | FastAPI application, dependencies or security. | 15768 | 1 | yes | no | no | no | no | KEEP |
| `app/api/__pycache__/security.cpython-312.pyc` | Other | FastAPI application, dependencies or security. | 4944 | 1 | yes | no | no | no | no | KEEP |
| `app/api/auth.py` | Python | FastAPI application, dependencies or security. | 256 | 2 | yes | no | no | no | no | KEEP |
| `app/api/common/__init__.py` | Python | FastAPI application, dependencies or security. | 58 | 2 | yes | no | no | no | no | KEEP |
| `app/api/common/__pycache__/__init__.cpython-312.pyc` | Other | FastAPI application, dependencies or security. | 214 | 1 | yes | no | no | no | no | KEEP |
| `app/api/common/__pycache__/errors.cpython-312.pyc` | Other | FastAPI application, dependencies or security. | 1552 | 1 | yes | no | no | no | no | KEEP |
| `app/api/common/__pycache__/validation.cpython-312.pyc` | Other | FastAPI application, dependencies or security. | 1464 | 1 | yes | no | no | no | no | KEEP |
| `app/api/common/errors.py` | Python | FastAPI application, dependencies or security. | 1246 | 2 | yes | no | no | no | no | KEEP |
| `app/api/common/validation.py` | Python | FastAPI application, dependencies or security. | 997 | 2 | yes | no | no | no | no | KEEP |
| `app/api/contracts/__init__.py` | Python | Pydantic/API contract. | 79 | 2 | yes | no | no | no | no | KEEP |
| `app/api/contracts/__pycache__/__init__.cpython-312.pyc` | Other | Pydantic/API contract. | 238 | 1 | yes | no | no | no | no | KEEP |
| `app/api/contracts/__pycache__/chart_products.cpython-312.pyc` | Other | Pydantic/API contract. | 1944 | 1 | yes | no | no | no | no | KEEP |
| `app/api/contracts/__pycache__/chat.cpython-312.pyc` | Other | Pydantic/API contract. | 691 | 1 | yes | no | no | no | no | KEEP |
| `app/api/contracts/__pycache__/compatibility.cpython-312.pyc` | Other | Pydantic/API contract. | 876 | 1 | yes | no | no | no | no | KEEP |
| `app/api/contracts/chart_products.py` | Python | Pydantic/API contract. | 813 | 4 | yes | no | no | no | no | KEEP |
| `app/api/contracts/chat.py` | Python | Pydantic/API contract. | 264 | 2 | yes | no | no | no | no | KEEP |
| `app/api/contracts/compatibility.py` | Python | Pydantic/API contract. | 398 | 2 | yes | no | no | no | no | KEEP |
| `app/api/deps.py` | Python | FastAPI application, dependencies or security. | 7508 | 11 | yes | no | no | no | no | KEEP |
| `app/api/main.py` | Python | FastAPI application, dependencies or security. | 13888 | 12 | yes | no | no | no | no | KEEP |
| `app/api/routers/__init__.py` | Python | HTTP API router. | 592 | 3 | yes | no | no | no | no | KEEP |
| `app/api/routers/__pycache__/__init__.cpython-312.pyc` | Other | HTTP API router. | 1076 | 1 | yes | no | no | no | no | KEEP |
| `app/api/routers/__pycache__/admin.cpython-312.pyc` | Other | HTTP API router. | 49861 | 1 | yes | no | no | no | no | KEEP |
| `app/api/routers/__pycache__/chart.cpython-312.pyc` | Other | HTTP API router. | 31018 | 1 | yes | no | no | no | no | KEEP |
| `app/api/routers/__pycache__/chart_products.cpython-312.pyc` | Other | HTTP API router. | 7652 | 1 | yes | no | no | no | no | KEEP |
| `app/api/routers/__pycache__/chat.cpython-312.pyc` | Other | HTTP API router. | 10676 | 1 | yes | no | no | no | no | KEEP |
| `app/api/routers/__pycache__/diary.cpython-312.pyc` | Other | HTTP API router. | 20104 | 1 | yes | no | no | no | no | KEEP |
| `app/api/routers/__pycache__/history.cpython-312.pyc` | Other | HTTP API router. | 5475 | 1 | yes | no | no | no | no | KEEP |
| `app/api/routers/__pycache__/jobs.cpython-312.pyc` | Other | HTTP API router. | 3376 | 1 | yes | no | no | no | no | KEEP |
| `app/api/routers/__pycache__/placements.cpython-312.pyc` | Other | HTTP API router. | 8154 | 1 | yes | no | no | no | no | KEEP |
| `app/api/routers/__pycache__/practices.cpython-312.pyc` | Other | HTTP API router. | 4875 | 1 | yes | no | no | no | no | KEEP |
| `app/api/routers/__pycache__/profile.cpython-312.pyc` | Other | HTTP API router. | 20932 | 1 | yes | no | no | no | no | KEEP |
| `app/api/routers/__pycache__/share.cpython-312.pyc` | Other | HTTP API router. | 8719 | 1 | yes | no | no | no | no | KEEP |
| `app/api/routers/__pycache__/shop.cpython-312.pyc` | Other | HTTP API router. | 11151 | 1 | yes | no | no | no | no | KEEP |
| `app/api/routers/__pycache__/tarot.cpython-312.pyc` | Other | HTTP API router. | 7772 | 1 | yes | no | no | no | no | KEEP |
| `app/api/routers/__pycache__/today.cpython-312.pyc` | Other | HTTP API router. | 8989 | 1 | yes | no | no | no | no | KEEP |
| `app/api/routers/__pycache__/webhooks.cpython-312.pyc` | Other | HTTP API router. | 19817 | 1 | yes | no | no | no | no | KEEP |
| `app/api/routers/admin.py` | Python | HTTP API router. | 31097 | 7 | yes | no | no | no | no | KEEP |
| `app/api/routers/chart.py` | Python | HTTP API router. | 24995 | 3 | yes | no | no | no | no | KEEP |
| `app/api/routers/chart_products.py` | Python | HTTP API router. | 5792 | 4 | yes | no | no | no | no | KEEP |
| `app/api/routers/chat.py` | Python | HTTP API router. | 7285 | 4 | yes | no | no | no | no | KEEP |
| `app/api/routers/diary.py` | Python | HTTP API router. | 14410 | 6 | yes | no | no | no | no | KEEP |
| `app/api/routers/history.py` | Python | HTTP API router. | 3964 | 7 | yes | no | no | no | no | KEEP |
| `app/api/routers/jobs.py` | Python | HTTP API router. | 1981 | 4 | yes | no | no | no | no | KEEP |
| `app/api/routers/placements.py` | Python | HTTP API router. | 5714 | 7 | yes | no | no | no | no | KEEP |
| `app/api/routers/practices.py` | Python | HTTP API router. | 2923 | 2 | yes | no | no | no | no | KEEP |
| `app/api/routers/profile.py` | Python | HTTP API router. | 14471 | 11 | yes | no | no | no | no | KEEP |
| `app/api/routers/share.py` | Python | HTTP API router. | 6122 | 2 | yes | no | no | no | no | KEEP |
| `app/api/routers/shop.py` | Python | HTTP API router. | 7070 | 5 | yes | no | no | no | no | KEEP |
| `app/api/routers/tarot.py` | Python | HTTP API router. | 4948 | 6 | yes | no | no | no | no | KEEP |
| `app/api/routers/today.py` | Python | HTTP API router. | 6572 | 2 | yes | no | no | no | no | KEEP |
| `app/api/routers/webhooks.py` | Python | HTTP API router. | 15097 | 9 | yes | no | no | no | no | KEEP |
| `app/api/security.py` | Python | FastAPI application, dependencies or security. | 4017 | 9 | yes | no | no | no | no | KEEP |
| `app/bot/__init__.py` | Python | Telegram bot handler and UX. | 0 | 2 | yes | no | no | no | no | KEEP |
| `app/bot/__pycache__/__init__.cpython-312.pyc` | Other | Telegram bot handler and UX. | 138 | 1 | yes | no | no | no | no | KEEP |
| `app/bot/__pycache__/chat.cpython-312.pyc` | Other | Telegram bot handler and UX. | 20270 | 1 | yes | no | no | no | no | KEEP |
| `app/bot/__pycache__/features.cpython-312.pyc` | Other | Telegram bot handler and UX. | 47168 | 1 | yes | no | no | no | no | KEEP |
| `app/bot/__pycache__/formatting.cpython-312.pyc` | Other | Telegram bot handler and UX. | 1760 | 1 | yes | no | no | no | no | KEEP |
| `app/bot/__pycache__/growth.cpython-312.pyc` | Other | Telegram bot handler and UX. | 19259 | 1 | yes | no | no | no | no | KEEP |
| `app/bot/__pycache__/keyboards.cpython-312.pyc` | Other | Telegram bot handler and UX. | 18317 | 1 | yes | no | no | no | no | KEEP |
| `app/bot/__pycache__/main.cpython-312.pyc` | Other | Telegram bot handler and UX. | 13448 | 1 | yes | no | no | no | no | KEEP |
| `app/bot/__pycache__/onboarding.cpython-312.pyc` | Other | Telegram bot handler and UX. | 38832 | 1 | yes | no | no | no | no | KEEP |
| `app/bot/__pycache__/profile.cpython-312.pyc` | Other | Telegram bot handler and UX. | 15303 | 1 | yes | no | no | no | no | KEEP |
| `app/bot/__pycache__/shop.cpython-312.pyc` | Other | Telegram bot handler and UX. | 22261 | 1 | yes | no | no | no | no | KEEP |
| `app/bot/chat.py` | Python | Telegram bot handler and UX. | 12410 | 3 | yes | no | no | no | no | KEEP |
| `app/bot/features.py` | Python | Telegram bot handler and UX. | 28659 | 2 | yes | no | no | no | no | KEEP |
| `app/bot/formatting.py` | Python | Telegram bot handler and UX. | 822 | 2 | yes | no | no | no | no | KEEP |
| `app/bot/growth.py` | Python | Telegram bot handler and UX. | 11810 | 2 | yes | no | no | no | no | KEEP |
| `app/bot/keyboards.py` | Python | Telegram bot handler and UX. | 17077 | 2 | yes | no | no | no | no | KEEP |
| `app/bot/main.py` | Python | Telegram bot handler and UX. | 8333 | 3 | yes | no | no | no | no | KEEP |
| `app/bot/onboarding.py` | Python | Telegram bot handler and UX. | 23586 | 3 | yes | no | no | no | no | KEEP |
| `app/bot/profile.py` | Python | Telegram bot handler and UX. | 8455 | 3 | yes | no | no | no | no | KEEP |
| `app/bot/shop.py` | Python | Telegram bot handler and UX. | 13896 | 2 | yes | no | no | no | no | KEEP |
| `app/config.py` | Python | Python repository file. | 9787 | 8 | yes | no | no | no | no | KEEP |
| `app/core/__init__.py` | Python | Domain, AI, safety, rendering or shared core service. | 0 | 2 | yes | no | no | no | no | KEEP |
| `app/core/__pycache__/__init__.cpython-312.pyc` | Other | Domain, AI, safety, rendering or shared core service. | 139 | 1 | yes | no | no | no | no | KEEP |
| `app/core/__pycache__/agent.cpython-312.pyc` | Other | Domain, AI, safety, rendering or shared core service. | 71016 | 1 | yes | no | no | no | no | KEEP |
| `app/core/__pycache__/astro.cpython-312.pyc` | Other | Domain, AI, safety, rendering or shared core service. | 52879 | 1 | yes | no | no | no | no | KEEP |
| `app/core/__pycache__/cards.cpython-312.pyc` | Other | Domain, AI, safety, rendering or shared core service. | 22707 | 1 | yes | no | no | no | no | KEEP |
| `app/core/__pycache__/chart_contract.cpython-312.pyc` | Other | Domain, AI, safety, rendering or shared core service. | 4737 | 1 | yes | no | no | no | no | KEEP |
| `app/core/__pycache__/chart_interpretation.cpython-312.pyc` | Other | Domain, AI, safety, rendering or shared core service. | 12710 | 1 | yes | no | no | no | no | KEEP |
| `app/core/__pycache__/chart_products.cpython-312.pyc` | Other | Domain, AI, safety, rendering or shared core service. | 21565 | 1 | yes | no | no | no | no | KEEP |
| `app/core/__pycache__/chart_rendering.cpython-312.pyc` | Other | Domain, AI, safety, rendering or shared core service. | 14267 | 1 | yes | no | no | no | no | KEEP |
| `app/core/__pycache__/flood.cpython-312.pyc` | Other | Domain, AI, safety, rendering or shared core service. | 2930 | 1 | yes | no | no | no | no | KEEP |
| `app/core/__pycache__/geo.cpython-312.pyc` | Other | Domain, AI, safety, rendering or shared core service. | 12093 | 1 | yes | no | no | no | no | KEEP |
| `app/core/__pycache__/interpretation.cpython-312.pyc` | Other | Domain, AI, safety, rendering or shared core service. | 24700 | 1 | yes | no | no | no | no | KEEP |
| `app/core/__pycache__/llm.cpython-312.pyc` | Other | Domain, AI, safety, rendering or shared core service. | 60313 | 1 | yes | no | no | no | no | KEEP |
| `app/core/__pycache__/matrix.cpython-312.pyc` | Other | Domain, AI, safety, rendering or shared core service. | 15539 | 1 | yes | no | no | no | no | KEEP |
| `app/core/__pycache__/memory.cpython-312.pyc` | Other | Domain, AI, safety, rendering or shared core service. | 27083 | 1 | yes | no | no | no | no | KEEP |
| `app/core/__pycache__/observability.cpython-312.pyc` | Other | Domain, AI, safety, rendering or shared core service. | 8125 | 1 | yes | no | no | no | no | KEEP |
| `app/core/__pycache__/palm.cpython-312.pyc` | Other | Domain, AI, safety, rendering or shared core service. | 40844 | 1 | yes | no | no | no | no | KEEP |
| `app/core/__pycache__/palm_full_scope.cpython-312.pyc` | Other | Domain, AI, safety, rendering or shared core service. | 12571 | 1 | yes | no | no | no | no | KEEP |
| `app/core/__pycache__/palm_landmarks.cpython-312.pyc` | Other | Domain, AI, safety, rendering or shared core service. | 8461 | 1 | yes | no | no | no | no | KEEP |
| `app/core/__pycache__/palm_lines.cpython-312.pyc` | Other | Domain, AI, safety, rendering or shared core service. | 9885 | 1 | yes | no | no | no | no | KEEP |
| `app/core/__pycache__/palm_vision.cpython-312.pyc` | Other | Domain, AI, safety, rendering or shared core service. | 4563 | 1 | yes | no | no | no | no | KEEP |
| `app/core/__pycache__/personas.cpython-312.pyc` | Other | Domain, AI, safety, rendering or shared core service. | 4390 | 1 | yes | no | no | no | no | KEEP |
| `app/core/__pycache__/placements.cpython-312.pyc` | Other | Domain, AI, safety, rendering or shared core service. | 15169 | 1 | yes | no | no | no | no | KEEP |
| `app/core/__pycache__/practices.cpython-312.pyc` | Other | Domain, AI, safety, rendering or shared core service. | 33939 | 1 | yes | no | no | no | no | KEEP |
| `app/core/__pycache__/product_cost.cpython-312.pyc` | Other | Domain, AI, safety, rendering or shared core service. | 6339 | 1 | yes | no | no | no | no | KEEP |
| `app/core/__pycache__/safety.cpython-312.pyc` | Other | Domain, AI, safety, rendering or shared core service. | 14714 | 1 | yes | no | no | no | no | KEEP |
| `app/core/__pycache__/sentry.cpython-312.pyc` | Other | Domain, AI, safety, rendering or shared core service. | 3209 | 1 | yes | no | no | no | no | KEEP |
| `app/core/__pycache__/shared_context.cpython-312.pyc` | Other | Domain, AI, safety, rendering or shared core service. | 13344 | 1 | yes | no | no | no | no | KEEP |
| `app/core/__pycache__/skills.cpython-312.pyc` | Other | Domain, AI, safety, rendering or shared core service. | 96497 | 1 | yes | no | no | no | no | KEEP |
| `app/core/__pycache__/stable.cpython-312.pyc` | Other | Domain, AI, safety, rendering or shared core service. | 1368 | 1 | yes | no | no | no | no | KEEP |
| `app/core/__pycache__/tarot.cpython-312.pyc` | Other | Domain, AI, safety, rendering or shared core service. | 29704 | 1 | yes | no | no | no | no | KEEP |
| `app/core/__pycache__/vedic.cpython-312.pyc` | Other | Domain, AI, safety, rendering or shared core service. | 32757 | 1 | yes | no | no | no | no | KEEP |
| `app/core/agent.py` | Python | Domain, AI, safety, rendering or shared core service. | 59593 | 7 | yes | no | no | no | no | KEEP |
| `app/core/agents/__init__.py` | Python | Agent runtime, persona, skill or domain knowledge. | 1154 | 2 | yes | no | no | no | no | KEEP |
| `app/core/agents/__pycache__/__init__.cpython-312.pyc` | Other | Agent runtime, persona, skill or domain knowledge. | 1275 | 1 | yes | no | no | no | no | KEEP |
| `app/core/agents/__pycache__/base.cpython-312.pyc` | Other | Agent runtime, persona, skill or domain knowledge. | 20305 | 1 | yes | no | no | no | no | KEEP |
| `app/core/agents/__pycache__/context.cpython-312.pyc` | Other | Agent runtime, persona, skill or domain knowledge. | 4960 | 1 | yes | no | no | no | no | KEEP |
| `app/core/agents/__pycache__/file_loader.cpython-312.pyc` | Other | Agent runtime, persona, skill or domain knowledge. | 30292 | 1 | yes | no | no | no | no | KEEP |
| `app/core/agents/__pycache__/routing.cpython-312.pyc` | Other | Agent runtime, persona, skill or domain knowledge. | 6891 | 1 | yes | no | no | no | no | KEEP |
| `app/core/agents/__pycache__/runtime.cpython-312.pyc` | Other | Agent runtime, persona, skill or domain knowledge. | 25735 | 1 | yes | no | no | no | no | KEEP |
| `app/core/agents/__pycache__/specs.cpython-312.pyc` | Other | Agent runtime, persona, skill or domain knowledge. | 21548 | 1 | yes | no | no | no | no | KEEP |
| `app/core/agents/base.py` | Python | Agent runtime, persona, skill or domain knowledge. | 19982 | 7 | yes | no | no | no | no | KEEP |
| `app/core/agents/context.py` | Python | Agent runtime, persona, skill or domain knowledge. | 3907 | 6 | yes | no | no | no | no | KEEP |
| `app/core/agents/file_loader.py` | Python | Agent runtime, persona, skill or domain knowledge. | 20430 | 2 | yes | no | no | no | no | KEEP |
| `app/core/agents/routing.py` | Python | Agent runtime, persona, skill or domain knowledge. | 4332 | 3 | yes | no | no | no | no | KEEP |
| `app/core/agents/runtime.py` | Python | Agent runtime, persona, skill or domain knowledge. | 20909 | 11 | yes | no | no | no | no | KEEP |
| `app/core/agents/specs.py` | Python | Agent runtime, persona, skill or domain knowledge. | 21171 | 3 | yes | no | no | no | no | KEEP |
| `app/core/astro.py` | Python | Domain, AI, safety, rendering or shared core service. | 45802 | 16 | yes | no | no | no | no | KEEP |
| `app/core/cards.py` | Python | Domain, AI, safety, rendering or shared core service. | 17117 | 2 | yes | no | no | no | no | KEEP |
| `app/core/chart_contract.py` | Python | Domain, AI, safety, rendering or shared core service. | 3851 | 9 | yes | no | no | no | no | KEEP |
| `app/core/chart_interpretation.py` | Python | Domain, AI, safety, rendering or shared core service. | 10550 | 2 | yes | no | no | no | no | KEEP |
| `app/core/chart_products.py` | Python | Domain, AI, safety, rendering or shared core service. | 17918 | 10 | yes | no | no | no | no | KEEP |
| `app/core/chart_rendering.py` | Python | Domain, AI, safety, rendering or shared core service. | 10222 | 4 | yes | no | no | no | no | KEEP |
| `app/core/flood.py` | Python | Domain, AI, safety, rendering or shared core service. | 3042 | 2 | yes | no | no | no | no | KEEP |
| `app/core/geo.py` | Python | Domain, AI, safety, rendering or shared core service. | 9344 | 3 | yes | no | no | no | no | KEEP |
| `app/core/interpretation.py` | Python | Domain, AI, safety, rendering or shared core service. | 19439 | 5 | yes | no | no | no | no | KEEP |
| `app/core/llm.py` | Python | Domain, AI, safety, rendering or shared core service. | 46734 | 8 | yes | no | no | no | no | KEEP |
| `app/core/matrix.py` | Python | Domain, AI, safety, rendering or shared core service. | 17212 | 2 | yes | no | no | no | no | KEEP |
| `app/core/memory.py` | Python | Domain, AI, safety, rendering or shared core service. | 19976 | 10 | yes | no | no | no | no | KEEP |
| `app/core/observability.py` | Python | Domain, AI, safety, rendering or shared core service. | 4883 | 3 | yes | no | no | no | no | KEEP |
| `app/core/palm.py` | Python | Domain, AI, safety, rendering or shared core service. | 40895 | 11 | yes | no | no | no | no | KEEP |
| `app/core/palm_full_scope.py` | Python | Domain, AI, safety, rendering or shared core service. | 9391 | 3 | yes | no | no | no | no | KEEP |
| `app/core/palm_landmarks.py` | Python | Domain, AI, safety, rendering or shared core service. | 7326 | 3 | yes | no | no | no | no | KEEP |
| `app/core/palm_lines.py` | Python | Domain, AI, safety, rendering or shared core service. | 6835 | 5 | yes | no | no | no | no | KEEP |
| `app/core/palm_vision.py` | Python | Domain, AI, safety, rendering or shared core service. | 3313 | 4 | yes | no | no | no | no | KEEP |
| `app/core/personas.py` | Python | Domain, AI, safety, rendering or shared core service. | 3499 | 2 | yes | no | no | no | no | KEEP |
| `app/core/placements.py` | Python | Domain, AI, safety, rendering or shared core service. | 13295 | 2 | yes | no | no | no | no | KEEP |
| `app/core/practices.py` | Python | Domain, AI, safety, rendering or shared core service. | 38800 | 2 | yes | no | no | no | no | KEEP |
| `app/core/product_cost.py` | Python | Domain, AI, safety, rendering or shared core service. | 5418 | 4 | yes | no | no | no | no | KEEP |
| `app/core/safety.py` | Python | Domain, AI, safety, rendering or shared core service. | 13740 | 8 | yes | no | no | no | no | KEEP |
| `app/core/sentry.py` | Python | Domain, AI, safety, rendering or shared core service. | 2598 | 2 | yes | no | no | no | no | KEEP |
| `app/core/shared_context.py` | Python | Domain, AI, safety, rendering or shared core service. | 9580 | 5 | yes | no | no | no | no | KEEP |
| `app/core/skills.py` | Python | Domain, AI, safety, rendering or shared core service. | 88863 | 10 | yes | no | no | no | no | KEEP |
| `app/core/stable.py` | Python | Domain, AI, safety, rendering or shared core service. | 804 | 2 | yes | no | no | no | no | KEEP |
| `app/core/tarot.py` | Python | Domain, AI, safety, rendering or shared core service. | 30883 | 10 | yes | no | no | no | no | KEEP |
| `app/core/vedic.py` | Python | Domain, AI, safety, rendering or shared core service. | 24515 | 4 | yes | no | no | no | no | KEEP |
| `app/data/__init__.py` | Python | Persistence, schema or database migration. | 688 | 2 | yes | no | no | no | no | KEEP |
| `app/data/__pycache__/__init__.cpython-312.pyc` | Other | Persistence, schema or database migration. | 839 | 1 | yes | no | no | no | no | KEEP |
| `app/data/__pycache__/migrations.cpython-312.pyc` | Other | Persistence, schema or database migration. | 25420 | 1 | yes | no | no | no | no | KEEP |
| `app/data/__pycache__/pg_schema.cpython-312.pyc` | Other | Persistence, schema or database migration. | 1364 | 1 | yes | no | no | no | no | KEEP |
| `app/data/__pycache__/postgres.cpython-312.pyc` | Other | Persistence, schema or database migration. | 15382 | 1 | yes | no | no | no | no | KEEP |
| `app/data/__pycache__/schema.cpython-312.pyc` | Other | Persistence, schema or database migration. | 25808 | 1 | yes | no | no | no | no | KEEP |
| `app/data/__pycache__/seed.cpython-312.pyc` | Other | Persistence, schema or database migration. | 22256 | 1 | yes | no | no | no | no | KEEP |
| `app/data/__pycache__/session.cpython-312.pyc` | Other | Persistence, schema or database migration. | 10064 | 1 | yes | no | no | no | no | KEEP |
| `app/data/migrations.py` | Python | Persistence, schema or database migration. | 20828 | 7 | yes | no | no | no | no | KEEP |
| `app/data/pg_schema.py` | Python | Persistence, schema or database migration. | 1030 | 2 | yes | no | no | no | no | KEEP |
| `app/data/postgres.py` | Python | Persistence, schema or database migration. | 8708 | 3 | yes | no | no | no | no | KEEP |
| `app/data/schema.py` | Python | Persistence, schema or database migration. | 27494 | 12 | yes | no | no | no | no | KEEP |
| `app/data/seed.py` | Python | Persistence, schema or database migration. | 21265 | 5 | yes | no | no | no | no | KEEP |
| `app/data/session.py` | Python | Persistence, schema or database migration. | 7308 | 5 | yes | no | no | no | no | KEEP |
| `app/db.py` | Python | Python repository file. | 4705 | 2 | yes | no | no | no | no | KEEP |
| `app/pdfgen/__init__.py` | Python | PDF report generation. | 1431 | 2 | yes | no | no | no | no | KEEP |
| `app/pdfgen/__pycache__/__init__.cpython-312.pyc` | Other | PDF report generation. | 1573 | 1 | yes | no | no | no | no | KEEP |
| `app/pdfgen/__pycache__/builder.cpython-312.pyc` | Other | PDF report generation. | 90454 | 1 | yes | no | no | no | no | KEEP |
| `app/pdfgen/__pycache__/layout.cpython-312.pyc` | Other | PDF report generation. | 22272 | 1 | yes | no | no | no | no | KEEP |
| `app/pdfgen/__pycache__/render.cpython-312.pyc` | Other | PDF report generation. | 3530 | 1 | yes | no | no | no | no | KEEP |
| `app/pdfgen/builder.py` | Python | PDF report generation. | 62576 | 4 | yes | no | no | no | no | KEEP |
| `app/pdfgen/layout.py` | Python | PDF report generation. | 19144 | 3 | yes | no | no | no | no | KEEP |
| `app/pdfgen/render.py` | Python | PDF report generation. | 2667 | 3 | yes | no | no | no | no | KEEP |
| `app/repo/__init__.py` | Python | Repository/data-access layer. | 1517 | 2 | yes | no | no | no | no | KEEP |
| `app/repo/__pycache__/__init__.cpython-312.pyc` | Other | Repository/data-access layer. | 1699 | 1 | yes | no | no | no | no | KEEP |
| `app/repo/__pycache__/admin.cpython-312.pyc` | Other | Repository/data-access layer. | 8216 | 1 | yes | no | no | no | no | KEEP |
| `app/repo/__pycache__/analytics.cpython-312.pyc` | Other | Repository/data-access layer. | 41967 | 1 | yes | no | no | no | no | KEEP |
| `app/repo/__pycache__/billing.cpython-312.pyc` | Other | Repository/data-access layer. | 32388 | 1 | yes | no | no | no | no | KEEP |
| `app/repo/__pycache__/comms.cpython-312.pyc` | Other | Repository/data-access layer. | 15221 | 1 | yes | no | no | no | no | KEEP |
| `app/repo/__pycache__/content.cpython-312.pyc` | Other | Repository/data-access layer. | 15756 | 1 | yes | no | no | no | no | KEEP |
| `app/repo/__pycache__/crm.cpython-312.pyc` | Other | Repository/data-access layer. | 7880 | 1 | yes | no | no | no | no | KEEP |
| `app/repo/__pycache__/dialog.cpython-312.pyc` | Other | Repository/data-access layer. | 27162 | 1 | yes | no | no | no | no | KEEP |
| `app/repo/__pycache__/growth.cpython-312.pyc` | Other | Repository/data-access layer. | 12905 | 1 | yes | no | no | no | no | KEEP |
| `app/repo/__pycache__/jobs.cpython-312.pyc` | Other | Repository/data-access layer. | 7735 | 1 | yes | no | no | no | no | KEEP |
| `app/repo/__pycache__/palm.cpython-312.pyc` | Other | Repository/data-access layer. | 4568 | 1 | yes | no | no | no | no | KEEP |
| `app/repo/__pycache__/readings.cpython-312.pyc` | Other | Repository/data-access layer. | 24503 | 1 | yes | no | no | no | no | KEEP |
| `app/repo/__pycache__/users.cpython-312.pyc` | Other | Repository/data-access layer. | 20999 | 1 | yes | no | no | no | no | KEEP |
| `app/repo/admin.py` | Python | Repository/data-access layer. | 5531 | 3 | yes | no | no | no | no | KEEP |
| `app/repo/analytics.py` | Python | Repository/data-access layer. | 30785 | 8 | yes | no | no | no | no | KEEP |
| `app/repo/billing.py` | Python | Repository/data-access layer. | 21498 | 3 | yes | no | no | no | no | KEEP |
| `app/repo/comms.py` | Python | Repository/data-access layer. | 9695 | 2 | yes | no | no | no | no | KEEP |
| `app/repo/content.py` | Python | Repository/data-access layer. | 12572 | 4 | yes | no | no | no | no | KEEP |
| `app/repo/crm.py` | Python | Repository/data-access layer. | 4166 | 3 | yes | no | no | no | no | KEEP |
| `app/repo/dialog.py` | Python | Repository/data-access layer. | 17866 | 5 | yes | no | no | no | no | KEEP |
| `app/repo/growth.py` | Python | Repository/data-access layer. | 8383 | 2 | yes | no | no | no | no | KEEP |
| `app/repo/jobs.py` | Python | Repository/data-access layer. | 4330 | 2 | yes | no | no | no | no | KEEP |
| `app/repo/palm.py` | Python | Repository/data-access layer. | 2582 | 7 | yes | no | no | no | no | KEEP |
| `app/repo/readings.py` | Python | Repository/data-access layer. | 15953 | 8 | yes | no | no | no | no | KEEP |
| `app/repo/users.py` | Python | Repository/data-access layer. | 15138 | 4 | yes | no | no | no | no | KEEP |
| `app/services/__init__.py` | Python | Application service or asynchronous task. | 1922 | 2 | yes | no | no | no | no | KEEP |
| `app/services/__pycache__/__init__.cpython-312.pyc` | Other | Application service or asynchronous task. | 2102 | 1 | yes | no | no | no | no | KEEP |
| `app/services/__pycache__/analytics.cpython-312.pyc` | Other | Application service or asynchronous task. | 15135 | 1 | yes | no | no | no | no | KEEP |
| `app/services/__pycache__/billing.cpython-312.pyc` | Other | Application service or asynchronous task. | 27333 | 1 | yes | no | no | no | no | KEEP |
| `app/services/__pycache__/broadcast.cpython-312.pyc` | Other | Application service or asynchronous task. | 8514 | 1 | yes | no | no | no | no | KEEP |
| `app/services/__pycache__/catalog.cpython-312.pyc` | Other | Application service or asynchronous task. | 5903 | 1 | yes | no | no | no | no | KEEP |
| `app/services/__pycache__/chat.cpython-312.pyc` | Other | Application service or asynchronous task. | 27099 | 1 | yes | no | no | no | no | KEEP |
| `app/services/__pycache__/compatibility.cpython-312.pyc` | Other | Application service or asynchronous task. | 5233 | 1 | yes | no | no | no | no | KEEP |
| `app/services/__pycache__/cryptobot.cpython-312.pyc` | Other | Application service or asynchronous task. | 7583 | 1 | yes | no | no | no | no | KEEP |
| `app/services/__pycache__/eligibility.cpython-312.pyc` | Other | Application service or asynchronous task. | 2911 | 1 | yes | no | no | no | no | KEEP |
| `app/services/__pycache__/horoscopes.cpython-312.pyc` | Other | Application service or asynchronous task. | 18272 | 1 | yes | no | no | no | no | KEEP |
| `app/services/__pycache__/invoices.cpython-312.pyc` | Other | Application service or asynchronous task. | 533 | 1 | yes | no | no | no | no | KEEP |
| `app/services/__pycache__/jobs.cpython-312.pyc` | Other | Application service or asynchronous task. | 3089 | 1 | yes | no | no | no | no | KEEP |
| `app/services/__pycache__/limits.cpython-312.pyc` | Other | Application service or asynchronous task. | 13251 | 1 | yes | no | no | no | no | KEEP |
| `app/services/__pycache__/paddle.cpython-312.pyc` | Other | Application service or asynchronous task. | 4273 | 1 | yes | no | no | no | no | KEEP |
| `app/services/__pycache__/payment_monitor.cpython-312.pyc` | Other | Application service or asynchronous task. | 27402 | 1 | yes | no | no | no | no | KEEP |
| `app/services/__pycache__/practices.cpython-312.pyc` | Other | Application service or asynchronous task. | 15371 | 1 | yes | no | no | no | no | KEEP |
| `app/services/__pycache__/rate_limit.cpython-312.pyc` | Other | Application service or asynchronous task. | 6753 | 1 | yes | no | no | no | no | KEEP |
| `app/services/__pycache__/referrals.cpython-312.pyc` | Other | Application service or asynchronous task. | 6663 | 1 | yes | no | no | no | no | KEEP |
| `app/services/__pycache__/scheduler.cpython-312.pyc` | Other | Application service or asynchronous task. | 43489 | 1 | yes | no | no | no | no | KEEP |
| `app/services/__pycache__/telegram.cpython-312.pyc` | Other | Application service or asynchronous task. | 7122 | 1 | yes | no | no | no | no | KEEP |
| `app/services/analytics.py` | Python | Application service or asynchronous task. | 11946 | 3 | yes | no | no | no | no | KEEP |
| `app/services/billing.py` | Python | Application service or asynchronous task. | 23165 | 8 | yes | no | no | no | no | KEEP |
| `app/services/broadcast.py` | Python | Application service or asynchronous task. | 6686 | 3 | yes | no | no | no | no | KEEP |
| `app/services/catalog.py` | Python | Application service or asynchronous task. | 3799 | 2 | yes | no | no | no | no | KEEP |
| `app/services/chat.py` | Python | Application service or asynchronous task. | 20874 | 10 | yes | no | no | no | no | KEEP |
| `app/services/compatibility.py` | Python | Application service or asynchronous task. | 3461 | 2 | yes | no | no | no | no | KEEP |
| `app/services/cryptobot.py` | Python | Application service or asynchronous task. | 5078 | 2 | yes | no | no | no | no | KEEP |
| `app/services/eligibility.py` | Python | Application service or asynchronous task. | 2106 | 3 | yes | no | no | no | no | KEEP |
| `app/services/horoscopes.py` | Python | Application service or asynchronous task. | 13432 | 2 | yes | no | no | no | no | KEEP |
| `app/services/invoices.py` | Python | Application service or asynchronous task. | 407 | 3 | yes | no | no | no | no | KEEP |
| `app/services/jobs.py` | Python | Application service or asynchronous task. | 2091 | 2 | yes | no | no | no | no | KEEP |
| `app/services/limits.py` | Python | Application service or asynchronous task. | 10878 | 2 | yes | no | no | no | no | KEEP |
| `app/services/paddle.py` | Python | Application service or asynchronous task. | 2831 | 2 | yes | no | no | no | no | KEEP |
| `app/services/payment_monitor.py` | Python | Application service or asynchronous task. | 18408 | 2 | yes | no | no | no | no | KEEP |
| `app/services/practices.py` | Python | Application service or asynchronous task. | 9995 | 2 | yes | no | no | no | no | KEEP |
| `app/services/rate_limit.py` | Python | Application service or asynchronous task. | 3640 | 2 | yes | no | no | no | no | KEEP |
| `app/services/referrals.py` | Python | Application service or asynchronous task. | 4829 | 2 | yes | no | no | no | no | KEEP |
| `app/services/scheduler.py` | Python | Application service or asynchronous task. | 32197 | 4 | yes | no | no | no | no | KEEP |
| `app/services/telegram.py` | Python | Application service or asynchronous task. | 4993 | 3 | yes | no | no | no | no | KEEP |
| `app/tasks/__init__.py` | Python | Application service or asynchronous task. | 58 | 2 | yes | no | no | no | no | KEEP |
| `app/tasks/__pycache__/__init__.cpython-312.pyc` | Other | Application service or asynchronous task. | 206 | 1 | yes | no | no | no | no | KEEP |
| `app/tasks/__pycache__/celery_app.cpython-312.pyc` | Other | Application service or asynchronous task. | 1834 | 1 | yes | no | no | no | no | KEEP |
| `app/tasks/__pycache__/tasks.cpython-312.pyc` | Other | Application service or asynchronous task. | 9947 | 1 | yes | no | no | no | no | KEEP |
| `app/tasks/celery_app.py` | Python | Application service or asynchronous task. | 1645 | 2 | yes | no | no | no | no | KEEP |
| `app/tasks/tasks.py` | Python | Application service or asynchronous task. | 5243 | 4 | yes | no | no | no | no | KEEP |
| `data/llm_eval/golden_cases.jsonl` | Other | Other repository file. | 78751 | 5 | yes | no | no | yes | no | REVIEW |
| `data/llm_eval/sample_responses.jsonl` | Other | Other repository file. | 52565 | 3 | yes | no | no | no | no | KEEP |
| `docs/AGENTS.md` | Markdown | Current product, engineering, operations or reference documentation. | 13187 | 1 | yes | no | no | no | no | KEEP |
| `docs/AGENT_ARCHITECTURE.md` | Markdown | Current product, engineering, operations or reference documentation. | 4288 | 2 | yes | no | no | no | no | KEEP |
| `docs/AGENT_DOMAIN_SOURCES.md` | Markdown | Current product, engineering, operations or reference documentation. | 2481 | 1 | yes | no | no | no | no | KEEP |
| `docs/AGENT_QUALITY_STANDARD.md` | Markdown | Current product, engineering, operations or reference documentation. | 4374 | 1 | yes | no | no | no | no | KEEP |
| `docs/AGENT_SKILL_LIBRARY.md` | Markdown | Current product, engineering, operations or reference documentation. | 3246 | 1 | yes | no | no | no | no | KEEP |
| `docs/AI_SYSTEM.md` | Markdown | Current product, engineering, operations or reference documentation. | 8111 | 3 | yes | no | no | no | yes | KEEP |
| `docs/ANALYTICS_EVENT_DICTIONARY.md` | Markdown | Current product, engineering, operations or reference documentation. | 9619 | 2 | yes | no | no | no | no | KEEP |
| `docs/API.md` | Markdown | Current product, engineering, operations or reference documentation. | 21378 | 2 | yes | no | no | no | yes | KEEP |
| `docs/API_RESILIENCE_MATRIX.md` | Markdown | Current product, engineering, operations or reference documentation. | 1961 | 2 | yes | no | no | no | no | KEEP |
| `docs/ARCHITECTURE.md` | Markdown | Current product, engineering, operations or reference documentation. | 14998 | 4 | yes | no | no | no | yes | KEEP |
| `docs/ARCHIVE/NEXT_STEPS_2026-08-26.md` | Markdown | Current product, engineering, operations or reference documentation. | 12458 | 2 | yes | no | no | no | no | ARCHIVE/REVIEW |
| `docs/ARCHIVE/README.md` | Markdown | Documentation index for the surrounding category. | 958 | 1 | yes | no | no | no | no | ARCHIVE/REVIEW |
| `docs/ARCHIVE/UI_PREMIUM_PLAN_RU_2026-08-09.md` | Markdown | Current product, engineering, operations or reference documentation. | 40788 | 2 | yes | no | no | no | no | ARCHIVE/REVIEW |
| `docs/ASTRONOMY_REFERENCE_QA.md` | Markdown | Current product, engineering, operations or reference documentation. | 7222 | 3 | yes | no | no | no | no | KEEP |
| `docs/BACKUP_RESTORE_DRILL.md` | Markdown | Current product, engineering, operations or reference documentation. | 1016 | 3 | yes | no | no | no | no | KEEP |
| `docs/CELERY_REDIS.md` | Markdown | Current product, engineering, operations or reference documentation. | 8556 | 2 | yes | no | no | no | no | KEEP |
| `docs/CHART_ENGINE_DECISION.md` | Markdown | Current product, engineering, operations or reference documentation. | 5279 | 1 | yes | no | no | no | no | KEEP |
| `docs/CHART_ENGINE_LICENSING.md` | Markdown | Current product, engineering, operations or reference documentation. | 2955 | 2 | yes | no | no | no | no | KEEP |
| `docs/CHART_PRODUCT_CONTRACTS.md` | Markdown | Current product, engineering, operations or reference documentation. | 8549 | 2 | yes | no | no | no | no | KEEP |
| `docs/CHART_TYPE_CAPABILITIES.md` | Markdown | Current product, engineering, operations or reference documentation. | 2849 | 2 | yes | no | no | no | no | KEEP |
| `docs/CHIROMANT_AVATAR_BRIEF.md` | Markdown | Current product, engineering, operations or reference documentation. | 794 | 1 | yes | no | no | no | no | KEEP |
| `docs/COMPETITOR_MATRIX.md` | Markdown | Current product, engineering, operations or reference documentation. | 8118 | 3 | yes | no | no | no | no | KEEP |
| `docs/COMPOSITE_AND_RETURNS_PRODUCT_SPEC.md` | Markdown | Current product, engineering, operations or reference documentation. | 8894 | 1 | yes | no | no | no | no | KEEP |
| `docs/CONTRIBUTING.md` | Markdown | Current product, engineering, operations or reference documentation. | 11095 | 1 | yes | no | no | no | yes | KEEP |
| `docs/DECISIONS.md` | Markdown | Current product, engineering, operations or reference documentation. | 11933 | 1 | yes | no | no | no | no | KEEP |
| `docs/DEPLOYMENT.md` | Markdown | Current product, engineering, operations or reference documentation. | 14364 | 5 | yes | no | no | no | yes | KEEP |
| `docs/DESIGN_COMPONENT_INVENTORY.md` | Markdown | Current product, engineering, operations or reference documentation. | 5101 | 1 | yes | no | no | no | no | KEEP |
| `docs/DESIGN_SYSTEM.md` | Markdown | Current product, engineering, operations or reference documentation. | 13582 | 4 | yes | no | no | no | yes | KEEP |
| `docs/DOMAIN/ASTROLOGY.md` | Markdown | Current product, engineering, operations or reference documentation. | 4295 | 1 | yes | no | no | no | yes | KEEP |
| `docs/DOMAIN/CONTRACTS.md` | Markdown | Current product, engineering, operations or reference documentation. | 7435 | 2 | yes | no | no | no | yes | KEEP |
| `docs/DOMAIN/PALM.md` | Markdown | Current product, engineering, operations or reference documentation. | 3209 | 1 | yes | no | no | no | yes | KEEP |
| `docs/DOMAIN/README.md` | Markdown | Documentation index for the surrounding category. | 2259 | 2 | yes | no | no | no | yes | KEEP |
| `docs/DOMAIN/TAROT.md` | Markdown | Current product, engineering, operations or reference documentation. | 2816 | 1 | yes | no | no | no | yes | KEEP |
| `docs/EVIDENCE/AUDIT/sqlite_scaling_10x_2026-08-26.md` | Markdown | Current product, engineering, operations or reference documentation. | 3430 | 3 | yes | no | no | no | no | ARCHIVE/REVIEW |
| `docs/EVIDENCE/AUDIT/staging_chat_indexes_2026-08-26.md` | Markdown | Current product, engineering, operations or reference documentation. | 7186 | 3 | yes | no | no | no | no | ARCHIVE/REVIEW |
| `docs/EVIDENCE/BASELINE_2026-08-26.md` | Markdown | Current product, engineering, operations or reference documentation. | 5235 | 3 | yes | no | yes | no | no | ARCHIVE/REVIEW |
| `docs/EVIDENCE/LIGHTHOUSE_AXE_REPORT_2026-08-27.md` | Markdown | Current product, engineering, operations or reference documentation. | 11307 | 1 | yes | no | yes | no | no | ARCHIVE/REVIEW |
| `docs/EVIDENCE/LOCAL_BROWSER_BASELINE_2026-08-27.md` | Markdown | Current product, engineering, operations or reference documentation. | 7418 | 6 | yes | no | yes | no | no | ARCHIVE/REVIEW |
| `docs/EVIDENCE/ORACLEAI_CONTINUATION_REPORT_2026-08-26.md` | Markdown | Current product, engineering, operations or reference documentation. | 13057 | 2 | yes | no | yes | no | no | ARCHIVE/REVIEW |
| `docs/EVIDENCE/ORACLEAI_DETAILED_REVIEW_RU_2026-08-27.md` | Markdown | Current product, engineering, operations or reference documentation. | 40148 | 1 | yes | no | no | no | no | ARCHIVE/REVIEW |
| `docs/EVIDENCE/ORACLEAI_FINAL_AUDIT_2026-08-26.md` | Markdown | Current product, engineering, operations or reference documentation. | 6911 | 4 | yes | no | no | no | no | ARCHIVE/REVIEW |
| `docs/EVIDENCE/ORACLEAI_SECURITY_REMEDIATION_PLAN_RU_2026-08-27.md` | Markdown | Current product, engineering, operations or reference documentation. | 39778 | 1 | yes | no | no | no | no | ARCHIVE/REVIEW |
| `docs/EVIDENCE/P2_QUALITY_GATE_2026-08-27.md` | Markdown | Current product, engineering, operations or reference documentation. | 3090 | 1 | yes | no | no | no | no | ARCHIVE/REVIEW |
| `docs/EVIDENCE/P2_RELEASE_CHECKLIST_2026-08-27.md` | Markdown | Current product, engineering, operations or reference documentation. | 5473 | 6 | yes | no | no | no | no | ARCHIVE/REVIEW |
| `docs/EVIDENCE/PERFORMANCE_BASELINE_2026-08-27.md` | Markdown | Current product, engineering, operations or reference documentation. | 2297 | 1 | yes | no | yes | no | no | ARCHIVE/REVIEW |
| `docs/EVIDENCE/PROJECT_AUDIT_AND_ROADMAP_2026-08-27.md` | Markdown | Current product, engineering, operations or reference documentation. | 54885 | 1 | yes | no | no | no | no | ARCHIVE/REVIEW |
| `docs/EVIDENCE/QA_REPORT_2026-08-26.md` | Markdown | Current product, engineering, operations or reference documentation. | 6891 | 1 | yes | no | yes | no | no | ARCHIVE/REVIEW |
| `docs/EVIDENCE/README.md` | Markdown | Documentation index for the surrounding category. | 1847 | 1 | yes | no | no | no | no | ARCHIVE/REVIEW |
| `docs/EVIDENCE/TRACEABILITY_MATRIX_2026-08-26.md` | Markdown | Current product, engineering, operations or reference documentation. | 15782 | 3 | yes | no | no | no | no | ARCHIVE/REVIEW |
| `docs/EVIDENCE/VISUAL_QA_A11Y_REPORT_2026-08-27.md` | Markdown | Current product, engineering, operations or reference documentation. | 30873 | 3 | yes | no | yes | no | no | ARCHIVE/REVIEW |
| `docs/FEATURES/BILLING.md` | Markdown | Current product, engineering, operations or reference documentation. | 7305 | 1 | yes | no | no | no | yes | KEEP |
| `docs/FEATURES/HISTORY.md` | Markdown | Current product, engineering, operations or reference documentation. | 3119 | 1 | yes | no | no | no | yes | KEEP |
| `docs/FEATURES/MEMORY.md` | Markdown | Current product, engineering, operations or reference documentation. | 3581 | 1 | yes | no | no | no | yes | KEEP |
| `docs/FEATURES/README.md` | Markdown | Documentation index for the surrounding category. | 1500 | 2 | yes | no | no | no | yes | KEEP |
| `docs/FULL_PRODUCT_SURFACE.md` | Markdown | Current product, engineering, operations or reference documentation. | 16023 | 5 | yes | no | no | no | no | KEEP |
| `docs/INCIDENT_RESPONSE_RUNBOOK.md` | Markdown | Current product, engineering, operations or reference documentation. | 5087 | 2 | yes | no | no | no | no | KEEP |
| `docs/INTERPRETATION_QUALITY_STANDARD.md` | Markdown | Current product, engineering, operations or reference documentation. | 10455 | 1 | yes | no | no | no | no | KEEP |
| `docs/LEGAL_REVIEW.md` | Markdown | Current product, engineering, operations or reference documentation. | 2890 | 2 | yes | no | no | no | no | KEEP |
| `docs/LLM_AGENT_TECHNICAL_AUDIT.md` | Markdown | Current product, engineering, operations or reference documentation. | 12077 | 3 | yes | no | no | no | no | KEEP |
| `docs/LLM_EVALUATION.md` | Markdown | Current product, engineering, operations or reference documentation. | 7202 | 2 | yes | no | no | no | no | KEEP |
| `docs/LOCALIZATION_GLOSSARY.md` | Markdown | Current product, engineering, operations or reference documentation. | 2051 | 4 | yes | no | no | no | no | KEEP |
| `docs/MEMORY_EVALUATION.md` | Markdown | Current product, engineering, operations or reference documentation. | 1099 | 1 | yes | no | no | no | no | KEEP |
| `docs/MONETIZATION_ASSUMPTIONS.csv` | Other | Current product, engineering, operations or reference documentation. | 8853 | 1 | yes | no | no | no | no | KEEP |
| `docs/MONETIZATION_EXTERNAL_SOURCES.md` | Markdown | Current product, engineering, operations or reference documentation. | 1441 | 2 | yes | no | no | no | no | KEEP |
| `docs/MONETIZATION_RESEARCH_PACK.md` | Markdown | Current product, engineering, operations or reference documentation. | 38685 | 1 | yes | no | no | no | no | KEEP |
| `docs/MONETIZATION_STRATEGY.md` | Markdown | Current product, engineering, operations or reference documentation. | 38271 | 3 | yes | no | no | no | no | KEEP |
| `docs/MONETIZATION_UNIT_ECONOMICS.md` | Markdown | Current product, engineering, operations or reference documentation. | 8212 | 3 | yes | no | no | no | no | KEEP |
| `docs/OPERATIONS.md` | Markdown | Current product, engineering, operations or reference documentation. | 4462 | 3 | yes | no | no | no | yes | KEEP |
| `docs/PALM_ENGINE_RESEARCH.md` | Markdown | Current product, engineering, operations or reference documentation. | 6470 | 3 | yes | no | no | no | no | KEEP |
| `docs/PAYMENTS_UX_AND_INTEGRATION.md` | Markdown | Current product, engineering, operations or reference documentation. | 5777 | 1 | yes | no | no | no | no | KEEP |
| `docs/PAYMENT_MONITORING.md` | Markdown | Current product, engineering, operations or reference documentation. | 12104 | 1 | yes | no | no | no | no | KEEP |
| `docs/PDF_SYSTEM.md` | Markdown | Current product, engineering, operations or reference documentation. | 3194 | 2 | yes | no | no | no | no | KEEP |
| `docs/PDF_TEMPLATE_CATALOG.md` | Markdown | Current product, engineering, operations or reference documentation. | 1933 | 4 | yes | no | no | no | no | KEEP |
| `docs/POSTGRES_MIGRATION.md` | Markdown | Current product, engineering, operations or reference documentation. | 5669 | 2 | yes | no | no | no | no | KEEP |
| `docs/PRODUCT.md` | Markdown | Current product, engineering, operations or reference documentation. | 14991 | 4 | yes | no | no | no | yes | KEEP |
| `docs/README.md` | Markdown | Current product, engineering, operations or reference documentation. | 6218 | 4 | yes | no | no | no | yes | KEEP |
| `docs/RELEASE/CHANGELOG.md` | Markdown | Current product, engineering, operations or reference documentation. | 10858 | 1 | yes | no | no | no | no | KEEP |
| `docs/RELEASE/CURRENT_STATUS.md` | Markdown | Current product, engineering, operations or reference documentation. | 5288 | 19 | yes | no | no | no | yes | KEEP |
| `docs/RELEASE/DOCUMENTATION_FINAL_REVIEW.md` | Markdown | Current product, engineering, operations or reference documentation. | 8334 | 1 | yes | no | no | no | no | KEEP |
| `docs/RELEASE/LAUNCH_GOVERNANCE.md` | Markdown | Current product, engineering, operations or reference documentation. | 9796 | 1 | yes | no | no | no | no | KEEP |
| `docs/RELEASE/P0_PRODUCTION_EXECUTION_PLAN.md` | Markdown | Current product, engineering, operations or reference documentation. | 17230 | 3 | yes | no | no | no | no | KEEP |
| `docs/RELEASE/P0_PRODUCTION_TEST_CASES.md` | Markdown | Current product, engineering, operations or reference documentation. | 19441 | 1 | yes | no | no | no | no | KEEP |
| `docs/RELEASE/PRODUCTION_READINESS.md` | Markdown | Current product, engineering, operations or reference documentation. | 32680 | 2 | yes | no | no | no | no | KEEP |
| `docs/RELEASE/TASKS.md` | Markdown | Current product, engineering, operations or reference documentation. | 12730 | 11 | yes | no | no | no | yes | KEEP |
| `docs/REPOSITORY_INVENTORY.md` | Markdown | Current product, engineering, operations or reference documentation. | 146426 | 1 | yes | no | no | no | no | KEEP |
| `docs/SCALE_AND_MIGRATION.md` | Markdown | Current product, engineering, operations or reference documentation. | 5850 | 1 | yes | no | no | no | no | KEEP |
| `docs/SECURITY.md` | Markdown | Current product, engineering, operations or reference documentation. | 17375 | 1 | yes | no | no | no | yes | KEEP |
| `docs/TESTING.md` | Markdown | Current product, engineering, operations or reference documentation. | 3287 | 3 | yes | no | no | no | yes | KEEP |
| `docs/VISUAL_QA.md` | Markdown | Current product, engineering, operations or reference documentation. | 12352 | 4 | yes | no | no | no | no | KEEP |
| `docs/architecture/LLM_CONTEXT_POLICY.md` | Markdown | Architecture reference or AI context policy. | 12729 | 2 | yes | no | no | no | no | KEEP |
| `docs/design/GENDER_AND_LANGUAGE_CONTRACT.md` | Markdown | Design-domain reference or UI contract. | 4566 | 1 | yes | no | no | no | no | KEEP |
| `docs/design/RITUAL_CHAT_EXPERIENCE_SPEC_2026-08.md` | Markdown | Design-domain reference or UI contract. | 12012 | 1 | yes | no | no | no | no | KEEP |
| `infra/Caddyfile` | Other | Deployment/container infrastructure. | 809 | 4 | yes | no | no | no | no | KEEP |
| `infra/Dockerfile` | Other | Deployment/container infrastructure. | 1661 | 7 | yes | no | no | no | no | KEEP |
| `infra/backup-postgres.sh` | Shell | Deployment/container infrastructure. | 1297 | 2 | yes | yes | no | no | no | KEEP |
| `infra/docker-compose.yml` | YAML | Deployment/container infrastructure. | 7229 | 10 | yes | no | no | no | no | KEEP |
| `infra/postgres-init.sql` | Other | Deployment/container infrastructure. | 193 | 1 | yes | no | no | no | no | KEEP |
| `infra/restore-postgres.sh` | Shell | Deployment/container infrastructure. | 1224 | 2 | yes | yes | no | no | no | KEEP |
| `load/README.md` | Markdown | Markdown repository file. | 2911 | 1 | yes | no | no | no | no | KEEP |
| `load/locustfile.py` | Python | Python repository file. | 3200 | 4 | yes | no | no | no | no | KEEP |
| `load/simulate.py` | Python | Python repository file. | 8261 | 2 | yes | no | no | no | no | KEEP |
| `miniapp/css/00-tokens.css` | CSS | Telegram Mini App client or static asset. | 5649 | 6 | yes | no | no | no | no | KEEP |
| `miniapp/css/01-sky-shell.css` | CSS | Telegram Mini App client or static asset. | 9160 | 1 | yes | no | no | no | no | KEEP |
| `miniapp/css/02-skeleton.css` | CSS | Telegram Mini App client or static asset. | 3987 | 1 | yes | no | no | no | no | KEEP |
| `miniapp/css/03-profile.css` | CSS | Telegram Mini App client or static asset. | 19572 | 1 | yes | no | no | no | no | KEEP |
| `miniapp/css/04-atmosphere.css` | CSS | Telegram Mini App client or static asset. | 4037 | 1 | yes | no | no | no | no | KEEP |
| `miniapp/css/05-agents.css` | CSS | Telegram Mini App client or static asset. | 5143 | 1 | yes | no | no | no | no | KEEP |
| `miniapp/css/06-composer-chat.css` | CSS | Telegram Mini App client or static asset. | 11094 | 1 | yes | no | no | no | no | KEEP |
| `miniapp/css/07-home-bg.css` | CSS | Telegram Mini App client or static asset. | 3070 | 1 | yes | no | no | no | no | KEEP |
| `miniapp/css/08-day-memory.css` | CSS | Telegram Mini App client or static asset. | 8552 | 1 | yes | no | no | no | no | KEEP |
| `miniapp/css/09-chart-panels.css` | CSS | Telegram Mini App client or static asset. | 4638 | 1 | yes | no | no | no | no | KEEP |
| `miniapp/css/10-tarot-carousel.css` | CSS | Telegram Mini App client or static asset. | 9876 | 1 | yes | no | no | no | no | KEEP |
| `miniapp/css/11-misc.css` | CSS | Telegram Mini App client or static asset. | 7938 | 1 | yes | no | no | no | no | KEEP |
| `miniapp/css/12-compat.css` | CSS | Telegram Mini App client or static asset. | 5977 | 1 | yes | no | no | no | no | KEEP |
| `miniapp/css/13-toolbar-sheet.css` | CSS | Telegram Mini App client or static asset. | 7540 | 1 | yes | no | no | no | no | KEEP |
| `miniapp/css/14-widgets.css` | CSS | Telegram Mini App client or static asset. | 13796 | 1 | yes | no | no | no | no | KEEP |
| `miniapp/css/15-ritual-redesign.css` | CSS | Telegram Mini App client or static asset. | 149149 | 7 | yes | no | no | no | no | KEEP |
| `miniapp/css/16-payments.css` | CSS | Telegram Mini App client or static asset. | 10842 | 3 | yes | no | no | no | no | KEEP |
| `miniapp/css/16-visual-qa.css` | CSS | Telegram Mini App client or static asset. | 7979 | 5 | yes | no | no | no | no | KEEP |
| `miniapp/css/17-premium-shell.css` | CSS | Telegram Mini App client or static asset. | 9628 | 2 | yes | no | no | no | no | KEEP |
| `miniapp/fonts/cinzel-0.woff2` | Asset/model | Telegram Mini App client or static asset. | 14540 | 1 | yes | no | no | no | no | KEEP |
| `miniapp/fonts/cinzel-1.woff2` | Asset/model | Telegram Mini App client or static asset. | 25904 | 1 | yes | no | no | no | no | KEEP |
| `miniapp/fonts/oracle-fonts.css` | CSS | Telegram Mini App client or static asset. | 8527 | 1 | yes | no | no | no | no | KEEP |
| `miniapp/fonts/pjs-2.woff2` | Asset/model | Telegram Mini App client or static asset. | 1716 | 1 | yes | no | no | no | no | KEEP |
| `miniapp/fonts/pjs-3.woff2` | Asset/model | Telegram Mini App client or static asset. | 8352 | 1 | yes | no | no | no | no | KEEP |
| `miniapp/fonts/pjs-4.woff2` | Asset/model | Telegram Mini App client or static asset. | 21728 | 1 | yes | no | no | no | no | KEEP |
| `miniapp/fonts/pjs-5.woff2` | Asset/model | Telegram Mini App client or static asset. | 27348 | 1 | yes | no | no | no | no | KEEP |
| `miniapp/img/agents/astro.jpg` | Asset/model | Telegram Mini App client or static asset. | 26777 | 1 | yes | no | no | no | no | KEEP |
| `miniapp/img/agents/chiromant.jpg` | Asset/model | Telegram Mini App client or static asset. | 50785 | 1 | yes | no | no | no | no | KEEP |
| `miniapp/img/agents/coach.jpg` | Asset/model | Telegram Mini App client or static asset. | 18615 | 1 | yes | no | no | no | no | KEEP |
| `miniapp/img/agents/keeper.jpg` | Asset/model | Telegram Mini App client or static asset. | 22338 | 1 | yes | no | no | no | no | KEEP |
| `miniapp/img/agents/numero.jpg` | Asset/model | Telegram Mini App client or static asset. | 28607 | 1 | yes | no | no | no | no | KEEP |
| `miniapp/img/agents/oracle.jpg` | Asset/model | Telegram Mini App client or static asset. | 23020 | 1 | yes | no | no | no | no | KEEP |
| `miniapp/img/agents/tarot.jpg` | Asset/model | Telegram Mini App client or static asset. | 22587 | 1 | yes | no | no | no | no | KEEP |
| `miniapp/img/bg-cosmos-2.jpg` | Asset/model | Telegram Mini App client or static asset. | 38095 | 1 | yes | no | no | no | no | KEEP |
| `miniapp/img/bg-cosmos.jpg` | Asset/model | Telegram Mini App client or static asset. | 41427 | 1 | yes | no | no | no | no | KEEP |
| `miniapp/img/card-art.jpg` | Asset/model | Telegram Mini App client or static asset. | 4743055 | 1 | yes | no | no | no | no | KEEP |
| `miniapp/img/card-back-alt.png` | Asset/model | Telegram Mini App client or static asset. | 2475795 | 1 | yes | no | no | no | no | KEEP |
| `miniapp/img/card-back-src.png` | Asset/model | Telegram Mini App client or static asset. | 2475795 | 1 | yes | no | no | no | no | KEEP |
| `miniapp/img/card-back.jpg` | Asset/model | Telegram Mini App client or static asset. | 166753 | 1 | yes | no | no | no | no | KEEP |
| `miniapp/img/card-face-src.png` | Asset/model | Telegram Mini App client or static asset. | 2546624 | 1 | yes | no | no | no | no | KEEP |
| `miniapp/img/card-face.jpg` | Asset/model | Telegram Mini App client or static asset. | 188740 | 1 | yes | no | no | no | no | KEEP |
| `miniapp/img/favicon.svg` | Asset/model | Telegram Mini App client or static asset. | 691 | 1 | yes | no | no | no | no | KEEP |
| `miniapp/img/lilith-sil.png` | Asset/model | Telegram Mini App client or static asset. | 307168 | 1 | yes | no | no | no | no | KEEP |
| `miniapp/img/og-card.jpg` | Asset/model | Telegram Mini App client or static asset. | 119261 | 1 | yes | no | no | no | no | KEEP |
| `miniapp/img/og-src.png` | Asset/model | Telegram Mini App client or static asset. | 2154953 | 1 | yes | no | no | no | no | KEEP |
| `miniapp/img/oracle-mark.png` | Asset/model | Telegram Mini App client or static asset. | 1483016 | 1 | yes | no | no | no | no | KEEP |
| `miniapp/img/tarot-back.png` | Asset/model | Telegram Mini App client or static asset. | 2475795 | 1 | yes | no | no | no | no | KEEP |
| `miniapp/img/tarot/cups01.jpg` | Asset/model | Telegram Mini App client or static asset. | 93923 | 1 | yes | no | no | no | no | KEEP |
| `miniapp/img/tarot/cups02.jpg` | Asset/model | Telegram Mini App client or static asset. | 93784 | 1 | yes | no | no | no | no | KEEP |
| `miniapp/img/tarot/cups03.jpg` | Asset/model | Telegram Mini App client or static asset. | 98364 | 1 | yes | no | no | no | no | KEEP |
| `miniapp/img/tarot/cups04.jpg` | Asset/model | Telegram Mini App client or static asset. | 87961 | 1 | yes | no | no | no | no | KEEP |
| `miniapp/img/tarot/cups05.jpg` | Asset/model | Telegram Mini App client or static asset. | 69692 | 1 | yes | no | no | no | no | KEEP |
| `miniapp/img/tarot/cups06.jpg` | Asset/model | Telegram Mini App client or static asset. | 105033 | 1 | yes | no | no | no | no | KEEP |
| `miniapp/img/tarot/cups07.jpg` | Asset/model | Telegram Mini App client or static asset. | 92718 | 1 | yes | no | no | no | no | KEEP |
| `miniapp/img/tarot/cups08.jpg` | Asset/model | Telegram Mini App client or static asset. | 84884 | 1 | yes | no | no | no | no | KEEP |
| `miniapp/img/tarot/cups09.jpg` | Asset/model | Telegram Mini App client or static asset. | 95040 | 1 | yes | no | no | no | no | KEEP |
| `miniapp/img/tarot/cups10.jpg` | Asset/model | Telegram Mini App client or static asset. | 94623 | 1 | yes | no | no | no | no | KEEP |
| `miniapp/img/tarot/cups11.jpg` | Asset/model | Telegram Mini App client or static asset. | 92222 | 1 | yes | no | no | no | no | KEEP |
| `miniapp/img/tarot/cups12.jpg` | Asset/model | Telegram Mini App client or static asset. | 93971 | 1 | yes | no | no | no | no | KEEP |
| `miniapp/img/tarot/cups13.jpg` | Asset/model | Telegram Mini App client or static asset. | 97403 | 1 | yes | no | no | no | no | KEEP |
| `miniapp/img/tarot/cups14.jpg` | Asset/model | Telegram Mini App client or static asset. | 95508 | 1 | yes | no | no | no | no | KEEP |
| `miniapp/img/tarot/m00.jpg` | Asset/model | Telegram Mini App client or static asset. | 89620 | 1 | yes | no | no | no | no | KEEP |
| `miniapp/img/tarot/m01.jpg` | Asset/model | Telegram Mini App client or static asset. | 93709 | 1 | yes | no | no | no | no | KEEP |
| `miniapp/img/tarot/m02.jpg` | Asset/model | Telegram Mini App client or static asset. | 99250 | 1 | yes | no | no | no | no | KEEP |
| `miniapp/img/tarot/m03.jpg` | Asset/model | Telegram Mini App client or static asset. | 108153 | 1 | yes | no | no | no | no | KEEP |
| `miniapp/img/tarot/m04.jpg` | Asset/model | Telegram Mini App client or static asset. | 103030 | 1 | yes | no | no | no | no | KEEP |
| `miniapp/img/tarot/m05.jpg` | Asset/model | Telegram Mini App client or static asset. | 104672 | 1 | yes | no | no | no | no | KEEP |
| `miniapp/img/tarot/m06.jpg` | Asset/model | Telegram Mini App client or static asset. | 107129 | 1 | yes | no | no | no | no | KEEP |
| `miniapp/img/tarot/m07.jpg` | Asset/model | Telegram Mini App client or static asset. | 101489 | 1 | yes | no | no | no | no | KEEP |
| `miniapp/img/tarot/m08.jpg` | Asset/model | Telegram Mini App client or static asset. | 86813 | 1 | yes | no | no | no | no | KEEP |
| `miniapp/img/tarot/m09.jpg` | Asset/model | Telegram Mini App client or static asset. | 77139 | 1 | yes | no | no | no | no | KEEP |
| `miniapp/img/tarot/m10.jpg` | Asset/model | Telegram Mini App client or static asset. | 103173 | 1 | yes | no | no | no | no | KEEP |
| `miniapp/img/tarot/m11.jpg` | Asset/model | Telegram Mini App client or static asset. | 103475 | 1 | yes | no | no | no | no | KEEP |
| `miniapp/img/tarot/m12.jpg` | Asset/model | Telegram Mini App client or static asset. | 93005 | 1 | yes | no | no | no | no | KEEP |
| `miniapp/img/tarot/m13.jpg` | Asset/model | Telegram Mini App client or static asset. | 103290 | 1 | yes | no | no | no | no | KEEP |
| `miniapp/img/tarot/m14.jpg` | Asset/model | Telegram Mini App client or static asset. | 107154 | 1 | yes | no | no | no | no | KEEP |
| `miniapp/img/tarot/m15.jpg` | Asset/model | Telegram Mini App client or static asset. | 93001 | 1 | yes | no | no | no | no | KEEP |
| `miniapp/img/tarot/m16.jpg` | Asset/model | Telegram Mini App client or static asset. | 91527 | 1 | yes | no | no | no | no | KEEP |
| `miniapp/img/tarot/m17.jpg` | Asset/model | Telegram Mini App client or static asset. | 94232 | 1 | yes | no | no | no | no | KEEP |
| `miniapp/img/tarot/m18.jpg` | Asset/model | Telegram Mini App client or static asset. | 95869 | 1 | yes | no | no | no | no | KEEP |
| `miniapp/img/tarot/m19.jpg` | Asset/model | Telegram Mini App client or static asset. | 107565 | 1 | yes | no | no | no | no | KEEP |
| `miniapp/img/tarot/m20.jpg` | Asset/model | Telegram Mini App client or static asset. | 104531 | 1 | yes | no | no | no | no | KEEP |
| `miniapp/img/tarot/m21.jpg` | Asset/model | Telegram Mini App client or static asset. | 103065 | 1 | yes | no | no | no | no | KEEP |
| `miniapp/img/tarot/pents01.jpg` | Asset/model | Telegram Mini App client or static asset. | 90165 | 1 | yes | no | no | no | no | KEEP |
| `miniapp/img/tarot/pents02.jpg` | Asset/model | Telegram Mini App client or static asset. | 87927 | 1 | yes | no | no | no | no | KEEP |
| `miniapp/img/tarot/pents03.jpg` | Asset/model | Telegram Mini App client or static asset. | 100067 | 1 | yes | no | no | no | no | KEEP |
| `miniapp/img/tarot/pents04.jpg` | Asset/model | Telegram Mini App client or static asset. | 80253 | 1 | yes | no | no | no | no | KEEP |
| `miniapp/img/tarot/pents05.jpg` | Asset/model | Telegram Mini App client or static asset. | 109197 | 1 | yes | no | no | no | no | KEEP |
| `miniapp/img/tarot/pents06.jpg` | Asset/model | Telegram Mini App client or static asset. | 90372 | 1 | yes | no | no | no | no | KEEP |
| `miniapp/img/tarot/pents07.jpg` | Asset/model | Telegram Mini App client or static asset. | 96451 | 1 | yes | no | no | no | no | KEEP |
| `miniapp/img/tarot/pents08.jpg` | Asset/model | Telegram Mini App client or static asset. | 89685 | 1 | yes | no | no | no | no | KEEP |
| `miniapp/img/tarot/pents09.jpg` | Asset/model | Telegram Mini App client or static asset. | 98960 | 1 | yes | no | no | no | no | KEEP |
| `miniapp/img/tarot/pents10.jpg` | Asset/model | Telegram Mini App client or static asset. | 109140 | 1 | yes | no | no | no | no | KEEP |
| `miniapp/img/tarot/pents11.jpg` | Asset/model | Telegram Mini App client or static asset. | 83289 | 1 | yes | no | no | no | no | KEEP |
| `miniapp/img/tarot/pents12.jpg` | Asset/model | Telegram Mini App client or static asset. | 81016 | 1 | yes | no | no | no | no | KEEP |
| `miniapp/img/tarot/pents13.jpg` | Asset/model | Telegram Mini App client or static asset. | 113432 | 1 | yes | no | no | no | no | KEEP |
| `miniapp/img/tarot/pents14.jpg` | Asset/model | Telegram Mini App client or static asset. | 101345 | 1 | yes | no | no | no | no | KEEP |
| `miniapp/img/tarot/swords01.jpg` | Asset/model | Telegram Mini App client or static asset. | 87772 | 1 | yes | no | no | no | no | KEEP |
| `miniapp/img/tarot/swords02.jpg` | Asset/model | Telegram Mini App client or static asset. | 80734 | 1 | yes | no | no | no | no | KEEP |
| `miniapp/img/tarot/swords03.jpg` | Asset/model | Telegram Mini App client or static asset. | 77691 | 1 | yes | no | no | no | no | KEEP |
| `miniapp/img/tarot/swords04.jpg` | Asset/model | Telegram Mini App client or static asset. | 89972 | 1 | yes | no | no | no | no | KEEP |
| `miniapp/img/tarot/swords05.jpg` | Asset/model | Telegram Mini App client or static asset. | 94531 | 1 | yes | no | no | no | no | KEEP |
| `miniapp/img/tarot/swords06.jpg` | Asset/model | Telegram Mini App client or static asset. | 91949 | 1 | yes | no | no | no | no | KEEP |
| `miniapp/img/tarot/swords07.jpg` | Asset/model | Telegram Mini App client or static asset. | 84022 | 1 | yes | no | no | no | no | KEEP |
| `miniapp/img/tarot/swords08.jpg` | Asset/model | Telegram Mini App client or static asset. | 92785 | 1 | yes | no | no | no | no | KEEP |
| `miniapp/img/tarot/swords09.jpg` | Asset/model | Telegram Mini App client or static asset. | 88378 | 1 | yes | no | no | no | no | KEEP |
| `miniapp/img/tarot/swords10.jpg` | Asset/model | Telegram Mini App client or static asset. | 83880 | 1 | yes | no | no | no | no | KEEP |
| `miniapp/img/tarot/swords11.jpg` | Asset/model | Telegram Mini App client or static asset. | 93399 | 1 | yes | no | no | no | no | KEEP |
| `miniapp/img/tarot/swords12.jpg` | Asset/model | Telegram Mini App client or static asset. | 97214 | 1 | yes | no | no | no | no | KEEP |
| `miniapp/img/tarot/swords13.jpg` | Asset/model | Telegram Mini App client or static asset. | 90305 | 1 | yes | no | no | no | no | KEEP |
| `miniapp/img/tarot/swords14.jpg` | Asset/model | Telegram Mini App client or static asset. | 96838 | 1 | yes | no | no | no | no | KEEP |
| `miniapp/img/tarot/wands01.jpg` | Asset/model | Telegram Mini App client or static asset. | 87809 | 1 | yes | no | no | no | no | KEEP |
| `miniapp/img/tarot/wands02.jpg` | Asset/model | Telegram Mini App client or static asset. | 87581 | 1 | yes | no | no | no | no | KEEP |
| `miniapp/img/tarot/wands03.jpg` | Asset/model | Telegram Mini App client or static asset. | 95190 | 1 | yes | no | no | no | no | KEEP |
| `miniapp/img/tarot/wands04.jpg` | Asset/model | Telegram Mini App client or static asset. | 89790 | 1 | yes | no | no | no | no | KEEP |
| `miniapp/img/tarot/wands05.jpg` | Asset/model | Telegram Mini App client or static asset. | 92032 | 1 | yes | no | no | no | no | KEEP |
| `miniapp/img/tarot/wands06.jpg` | Asset/model | Telegram Mini App client or static asset. | 95119 | 1 | yes | no | no | no | no | KEEP |
| `miniapp/img/tarot/wands07.jpg` | Asset/model | Telegram Mini App client or static asset. | 82574 | 1 | yes | no | no | no | no | KEEP |
| `miniapp/img/tarot/wands08.jpg` | Asset/model | Telegram Mini App client or static asset. | 84287 | 1 | yes | no | no | no | no | KEEP |
| `miniapp/img/tarot/wands09.jpg` | Asset/model | Telegram Mini App client or static asset. | 95283 | 1 | yes | no | no | no | no | KEEP |
| `miniapp/img/tarot/wands10.jpg` | Asset/model | Telegram Mini App client or static asset. | 87686 | 1 | yes | no | no | no | no | KEEP |
| `miniapp/img/tarot/wands11.jpg` | Asset/model | Telegram Mini App client or static asset. | 95587 | 1 | yes | no | no | no | no | KEEP |
| `miniapp/img/tarot/wands12.jpg` | Asset/model | Telegram Mini App client or static asset. | 100968 | 1 | yes | no | no | no | no | KEEP |
| `miniapp/img/tarot/wands13.jpg` | Asset/model | Telegram Mini App client or static asset. | 104911 | 1 | yes | no | no | no | no | KEEP |
| `miniapp/img/tarot/wands14.jpg` | Asset/model | Telegram Mini App client or static asset. | 105080 | 1 | yes | no | no | no | no | KEEP |
| `miniapp/index.html` | HTML | Telegram Mini App client or static asset. | 4093 | 15 | yes | no | no | no | no | KEEP |
| `miniapp/js/00-runtime.js` | JavaScript/TypeScript | Telegram Mini App client or static asset. | 1196 | 4 | yes | no | no | no | no | KEEP |
| `miniapp/js/01-utils.js` | JavaScript/TypeScript | Telegram Mini App client or static asset. | 38019 | 7 | yes | no | no | no | no | KEEP |
| `miniapp/js/02-art.js` | JavaScript/TypeScript | Telegram Mini App client or static asset. | 6908 | 4 | yes | no | no | no | no | KEEP |
| `miniapp/js/03-data.js` | JavaScript/TypeScript | Telegram Mini App client or static asset. | 14023 | 6 | yes | no | no | no | no | KEEP |
| `miniapp/js/05-app.js` | JavaScript/TypeScript | Telegram Mini App client or static asset. | 25376 | 8 | yes | no | no | no | no | KEEP |
| `miniapp/js/06-home.js` | JavaScript/TypeScript | Telegram Mini App client or static asset. | 18710 | 6 | yes | no | no | no | no | KEEP |
| `miniapp/js/07-chat.js` | JavaScript/TypeScript | Telegram Mini App client or static asset. | 41617 | 5 | yes | no | no | no | no | KEEP |
| `miniapp/js/08-widgets.js` | JavaScript/TypeScript | Telegram Mini App client or static asset. | 31475 | 4 | yes | no | no | no | no | KEEP |
| `miniapp/js/09-tarot.js` | JavaScript/TypeScript | Telegram Mini App client or static asset. | 13842 | 3 | yes | no | no | no | no | KEEP |
| `miniapp/js/10-chart.js` | JavaScript/TypeScript | Telegram Mini App client or static asset. | 23636 | 4 | yes | no | no | no | no | KEEP |
| `miniapp/js/11-compat.js` | JavaScript/TypeScript | Telegram Mini App client or static asset. | 13680 | 3 | yes | no | no | no | no | KEEP |
| `miniapp/js/12-misc.js` | JavaScript/TypeScript | Telegram Mini App client or static asset. | 50015 | 7 | yes | no | no | no | no | KEEP |
| `miniapp/js/13-events.js` | JavaScript/TypeScript | Telegram Mini App client or static asset. | 1353 | 5 | yes | no | no | no | no | KEEP |
| `miniapp/js/13-palm.js` | JavaScript/TypeScript | Telegram Mini App client or static asset. | 12646 | 3 | yes | no | no | no | no | KEEP |
| `miniapp/js/14-gestures.js` | JavaScript/TypeScript | Telegram Mini App client or static asset. | 4479 | 3 | yes | no | no | no | no | KEEP |
| `miniapp/js/14-products.js` | JavaScript/TypeScript | Telegram Mini App client or static asset. | 15904 | 4 | yes | no | no | no | no | KEEP |
| `miniapp/js/15-actions.js` | JavaScript/TypeScript | Telegram Mini App client or static asset. | 5682 | 8 | yes | no | no | no | no | KEEP |
| `miniapp/js/16-placements.js` | JavaScript/TypeScript | Telegram Mini App client or static asset. | 10708 | 4 | yes | no | no | no | no | KEEP |
| `miniapp/js/17-payments.js` | JavaScript/TypeScript | Telegram Mini App client or static asset. | 18721 | 8 | yes | no | no | no | no | KEEP |
| `miniapp/styles.css` | CSS | Telegram Mini App client or static asset. | 1524 | 8 | yes | no | no | no | no | KEEP |
| `models/THIRD_PARTY_NOTICES.md` | Markdown | Vendored model or provenance notice. | 1614 | 3 | yes | no | no | no | no | KEEP |
| `models/hand_landmarker.task` | Asset/model | Vendored model or provenance notice. | 7819105 | 2 | yes | no | no | no | no | KEEP |
| `models/palm_line_student_fp16.onnx` | Asset/model | Vendored model or provenance notice. | 11284720 | 3 | yes | no | no | no | no | KEEP |
| `models/palm_line_student_int8.onnx` | Asset/model | Vendored model or provenance notice. | 5904771 | 1 | yes | no | no | no | no | KEEP |
| `prompts/images-pack-a.txt` | Text | Image prompt source material. | 1539 | 1 | yes | no | no | no | no | KEEP |
| `prompts/images-pack-b.txt` | Text | Image prompt source material. | 1844 | 1 | yes | no | no | no | no | KEEP |
| `prompts/images-pack-c.txt` | Text | Image prompt source material. | 1986 | 1 | yes | no | no | no | no | KEEP |
| `prompts/images-pack-d.txt` | Text | Image prompt source material. | 1996 | 1 | yes | no | no | no | no | KEEP |
| `prompts/images-pack-e.txt` | Text | Image prompt source material. | 2151 | 1 | yes | no | no | no | no | KEEP |
| `pytest.ini` | Other | Other repository file. | 277 | 1 | yes | no | no | no | no | KEEP |
| `requirements-dev.txt` | Text | Text repository file. | 352 | 7 | yes | no | no | no | no | KEEP |
| `requirements.txt` | Text | Text repository file. | 1930 | 10 | yes | no | no | no | no | KEEP |
| `scripts/__pycache__/benchmark_mira_lenormand.cpython-312.pyc` | Other | Operational, QA, benchmark or release script. | 4596 | 1 | yes | no | yes | no | no | KEEP |
| `scripts/__pycache__/benchmark_palm_cv.cpython-312.pyc` | Other | Operational, QA, benchmark or release script. | 3607 | 1 | yes | no | yes | no | no | KEEP |
| `scripts/__pycache__/benchmark_product_performance.cpython-312.pyc` | Other | Operational, QA, benchmark or release script. | 9040 | 1 | yes | no | yes | no | no | KEEP |
| `scripts/__pycache__/benchmark_skill_routing.cpython-312.pyc` | Other | Operational, QA, benchmark or release script. | 3747 | 1 | yes | no | yes | no | no | KEEP |
| `scripts/__pycache__/benchmark_vedic_routing.cpython-312.pyc` | Other | Operational, QA, benchmark or release script. | 3335 | 1 | yes | no | yes | no | no | KEEP |
| `scripts/__pycache__/build_skill_manifests.cpython-312.pyc` | Other | Operational, QA, benchmark or release script. | 2322 | 1 | yes | no | no | no | no | KEEP |
| `scripts/__pycache__/capture_visual_baseline.cpython-312.pyc` | Other | Operational, QA, benchmark or release script. | 10433 | 1 | yes | no | yes | no | no | KEEP |
| `scripts/__pycache__/celery_smoke.cpython-312.pyc` | Other | Operational, QA, benchmark or release script. | 2626 | 1 | yes | no | no | no | no | KEEP |
| `scripts/__pycache__/check_agent_context_contracts.cpython-312.pyc` | Other | Operational, QA, benchmark or release script. | 3226 | 1 | yes | no | no | no | no | KEEP |
| `scripts/__pycache__/check_agent_quality.cpython-312.pyc` | Other | Operational, QA, benchmark or release script. | 10210 | 1 | yes | no | no | no | no | KEEP |
| `scripts/__pycache__/check_agent_stability.cpython-312.pyc` | Other | Operational, QA, benchmark or release script. | 3293 | 1 | yes | no | no | no | no | KEEP |
| `scripts/__pycache__/check_backup_restore_drill.cpython-312.pyc` | Other | Operational, QA, benchmark or release script. | 4627 | 1 | yes | no | no | no | no | KEEP |
| `scripts/__pycache__/check_cache_busting.cpython-312.pyc` | Other | Operational, QA, benchmark or release script. | 2684 | 1 | yes | no | no | no | no | KEEP |
| `scripts/__pycache__/check_design_contract.cpython-312.pyc` | Other | Operational, QA, benchmark or release script. | 5028 | 1 | yes | no | no | no | no | KEEP |
| `scripts/__pycache__/check_domain_evals.cpython-312.pyc` | Other | Operational, QA, benchmark or release script. | 2673 | 1 | yes | no | no | no | no | KEEP |
| `scripts/__pycache__/check_expanded_chart.cpython-312.pyc` | Other | Operational, QA, benchmark or release script. | 1792 | 1 | yes | no | no | no | no | KEEP |
| `scripts/__pycache__/check_p2_quality.cpython-312.pyc` | Other | Operational, QA, benchmark or release script. | 11460 | 1 | yes | no | no | no | no | KEEP |
| `scripts/__pycache__/check_pdf_golden_cases.cpython-312.pyc` | Other | Operational, QA, benchmark or release script. | 4976 | 1 | yes | no | no | yes | no | REVIEW |
| `scripts/__pycache__/check_repository_hygiene.cpython-312.pyc` | Other | Operational, QA, benchmark or release script. | 3197 | 1 | yes | no | no | no | no | KEEP |
| `scripts/__pycache__/check_visual_contrast.cpython-312.pyc` | Other | Operational, QA, benchmark or release script. | 6181 | 1 | yes | no | no | no | no | KEEP |
| `scripts/__pycache__/db_health_report.cpython-312.pyc` | Other | Operational, QA, benchmark or release script. | 4780 | 1 | yes | no | yes | no | no | KEEP |
| `scripts/__pycache__/desktop_layout_audit.cpython-312.pyc` | Other | Operational, QA, benchmark or release script. | 4815 | 1 | yes | no | no | no | no | KEEP |
| `scripts/__pycache__/domain_qa.cpython-312.pyc` | Other | Operational, QA, benchmark or release script. | 13466 | 1 | yes | no | no | no | no | KEEP |
| `scripts/__pycache__/evaluate_llm.cpython-312.pyc` | Other | Operational, QA, benchmark or release script. | 12427 | 1 | yes | no | no | no | no | KEEP |
| `scripts/__pycache__/evaluate_memory.cpython-312.pyc` | Other | Operational, QA, benchmark or release script. | 7443 | 1 | yes | no | no | no | no | KEEP |
| `scripts/__pycache__/expand_domain_evals.cpython-312.pyc` | Other | Operational, QA, benchmark or release script. | 7913 | 1 | yes | no | no | no | no | KEEP |
| `scripts/__pycache__/expand_skill_library.cpython-312.pyc` | Other | Operational, QA, benchmark or release script. | 12463 | 1 | yes | no | no | no | no | KEEP |
| `scripts/__pycache__/export_tarot_knowledge.cpython-312.pyc` | Other | Operational, QA, benchmark or release script. | 2290 | 1 | yes | no | no | no | no | KEEP |
| `scripts/__pycache__/final_prompt_cleanup.cpython-312.pyc` | Other | Operational, QA, benchmark or release script. | 4574 | 1 | yes | no | no | no | no | KEEP |
| `scripts/__pycache__/gen_pdf.cpython-312.pyc` | Other | Operational, QA, benchmark or release script. | 13575 | 1 | yes | no | no | no | no | KEEP |
| `scripts/__pycache__/gen_promo.cpython-312.pyc` | Other | Operational, QA, benchmark or release script. | 5335 | 1 | yes | no | no | no | no | KEEP |
| `scripts/__pycache__/generate_eval_set.cpython-312.pyc` | Other | Operational, QA, benchmark or release script. | 13576 | 1 | yes | no | no | no | no | KEEP |
| `scripts/__pycache__/healthcheck.cpython-312.pyc` | Other | Operational, QA, benchmark or release script. | 2461 | 1 | yes | no | no | no | no | KEEP |
| `scripts/__pycache__/migrate_agent_profiles.cpython-312.pyc` | Other | Operational, QA, benchmark or release script. | 14479 | 1 | yes | no | no | no | no | KEEP |
| `scripts/__pycache__/migrate_sqlite_to_postgres.cpython-312.pyc` | Other | Operational, QA, benchmark or release script. | 8651 | 1 | yes | no | no | no | no | KEEP |
| `scripts/__pycache__/migration_manifest.cpython-312.pyc` | Other | Operational, QA, benchmark or release script. | 3487 | 1 | yes | no | no | no | no | KEEP |
| `scripts/__pycache__/new_agent_skill.cpython-312.pyc` | Other | Operational, QA, benchmark or release script. | 4686 | 1 | yes | no | no | no | no | KEEP |
| `scripts/__pycache__/ops_alerts.cpython-312.pyc` | Other | Operational, QA, benchmark or release script. | 9072 | 1 | yes | no | no | no | no | KEEP |
| `scripts/__pycache__/pdf_matrix.cpython-312.pyc` | Other | Operational, QA, benchmark or release script. | 7820 | 1 | yes | no | no | no | no | KEEP |
| `scripts/__pycache__/release_gate.cpython-312.pyc` | Other | Operational, QA, benchmark or release script. | 5275 | 1 | yes | no | no | no | no | KEEP |
| `scripts/__pycache__/rewrite_tov.cpython-312.pyc` | Other | Operational, QA, benchmark or release script. | 11111 | 1 | yes | no | no | no | no | KEEP |
| `scripts/__pycache__/run_api.cpython-312.pyc` | Other | Operational, QA, benchmark or release script. | 1196 | 1 | yes | no | no | no | no | KEEP |
| `scripts/__pycache__/run_llm_eval_live.cpython-312.pyc` | Other | Operational, QA, benchmark or release script. | 15965 | 1 | yes | no | no | no | no | KEEP |
| `scripts/__pycache__/seed_load.cpython-312.pyc` | Other | Operational, QA, benchmark or release script. | 8736 | 1 | yes | no | no | no | no | KEEP |
| `scripts/__pycache__/seed_visual_user.cpython-312.pyc` | Other | Operational, QA, benchmark or release script. | 3344 | 1 | yes | no | no | no | no | KEEP |
| `scripts/__pycache__/selfcheck.cpython-312.pyc` | Other | Operational, QA, benchmark or release script. | 35830 | 1 | yes | no | no | no | no | KEEP |
| `scripts/__pycache__/standards_audit.cpython-312.pyc` | Other | Operational, QA, benchmark or release script. | 7131 | 1 | yes | no | no | no | no | KEEP |
| `scripts/__pycache__/summarize_standards_audit.cpython-312.pyc` | Other | Operational, QA, benchmark or release script. | 2353 | 1 | yes | no | no | no | no | KEEP |
| `scripts/__pycache__/summarize_visual_qa.cpython-312.pyc` | Other | Operational, QA, benchmark or release script. | 1004 | 1 | yes | no | no | no | no | KEEP |
| `scripts/__pycache__/validate_monetization_assumptions.cpython-312.pyc` | Other | Operational, QA, benchmark or release script. | 4670 | 1 | yes | no | no | no | no | KEEP |
| `scripts/__pycache__/validate_skill_library.cpython-312.pyc` | Other | Operational, QA, benchmark or release script. | 2804 | 1 | yes | no | no | no | no | KEEP |
| `scripts/__pycache__/visual_qa_capture.cpython-312.pyc` | Other | Operational, QA, benchmark or release script. | 7627 | 1 | yes | no | no | no | no | KEEP |
| `scripts/backup_db.sh` | Shell | Operational, QA, benchmark or release script. | 3269 | 2 | yes | yes | no | no | no | KEEP |
| `scripts/benchmark_mira_lenormand.py` | Python | Operational, QA, benchmark or release script. | 4049 | 4 | yes | no | yes | no | no | KEEP |
| `scripts/benchmark_palm_cv.py` | Python | Operational, QA, benchmark or release script. | 2606 | 4 | yes | no | yes | no | no | KEEP |
| `scripts/benchmark_product_performance.py` | Python | Operational, QA, benchmark or release script. | 5171 | 7 | yes | no | yes | no | no | KEEP |
| `scripts/benchmark_skill_routing.py` | Python | Operational, QA, benchmark or release script. | 3318 | 2 | yes | no | yes | no | no | KEEP |
| `scripts/benchmark_vedic_routing.py` | Python | Operational, QA, benchmark or release script. | 1958 | 4 | yes | no | yes | no | no | KEEP |
| `scripts/build_skill_manifests.py` | Python | Operational, QA, benchmark or release script. | 1372 | 3 | yes | no | no | no | no | KEEP |
| `scripts/capture_visual_baseline.py` | Python | Operational, QA, benchmark or release script. | 8449 | 5 | yes | no | yes | no | no | KEEP |
| `scripts/celery_smoke.py` | Python | Operational, QA, benchmark or release script. | 1363 | 3 | yes | no | no | no | no | KEEP |
| `scripts/check_agent_context_contracts.py` | Python | Operational, QA, benchmark or release script. | 2512 | 2 | yes | no | no | no | no | KEEP |
| `scripts/check_agent_quality.py` | Python | Operational, QA, benchmark or release script. | 7093 | 5 | yes | no | no | no | no | KEEP |
| `scripts/check_agent_stability.py` | Python | Operational, QA, benchmark or release script. | 1810 | 5 | yes | no | no | no | no | KEEP |
| `scripts/check_backup_restore_drill.py` | Python | Operational, QA, benchmark or release script. | 2950 | 7 | yes | no | no | no | no | KEEP |
| `scripts/check_cache_busting.py` | Python | Operational, QA, benchmark or release script. | 1957 | 4 | yes | no | no | no | no | KEEP |
| `scripts/check_design_contract.py` | Python | Operational, QA, benchmark or release script. | 3671 | 7 | yes | no | no | no | no | KEEP |
| `scripts/check_domain_evals.py` | Python | Operational, QA, benchmark or release script. | 1674 | 5 | yes | no | no | no | no | KEEP |
| `scripts/check_expanded_chart.py` | Python | Operational, QA, benchmark or release script. | 856 | 3 | yes | no | no | no | no | KEEP |
| `scripts/check_p2_quality.py` | Python | Operational, QA, benchmark or release script. | 7474 | 4 | yes | no | no | no | no | KEEP |
| `scripts/check_pdf_golden_cases.py` | Python | Operational, QA, benchmark or release script. | 3346 | 5 | yes | no | no | yes | no | REVIEW |
| `scripts/check_repository_hygiene.py` | Python | Operational, QA, benchmark or release script. | 2100 | 8 | yes | no | no | no | no | KEEP |
| `scripts/check_visual_contrast.py` | Python | Operational, QA, benchmark or release script. | 4004 | 7 | yes | no | no | no | no | KEEP |
| `scripts/db_health_report.py` | Python | Operational, QA, benchmark or release script. | 2698 | 3 | yes | no | yes | no | no | KEEP |
| `scripts/desktop_layout_audit.py` | Python | Operational, QA, benchmark or release script. | 3483 | 2 | yes | no | no | no | no | KEEP |
| `scripts/domain_qa.py` | Python | Operational, QA, benchmark or release script. | 9874 | 5 | yes | no | no | no | no | KEEP |
| `scripts/evaluate_llm.py` | Python | Operational, QA, benchmark or release script. | 7714 | 5 | yes | no | no | no | no | KEEP |
| `scripts/evaluate_memory.py` | Python | Operational, QA, benchmark or release script. | 5129 | 4 | yes | no | no | no | no | KEEP |
| `scripts/expand_domain_evals.py` | Python | Operational, QA, benchmark or release script. | 7876 | 2 | yes | no | no | no | no | KEEP |
| `scripts/expand_skill_library.py` | Python | Operational, QA, benchmark or release script. | 12349 | 2 | yes | no | no | no | no | KEEP |
| `scripts/export_tarot_knowledge.py` | Python | Operational, QA, benchmark or release script. | 1412 | 2 | yes | no | no | no | no | KEEP |
| `scripts/final_prompt_cleanup.py` | Python | Operational, QA, benchmark or release script. | 3811 | 2 | yes | no | no | no | no | KEEP |
| `scripts/gen_pdf.py` | Python | Operational, QA, benchmark or release script. | 8537 | 2 | yes | no | no | no | no | KEEP |
| `scripts/gen_promo.py` | Python | Operational, QA, benchmark or release script. | 3511 | 2 | yes | no | no | no | no | KEEP |
| `scripts/generate_eval_set.py` | Python | Operational, QA, benchmark or release script. | 11904 | 4 | yes | no | no | no | no | KEEP |
| `scripts/healthcheck.py` | Python | Operational, QA, benchmark or release script. | 1672 | 3 | yes | no | no | no | no | KEEP |
| `scripts/migrate_agent_profiles.py` | Python | Operational, QA, benchmark or release script. | 12940 | 2 | yes | no | no | no | no | KEEP |
| `scripts/migrate_sqlite_to_postgres.py` | Python | Operational, QA, benchmark or release script. | 4656 | 3 | yes | no | no | no | no | KEEP |
| `scripts/migration_manifest.py` | Python | Operational, QA, benchmark or release script. | 1904 | 3 | yes | no | no | no | no | KEEP |
| `scripts/new_agent_skill.py` | Python | Operational, QA, benchmark or release script. | 3305 | 3 | yes | no | no | no | no | KEEP |
| `scripts/ops_alerts.py` | Python | Operational, QA, benchmark or release script. | 6291 | 3 | yes | no | no | no | no | KEEP |
| `scripts/pdf_matrix.py` | Python | Operational, QA, benchmark or release script. | 5255 | 3 | yes | no | no | no | no | KEEP |
| `scripts/release_gate.py` | Python | Operational, QA, benchmark or release script. | 3015 | 10 | yes | no | no | no | no | KEEP |
| `scripts/restore_db.sh` | Shell | Operational, QA, benchmark or release script. | 1634 | 4 | yes | yes | no | no | no | KEEP |
| `scripts/rewrite_tov.py` | Python | Operational, QA, benchmark or release script. | 10862 | 2 | yes | no | no | no | no | KEEP |
| `scripts/run_api.py` | Python | Operational, QA, benchmark or release script. | 761 | 2 | yes | no | no | no | no | KEEP |
| `scripts/run_axe_core.mjs` | Other | Operational, QA, benchmark or release script. | 2753 | 1 | yes | no | no | no | no | KEEP |
| `scripts/run_lighthouse_axe.mjs` | Other | Operational, QA, benchmark or release script. | 5174 | 1 | yes | no | no | no | no | KEEP |
| `scripts/run_llm_eval_live.py` | Python | Operational, QA, benchmark or release script. | 10187 | 4 | yes | no | no | no | no | KEEP |
| `scripts/seed_load.py` | Python | Operational, QA, benchmark or release script. | 5991 | 6 | yes | no | no | no | no | KEEP |
| `scripts/seed_visual_user.py` | Python | Operational, QA, benchmark or release script. | 1860 | 4 | yes | no | no | no | no | KEEP |
| `scripts/selfcheck.py` | Python | Operational, QA, benchmark or release script. | 23843 | 6 | yes | no | no | no | no | KEEP |
| `scripts/standards_audit.py` | Python | Operational, QA, benchmark or release script. | 5803 | 2 | yes | no | no | no | no | KEEP |
| `scripts/summarize_standards_audit.py` | Python | Operational, QA, benchmark or release script. | 1216 | 2 | yes | no | no | no | no | KEEP |
| `scripts/summarize_visual_qa.py` | Python | Operational, QA, benchmark or release script. | 482 | 2 | yes | no | no | no | no | KEEP |
| `scripts/validate_monetization_assumptions.py` | Python | Operational, QA, benchmark or release script. | 3238 | 2 | yes | no | no | no | no | KEEP |
| `scripts/validate_skill_library.py` | Python | Operational, QA, benchmark or release script. | 1358 | 6 | yes | no | no | no | no | KEEP |
| `scripts/visual_qa_capture.py` | Python | Operational, QA, benchmark or release script. | 6217 | 6 | yes | no | no | no | no | KEEP |
| `tests/__pycache__/conftest.cpython-312-pytest-9.1.1.pyc` | Other | Automated test or reproducible fixture. | 5694 | 1 | yes | no | no | no | no | KEEP |
| `tests/__pycache__/conftest.cpython-312.pyc` | Other | Automated test or reproducible fixture. | 5056 | 1 | yes | no | no | no | no | KEEP |
| `tests/__pycache__/test_agent_context.cpython-312-pytest-9.1.1.pyc` | Other | Automated test or reproducible fixture. | 19598 | 1 | yes | no | no | no | no | KEEP |
| `tests/__pycache__/test_agent_context.cpython-312.pyc` | Other | Automated test or reproducible fixture. | 6340 | 1 | yes | no | no | no | no | KEEP |
| `tests/__pycache__/test_agent_context_integrity.cpython-312-pytest-9.1.1.pyc` | Other | Automated test or reproducible fixture. | 22045 | 1 | yes | no | no | no | no | KEEP |
| `tests/__pycache__/test_agent_context_integrity.cpython-312.pyc` | Other | Automated test or reproducible fixture. | 7676 | 1 | yes | no | no | no | no | KEEP |
| `tests/__pycache__/test_agent_file_harness.cpython-312-pytest-9.1.1.pyc` | Other | Automated test or reproducible fixture. | 44863 | 1 | yes | no | no | no | no | KEEP |
| `tests/__pycache__/test_agent_file_harness.cpython-312.pyc` | Other | Automated test or reproducible fixture. | 11747 | 1 | yes | no | no | no | no | KEEP |
| `tests/__pycache__/test_agent_routing.cpython-312-pytest-9.1.1.pyc` | Other | Automated test or reproducible fixture. | 10611 | 1 | yes | no | no | no | no | KEEP |
| `tests/__pycache__/test_agent_routing.cpython-312.pyc` | Other | Automated test or reproducible fixture. | 2775 | 1 | yes | no | no | no | no | KEEP |
| `tests/__pycache__/test_analytics.cpython-312-pytest-9.1.1.pyc` | Other | Automated test or reproducible fixture. | 14363 | 1 | yes | no | no | no | no | KEEP |
| `tests/__pycache__/test_analytics.cpython-312.pyc` | Other | Automated test or reproducible fixture. | 8837 | 1 | yes | no | no | no | no | KEEP |
| `tests/__pycache__/test_api.cpython-312-pytest-9.1.1.pyc` | Other | Automated test or reproducible fixture. | 218707 | 1 | yes | no | no | no | no | KEEP |
| `tests/__pycache__/test_api.cpython-312.pyc` | Other | Automated test or reproducible fixture. | 79657 | 1 | yes | no | no | no | no | KEEP |
| `tests/__pycache__/test_api_chart_products.cpython-312-pytest-9.1.1.pyc` | Other | Automated test or reproducible fixture. | 34706 | 1 | yes | no | no | no | no | KEEP |
| `tests/__pycache__/test_api_chart_products.cpython-312.pyc` | Other | Automated test or reproducible fixture. | 12890 | 1 | yes | no | no | no | no | KEEP |
| `tests/__pycache__/test_api_growth.cpython-312-pytest-9.1.1.pyc` | Other | Automated test or reproducible fixture. | 53053 | 1 | yes | no | no | no | no | KEEP |
| `tests/__pycache__/test_api_growth.cpython-312.pyc` | Other | Automated test or reproducible fixture. | 22855 | 1 | yes | no | no | no | no | KEEP |
| `tests/__pycache__/test_api_resilience.cpython-312-pytest-9.1.1.pyc` | Other | Automated test or reproducible fixture. | 12421 | 1 | yes | no | no | no | no | KEEP |
| `tests/__pycache__/test_api_resilience.cpython-312.pyc` | Other | Automated test or reproducible fixture. | 5338 | 1 | yes | no | no | no | no | KEEP |
| `tests/__pycache__/test_architecture_boundaries.cpython-312-pytest-9.1.1.pyc` | Other | Automated test or reproducible fixture. | 12013 | 1 | yes | no | no | no | no | KEEP |
| `tests/__pycache__/test_architecture_boundaries.cpython-312.pyc` | Other | Automated test or reproducible fixture. | 5260 | 1 | yes | no | no | no | no | KEEP |
| `tests/__pycache__/test_billing.cpython-312-pytest-9.1.1.pyc` | Other | Automated test or reproducible fixture. | 62747 | 1 | yes | no | no | no | no | KEEP |
| `tests/__pycache__/test_billing.cpython-312.pyc` | Other | Automated test or reproducible fixture. | 31384 | 1 | yes | no | no | no | no | KEEP |
| `tests/__pycache__/test_bot_fsm.cpython-312-pytest-9.1.1.pyc` | Other | Automated test or reproducible fixture. | 22122 | 1 | yes | no | no | no | no | KEEP |
| `tests/__pycache__/test_bot_fsm.cpython-312.pyc` | Other | Automated test or reproducible fixture. | 11526 | 1 | yes | no | no | no | no | KEEP |
| `tests/__pycache__/test_broadcast.cpython-312-pytest-9.1.1.pyc` | Other | Automated test or reproducible fixture. | 11685 | 1 | yes | no | no | no | no | KEEP |
| `tests/__pycache__/test_broadcast.cpython-312.pyc` | Other | Automated test or reproducible fixture. | 7120 | 1 | yes | no | no | no | no | KEEP |
| `tests/__pycache__/test_chart_contract.cpython-312-pytest-9.1.1.pyc` | Other | Automated test or reproducible fixture. | 19860 | 1 | yes | no | no | no | no | KEEP |
| `tests/__pycache__/test_chart_contract.cpython-312.pyc` | Other | Automated test or reproducible fixture. | 6494 | 1 | yes | no | no | no | no | KEEP |
| `tests/__pycache__/test_chart_interpretation.cpython-312-pytest-9.1.1.pyc` | Other | Automated test or reproducible fixture. | 13358 | 1 | yes | no | no | no | no | KEEP |
| `tests/__pycache__/test_chart_interpretation.cpython-312.pyc` | Other | Automated test or reproducible fixture. | 8306 | 1 | yes | no | no | no | no | KEEP |
| `tests/__pycache__/test_chart_products.cpython-312-pytest-9.1.1.pyc` | Other | Automated test or reproducible fixture. | 38753 | 1 | yes | no | no | no | no | KEEP |
| `tests/__pycache__/test_chart_products.cpython-312.pyc` | Other | Automated test or reproducible fixture. | 13416 | 1 | yes | no | no | no | no | KEEP |
| `tests/__pycache__/test_content_localization.cpython-312-pytest-9.1.1.pyc` | Other | Automated test or reproducible fixture. | 5491 | 1 | yes | no | no | no | no | KEEP |
| `tests/__pycache__/test_content_localization.cpython-312.pyc` | Other | Automated test or reproducible fixture. | 2798 | 1 | yes | no | no | no | no | KEEP |
| `tests/__pycache__/test_core.cpython-312-pytest-9.1.1.pyc` | Other | Automated test or reproducible fixture. | 79410 | 1 | yes | no | no | no | no | KEEP |
| `tests/__pycache__/test_core.cpython-312.pyc` | Other | Automated test or reproducible fixture. | 25110 | 1 | yes | no | no | no | no | KEEP |
| `tests/__pycache__/test_data.cpython-312-pytest-9.1.1.pyc` | Other | Automated test or reproducible fixture. | 42141 | 1 | yes | no | no | no | no | KEEP |
| `tests/__pycache__/test_data.cpython-312.pyc` | Other | Automated test or reproducible fixture. | 23713 | 1 | yes | no | no | no | no | KEEP |
| `tests/__pycache__/test_diary.cpython-312-pytest-9.1.1.pyc` | Other | Automated test or reproducible fixture. | 12454 | 1 | yes | no | no | no | no | KEEP |
| `tests/__pycache__/test_diary.cpython-312.pyc` | Other | Automated test or reproducible fixture. | 6558 | 1 | yes | no | no | no | no | KEEP |
| `tests/__pycache__/test_domain_qa.cpython-312-pytest-9.1.1.pyc` | Other | Automated test or reproducible fixture. | 9578 | 1 | yes | no | no | no | no | KEEP |
| `tests/__pycache__/test_domain_qa.cpython-312.pyc` | Other | Automated test or reproducible fixture. | 3367 | 1 | yes | no | no | no | no | KEEP |
| `tests/__pycache__/test_flood.cpython-312-pytest-9.1.1.pyc` | Other | Automated test or reproducible fixture. | 9198 | 1 | yes | no | no | no | no | KEEP |
| `tests/__pycache__/test_flood.cpython-312.pyc` | Other | Automated test or reproducible fixture. | 5810 | 1 | yes | no | no | no | no | KEEP |
| `tests/__pycache__/test_growth.cpython-312-pytest-9.1.1.pyc` | Other | Automated test or reproducible fixture. | 65902 | 1 | yes | no | no | no | no | KEEP |
| `tests/__pycache__/test_growth.cpython-312.pyc` | Other | Automated test or reproducible fixture. | 24709 | 1 | yes | no | no | no | no | KEEP |
| `tests/__pycache__/test_interpretation_guardrails.cpython-312-pytest-9.1.1.pyc` | Other | Automated test or reproducible fixture. | 11230 | 1 | yes | no | no | no | no | KEEP |
| `tests/__pycache__/test_interpretation_guardrails.cpython-312.pyc` | Other | Automated test or reproducible fixture. | 5073 | 1 | yes | no | no | no | no | KEEP |
| `tests/__pycache__/test_jobs.cpython-312-pytest-9.1.1.pyc` | Other | Automated test or reproducible fixture. | 28189 | 1 | yes | no | no | no | no | KEEP |
| `tests/__pycache__/test_jobs.cpython-312.pyc` | Other | Automated test or reproducible fixture. | 11976 | 1 | yes | no | no | no | no | KEEP |
| `tests/__pycache__/test_limits.cpython-312-pytest-9.1.1.pyc` | Other | Automated test or reproducible fixture. | 47580 | 1 | yes | no | no | no | no | KEEP |
| `tests/__pycache__/test_limits.cpython-312.pyc` | Other | Automated test or reproducible fixture. | 21216 | 1 | yes | no | no | no | no | KEEP |
| `tests/__pycache__/test_live_llm_runner.cpython-312-pytest-9.1.1.pyc` | Other | Automated test or reproducible fixture. | 4344 | 1 | yes | no | no | no | no | KEEP |
| `tests/__pycache__/test_live_llm_runner.cpython-312.pyc` | Other | Automated test or reproducible fixture. | 1437 | 1 | yes | no | no | no | no | KEEP |
| `tests/__pycache__/test_llm.cpython-312-pytest-9.1.1.pyc` | Other | Automated test or reproducible fixture. | 25541 | 1 | yes | no | no | no | no | KEEP |
| `tests/__pycache__/test_llm.cpython-312.pyc` | Other | Automated test or reproducible fixture. | 14404 | 1 | yes | no | no | no | no | KEEP |
| `tests/__pycache__/test_llm_evaluation.cpython-312-pytest-9.1.1.pyc` | Other | Automated test or reproducible fixture. | 7210 | 1 | yes | no | no | no | no | KEEP |
| `tests/__pycache__/test_llm_evaluation.cpython-312.pyc` | Other | Automated test or reproducible fixture. | 3036 | 1 | yes | no | no | no | no | KEEP |
| `tests/__pycache__/test_memory_evaluation.cpython-312-pytest-9.1.1.pyc` | Other | Automated test or reproducible fixture. | 9384 | 1 | yes | no | no | no | no | KEEP |
| `tests/__pycache__/test_memory_evaluation.cpython-312.pyc` | Other | Automated test or reproducible fixture. | 3878 | 1 | yes | no | no | no | no | KEEP |
| `tests/__pycache__/test_migrations.cpython-312-pytest-9.1.1.pyc` | Other | Automated test or reproducible fixture. | 24135 | 1 | yes | no | no | no | no | KEEP |
| `tests/__pycache__/test_migrations.cpython-312.pyc` | Other | Automated test or reproducible fixture. | 13627 | 1 | yes | no | no | no | no | KEEP |
| `tests/__pycache__/test_miniapp_actions.cpython-312-pytest-9.1.1.pyc` | Other | Automated test or reproducible fixture. | 42817 | 1 | yes | no | no | no | no | KEEP |
| `tests/__pycache__/test_miniapp_actions.cpython-312.pyc` | Other | Automated test or reproducible fixture. | 12111 | 1 | yes | no | no | no | no | KEEP |
| `tests/__pycache__/test_monetization_phase_a.cpython-312-pytest-9.1.1.pyc` | Other | Automated test or reproducible fixture. | 27520 | 1 | yes | no | no | no | no | KEEP |
| `tests/__pycache__/test_monetization_phase_a.cpython-312.pyc` | Other | Automated test or reproducible fixture. | 13676 | 1 | yes | no | no | no | no | KEEP |
| `tests/__pycache__/test_natal_sections.cpython-312-pytest-9.1.1.pyc` | Other | Automated test or reproducible fixture. | 19641 | 1 | yes | no | no | no | no | KEEP |
| `tests/__pycache__/test_natal_sections.cpython-312.pyc` | Other | Automated test or reproducible fixture. | 10414 | 1 | yes | no | no | no | no | KEEP |
| `tests/__pycache__/test_openai_compat.cpython-312-pytest-9.1.1.pyc` | Other | Automated test or reproducible fixture. | 35911 | 1 | yes | no | no | no | no | KEEP |
| `tests/__pycache__/test_openai_compat.cpython-312.pyc` | Other | Automated test or reproducible fixture. | 23745 | 1 | yes | no | no | no | no | KEEP |
| `tests/__pycache__/test_p1_controls.cpython-312-pytest-9.1.1.pyc` | Other | Automated test or reproducible fixture. | 9069 | 1 | yes | no | no | no | no | KEEP |
| `tests/__pycache__/test_p1_controls.cpython-312.pyc` | Other | Automated test or reproducible fixture. | 3490 | 1 | yes | no | no | no | no | KEEP |
| `tests/__pycache__/test_p2_contracts.cpython-312-pytest-9.1.1.pyc` | Other | Automated test or reproducible fixture. | 6710 | 1 | yes | no | no | no | no | KEEP |
| `tests/__pycache__/test_p2_contracts.cpython-312.pyc` | Other | Automated test or reproducible fixture. | 2702 | 1 | yes | no | no | no | no | KEEP |
| `tests/__pycache__/test_palm_integration.cpython-312-pytest-9.1.1.pyc` | Other | Automated test or reproducible fixture. | 59984 | 1 | yes | no | no | no | no | KEEP |
| `tests/__pycache__/test_palm_integration.cpython-312.pyc` | Other | Automated test or reproducible fixture. | 21774 | 1 | yes | no | no | no | no | KEEP |
| `tests/__pycache__/test_palm_vision.cpython-312-pytest-9.1.1.pyc` | Other | Automated test or reproducible fixture. | 12314 | 1 | yes | no | no | no | no | KEEP |
| `tests/__pycache__/test_palm_vision.cpython-312.pyc` | Other | Automated test or reproducible fixture. | 4278 | 1 | yes | no | no | no | no | KEEP |
| `tests/__pycache__/test_payment_monitor.cpython-312-pytest-9.1.1.pyc` | Other | Automated test or reproducible fixture. | 20941 | 1 | yes | no | no | no | no | KEEP |
| `tests/__pycache__/test_payment_monitor.cpython-312.pyc` | Other | Automated test or reproducible fixture. | 7682 | 1 | yes | no | no | no | no | KEEP |
| `tests/__pycache__/test_pdf_matrix.cpython-312-pytest-9.1.1.pyc` | Other | Automated test or reproducible fixture. | 4901 | 1 | yes | no | no | no | no | KEEP |
| `tests/__pycache__/test_pdf_matrix.cpython-312.pyc` | Other | Automated test or reproducible fixture. | 2098 | 1 | yes | no | no | no | no | KEEP |
| `tests/__pycache__/test_pdfgen.cpython-312-pytest-9.1.1.pyc` | Other | Automated test or reproducible fixture. | 45413 | 1 | yes | no | no | no | no | KEEP |
| `tests/__pycache__/test_pdfgen.cpython-312.pyc` | Other | Automated test or reproducible fixture. | 9910 | 1 | yes | no | no | no | no | KEEP |
| `tests/__pycache__/test_placements_palm.cpython-312-pytest-9.1.1.pyc` | Other | Automated test or reproducible fixture. | 33719 | 1 | yes | no | no | no | no | KEEP |
| `tests/__pycache__/test_placements_palm.cpython-312.pyc` | Other | Automated test or reproducible fixture. | 9581 | 1 | yes | no | no | no | no | KEEP |
| `tests/__pycache__/test_postgres_adapter.cpython-312-pytest-9.1.1.pyc` | Other | Automated test or reproducible fixture. | 6350 | 1 | yes | no | no | no | no | KEEP |
| `tests/__pycache__/test_postgres_adapter.cpython-312.pyc` | Other | Automated test or reproducible fixture. | 2850 | 1 | yes | no | no | no | no | KEEP |
| `tests/__pycache__/test_practices.cpython-312-pytest-9.1.1.pyc` | Other | Automated test or reproducible fixture. | 34645 | 1 | yes | no | no | no | no | KEEP |
| `tests/__pycache__/test_practices.cpython-312.pyc` | Other | Automated test or reproducible fixture. | 16788 | 1 | yes | no | no | no | no | KEEP |
| `tests/__pycache__/test_release_gate.cpython-312-pytest-9.1.1.pyc` | Other | Automated test or reproducible fixture. | 5724 | 1 | yes | no | no | no | no | KEEP |
| `tests/__pycache__/test_release_gate.cpython-312.pyc` | Other | Automated test or reproducible fixture. | 1719 | 1 | yes | no | no | no | no | KEEP |
| `tests/__pycache__/test_report_history.cpython-312-pytest-9.1.1.pyc` | Other | Automated test or reproducible fixture. | 9001 | 1 | yes | no | yes | no | no | KEEP |
| `tests/__pycache__/test_report_history.cpython-312.pyc` | Other | Automated test or reproducible fixture. | 4595 | 1 | yes | no | yes | no | no | KEEP |
| `tests/__pycache__/test_safety.cpython-312-pytest-9.1.1.pyc` | Other | Automated test or reproducible fixture. | 17579 | 1 | yes | no | no | no | no | KEEP |
| `tests/__pycache__/test_safety.cpython-312.pyc` | Other | Automated test or reproducible fixture. | 6790 | 1 | yes | no | no | no | no | KEEP |
| `tests/__pycache__/test_scale_contract.cpython-312-pytest-9.1.1.pyc` | Other | Automated test or reproducible fixture. | 5769 | 1 | yes | no | no | no | no | KEEP |
| `tests/__pycache__/test_scale_contract.cpython-312.pyc` | Other | Automated test or reproducible fixture. | 2067 | 1 | yes | no | no | no | no | KEEP |
| `tests/__pycache__/test_scheduler.cpython-312-pytest-9.1.1.pyc` | Other | Automated test or reproducible fixture. | 36112 | 1 | yes | no | no | no | no | KEEP |
| `tests/__pycache__/test_scheduler.cpython-312.pyc` | Other | Automated test or reproducible fixture. | 20908 | 1 | yes | no | no | no | no | KEEP |
| `tests/__pycache__/test_security_regressions.cpython-312-pytest-9.1.1.pyc` | Other | Automated test or reproducible fixture. | 35731 | 1 | yes | no | no | no | no | KEEP |
| `tests/__pycache__/test_security_regressions.cpython-312.pyc` | Other | Automated test or reproducible fixture. | 15790 | 1 | yes | no | no | no | no | KEEP |
| `tests/__pycache__/test_session.cpython-312-pytest-9.1.1.pyc` | Other | Automated test or reproducible fixture. | 4370 | 1 | yes | no | no | no | no | KEEP |
| `tests/__pycache__/test_session.cpython-312.pyc` | Other | Automated test or reproducible fixture. | 3347 | 1 | yes | no | no | no | no | KEEP |
| `tests/__pycache__/test_shared_context.cpython-312-pytest-9.1.1.pyc` | Other | Automated test or reproducible fixture. | 13644 | 1 | yes | no | no | no | no | KEEP |
| `tests/__pycache__/test_shared_context.cpython-312.pyc` | Other | Automated test or reproducible fixture. | 5299 | 1 | yes | no | no | no | no | KEEP |
| `tests/__pycache__/test_stage0_operations.cpython-312-pytest-9.1.1.pyc` | Other | Automated test or reproducible fixture. | 12225 | 1 | yes | no | no | no | no | KEEP |
| `tests/__pycache__/test_stage0_operations.cpython-312.pyc` | Other | Automated test or reproducible fixture. | 4897 | 1 | yes | no | no | no | no | KEEP |
| `tests/__pycache__/test_tarot_contract.cpython-312-pytest-9.1.1.pyc` | Other | Automated test or reproducible fixture. | 10934 | 1 | yes | no | no | no | no | KEEP |
| `tests/__pycache__/test_tarot_contract.cpython-312.pyc` | Other | Automated test or reproducible fixture. | 3239 | 1 | yes | no | no | no | no | KEEP |
| `tests/__pycache__/test_vedic.cpython-312-pytest-9.1.1.pyc` | Other | Automated test or reproducible fixture. | 24841 | 1 | yes | no | no | no | no | KEEP |
| `tests/__pycache__/test_vedic.cpython-312.pyc` | Other | Automated test or reproducible fixture. | 7491 | 1 | yes | no | no | no | no | KEEP |
| `tests/conftest.py` | Python | Automated test or reproducible fixture. | 3372 | 3 | yes | no | no | no | no | KEEP |
| `tests/fixtures/palm/README.md` | Markdown | Automated test or reproducible fixture. | 909 | 1 | yes | no | no | no | no | KEEP |
| `tests/fixtures/palm/palm_hand.jpg` | Asset/model | Automated test or reproducible fixture. | 1581197 | 3 | yes | no | no | no | no | KEEP |
| `tests/test_agent_context.py` | Python | Automated test or reproducible fixture. | 4638 | 8 | yes | no | no | no | no | KEEP |
| `tests/test_agent_context_integrity.py` | Python | Automated test or reproducible fixture. | 5399 | 7 | yes | no | no | no | no | KEEP |
| `tests/test_agent_file_harness.py` | Python | Automated test or reproducible fixture. | 7826 | 5 | yes | no | no | no | no | KEEP |
| `tests/test_agent_routing.py` | Python | Automated test or reproducible fixture. | 1920 | 5 | yes | no | no | no | no | KEEP |
| `tests/test_analytics.py` | Python | Automated test or reproducible fixture. | 4658 | 4 | yes | no | no | no | no | KEEP |
| `tests/test_api.py` | Python | Automated test or reproducible fixture. | 46732 | 9 | yes | no | no | no | no | KEEP |
| `tests/test_api_chart_products.py` | Python | Automated test or reproducible fixture. | 8319 | 4 | yes | no | no | no | no | KEEP |
| `tests/test_api_growth.py` | Python | Automated test or reproducible fixture. | 15069 | 4 | yes | no | no | no | no | KEEP |
| `tests/test_api_resilience.py` | Python | Automated test or reproducible fixture. | 2587 | 7 | yes | no | no | no | no | KEEP |
| `tests/test_architecture_boundaries.py` | Python | Automated test or reproducible fixture. | 2949 | 5 | yes | no | no | no | no | KEEP |
| `tests/test_billing.py` | Python | Automated test or reproducible fixture. | 19222 | 6 | yes | no | no | no | no | KEEP |
| `tests/test_bot_fsm.py` | Python | Automated test or reproducible fixture. | 5580 | 4 | yes | no | no | no | no | KEEP |
| `tests/test_broadcast.py` | Python | Automated test or reproducible fixture. | 3599 | 4 | yes | no | no | no | no | KEEP |
| `tests/test_chart_contract.py` | Python | Automated test or reproducible fixture. | 4237 | 5 | yes | no | no | no | no | KEEP |
| `tests/test_chart_interpretation.py` | Python | Automated test or reproducible fixture. | 5872 | 4 | yes | no | no | no | no | KEEP |
| `tests/test_chart_products.py` | Python | Automated test or reproducible fixture. | 8382 | 6 | yes | no | no | no | no | KEEP |
| `tests/test_content_localization.py` | Python | Automated test or reproducible fixture. | 1574 | 4 | yes | no | no | no | no | KEEP |
| `tests/test_core.py` | Python | Automated test or reproducible fixture. | 15720 | 7 | yes | no | no | no | no | KEEP |
| `tests/test_data.py` | Python | Automated test or reproducible fixture. | 13716 | 7 | yes | no | no | no | no | KEEP |
| `tests/test_diary.py` | Python | Automated test or reproducible fixture. | 3618 | 4 | yes | no | no | no | no | KEEP |
| `tests/test_domain_qa.py` | Python | Automated test or reproducible fixture. | 1166 | 4 | yes | no | no | no | no | KEEP |
| `tests/test_flood.py` | Python | Automated test or reproducible fixture. | 3047 | 4 | yes | no | no | no | no | KEEP |
| `tests/test_growth.py` | Python | Automated test or reproducible fixture. | 14353 | 5 | yes | no | no | no | no | KEEP |
| `tests/test_interpretation_guardrails.py` | Python | Automated test or reproducible fixture. | 2946 | 4 | yes | no | no | no | no | KEEP |
| `tests/test_jobs.py` | Python | Automated test or reproducible fixture. | 6797 | 5 | yes | no | no | no | no | KEEP |
| `tests/test_limits.py` | Python | Automated test or reproducible fixture. | 11117 | 4 | yes | no | no | no | no | KEEP |
| `tests/test_live_llm_runner.py` | Python | Automated test or reproducible fixture. | 987 | 5 | yes | no | no | no | no | KEEP |
| `tests/test_llm.py` | Python | Automated test or reproducible fixture. | 7437 | 7 | yes | no | no | no | no | KEEP |
| `tests/test_llm_evaluation.py` | Python | Automated test or reproducible fixture. | 1742 | 4 | yes | no | no | no | no | KEEP |
| `tests/test_memory_evaluation.py` | Python | Automated test or reproducible fixture. | 1942 | 8 | yes | no | no | no | no | KEEP |
| `tests/test_migrations.py` | Python | Automated test or reproducible fixture. | 9411 | 6 | yes | no | no | no | no | KEEP |
| `tests/test_miniapp_actions.py` | Python | Automated test or reproducible fixture. | 7934 | 7 | yes | no | no | no | no | KEEP |
| `tests/test_monetization_phase_a.py` | Python | Automated test or reproducible fixture. | 9678 | 5 | yes | no | no | no | no | KEEP |
| `tests/test_natal_sections.py` | Python | Automated test or reproducible fixture. | 7355 | 5 | yes | no | no | no | no | KEEP |
| `tests/test_openai_compat.py` | Python | Automated test or reproducible fixture. | 15232 | 5 | yes | no | no | no | no | KEEP |
| `tests/test_p1_controls.py` | Python | Automated test or reproducible fixture. | 1930 | 4 | yes | no | no | no | no | KEEP |
| `tests/test_p2_contracts.py` | Python | Automated test or reproducible fixture. | 1517 | 4 | yes | no | no | no | no | KEEP |
| `tests/test_palm_integration.py` | Python | Automated test or reproducible fixture. | 14399 | 6 | yes | no | no | no | no | KEEP |
| `tests/test_palm_vision.py` | Python | Automated test or reproducible fixture. | 2363 | 5 | yes | no | no | no | no | KEEP |
| `tests/test_payment_monitor.py` | Python | Automated test or reproducible fixture. | 4250 | 5 | yes | no | no | no | no | KEEP |
| `tests/test_pdf_matrix.py` | Python | Automated test or reproducible fixture. | 996 | 5 | yes | no | no | no | no | KEEP |
| `tests/test_pdfgen.py` | Python | Automated test or reproducible fixture. | 6816 | 7 | yes | no | no | no | no | KEEP |
| `tests/test_placements_palm.py` | Python | Automated test or reproducible fixture. | 7740 | 5 | yes | no | no | no | no | KEEP |
| `tests/test_postgres_adapter.py` | Python | Automated test or reproducible fixture. | 1494 | 4 | yes | no | no | no | no | KEEP |
| `tests/test_practices.py` | Python | Automated test or reproducible fixture. | 9742 | 4 | yes | no | no | no | no | KEEP |
| `tests/test_release_gate.py` | Python | Automated test or reproducible fixture. | 1053 | 4 | yes | no | no | no | no | KEEP |
| `tests/test_report_history.py` | Python | Automated test or reproducible fixture. | 2667 | 8 | yes | no | yes | no | no | KEEP |
| `tests/test_safety.py` | Python | Automated test or reproducible fixture. | 4354 | 6 | yes | no | no | no | no | KEEP |
| `tests/test_scale_contract.py` | Python | Automated test or reproducible fixture. | 1402 | 4 | yes | no | no | no | no | KEEP |
| `tests/test_scheduler.py` | Python | Automated test or reproducible fixture. | 11243 | 4 | yes | no | no | no | no | KEEP |
| `tests/test_security_regressions.py` | Python | Automated test or reproducible fixture. | 9250 | 7 | yes | no | no | no | no | KEEP |
| `tests/test_session.py` | Python | Automated test or reproducible fixture. | 1900 | 4 | yes | no | no | no | no | KEEP |
| `tests/test_shared_context.py` | Python | Automated test or reproducible fixture. | 3458 | 4 | yes | no | no | no | no | KEEP |
| `tests/test_stage0_operations.py` | Python | Automated test or reproducible fixture. | 3164 | 5 | yes | no | no | no | no | KEEP |
| `tests/test_tarot_contract.py` | Python | Automated test or reproducible fixture. | 1344 | 7 | yes | no | no | no | no | KEEP |
| `tests/test_vedic.py` | Python | Automated test or reproducible fixture. | 4323 | 5 | yes | no | no | no | no | KEEP |
| `web/landing-en.html` | HTML | Public landing/legal/SEO web surface. | 6066 | 2 | yes | no | no | no | no | KEEP |
| `web/landing.css` | CSS | Public landing/legal/SEO web surface. | 6418 | 1 | yes | no | no | no | no | KEEP |
| `web/landing.html` | HTML | Public landing/legal/SEO web surface. | 7909 | 3 | yes | no | no | no | no | KEEP |
| `web/privacy-en.html` | HTML | Public landing/legal/SEO web surface. | 4222 | 1 | yes | no | no | no | no | KEEP |
| `web/privacy.html` | HTML | Public landing/legal/SEO web surface. | 8395 | 2 | yes | no | no | no | no | KEEP |
| `web/robots.txt` | Text | Public landing/legal/SEO web surface. | 122 | 1 | yes | no | no | no | no | KEEP |
| `web/sitemap.xml` | Other | Public landing/legal/SEO web surface. | 367 | 1 | yes | no | no | no | no | KEEP |
| `web/terms-en.html` | HTML | Public landing/legal/SEO web surface. | 4016 | 1 | yes | no | no | no | no | KEEP |
| `web/terms.html` | HTML | Public landing/legal/SEO web surface. | 7459 | 1 | yes | no | no | no | no | KEEP |

## Review notes

1. The inventory intentionally keeps source code, tests, migrations, deployment configuration, model notices and legal material in scope. A file is not disposable merely because it has no literal reference.
2. Documentation classification and final move/delete decisions are recorded in `docs/README.md` and `docs/RELEASE/DOCUMENTATION_FINAL_REVIEW.md`.
3. Re-run the generator outside the repository when the tree changes; the generator itself is not part of the product repository.
