"""Static safety checks for the Mini App's declarative button registry."""
from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
JS_DIR = ROOT / "miniapp" / "js"
ACTIONS = JS_DIR / "15-actions.js"


def _frontend_source() -> str:
    return "\n".join(
        path.read_text(encoding="utf-8")
        for path in sorted(JS_DIR.glob("*.js"))
    )


def _action_registry_keys() -> set[str]:
    source = ACTIONS.read_text(encoding="utf-8")
    registry = source.split("const actionHandlers = {", 1)[1].split("\n  };", 1)[0]
    return {
        quoted or plain
        for quoted, plain in re.findall(
            r"^\s*(?:'([^']+)'|([A-Za-z][\w-]*))\s*:",
            registry,
            flags=re.MULTILINE,
        )
    }


def test_every_static_miniapp_action_has_a_registered_handler() -> None:
    source = _frontend_source()
    declared = {
        double or single
        for double, single in re.findall(r"data-act=(?:\"([^\"]+)\"|'([^']+)')", source)
    }
    registered = _action_registry_keys()

    assert declared, "No declarative Mini App actions were found"
    assert not declared - registered, (
        "Mini App actions without a registered handler: "
        + ", ".join(sorted(declared - registered))
    )


def test_every_explicit_action_target_is_implemented_on_app() -> None:
    actions_source = ACTIONS.read_text(encoding="utf-8")
    frontend = _frontend_source()
    methods = set(re.findall(r"call\('([A-Za-z][A-Za-z0-9_]*)'", actions_source))
    missing = {
        method
        for method in methods
        if not re.search(rf"\bapp\.{re.escape(method)}\s*=", frontend)
    }

    assert not missing, (
        "Action registry calls methods not implemented on app: "
        + ", ".join(sorted(missing))
    )
