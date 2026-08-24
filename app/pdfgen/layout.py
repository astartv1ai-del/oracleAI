"""Вёрстка PDF: страница, типографика, колесо карты, октаграмма Матрицы.

Один визуальный язык с Mini App — те же цвета и тот же «дорогой мистический»
тон. Покупательница, пришедшая с маркетплейса, должна узнать продукт, когда
откроет бота.

CSS ориентирован на печать: A4, поля, разрывы страниц по разделам. Всё внутри
одного файла без внешних ресурсов — PDF обязан собираться на машине без сети.
"""
from __future__ import annotations

import html
import math

PAGE_CSS = """
@page {
  size: A4;
  margin: 14mm 15mm 16mm 15mm;
  background: #0b0722;
  @bottom-center {
    content: "OracleAI · " counter(page);
    color: #6f6494;
    font-size: 8.5pt;
    font-family: Georgia, serif;
  }
}
* { box-sizing: border-box; }
body {
  margin: 0;
  background: #0b0722;
  color: #f4efff;
  font-family: Georgia, 'Times New Roman', serif;
  font-size: 10.5pt;
  line-height: 1.46;
  overflow-wrap: anywhere;
}
h1, h2, h3 { font-weight: normal; color: #e8c56b; }
h1 { font-size: 30pt; line-height: 1.08; margin: 0 0 7mm; }
h2 {
  font-size: 16pt;
  margin: 0 0 4mm;
  padding-bottom: 2mm;
  border-bottom: 1px solid rgba(232, 197, 107, .35);
}
h3 { font-size: 11.5pt; margin: 4mm 0 1.5mm; color: #f3dc9a; }
p { margin: 0 0 2.5mm; }
.muted { color: #a99fc9; }
.small { font-size: 9.5pt; }
.center { text-align: center; }

/* Разделы текут непрерывно; отдельный page break используется только для cover. */
.section { margin: 0 0 8mm; break-inside: auto; }
.section h2 { break-after: avoid; }
.cover {
  min-height: 245mm;
  text-align: center;
  padding: 20mm 10mm 12mm;
  page-break-after: always;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}
.cover .brand { color: #e8c56b; font-size: 12pt; letter-spacing: 2px; text-transform: uppercase; }
.cover .eyebrow { color: #a99fc9; font-size: 9pt; letter-spacing: 1.5px; text-transform: uppercase; margin: 6mm 0; }
.cover .sub { color: #a99fc9; font-size: 12pt; margin-top: 3mm; max-width: 125mm; }
.cover .who { margin-top: 13mm; font-size: 17pt; color: #f4efff; }
.cover .born { color: #a99fc9; font-size: 10.5pt; margin-top: 2mm; }
.cover .project-link { color: #e8c56b; font-size: 9.5pt; margin-top: 9mm; overflow-wrap: anywhere; }
.cover-wheel { width: 76mm; max-width: 100%; margin: 3mm auto 1mm; }
.cover-wheel svg { display: block; width: 100%; height: auto; max-width: 76mm; margin: 0 auto; }
.brand-mark { margin: 0 auto 4mm; }
.brand-mark svg { width: 43mm; height: 43mm; }

.overview-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 6mm; align-items: start; }
.overview-visuals { display: grid; gap: 3mm; justify-items: center; }
.overview-visuals .wheel { margin: 0; width: 100%; }
.overview-visuals svg { max-width: 100%; height: auto; }
.closing-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 5mm; margin-top: 5mm; }
.closing-grid .card { margin-bottom: 0; }
.closing-grid h3 { margin-top: 0; }

.card {
  border: 1px solid rgba(232, 197, 107, .30);
  border-radius: 4mm;
  padding: 4mm 5mm;
  margin: 0 0 4mm;
  background: rgba(255, 255, 255, .04);
}
.kv { display: flex; justify-content: space-between; gap: 6mm;
      padding: 1.6mm 0; border-bottom: 1px dotted rgba(255,255,255,.12); }
.kv:last-child { border-bottom: none; }
.kv b { color: #e8c56b; font-weight: normal; }

table { width: 100%; border-collapse: collapse; table-layout: fixed; }
td, th { padding: 1.15mm 1.1mm; vertical-align: top; overflow-wrap: anywhere; }
th { color: #e8c56b; text-align: left; font-weight: normal; border-bottom: 1px solid rgba(232,197,107,.35); }
td.label { color: #a99fc9; width: 42%; }
table.data-table { font-size: 8.6pt; line-height: 1.22; }
table.data-table td, table.data-table th { border-bottom: 1px dotted rgba(255,255,255,.12); }
.card, .ticket { break-inside: avoid; }

@media screen {
  body { font-size: 12pt; line-height: 1.55; padding: 12px; }
  .section { margin: 0 auto 28px; max-width: 760px; }
  .cover { padding-top: 28px; min-height: 0; }
  .cover-wheel { width: min(76mm, 100%); }
  h1 { font-size: 27pt; }
  h2 { font-size: 19pt; }
  .card { padding: 16px; border-radius: 14px; }
  td, th { padding: 7px 5px; }
  table.data-table { font-size: 10.5pt; line-height: 1.35; }
  .overview-grid { grid-template-columns: 1fr; }
  .closing-grid { grid-template-columns: 1fr; }
  .wheel svg { max-width: 100%; height: auto; }
}

@media print {
  body { overflow-wrap: normal; }
  .cover { page-break-after: always; }
  .overview-grid, .card, table, .ticket { break-inside: avoid; }
  tr { break-inside: avoid; }
}

.wheel { text-align: center; margin: 4mm 0 6mm; }
.ticket {
  margin-top: 8mm;
  border: 1.4px dashed #e8c56b;
  border-radius: 4mm;
  padding: 7mm;
  text-align: center;
  background: rgba(232, 197, 107, .07);
}
.ticket .code {
  font-family: 'DejaVu Sans Mono', monospace;
  font-size: 20pt;
  letter-spacing: 3px;
  color: #e8c56b;
  margin: 4mm 0;
}
.disclaimer { color: #6f6494; font-size: 8.5pt; margin-top: 10mm; }
"""

