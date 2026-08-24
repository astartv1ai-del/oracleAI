"""Deterministic quality gate for the file-backed agent harness."""
from __future__ import annotations

import json
from pathlib import Path

import yaml

from app.core import skills
from app.core.agents.file_loader import (
    load_profiles,
    resolve_skill_dependencies,
    select_skills,
)
from app.core.agents.specs import get

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = {"oracle", "astro", "tarot", "chiromant"}
ROUTING_CASES = {
    "chiromant": "фото ладони и линия сердца",
    "astro": "Раху Кету и аспекты натальной карты",
    "tarot": "расклад на выбор между двумя вариантами",
    "oracle": "Матрица Судьбы и повторяющийся сценарий",
}


def build_report() -> dict:
    profiles = load_profiles()
    errors: list[str] = []
    if {p.legacy_code for p in profiles.values()} != EXPECTED:
        errors.append("profile legacy-code set does not match the four live agents")
    tool_names = set(skills.SKILLS)
    total_cases = 0
    rows = []
    for profile in profiles.values():
        spec = get(profile.legacy_code)
        declared = set(profile.data.get("tools") or ())
        missing = declared - tool_names
        if missing:
            errors.append(f"{profile.agent_id}: missing tool implementations: {sorted(missing)}")
        if "anti-barnum-protocol" not in {s.name for s in profile.skills}:
            errors.append(f"{profile.agent_id}: anti-barnum-protocol is missing")
        if not profile.handbook:
            errors.append(f"{profile.agent_id}: domain handbook is empty")
        if spec.skills_max_active != int(profile.data.get("skills_max_active", 3)):
            errors.append(f"{profile.agent_id}: skills_max_active is not live")
        limits = profile.data.get("limits") or {}
        for key in ("max_turns", "max_tool_calls", "timeout_s"):
            if float(limits.get(key, 0)) <= 0:
                errors.append(f"{profile.agent_id}: invalid {key}")
        for skill in profile.skills:
            try:
                resolve_skill_dependencies(profile, [skill])
            except ValueError as exc:
                errors.append(str(exc))
        selected = select_skills(profile, ROUTING_CASES[profile.legacy_code], spec.skills_max_active)
        if not selected:
            errors.append(f"{profile.agent_id}: routing selected no skills")
        eval_path = ROOT / "app" / "agents" / profile.agent_id / "evals" / "cases.yaml"
        cases = yaml.safe_load(eval_path.read_text(encoding="utf-8")).get("cases", [])
        total_cases += len(cases)
        rows.append({
            "agent": profile.agent_id,
            "legacy_code": profile.legacy_code,
            "skills": len(profile.skills),
            "tools": len(declared),
            "active_cap": spec.skills_max_active,
            "selected": [s.name for s in selected],
            "eval_cases": len(cases),
        })
    for name, item in skills.SKILLS.items():
        schema = item.get("schema") or {}
        if not callable(item.get("run")):
            errors.append(f"{name}: tool runner is not callable")
        for key in ("name", "description", "input_schema"):
            if not schema.get(key):
                errors.append(f"{name}: schema missing {key}")
        if schema.get("name") != name:
            errors.append(f"{name}: schema name mismatch")
    frontend = "\n".join(
        (ROOT / "miniapp" / "js" / name).read_text(encoding="utf-8")
        for name in ("01-utils.js", "06-home.js", "07-chat.js")
    )
    if "agent-proof-row" not in frontend or "message-proof" not in frontend:
        errors.append("Mini App proof surfaces are not wired")
    return {"ok": not errors, "tool_count": len(tool_names), "eval_cases": total_cases, "agents": rows, "errors": errors}


def main() -> int:
    report = build_report()
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
