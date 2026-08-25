from __future__ import annotations

import csv
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXCLUDED_PARTS = {".git", ".pytest_cache", ".ruff_cache", "__pycache__", "node_modules"}


def category(path: Path) -> str:
    parts = path.parts
    if "tests" in parts:
        return "test"
    if "scripts" in parts:
        return "tooling"
    if "docs" in parts:
        return "documentation"
    if "miniapp" in parts or "admin" in parts or "web" in parts:
        return "frontend"
    if "infra" in parts:
        return "infrastructure"
    if path.suffix in {".svg", ".png", ".jpg", ".jpeg", ".webp", ".woff", ".woff2", ".ttf"}:
        return "asset"
    if "app" in parts:
        return "backend"
    return "repository"


def role(path: Path) -> str:
    name = path.name.lower()
    rel = path.relative_to(ROOT).as_posix()
    if name in {"dockerfile", "docker-compose.yml", "caddyfile"} or rel.startswith("infra/"):
        return "deployment/runtime infrastructure"
    if rel.startswith("app/api/"):
        return "HTTP API"
    if rel.startswith("app/bot/"):
        return "Telegram bot"
    if rel.startswith("app/core/"):
        return "domain/runtime core"
    if rel.startswith("app/data/") or rel.startswith("app/repo/"):
        return "data/schema/repository"
    if rel.startswith("app/pdfgen/"):
        return "PDF generation"
    if rel.startswith("app/services/"):
        return "application service"
    if rel.startswith("miniapp/"):
        return "Mini App client"
    if rel.startswith("tests/"):
        return "automated verification"
    if rel.startswith("docs/"):
        return "source-of-truth documentation"
    if rel.startswith("scripts/"):
        return "QA/operations/tooling"
    return "repository configuration or asset"


def files() -> list[Path]:
    out = []
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        rel_parts = set(path.relative_to(ROOT).parts)
        if rel_parts & EXCLUDED_PARTS:
            continue
        out.append(path)
    return sorted(out)


items = files()
with (ROOT / "docs" / "FILE_AUDIT.csv").open("w", newline="", encoding="utf-8") as fh:
    writer = csv.writer(fh, lineterminator="\n")
    writer.writerow(["path", "category", "role", "bytes", "sha256", "tracked"])
    tracked = set()
    import subprocess
    tracked.update(subprocess.check_output(["git", "ls-files"], cwd=ROOT, text=True).splitlines())
    for path in items:
        rel = path.relative_to(ROOT).as_posix()
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        writer.writerow([rel, category(path), role(path), path.stat().st_size, digest, rel in tracked])

counts: dict[str, int] = {}
for path in items:
    counts[category(path)] = counts.get(category(path), 0) + 1

project_map = """# OracleAI project map\n\n**Generated:** 2026-08-25 from the current checkout.\n**Scope:** runtime source, clients, infrastructure, tests, tooling and source-of-truth documentation.\n\n## Runtime topology\n\nThe repository contains a Python FastAPI/backend and Telegram bot under `app/`, a vanilla JavaScript/CSS Telegram Mini App under `miniapp/`, static landing/legal pages under `web/`, a small admin surface under `admin/`, and Docker/Caddy deployment material under `infra/`. Deterministic domain calculations and safety/evidence boundaries live in `app/core/`; persistence and migrations live in `app/data/` and `app/repo/`; HTTP contracts live in `app/api/`; Telegram handlers live in `app/bot/`; PDF generation lives in `app/pdfgen/`.\n\n## Critical flows\n\n| Flow | Primary entrypoints | Evidence/checks |\n|---|---|---|\n| Telegram onboarding and chat | `app/bot/`, `app/core/agents/`, `app/core/agent.py` | `tests/test_bot_fsm.py`, `tests/test_agent_context.py`, `tests/test_safety.py` |\n| Mini App authenticated API | `app/api/main.py`, `app/api/routers/`, `miniapp/js/` | `tests/test_api.py`, `tests/test_miniapp_actions.py`, JS syntax gate |\n| Natal calculation and chart rendering | `app/core/chart_contract.py`, `app/core/astro.py`, `miniapp/js/04-nativity.js` | `tests/test_chart_contract.py`, `tests/test_natal_sections.py`, `tests/check_nativity_svg.js` |\n| Structured LLM interpretation | `app/core/chart_interpretation.py`, `app/core/interpretation.py`, `app/core/llm.py` | `tests/test_chart_interpretation.py`, `tests/test_interpretation_guardrails.py`, `tests/test_llm.py` |\n| Memory and diary | `app/core/memory.py`, `app/repo/`, `app/api/routers/`, `miniapp/js/08-widgets.js` | `tests/test_diary.py`, `tests/test_agent_context.py`, `tests/test_security_regressions.py` |\n| Tarot/Lenormand/palm | `app/core/tarot.py`, `app/agents/lenormand/`, `app/core/palm.py`, `miniapp/js/09-tarot.js`, `miniapp/js/13-palm.js` | domain/routing/palm test suite and benchmark scripts |\n| PDF/report | `app/pdfgen/`, `scripts/gen_pdf.py`, `scripts/qa_pdf_profiles.py` | `tests/test_pdfgen.py`, `docs/audit/pdf_samples_v2/`, PDF profile QA |\n| Billing and entitlements | `app/services/billing.py`, `app/api/routers/payments.py`, `tests/test_billing.py` | sandbox/fixture tests only; live payment remains gated |\n| Scheduled/background work | `app/services/scheduler.py`, `app/bot/`, `scripts/ops_alerts.py` | `tests/test_scheduler.py`, `tests/test_broadcast.py`; production scheduler evidence remains open |\n| Backup/restore | `scripts/backup_db.sh`, `scripts/restore_db.sh` | disposable plaintext/encrypted restore drill; production off-site evidence remains open |\n\n## External boundaries\n\nTelegram authentication and bot API, LLM provider chain, geocoding/timezone services, payment providers, Sentry/observability, and deployment infrastructure are external boundaries. Local tests use fixtures/mocks unless explicitly marked otherwise; live provider/device/payment/production-host evidence is not inferred from unit tests.\n\n## Inventory counts\n\n""" + "\n".join(f"- **{key}:** {value} files" for key, value in sorted(counts.items())) + """\n\n## Source-of-truth documents\n\n`docs/PRODUCT.md`, `docs/ARCHITECTURE.md`, `docs/API.md`, `docs/DESIGN_SYSTEM.md`, `docs/SECURITY.md`, `docs/LAUNCH_GOVERNANCE.md`, `docs/DEPLOYMENT.md`, `docs/LLM_EVALUATION.md`, and `docs/MONETIZATION_BASELINE.md` define current contracts. `docs/FILE_AUDIT.csv` is the generated per-file inventory; regenerate it with `python scripts/generate_project_audit.py` after structural changes.\n"""
(ROOT / "docs" / "PROJECT_MAP.md").write_text(project_map, encoding="utf-8")
print(f"audited_files={len(items)}")
print("wrote=docs/PROJECT_MAP.md,docs/FILE_AUDIT.csv")
