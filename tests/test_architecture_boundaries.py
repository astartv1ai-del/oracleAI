"""Небольшие архитектурные тесты, защищающие новые границы модульного монолита."""
from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ROUTERS = ROOT / "app" / "api" / "routers"
INDEX = ROOT / "miniapp" / "index.html"


def test_api_routers_do_not_import_each_other() -> None:
    router_names = {
        path.stem for path in ROUTERS.glob("*.py") if path.name != "__init__.py"
    }
    pattern = re.compile(
        r"^\s*(?:from\s+\.|import\s+app\.api\.routers\.)"
        r"(" + "|".join(sorted(map(re.escape, router_names))) + r")"
    )

    violations = []
    for path in ROUTERS.glob("*.py"):
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if pattern.search(line):
                violations.append(f"{path.relative_to(ROOT)}:{number}: {line.strip()}")

    assert not violations, "router-to-router imports found:\n" + "\n".join(violations)


def test_frontend_runtime_boundaries_have_stable_order() -> None:
    html = INDEX.read_text(encoding="utf-8")
    scripts = re.findall(r'<script[^>]+src="([^"]+)"', html)

    def position(filename: str) -> int:
        for index, script in enumerate(scripts):
            if script.split("?", 1)[0].endswith("/" + filename):
                return index
        raise AssertionError(f"{filename} is not declared in miniapp/index.html")

    assert position("00-runtime.js") < position("05-app.js")
    assert position("15-actions.js") < position("13-events.js")
    assert "/static/js/00-runtime.js?v=69" in html
    assert "/static/js/15-actions.js?v=69" in html


def test_refactored_backend_boundaries_exist() -> None:
    expected = [
        ROOT / "app" / "api" / "common" / "errors.py",
        ROOT / "app" / "api" / "common" / "validation.py",
        ROOT / "app" / "api" / "contracts" / "chat.py",
        ROOT / "app" / "api" / "contracts" / "compatibility.py",
        ROOT / "app" / "services" / "compatibility.py",
    ]
    missing = [str(path.relative_to(ROOT)) for path in expected if not path.exists()]
    assert not missing, "refactored boundary files are missing: " + ", ".join(missing)
