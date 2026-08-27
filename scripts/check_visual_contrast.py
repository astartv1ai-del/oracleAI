"""Check the core OracleAI semantic color pairs against WCAG contrast ratios."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOKENS = (ROOT / "miniapp" / "css" / "00-tokens.css").read_text(encoding="utf-8")


def parse_color(name: str) -> tuple[int, int, int]:
    match = re.search(rf"{re.escape(name)}:\s*(#[0-9a-fA-F]{{6}})", TOKENS)
    if not match:
        raise ValueError(f"missing {name}")
    raw = match.group(1)[1:]
    return tuple(int(raw[i : i + 2], 16) for i in (0, 2, 4))


def luminance(rgb: tuple[int, int, int]) -> float:
    channels = []
    for value in rgb:
        srgb = value / 255
        channels.append(srgb / 12.92 if srgb <= .04045 else ((srgb + .055) / 1.055) ** 2.4)
    return .2126 * channels[0] + .7152 * channels[1] + .0722 * channels[2]


def ratio(foreground: tuple[int, int, int], background: tuple[int, int, int]) -> float:
    light = max(luminance(foreground), luminance(background))
    dark = min(luminance(foreground), luminance(background))
    return (light + .05) / (dark + .05)


pairs = [
    ("--color-text-primary", "--color-bg-primary", 4.5),
    ("--color-text-secondary", "--color-bg-primary", 4.5),
    ("--color-text-muted", "--color-bg-primary", 4.5),
    ("--color-on-accent", "--color-accent-strong", 4.5),
]
for foreground, background, threshold in pairs:
    value = ratio(parse_color(foreground), parse_color(background))
    status = "PASS" if value >= threshold else "REVIEW"
    print(f"{status}: {foreground} on {background} = {value:.2f}:1 (target {threshold:.1f}:1)")
