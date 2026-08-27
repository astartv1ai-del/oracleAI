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
    version = re.search(r'/static/js/00-runtime\.js\?v=(\d+)', html)
    assert version, "runtime asset must be cache-busted"
    value = version.group(1)
    assert f"/static/js/15-actions.js?v={value}" in html


def test_frontend_cache_version_covers_new_modules() -> None:
    html = INDEX.read_text(encoding="utf-8")
    styles = (ROOT / "miniapp" / "styles.css").read_text(encoding="utf-8")
    version = re.search(r"/static/styles\.css\?v=(\d+)", html)
    assert version, "styles asset must be cache-busted"
    value = version.group(1)
    assert value == "100"
    assert "?v=99" not in html and "?v=99" not in styles
    assert f"/static/js/17-payments.js?v={value}" in html
    for filename in ("16-visual-qa.css", "16-payments.css"):
        assert f"css/{filename}?v={value}" in styles


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
