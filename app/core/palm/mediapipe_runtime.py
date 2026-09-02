"""Process-local, thread-safe MediaPipe Hand Landmarker runtime."""
from __future__ import annotations

import io
import os
import tempfile
import threading
from pathlib import Path
from typing import Any

from PIL import Image

from .. import palm_vision

ADAPTER_VERSION = "mediapipe-hand-landmarker-v2"
DEFAULT_MODEL_PATH = Path(__file__).resolve().parents[2] / "models" / "hand_landmarker.task"
MAX_DETECTION_SIDE = 1280
_LOCK = threading.Lock()
_DETECTOR: Any = None
_DETECTOR_KEY: str | None = None


def _model_path() -> Path:
    configured = os.getenv("ORACLEAI_MEDIAPIPE_MODEL", "").strip()
    return Path(configured).expanduser() if configured else DEFAULT_MODEL_PATH


def _empty(status: str, issues: list[str]) -> dict[str, Any]:
    return {
        "version": ADAPTER_VERSION,
        "status": status,
        "hands": [],
        "hand_count": 0,
        "issues": issues[:8],
        "model": "hand_landmarker_full_float16",
    }


def _get_detector(path: Path):
    global _DETECTOR, _DETECTOR_KEY
    key = str(path.resolve())
    with _LOCK:
        if _DETECTOR is not None and _DETECTOR_KEY == key:
            return _DETECTOR
        from mediapipe.tasks import python  # type: ignore[import-not-found]
        from mediapipe.tasks.python import vision  # type: ignore[import-not-found]

        options = vision.HandLandmarkerOptions(
            base_options=python.BaseOptions(model_asset_path=key),
            running_mode=vision.RunningMode.IMAGE,
            num_hands=2,
            min_hand_detection_confidence=0.65,
            min_hand_presence_confidence=0.65,
            min_tracking_confidence=0.65,
        )
        detector = vision.HandLandmarker.create_from_options(options)
        _DETECTOR = detector
        _DETECTOR_KEY = key
        return detector


def _landmark(item: Any) -> dict[str, float]:
    return {"x": round(float(item.x), 6), "y": round(float(item.y), 6), "z": round(float(item.z), 6)}


def analyze(image_bytes: bytes, *, model_path: str | None = None) -> dict[str, Any]:
    path = Path(model_path).expanduser() if model_path else _model_path()
    if not image_bytes:
        return _empty("invalid_image", ["image_empty"])
    quality = palm_vision.analyze(image_bytes)
    issues = set(quality.get("issues") or [])
    if quality.get("status") == "invalid_image":
        return _empty("invalid_image", ["image_decode_failed"])
    if quality.get("status") == "reshoot_recommended" and {
        "underexposed", "overexposed", "low_contrast_or_flat_light", "soft_or_blurred_edges",
    } & issues:
        return _empty("quality_limited", ["hand_detection_skipped_for_quality"])
    if not path.is_file():
        return _empty("model_missing", ["mediapipe_model_missing"])

    try:
        with Image.open(io.BytesIO(image_bytes)) as source:
            rgb = source.convert("RGB")
            original_width, original_height = rgb.size
            scale = min(1.0, MAX_DETECTION_SIDE / max(original_width, original_height))
            if scale < 1.0:
                rgb = rgb.resize(
                    (max(1, round(original_width * scale)), max(1, round(original_height * scale))),
                    Image.Resampling.LANCZOS,
                )
            width, height = rgb.size
            with tempfile.NamedTemporaryFile(suffix=".jpg") as tmp:
                rgb.save(tmp, format="JPEG", quality=92)
                tmp.flush()
                detector = _get_detector(path)
                mp_image = python_image_from_path(tmp.name)
                result = detector.detect(mp_image)
    except Exception as exc:  # noqa: BLE001
        return _empty("detection_error", [type(exc).__name__])

    hands = []
    for idx, landmarks in enumerate(result.hand_landmarks or []):
        handedness = "unknown"
        if idx < len(result.handedness):
            try:
                handedness = str(result.handedness[idx][0].category_name or "unknown")
            except (IndexError, AttributeError):
                pass
        hands.append({
            "handedness": handedness,
            "landmarks": [_landmark(item) for item in landmarks],
        })
    return {
        "version": ADAPTER_VERSION,
        "status": "ok" if hands else "no_hand",
        "hands": hands,
        "hand_count": len(hands),
        "issues": sorted(issues)[:8],
        "model": "hand_landmarker_full_float16",
        "image_size": {"width": width, "height": height},
        "source_size": {"width": original_width, "height": original_height},
    }


def python_image_from_path(path: str):
    from mediapipe import Image as MpImage, ImageFormat  # type: ignore[import-not-found]

    return MpImage.create_from_file(path)
