"""Check OracleAI's shared design tokens and visual release contract."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOKENS = ROOT / "miniapp" / "css" / "00-tokens.css"
STYLES = ROOT / "miniapp" / "styles.css"
INVENTORY = ROOT / "docs" / "DESIGN_COMPONENT_INVENTORY.md"

REQUIRED_TOKENS = {
    "--bg-0", "--bg-1", "--bg-2", "--gold", "--gold-bright", "--violet",
    "--text", "--text-dim", "--text-faint", "--border", "--border-strong",
    "--font-body", "--r-s", "--r-m", "--r-l", "--motion-quick",
    "--motion-base", "--motion-slow", "--sh-card", "--sh-gold",
    "--color-bg-primary", "--color-bg-secondary", "--color-bg-elevated",
    "--color-accent", "--color-text-primary", "--color-text-secondary",
    "--color-border", "--color-success", "--color-error", "--color-warning",
    "--font-size-h1", "--font-size-body", "--font-size-caption", "--space-4",
    "--radius-control", "--touch-target", "--motion-enter", "--focus-ring",
}


def main() -> int:
    tokens = TOKENS.read_text(encoding="utf-8")
    styles = STYLES.read_text(encoding="utf-8")
    inventory = INVENTORY.read_text(encoding="utf-8")
    missing = sorted(token for token in REQUIRED_TOKENS
                     if not re.search(rf"{re.escape(token)}\s*:", tokens))
    imports = re.findall(r"@import\s+url\('css/([^']+)'", styles)
    expected = [f"{idx:02d}-" for idx in range(18)]
    import_order_ok = len(imports) == 18 and all(
        imports[idx].startswith(expected[idx]) for idx in range(18)
    )
    reduced_motion = "prefers-reduced-motion: reduce" in styles or any(
        "prefers-reduced-motion: reduce" in path.read_text(encoding="utf-8")
        for path in (ROOT / "miniapp" / "css").glob("*.css")
    )
    required_components = [
        "Chat composer", "Tool chip", "Tool sheet", "Age gate", "Memory control",
        "Tarot widget", "Chart widget", "Compatibility widget", "Safety banner",
    ]
    missing_components = [item for item in required_components if item not in inventory]
    if missing or not import_order_ok or not reduced_motion or missing_components:
        print({
            "missing_tokens": missing,
            "import_order_ok": import_order_ok,
            "reduced_motion": reduced_motion,
            "missing_components": missing_components,
        })
        return 1
    print("design contract ok: tokens, import order, reduced motion, component inventory")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
