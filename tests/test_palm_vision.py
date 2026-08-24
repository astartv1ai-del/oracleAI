from __future__ import annotations

import io

from PIL import Image, ImageDraw

from app.core import palm_vision


def _image_bytes(kind: str) -> bytes:
    image = Image.new("RGB", (640, 640), "gray" if kind == "flat" else "white")
    if kind == "checker":
        draw = ImageDraw.Draw(image)
        for row in range(0, 640, 40):
            for col in range(0, 640, 40):
                if (row // 40 + col // 40) % 2:
                    draw.rectangle((col, row, col + 39, row + 39), fill="black")
    output = io.BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()


def test_precheck_rejects_invalid_image_without_guessing():
    result = palm_vision.analyze(b"not-an-image")
    assert result["status"] == "invalid_image"
    assert result["score"] == 0.0
    assert result["hand_detection"] == "not_attempted"


def test_precheck_flags_flat_capture():
    result = palm_vision.analyze(_image_bytes("flat"))
    assert result["status"] == "reshoot_recommended"
    assert "low_contrast_or_flat_light" in result["issues"]
    assert result["line_segmentation"] == "not_attempted"


def test_precheck_produces_bounded_metrics_for_usable_capture():
    result = palm_vision.analyze(_image_bytes("checker"))
    assert result["status"] == "usable"
    assert 0.0 <= result["score"] <= 1.0
    assert result["width"] == 640 and result["height"] == 640
    assert 0.0 <= result["brightness"] <= 255.0
    assert result["version"] == "palm-precheck-v1"
