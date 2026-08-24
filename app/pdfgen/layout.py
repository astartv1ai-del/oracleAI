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
    content: counter(page);
    color: #6f6494;
    font-size: 9pt;
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
.cover .project-link { color: #e8c56b; font-size: 9.5pt; margin-top: 12mm; overflow-wrap: anywhere; }
.brand-mark { margin: 0 auto 6mm; }
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
    """Натальное колесо: знаки, куспиды домов, планеты по долготе.

    Планеты, стоящие рядом, разводим по радиусу — иначе символы наезжают и
    колесо выглядит браком печати.
    """
    cx = cy = size / 2
    R = size * 0.47
    Rin = size * 0.36
    parts = [
        f'<circle cx="{cx}" cy="{cy}" r="{R:.1f}" fill="none" '
        f'stroke="rgba(232,197,107,.55)" stroke-width="1"/>',
        f'<circle cx="{cx}" cy="{cy}" r="{Rin:.1f}" fill="none" '
        f'stroke="rgba(255,255,255,.22)" stroke-width="1"/>',
        f'<circle cx="{cx}" cy="{cy}" r="{size * 0.17:.1f}" fill="none" '
        f'stroke="rgba(255,255,255,.14)" stroke-width="1"/>',
    ]

    for i in range(12):
        a = math.radians(i * 30 - 90)
        parts.append(
            f'<line x1="{cx + Rin * math.cos(a):.1f}" y1="{cy + Rin * math.sin(a):.1f}" '
            f'x2="{cx + R * math.cos(a):.1f}" y2="{cy + R * math.sin(a):.1f}" '
            f'stroke="rgba(255,255,255,.22)" stroke-width="0.8"/>')
        am = math.radians(i * 30 + 15 - 90)
        parts.append(
            f'<text x="{cx + (R - 15) * math.cos(am):.1f}" '
            f'y="{cy + (R - 15) * math.sin(am) + 4:.1f}" fill="#e8c56b" '
            f'font-size="13" text-anchor="middle">{SIGN_GLYPHS[i]}</text>')

    for house in (chart.get("houses") or []):
        a = math.radians((house.get("abs_deg") or 0) - 90)
        r0 = size * 0.17
        parts.append(
            f'<line x1="{cx + r0 * math.cos(a):.1f}" y1="{cy + r0 * math.sin(a):.1f}" '
            f'x2="{cx + Rin * math.cos(a):.1f}" y2="{cy + Rin * math.sin(a):.1f}" '
            f'stroke="rgba(255,255,255,.16)" stroke-width="0.7" '
            f'stroke-dasharray="3 3"/>')
        rl = size * 0.21
        parts.append(
            f'<text x="{cx + rl * math.cos(a):.1f}" y="{cy + rl * math.sin(a) + 3:.1f}" '
            f'fill="#a99fc9" font-size="8" text-anchor="middle">{house.get("n")}</text>')

    used: list[tuple[float, float]] = []
    wheel_points = list(chart.get("planets") or [])
    wheel_points.extend(
        node for node in (chart.get("nodes") or [])
        if node.get("name", "").startswith(("Раху", "Кету"))
    )
    for planet in wheel_points:
        deg = planet.get("abs_deg_exact", planet.get("abs_deg")) or 0
        radius = size * 0.28
        while any(abs(d - deg) < 9 and abs(r - radius) < 9 for d, r in used):
            radius -= size * 0.05
            if radius < size * 0.19:
                radius = size * 0.28
                break
        used.append((deg, radius))
        a = math.radians(deg - 90)
        px, py = cx + radius * math.cos(a), cy + radius * math.sin(a)
        glyph = PLANET_GLYPHS.get(planet.get("name", ""), "•")
        parts.append(
            f'<circle cx="{px:.1f}" cy="{py:.1f}" r="9" '
            f'fill="rgba(232,197,107,.14)"/>'
            f'<text x="{px:.1f}" y="{py + 4:.1f}" fill="#f4efff" font-size="12" '
            f'text-anchor="middle">{glyph}</text>')
        if planet.get("retro"):
            parts.append(f'<text x="{px + 8:.1f}" y="{py - 6:.1f}" fill="#e88f8f" '
                         f'font-size="7">R</text>')

    if not (chart.get("planets") or []) and chart.get("sun"):
        parts.append(
            f'<text x="{cx}" y="{cy + 14}" fill="#e8c56b" font-size="40" '
            f'text-anchor="middle">{esc(chart["sun"].get("symbol", "☉"))}</text>')

    return (f'<svg viewBox="0 0 {size} {size}" width="{size}" height="{size}" '
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
