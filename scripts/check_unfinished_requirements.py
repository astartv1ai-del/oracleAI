from __future__ import annotations

import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs/audit/unfinished_requirements_check_2026-08-25.txt"
ENV = {**os.environ, "PYTHONPATH": str(ROOT)}

COMMANDS: list[tuple[str, list[str]]] = [
    ("git_state", ["git", "status", "--short"]),
    ("targeted_tests", ["pytest", "-q", "-p", "no:cacheprovider", "tests/test_billing.py", "tests/test_api.py", "tests/test_pdfgen.py", "tests/test_security_regressions.py", "tests/test_scheduler.py"]),
    ("domain_evals", ["python", "scripts/check_domain_evals.py"]),
    ("routing", ["python", "scripts/benchmark_agent_routing.py"]),
    ("skill_routing", ["python", "scripts/benchmark_skill_routing.py"]),
    ("backup_scripts", ["bash", "-lc", "test -x scripts/backup_db.sh && test -x scripts/restore_db.sh && echo backup_restore_scripts=present"]),
    ("load_harness", ["bash", "-lc", "test -f load/locustfile.py && test -f load/simulate.py && echo load_harness=present"]),
    ("support_docs", ["bash", "-lc", "grep -RIlE 'support|SLA|FAQ|escalation' docs app web | head -20"]),
    ("accessibility_contract", ["bash", "-lc", "grep -RIlE 'reduced.motion|screen.reader|safe.area|contrast|keyboard|focus' docs miniapp web tests | head -30"]),
    ("payment_contract", ["bash", "-lc", "test -f tests/test_billing.py && grep -RIlE 'webhook|refund|idempot|entitlement' tests app/services app/api/routers | head -40"]),
    ("docker_availability", ["bash", "-lc", "if command -v docker >/dev/null; then docker --version; else echo docker_unavailable_in_sandbox; fi"]),
    ("dependency_audit", ["bash", "-lc", "if command -v pip-audit >/dev/null; then pip-audit; else echo pip-audit_unavailable_in_sandbox; fi"]),
    ("live_llm", ["bash", "-lc", "if [ \"${SELF_CHECK_LIVE:-0}\" = 1 ]; then echo live_llm_enabled; else echo live_llm_not_run; fi"]),
]

chunks = [f"checked_at={datetime.now(timezone.utc).isoformat()}"]
for name, command in COMMANDS:
    proc = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, env=ENV)
    chunks.extend([
        f"\n===== {name} =====",
        "+ " + " ".join(command),
        proc.stdout.rstrip(),
        proc.stderr.rstrip(),
        f"[{name}_exit={proc.returncode}]",
    ])
OUT.write_text("\n".join(part for part in chunks if part) + "\n", encoding="utf-8")
print(f"wrote={OUT}")