SIGN_GLYPHS = ["♈", "♉", "♊", "♋", "♌", "♍", "♎", "♏", "♐", "♑", "♒", "♓"]
PLANET_GLYPHS = {
    "Солнце": "☉", "Луна": "☽", "Меркурий": "☿", "Венера": "♀", "Марс": "♂",
    "Юпитер": "♃", "Сатурн": "♄", "Уран": "♅", "Нептун": "♆", "Плутон": "♇",
    "Раху (Северный узел)": "☊", "Кету (Южный узел)": "☋", "Лилит (Чёрная Луна)": "⚸",
    "Хирон": "⚷", "Джуно": "⚵", "Церера": "⚳", "Веста": "⚶", "Паллада": "⚴",
}


def esc(text) -> str:
    return html.escape(str(text if text is not None else ""))


def paragraphs(text: str) -> str:
    """Текст модели → абзацы. Теги <b>/<i> из бота вычищаем: тут своя вёрстка."""
    clean = (text or "").replace("<b>", "").replace("</b>", "") \
                        .replace("<i>", "").replace("</i>", "")
    out = []
    for block in clean.split("\n"):
        block = block.strip()
        if not block:
            continue
        # строка-заголовок раздела от модели («1. Кто ты по карте»)
        if len(block) < 80 and block.rstrip().endswith(":"):
            out.append(f"<h3>{esc(block.rstrip(':'))}</h3>")
        else:
            out.append(f"<p>{esc(block)}</p>")
    return "\n".join(out)


