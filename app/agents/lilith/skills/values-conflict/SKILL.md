---
name: values-conflict
version: 1.0.0
description: Map a stated decision to competing values and trade-offs.
depends_on:
  - anti-barnum-protocol
requires_tools: recall_memory recall_diary
tags: ['values', 'decision']
license: Proprietary
compatibility: OracleAI file-backed agent harness.
metadata:
  oracleai_agent: lilith
  oracleai_domain: specialist-domain
  oracleai_loading: on_demand
  oracleai_output_contract: agent_response.v1
---

# values-conflict

## Purpose

Map a stated decision to competing values and trade-offs. This skill is a focused capability, not a replacement for deterministic tools, safety policy or professional services.

## Evidence contract

Use only this evidence class: **user-stated values and choice constraints**. Before interpretation, record what is directly available, what comes from the user's words and what remains unknown. If the required evidence is absent or low quality, stop and ask for the smallest missing input.

## Workflow

1. Classify the question and verify that this skill is the narrowest relevant capability.
2. Call only the allow-listed tool needed for the evidence; never invent tool output.
3. Write an internal ledger of observation, traditional/domain association, hypothesis and uncertainty.
4. Add one counter-hypothesis and one observation that could support or contradict the hypothesis.
5. Give one bounded interpretation and one low-pressure, observable next step.

## Domain-specific failure mode

Do not choose for the user or turn values into identity labels.

## Anti-Barnum gate

Do not use universal personality labels, deterministic predictions, third-party mind reading, diagnosis, or certainty language. Every concrete sentence must be tied to evidence or explicitly marked as a symbolic/domain hypothesis. If the user rejects the hypothesis, update the frame rather than defending it.

## Output contract

Return: evidence → bounded interpretation → limitation → alternative explanation → user-agency step. If the user requests a forbidden claim, explain the boundary and offer a grounded reflective alternative.
