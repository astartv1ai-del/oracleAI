"""Full-scope palm CV evidence for Mira.

This adapter deliberately searches for candidate creases and geometry across the
complete palmistry catalog. It does not label a candidate as a semantic line and
does not interpret palmistry; the vision model is the final visual adjudicator.
Raw pixels, edge maps and masks are never returned or persisted.
"""
from __future__ import annotations

import io
import math
from typing import Any

from PIL import Image, ImageOps, UnidentifiedImageError

ADAPTER_VERSION = "palm-full-scope-cv-v1"
MAX_SIDE = 1280
MAX_CANDIDATES = 64

LINE_CATALOG = (
    "life_line", "head_line", "heart_line", "fate_line", "sun_line",
    "mercury_line", "relationship_lines", "children_lines", "travel_lines",
    "girdle_of_venus", "ring_of_solomon", "ring_of_apollo", "via_lasciva",
    "mars_lines", "influence_lines", "bracelets",
)
ZONE_CATALOG = LINE_CATALOG + ("mounts", "fingers", "markings")
FOLDED_EDGE_ONLY = {"relationship_lines", "children_lines", "travel_lines"}


def _empty(status: str, issues: list[str]) -> dict[str, Any]:
    return {
        "version": ADAPTER_VERSION,
        "status": status,
        "view_type": "unclear",
        "engine": "opencv_candidate_search",
        "candidate_count": 0,
        "candidate_segments": [],
        "line_catalog": list(LINE_CATALOG),
        "zone_evidence": _zone_evidence("unclear", 0, None),
        "issues": issues[:8],
        "raw_edge_map_stored": False,
        "raw_mask_stored": False,
        "limitations": [
            "Candidate crease search only; semantic line labels require vision adjudication.",
            "No candidate is a palmistry interpretation or a medical/predictive claim.",
        ],
    }


def _view_type(hand_geometry: dict[str, Any] | None) -> str:
    hands = (hand_geometry or {}).get("hands") or []
    if not hands:
        return "unclear"
    points = hands[0].get("landmarks") or []
    if len(points) < 21:
        return "unclear"
    # MediaPipe indices: tips 4/8/12/16/20; MCP joints 2/5/9/13/17.
    tips = (4, 8, 12, 16, 20)
    mcps = (2, 5, 9, 13, 17)
    extended = sum(
        1 for tip, mcp in zip(tips, mcps)
        if float(points[tip].get("y", 0.0)) < float(points[mcp].get("y", 0.0)) - 0.035
    )
    if extended >= 3:
        return "open_palm"
    if extended <= 1:
        return "folded_edge"
    return "unclear"


def _hand_mask(cv2, np, width: int, height: int, hand_geometry: dict[str, Any] | None):
    hands = (hand_geometry or {}).get("hands") or []
    if not hands:
        return None
    points = hands[0].get("landmarks") or []
    if len(points) < 21:
        return None
    coords = np.array([
        [int(max(0, min(width - 1, float(point.get("x", 0.0)) * width))),
         int(max(0, min(height - 1, float(point.get("y", 0.0)) * height)))]
        for point in points
    ], dtype=np.int32)
    hull = cv2.convexHull(coords)
    mask = np.zeros((height, width), dtype=np.uint8)
    cv2.fillConvexPoly(mask, hull, 255)
    kernel = np.ones((9, 9), dtype=np.uint8)
    return cv2.dilate(mask, kernel, iterations=2)


def _candidate_segments(cv2, np, gray, edges, hand_mask) -> list[dict[str, Any]]:
    if hand_mask is not None:
        scoped = cv2.bitwise_and(edges, edges, mask=hand_mask)
    else:
        scoped = edges
    height, width = gray.shape[:2]
    threshold = max(18, int(min(width, height) * 0.045))
    min_length = max(22, int(min(width, height) * 0.06))
    raw = cv2.HoughLinesP(
        scoped, 1, np.pi / 180.0, threshold=threshold,
        minLineLength=min_length, maxLineGap=max(8, int(min(width, height) * 0.018)),
    )
    if raw is None:
        return []
    candidates: list[dict[str, Any]] = []
    for line in raw[: MAX_CANDIDATES * 5]:
        values = np.asarray(line).reshape(-1)
        if values.size < 4:
            continue
        x1, y1, x2, y2 = [int(value) for value in values[:4]]
        length = math.hypot(x2 - x1, y2 - y1)
        if length < min_length:
            continue
        angle = math.degrees(math.atan2(y2 - y1, x2 - x1))
        region = gray[max(0, min(y1, y2)): min(height, max(y1, y2) + 1),
                      max(0, min(x1, x2)): min(width, max(x1, x2) + 1)]
        contrast = float(np.std(region)) if region.size else 0.0
        candidates.append({
            "x1": round(x1 / width, 4), "y1": round(y1 / height, 4),
            "x2": round(x2 / width, 4), "y2": round(y2 / height, 4),
            "length_px": round(length, 1),
            "angle_degrees": round(angle, 1),
            "local_contrast": round(min(1.0, contrast / 64.0), 3),
        })
    candidates.sort(key=lambda item: (item["length_px"], item["local_contrast"]), reverse=True)
    # Deduplicate nearly identical Hough segments to keep the evidence compact.
    unique: list[dict[str, Any]] = []
    for item in candidates:
        if any(
            abs(item["x1"] - old["x1"]) < 0.025
            and abs(item["y1"] - old["y1"]) < 0.025
            and abs(item["x2"] - old["x2"]) < 0.025
            and abs(item["y2"] - old["y2"]) < 0.025
            for old in unique
        ):
            continue
        unique.append(item)
        if len(unique) >= MAX_CANDIDATES:
            break
    return unique