def wheel_svg(chart: dict, size: int = 330) -> str:
    """Premium natal wheel with shared geometry, aspect lines and label lanes."""
    cx = cy = size / 2
    outer = size * .455
    zodiac = size * .385
    house_ring = size * .315
    aspect_ring = size * .255
    marker_base = size * .285
    lane_step = max(size * .035, 7)
    sign_colors = ["#e9b27e", "#c8b58a", "#b9b9d8", "#9cc7d8"]

    def norm(value) -> float:
        return (float(value or 0) % 360 + 360) % 360

    def polar(deg: float, radius: float) -> tuple[float, float]:
        angle = math.radians(norm(deg) - 90)
        return cx + math.cos(angle) * radius, cy + math.sin(angle) * radius

    def arc_path(start: float, end: float, r0: float, r1: float) -> str:
        sweep = (norm(end) - norm(start)) % 360 or 30
        large = 1 if sweep > 180 else 0
        a0 = polar(start, r1)
        b0 = polar(start + sweep, r1)
        a1 = polar(start, r0)
        b1 = polar(start + sweep, r0)
        return (f"M {a0[0]:.1f} {a0[1]:.1f} A {r1:.1f} {r1:.1f} 0 {large} 1 {b0[0]:.1f} {b0[1]:.1f} "
                f"L {b1[0]:.1f} {b1[1]:.1f} A {r0:.1f} {r0:.1f} 0 {large} 0 {a1[0]:.1f} {a1[1]:.1f} Z")

    parts = [
        f'<circle cx="{cx}" cy="{cy}" r="{outer:.1f}" fill="none" stroke="rgba(232,197,107,.55)" stroke-width=".8"/>',
        f'<circle cx="{cx}" cy="{cy}" r="{zodiac:.1f}" fill="none" stroke="rgba(255,255,255,.22)" stroke-width=".7"/>',
        f'<circle cx="{cx}" cy="{cy}" r="{size * .16:.1f}" fill="rgba(20,12,48,.18)" stroke="rgba(255,255,255,.14)" stroke-width=".7"/>',
    ]
    for i in range(12):
        start = i * 30
        parts.append(f'<path d="{arc_path(start, start + 30, zodiac, outer - size * .022)}" fill="{sign_colors[i % 4]}" opacity=".055"/>')
        tick_a = polar(start, zodiac)
        tick_b = polar(start, outer - size * .025)
        parts.append(f'<line x1="{tick_a[0]:.1f}" y1="{tick_a[1]:.1f}" x2="{tick_b[0]:.1f}" y2="{tick_b[1]:.1f}" stroke="rgba(255,255,255,.22)" stroke-width=".65"/>')
        label = polar(start + 15, outer - size * .045)
        parts.append(f'<text x="{label[0]:.1f}" y="{label[1] + size * .014:.1f}" fill="{sign_colors[i % 4]}" font-size="{max(10, size * .052):.1f}" text-anchor="middle">{SIGN_GLYPHS[i]}</text>')

    houses = chart.get("houses") or []
    house_points = houses or [{"n": i + 1, "abs_deg": i * 30} for i in range(12)]
    for i, house in enumerate(house_points):
        deg = house.get("abs_deg") if house.get("abs_deg") is not None else i * 30
        p0 = polar(deg, size * .16)
        p1 = polar(deg, house_ring)
        dash = "2 2" if houses else "1 3"
        parts.append(f'<line x1="{p0[0]:.1f}" y1="{p0[1]:.1f}" x2="{p1[0]:.1f}" y2="{p1[1]:.1f}" stroke="rgba(255,255,255,.16)" stroke-width=".6" stroke-dasharray="{dash}"/>')
        if houses:
            label = polar(float(deg) + 13, size * .205)
            parts.append(f'<text x="{label[0]:.1f}" y="{label[1] + size * .01:.1f}" fill="#a99fc9" font-size="{max(7, size * .031):.1f}" text-anchor="middle">{esc(house.get("n", i + 1))}</text>')

    planets = list(chart.get("planets") or [])
    nodes = [node for node in chart.get("nodes") or []
             if str(node.get("name", "")).startswith(("Раху", "Кету"))]
    entries = ([{"point": point, "index": index, "is_node": False}
                for index, point in enumerate(planets)]
               + [{"point": point, "index": index, "is_node": True}
                  for index, point in enumerate(nodes)])
    placed: list[dict] = []
    radial_lanes = [0, -1, 1, -2, 2, -3, 3, -4, 4, -5, 5]
    angle_offsets = [0]
    for step in range(8, 177, 8):
        angle_offsets.extend((-step, step))

    def marker_radius(entry: dict) -> float:
        return max(6, size * .034) if entry["is_node"] else max(7, size * .042)

    def base_radius(entry: dict) -> float:
        return size * .335 if entry["is_node"] else marker_base

    for entry in sorted(entries, key=lambda item: norm(item["point"].get("abs_deg_exact", item["point"].get("abs_deg")))):
        point = entry["point"]
        deg = norm(point.get("abs_deg_exact", point.get("abs_deg")))
        candidates: list[dict] = []
        for offset in angle_offsets:
            for lane in radial_lanes:
                radius = max(size * .17, min(size * .39, base_radius(entry) + lane * lane_step))
                display_deg = norm(deg + offset)
                x, y = polar(display_deg, radius)
                clearance = marker_radius(entry) + size * .012
                collision = any(
                    math.hypot(item["x"] - x, item["y"] - y)
                    < marker_radius(item) + clearance for item in placed
                )
                candidate = {**entry, "deg": deg, "display_deg": display_deg,
                             "radius": radius, "x": x, "y": y, "collision": collision}
                candidates.append(candidate)
                if not collision:
                    break
            if candidates and not candidates[-1]["collision"]:
                break
        selected = next((candidate for candidate in candidates if not candidate["collision"]), None)
        if selected is None:
            selected = max(
                candidates,
                key=lambda candidate: min(
                    (math.hypot(item["x"] - candidate["x"], item["y"] - candidate["y"])
                     for item in placed), default=float("inf")))
        placed.append(selected)

    positions: dict[str, tuple[float, float]] = {}
    for item in placed:
        point = item["point"]
        x, y = item["x"], item["y"]
        positions[point.get("name", "")] = (x, y)
        glyph = PLANET_GLYPHS.get(point.get("name", ""), "•")
        stroke = "#a78bfa" if item["is_node"] else "#e6c178"
        fill = "#c7b1ff" if item["is_node"] else "#ffd98f"
        parts.append(f'<g><circle cx="{x:.1f}" cy="{y:.1f}" r="{marker_radius(item):.1f}" fill="rgba(20,16,39,.94)" stroke="{stroke}" stroke-width=".8"/><text x="{x:.1f}" y="{y + size * .015:.1f}" fill="{fill}" font-size="{max(8, size * .05):.1f}" text-anchor="middle">{esc(glyph)}</text>')
        if point.get("retro"):
            parts.append(f'<text x="{x + size * .027:.1f}" y="{y - size * .025:.1f}" fill="#e88f8f" font-size="{max(6, size * .027):.1f}">R</text>')
        parts.append('</g>')

    for aspect in (chart.get("aspects") or [])[:10]:
        first = positions.get(aspect.get("p1"))
        second = positions.get(aspect.get("p2"))
        if not first or not second:
            continue
        x1 = cx + (first[0] - cx) * aspect_ring / marker_base
        y1 = cy + (first[1] - cy) * aspect_ring / marker_base
        x2 = cx + (second[0] - cx) * aspect_ring / marker_base
        y2 = cy + (second[1] - cy) * aspect_ring / marker_base
        color = {"△": "#e6c178", "□": "#a78bfa", "☍": "#e99b96"}.get(aspect.get("glyph"), "#b8b1c9")
        dash = "" if aspect.get("glyph") in {"△", "⚹"} else "3 3"
        parts.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{color}" stroke-width=".65" stroke-dasharray="{dash}" opacity=".55"/>')

    sun = chart.get("sun") or {}
    if sun:
        parts.append(f'<text x="{cx}" y="{cy + size * .018:.1f}" fill="#e8c56b" font-size="{max(20, size * .085):.1f}" text-anchor="middle">{esc(sun.get("symbol", "☉"))}</text>')
    return (f'<svg viewBox="0 0 {size} {size}" width="{size}" height="{size}" preserveAspectRatio="xMidYMid meet" '
            f'xmlns="http://www.w3.org/2000/svg">{"".join(parts)}</svg>')


