# OracleAI agent and tool quality audit baseline

## Scope

This audit covers the four file-backed profiles (`lilith`, `urania`, `lenormand`, `mira`), the shared agent runtime, the shared tool registry, the Mini App agent/tool surfaces, and the existing deterministic eval gates.

## Current inventory

| Agent | Legacy code | Skills | Knowledge files | Eval files | Declared tools |
|---|---|---:|---:|---:|---:|
| Lilith | `oracle` | 31 | 2 | 2 | 11 |
| Urania | `astro` | 30 | 2 | 2 | 12 |
| Madame Lenormand | `tarot` | 31 | 2 | 2 | 3 |
| Mira | `chiromant` | 30 | 2 | 2 | 3 |

The repository currently has a shared registry of approximately 20 deterministic tools in `app/core/skills.py`. The profiles declare `uses_persona`, `skills_max_active`, `limits`, `memory`, `risk_level`, and `output_contract`, but the legacy `AgentSpec`/profile bridge does not currently carry all of those fields into the live runtime.

## Confirmed quality gaps

1. `app/core/agents/specs.py` overlays display fields, model tier, history and tool names, but drops `uses_persona`, `skills_max_active`, `limits`, `memory`, `risk_level`, and `output_contract`. These fields are therefore aspirational configuration rather than enforced behavior.
2. `app/core/agents/runtime.py` hardcodes `skill_context(..., limit=3)`, uses global `llm` workflow limits instead of per-profile limits, and calls `run_agent` with a premium-only iteration override. The profile-specific limits are not observable in execution.
3. `app/core/agents/file_loader.py` selects skills through token overlap over names/descriptions/body. It supports dependencies and tool allow-lists, but skills have no first-class activation phrases, output checks, or evidence-level metadata in the selector.
4. The shared tool layer in `app/core/skills.py` is a large dictionary with hand-written schemas. `execute` catches every exception and returns a plain string, which makes structured error states and evidence provenance difficult to expose or test.
5. The current output contract is a single generic `agent_response.v1`; the runtime safety validator is not agent-specific and does not verify that a response contains evidence, uncertainty and an observable next step.
6. User-facing chat responses are mostly text-only. The Mini App has visual agent/tool surfaces and chart/tarot/palm widgets, but the response payload does not yet expose a consistent proof/evidence envelope that lets a user see which facts were calculated, which interpretation is symbolic, and what confidence/limitations apply.
7. Existing profile evals cover skill selection fixtures and must/must-not markers, but they do not fully exercise live profile limits, tool argument validation, structured evidence, RU/EN outputs, or agent-specific visual proof.

## Strong foundations to preserve

The project already has a modular `SKILL.md` library, deterministic natal/Tarot/Matrix/palm domain functions, dependency resolution, anti-Barnum protocols, safety middleware, bounded history, offline fallbacks, and separate offline/live acceptance gates. Changes must preserve legacy agent codes and current API compatibility.

## Planned quality direction

The next refactor should make profile metadata live, introduce typed tool envelopes while retaining string compatibility at the boundary, improve skill selection with optional activation metadata and domain-aware scoring, add agent-specific structured output requirements, and expose compact user-visible evidence/proof cards in bot/Mini App responses. The work should remain file-backed and easy to extend with additional `SKILL.md`, tool contracts, knowledge modules and eval cases.
