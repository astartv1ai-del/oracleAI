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



def test_chat_exposes_one_visible_tool_entry_point() -> None:
    chat = (JS_DIR / "07-chat.js").read_text(encoding="utf-8")
    assert chat.count('class="composer-tools-copy"') == 1
    assert 'id="tool-btn"' not in chat
    assert 'class="command-tray"' not in chat
    assert 'class="te-agent-switcher"' not in chat
    assert 'otherAgents' not in chat


def test_miniapp_stylesheet_imports_match_asset_version() -> None:
    index = (ROOT / "miniapp" / "index.html").read_text(encoding="utf-8")
    styles = (ROOT / "miniapp" / "styles.css").read_text(encoding="utf-8")
    assert '/static/styles.css?v=85' in index
    assert '?v=85' in styles
    assert '?v=84' not in styles


def test_new_explorers_are_loaded_and_expose_accessible_states() -> None:
    index = (ROOT / "miniapp" / "index.html").read_text(encoding="utf-8")
    placements = (JS_DIR / "16-placements.js").read_text(encoding="utf-8")
    palm = (JS_DIR / "13-palm.js").read_text(encoding="utf-8")
    css = (ROOT / "miniapp" / "css" / "15-ritual-redesign.css").read_text(encoding="utf-8")
    assert '/static/js/16-placements.js?v=85' in index
    assert 'app.featurePlacements' in placements
    assert 'aria-live="polite"' in placements
    assert 'data-placement-code' in placements
    assert 'palm-preview' in palm and 'palm-confidence' in palm
    assert '.placement-explorer' in css and '.palm-progress' in css
