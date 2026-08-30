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
    assert int(value) >= 100
    assert "?v=99" not in html and "?v=99" not in styles
    assert f"/static/js/17-payments.js?v={value}" in html
    for filename in ("16-visual-qa.css", "16-payments.css"):
        assert f"css/{filename}?v={value}" in styles


def test_visual_capture_uses_distinct_server_side_locale_users() -> None:
    capture = (ROOT / "scripts" / "capture_visual_baseline.py").read_text(encoding="utf-8")
    seed = (ROOT / "scripts" / "seed_visual_user.py").read_text(encoding="utf-8")
    assert 'LOCALE_USERS = {"ru": 10001, "en": 10002}' in capture
    assert "BASE_URL_TEMPLATE.format(dev_user=LOCALE_USERS[locale_key])" in capture
    assert "(10001, \"ru\"), (10002, \"en\")" in seed
    assert 'localeContract' in capture
    assert 'paymentPlanCount' in capture and 'paymentProductCount' in capture
    assert "'.nav-btn[data-goto=\"{view_name}\"]'" in capture


def test_chat_surface_has_explicit_ru_en_copy_contract() -> None:
    chat = (ROOT / "miniapp" / "js" / "07-chat.js").read_text(encoding="utf-8")
    assert "const CHAT_I18N =" in chat
    assert "const CHAT_AGENT_EN =" in chat
    assert "Write to " in chat and "Напиши " in chat
    assert "What matters most to notice in this situation?" in chat
    assert "DIALOGUE TOOLS" in chat and "ИНСТРУМЕНТЫ ДИАЛОГА" in chat


def test_payment_surface_has_explicit_ru_en_copy_contract() -> None:
    payments = (ROOT / "miniapp" / "js" / "17-payments.js").read_text(encoding="utf-8")
    assert "const PAYMENT_I18N =" in payments
    assert "const PAYMENT_CATALOG =" in payments
    assert "payLang" in payments and "catalogText" in payments
    assert "Your Crystals" in payments and "Твои Кристаллы" in payments
    assert "Open Stars checkout" in payments and "Открыть оплату Stars" in payments


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


# ── ARCH-001..003 monolith split — target structure boundaries ─────────────
# The multi-etap plan (Etap 5) splits app/core/palm.py, app/core/agent.py and
# app/core/tool_registry.py into sub-packages. The scenarios/* split for
# agent.py has already landed (see ADR-0002). These tests encode the
# post-split invariants so the remaining splits can proceed in separate PRs
# without introducing forward-only imports.


def test_scenarios_package_has_expected_modules() -> None:
    """ARCH-002 (agent.py → scenarios/*) already landed — every scenario
    module is present and exports the documented public function."""
    scenarios_dir = ROOT / "app" / "core" / "scenarios"
    for name in ("forecast", "tarot", "compat", "report", "memory"):
        module = scenarios_dir / f"{name}.py"
        assert module.is_file(), f"missing scenario module: {module.relative_to(ROOT)}"


def test_agent_facade_stays_thin() -> None:
    """app/core/agent.py is a compatibility facade — it must NOT grow back
    into a monolith. The facade should stay under 120 lines and contain
    zero prompt strings or business rules."""
    facade = (ROOT / "app" / "core" / "agent.py").read_text(encoding="utf-8")
    lines = facade.splitlines()
    assert len(lines) < 120, (
        f"app/core/agent.py has {len(lines)} lines — the facade is thickening. "
        "Move new logic into app/core/scenarios/<domain>.py instead."
    )
    # No prompt-shaped literals: multiline SYSTEM messages and tool-user
    # instructions belong in scenarios/_impl.py or agents/*/SYSTEM.md.
    banned = ("Правила ", "Реши задачу", "You are ", "Ты — ")
    for token in banned:
        assert token not in facade, (
            f"app/core/agent.py contains prompt-shaped literal {token!r} — "
            "move to scenarios/_impl.py or app/agents/<code>/SYSTEM.md"
        )


def test_scenarios_impl_never_imports_from_agent_facade() -> None:
    """Cycle guard: the facade re-exports from scenarios; scenarios must NOT
    import back from the facade or the whole app.core.agent module."""
    for name in ("_impl", "forecast", "tarot", "compat", "report", "memory"):
        module = ROOT / "app" / "core" / "scenarios" / f"{name}.py"
        if not module.is_file():
            continue
        text = module.read_text(encoding="utf-8")
        assert "from ..agent" not in text and "import ..agent" not in text, (
            f"{module.relative_to(ROOT)}: scenarios must not depend on the facade"
        )


def test_tool_registry_is_the_only_executable_tools_module() -> None:
    """ARCH-003 preparation: SKILL.md files must not contain executable code,
    and app/core/skills.py must remain removed. The architecture lint enforces
    this at CI time; this test provides a fast local signal."""
    assert not (ROOT / "app" / "core" / "skills.py").exists(), (
        "app/core/skills.py returned — it was renamed to tool_registry.py"
    )
    assert (ROOT / "app" / "core" / "tool_registry.py").is_file()
    for skill_md in (ROOT / "app" / "agents").rglob("SKILL.md"):
        text = skill_md.read_text(encoding="utf-8")
        for fence in ("```python", "```py", "```bash", "```shell"):
            assert fence not in text.lower(), (
                f"{skill_md.relative_to(ROOT)}: SKILL.md must not embed "
                f"executable {fence} blocks — put runnable code in "
                "app/core/tool_registry.py"
            )


def test_palm_module_is_below_the_split_ceiling_or_split() -> None:
    """ARCH-001: app/core/palm.py is scheduled to split into
    core/palm/{prompts,evidence,service}.py. Until the split lands the
    monolith must not grow — 1200 lines is the absolute ceiling; the
    current baseline is ~842 lines."""
    palm = ROOT / "app" / "core" / "palm.py"
    palm_pkg = ROOT / "app" / "core" / "palm"
    if palm_pkg.is_dir():
        # Split already done; the flat file may be gone or become a thin facade.
        return
    assert palm.is_file(), "app/core/palm.py missing (unexpected)"
    lines = palm.read_text(encoding="utf-8").splitlines()
    assert len(lines) < 1200, (
        f"app/core/palm.py has {len(lines)} lines — split it into "
        "app/core/palm/{prompts,evidence,service}.py (ARCH-001)."
    )