def _zone_evidence(view_type: str, candidate_count: int, hand_geometry: dict[str, Any] | None) -> dict[str, dict[str, Any]]:
    has_hand = bool((hand_geometry or {}).get("hand_count"))
    evidence: dict[str, dict[str, Any]] = {}
    for zone in ZONE_CATALOG:
        if zone in FOLDED_EDGE_ONLY and view_type == "open_palm":
            evidence[zone] = {
                "status": "not_visible", "engine": "capture_geometry",
                "requires_view": "folded_edge", "semantic_labeling": "vision_llm",
            }
        elif zone in FOLDED_EDGE_ONLY and view_type != "folded_edge":
            evidence[zone] = {
                "status": "requires_view", "engine": "capture_geometry",
                "requires_view": "folded_edge", "semantic_labeling": "vision_llm",
            }
        elif zone in {"mounts", "fingers"} and not has_hand:
            evidence[zone] = {
                "status": "unclear", "engine": "mediapipe_geometry_missing",
                "semantic_labeling": "vision_llm",
            }
        else:
            evidence[zone] = {
                "status": "candidate_search" if candidate_count else "unclear",
                "engine": "opencv_candidate_search",
                "semantic_labeling": "vision_llm",
            }
    return evidence


def analyze(image_bytes: bytes, *, hand_geometry: dict[str, Any] | None = None) -> dict[str, Any]:
    if not image_bytes:
        return _empty("invalid_image", ["image_empty"])
    try:
        import cv2
        import numpy as np
        with Image.open(io.BytesIO(image_bytes)) as source:
            source.verify()
        with Image.open(io.BytesIO(image_bytes)) as source:
            frame = ImageOps.exif_transpose(source).convert("RGB")
            original_width, original_height = frame.size
            scale = min(1.0, MAX_SIDE / max(original_width, original_height))
            if scale < 1.0:
                frame = frame.resize((round(original_width * scale), round(original_height * scale)), Image.Resampling.LANCZOS)
            rgb = np.asarray(frame)
        gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)
        median = float(np.median(enhanced))
        lower = int(max(0, 0.66 * median))
        upper = int(min(255, max(lower + 20, 1.33 * median)))
        edges = cv2.Canny(enhanced, lower, upper, apertureSize=3)
        resized_geometry = hand_geometry
        mask = _hand_mask(cv2, np, gray.shape[1], gray.shape[0], resized_geometry)
        candidates = _candidate_segments(cv2, np, gray, edges, mask)
        edge_density = float(np.count_nonzero(edges)) / float(edges.size or 1)
        view_type = _view_type(hand_geometry)
        return {
            "version": ADAPTER_VERSION,
            "status": "candidate_evidence" if candidates else "no_candidates",
            "view_type": view_type,
            "engine": "opencv_candidate_search",
            "image_size": {"width": original_width, "height": original_height},
            "working_size": {"width": int(gray.shape[1]), "height": int(gray.shape[0])},
            "edge_density": round(min(1.0, edge_density), 5),
            "candidate_count": len(candidates),
            "candidate_segments": candidates,
            "zone_evidence": _zone_evidence(view_type, len(candidates), hand_geometry),
            "line_catalog": list(LINE_CATALOG),
            "raw_edge_map_stored": False,
            "raw_mask_stored": False,
            "limitations": [
                "Candidate crease search only; semantic line labels require vision adjudication.",
                "Folded-edge relationship, children and travel lines require the folded-edge view.",
                "No candidate is a palmistry interpretation or a medical/predictive claim.",
            ],
        }
    except (ImportError, UnidentifiedImageError, OSError, ValueError):
        return _empty("unavailable", ["opencv_full_scope_unavailable"])
    except Exception:
        return _empty("runtime_error", ["opencv_full_scope_runtime_error"])