def matrix_svg(matrix: dict, size: int = 300, labels: dict[str, str] | None = None) -> str:
    """Октаграмма Матрицы Судьбы: два наложенных квадрата и арканы по вершинам."""
    cx = cy = size / 2
    R = size * 0.38
    parts = []
    for rot in (0, 45):
        points = " ".join(
            f"{cx + R * math.cos(math.radians(a + rot - 90)):.1f},"
            f"{cy + R * math.sin(math.radians(a + rot - 90)):.1f}"
            for a in (0, 90, 180, 270))
        parts.append(f'<polygon points="{points}" fill="none" '
                     f'stroke="rgba(232,197,107,.45)" stroke-width="1.1"/>')

    keys = ["personal", "spirit", "family", "destiny", "love", "money"]
    items = [matrix[k] for k in keys if k in matrix]
    for i, item in enumerate(items):
        a = math.radians(i * 60 - 90)
        x, y = cx + R * math.cos(a), cy + R * math.sin(a)
        label = (labels or {}).get(item.get("title"), item["title"])
        label = label.replace("Arcana ", "").replace("Line ", "")
        label = label.replace("Аркан ", "").replace("Линия ", "")
        parts.append(
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="20" fill="#140c30" '
            f'stroke="rgba(232,197,107,.55)"/>'
            f'<text x="{x:.1f}" y="{y + 5:.1f}" fill="#e8c56b" font-size="14" '
            f'text-anchor="middle">{item["n"]}</text>'
            f'<text x="{x:.1f}" y="{y + 33:.1f}" fill="#a99fc9" font-size="8" '
            f'text-anchor="middle">{esc(label)}</text>')

    center = matrix.get("center")
    if center:
        parts.append(
            f'<circle cx="{cx}" cy="{cy}" r="25" fill="#140c30" '
            f'stroke="rgba(232,197,107,.55)"/>'
            f'<text x="{cx}" y="{cy + 5}" fill="#e8c56b" font-size="16" '
            f'text-anchor="middle">{center["n"]}</text>')

    return (f'<svg viewBox="0 0 {size} {size}" width="{size}" height="{size}" '
            f'xmlns="http://www.w3.org/2000/svg">{"".join(parts)}</svg>')


