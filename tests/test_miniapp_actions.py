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
    version = re.search(r'/static/styles\.css\?v=(\d+)', index)
    assert version, "index.html must declare a cache-busted stylesheet"
    value = version.group(1)
    assert f'?v={value}' in styles
    assert f'?v={int(value) - 1}' not in styles


def test_frontend_errors_use_user_facing_mapping() -> None:
    sources = {
        path.name: path.read_text(encoding="utf-8")
        for path in JS_DIR.glob("*.js")
    }
    assert "function friendlyError" in sources["01-utils.js"]
    raw_error_sites = []
    for name, source in sources.items():
        if name == "01-utils.js":
            continue
        if re.search(r"(?:e|err|error)\.message", source):
            raw_error_sites.append(name)
    assert not raw_error_sites, "raw error details exposed in: " + ", ".join(raw_error_sites)


def test_chiromant_is_present_on_all_agent_surfaces() -> None:
    data = (JS_DIR / "03-data.js").read_text(encoding="utf-8")
    app = (JS_DIR / "05-app.js").read_text(encoding="utf-8")
    art = (JS_DIR / "02-art.js").read_text(encoding="utf-8")
    home = (JS_DIR / "06-home.js").read_text(encoding="utf-8")
    chat = (JS_DIR / "07-chat.js").read_text(encoding="utf-8")
    specs = (ROOT / "app" / "core" / "agents" / "specs.py").read_text(encoding="utf-8")
    for source in (data, app, art, home, chat, specs):
        assert "chiromant" in source
    assert "chiromant.jpg" in app
    assert "get_palm_focus" in specs
    assert "agents.slice(0, 4)" in chat


def test_palm_photo_flow_and_agent_theme_contract() -> None:
    data = (JS_DIR / "03-data.js").read_text(encoding="utf-8")
    palm = (JS_DIR / "13-palm.js").read_text(encoding="utf-8")
    chat = (JS_DIR / "07-chat.js").read_text(encoding="utf-8")
    actions = ACTIONS.read_text(encoding="utf-8")
    css = (ROOT / "miniapp" / "css" / "15-ritual-redesign.css").read_text(encoding="utf-8")
    assert "t: 'Личная опора'" not in data
    assert "chatPractice" not in palm + chat
    assert "palm-quick-upload" in chat and "palm-start" in actions
    assert "palm-camera" in palm and "palm-gallery" in palm and 'capture="environment"' in palm
    assert ".tool-expand { z-index: 400" in css or ".tool-expand {\n  z-index: 400" in css
    for color in ("#e8c56b", "#8cc8ff", "#e7a8d8", "#6fd6b0"):
        assert color in (data + chat + css)


def test_new_explorers_are_loaded_and_expose_accessible_states() -> None:
    index = (ROOT / "miniapp" / "index.html").read_text(encoding="utf-8")
    data = (JS_DIR / "03-data.js").read_text(encoding="utf-8")
    placements = (JS_DIR / "16-placements.js").read_text(encoding="utf-8")
    palm = (JS_DIR / "13-palm.js").read_text(encoding="utf-8")
    css = (ROOT / "miniapp" / "css" / "15-ritual-redesign.css").read_text(encoding="utf-8")
    assert re.search(r'/static/js/16-placements\.js\?v=\d+', index)
    assert 'app.featurePlacements' in placements
    assert 'aria-live="polite"' in placements
    assert 'data-placement-code' in placements
    assert 'palm-preview' in palm and 'palm-confidence' in palm
    assert all(name in palm for name in ('featurePalmMap', 'featurePalmQuality', 'featurePalmCompare', 'palm-workflow'))
    assert 'featurePalmMap' in data and 'featurePalmCompare' in data
    assert '.placement-explorer' in css and '.palm-progress' in css
