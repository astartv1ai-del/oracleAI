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
  margin: 18mm 16mm 20mm 16mm;
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
  font-size: 11pt;
  line-height: 1.62;
}
h1, h2, h3 { font-weight: normal; color: #e8c56b; }
h1 { font-size: 30pt; line-height: 1.15; margin: 0 0 8mm; }
h2 {
  font-size: 17pt;
  margin: 0 0 5mm;
  padding-bottom: 2mm;
  border-bottom: 1px solid rgba(232, 197, 107, .35);
}
h3 { font-size: 12.5pt; margin: 6mm 0 2mm; color: #f3dc9a; }
p { margin: 0 0 3.5mm; }
.muted { color: #a99fc9; }
.small { font-size: 9.5pt; }
.center { text-align: center; }

/* Разделы начинаются с новой страницы: разбор читают по частям, а не подряд */
.section { page-break-before: always; }
.section:first-of-type { page-break-before: avoid; }

.cover { text-align: center; padding-top: 22mm; }
.cover .sub { color: #a99fc9; font-size: 12pt; margin-top: 4mm; }
.cover .who {
  margin-top: 14mm;
  font-size: 15pt;
  color: #f4efff;
}
.cover .born { color: #a99fc9; font-size: 11pt; margin-top: 2mm; }

.card {
  border: 1px solid rgba(232, 197, 107, .30);
  border-radius: 4mm;
  padding: 5mm 6mm;
  margin: 0 0 5mm;
  background: rgba(255, 255, 255, .04);
}
.kv { display: flex; justify-content: space-between; gap: 6mm;
      padding: 1.6mm 0; border-bottom: 1px dotted rgba(255,255,255,.12); }
.kv:last-child { border-bottom: none; }
.kv b { color: #e8c56b; font-weight: normal; }

table { width: 100%; border-collapse: collapse; }
td { padding: 1.6mm 0; vertical-align: top; }
td.label { color: #a99fc9; width: 42%; }

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
    for planet in (chart.get("planets") or []):
        deg = planet.get("abs_deg") or 0
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


def matrix_svg(matrix: dict, size: int = 300) -> str:
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
        label = item["title"].replace("Аркан ", "").replace("Линия ", "")
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


def document(title: str, blocks: list[str]) -> str:
    """Собирает готовую HTML-страницу разбора."""
    body = "\n".join(blocks)
    return (f'<!DOCTYPE html><html lang="ru"><head><meta charset="utf-8">'
            f'<title>{esc(title)}</title><style>{PAGE_CSS}</style></head>'
            f'<body>{body}</body></html>')
