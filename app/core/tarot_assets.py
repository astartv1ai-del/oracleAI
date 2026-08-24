"""Deterministic validation for enabled Tarot/Lenormand visual assets."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from PIL import Image

from . import tarot_decks


def _local_asset(repo_root: Path, entry: dict[str, Any]) -> Path:
    raw = str(entry.get("file") or entry.get("asset") or "")
    if raw.startswith("/static/"):
        return repo_root / "miniapp" / raw.removeprefix("/static/")
    if raw.startswith("miniapp/"):
        return repo_root / raw
    return repo_root / "miniapp" / raw.lstrip("/")


def validate_assets(repo_root: Path) -> dict[str, Any]:
    """Return a machine-readable report; never silently repairs a manifest."""
    errors: list[str] = []
    decks: list[dict[str, Any]] = []
    expected_by_deck = {
        "rws-78-geldard-v1": {f"m{index:02d}" for index in range(22)} | {
            f"{suit}{number:02d}" for suit in ("cups", "pents", "swords", "wands")
            for number in range(1, 15)},
        "lenormand-36-game-of-hope-v1": {
            f"{index:02d}-{slug}" for index, (slug, *_rest) in enumerate(
                tarot_decks.LENORMAND_CARDS, 1)},
        "marseille-78-conver-v1": {"m%02d" % index for index in range(22)} | {
            f"{suit}{number:02d}" for suit in ("cups", "pents", "swords", "wands")
            for number in range(1, 15)},
    }
    for deck_id, metadata in tarot_decks.DECK_METADATA.items():
        manifest_url = str(metadata["asset_manifest"])
        manifest_path = repo_root / "miniapp" / manifest_url.removeprefix("/static/")
        deck_report: dict[str, Any] = {"deck_id": deck_id, "manifest": str(manifest_path), "ok": True}
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            errors.append(f"{deck_id}: manifest unreadable: {exc}")
            deck_report["ok"] = False
            decks.append(deck_report)
            continue
        entries = manifest.get("cards") or []
        ids = set()
        for entry in entries:
            if entry.get("card_id"):
                ids.add(str(entry["card_id"]))
            elif entry.get("number") and entry.get("slug"):
                ids.add(f"{int(entry['number']):02d}-{entry['slug']}")
            else:
                ids.add(Path(str(entry.get("file", ""))).stem)
        expected = expected_by_deck[deck_id]
        if manifest.get("deck_id") != deck_id:
            errors.append(f"{deck_id}: manifest deck_id mismatch")
        if manifest.get("card_count") != metadata["card_count"] or len(entries) != metadata["card_count"]:
            errors.append(f"{deck_id}: card count mismatch")
        if ids != expected:
            errors.append(f"{deck_id}: card IDs mismatch missing={sorted(expected - ids)} extra={sorted(ids - expected)}")
        seen_files: set[str] = set()
        for entry in entries:
            asset_path = _local_asset(repo_root, entry)
            key = str(asset_path)
            if key in seen_files:
                errors.append(f"{deck_id}: duplicate asset path {asset_path}")
            seen_files.add(key)
            if not asset_path.is_file() or asset_path.stat().st_size == 0:
                errors.append(f"{deck_id}: missing asset {asset_path}")
                continue
            try:
                with Image.open(asset_path) as image:
                    image.verify()
            except Exception as exc:  # PIL raises format-specific exceptions
                errors.append(f"{deck_id}: unreadable asset {asset_path}: {exc}")
            expected_hash = entry.get("sha256")
            if expected_hash:
                actual_hash = hashlib.sha256(asset_path.read_bytes()).hexdigest()
                if actual_hash != expected_hash:
                    errors.append(f"{deck_id}: sha256 mismatch {asset_path}")
        deck_report.update({
            "manifest_cards": len(entries), "unique_ids": len(ids),
            "source_verification": manifest.get("source_verification") or manifest.get("asset_status") or "unspecified",
        })
        deck_report["ok"] = not any(error.startswith(f"{deck_id}:") for error in errors)
        decks.append(deck_report)
    return {"ok": not errors, "decks": decks, "errors": errors}