def brand_mark_svg(size: int = 180) -> str:
    """Минималистичный векторный знак OracleAI для cover без внешних assets."""
    center = size / 2
    return (f'<svg viewBox="0 0 {size} {size}" xmlns="http://www.w3.org/2000/svg" '
            f'role="img" aria-label="OracleAI">'
            f'<circle cx="{center}" cy="{center}" r="65" fill="none" stroke="#e8c56b" stroke-width="2"/>'
            f'<circle cx="{center}" cy="{center}" r="48" fill="#140c30" stroke="#a99fc9" stroke-width="1"/>'
            f'<path d="M{center-18} {center+30} A38 38 0 1 1 {center+18} {center-30} A28 28 0 1 0 {center-18} {center+30}" fill="#e8c56b"/>'
            f'<circle cx="{center+55}" cy="{center-47}" r="4" fill="#e8c56b"/>'
            f'<circle cx="{center-63}" cy="{center+18}" r="2.5" fill="#a99fc9"/>'
            f'</svg>')


def document(title: str, blocks: list[str], *, lang: str = "ru") -> str:
    """Собирает готовую responsive HTML-страницу разбора."""
    body = "\n".join(blocks)
    html_lang = "en" if (lang or "").lower().startswith("en") else "ru"
    return (f'<!DOCTYPE html><html lang="{html_lang}"><head><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">'
            f'<meta name="theme-color" content="#0b0722">'
            f'<title>{esc(title)}</title><style>{PAGE_CSS}</style></head>'
            f'<body>{body}</body></html>')
