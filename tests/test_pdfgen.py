"""PDF-разборы: честный фолбэк на HTML, когда WeasyPrint не установлен (G28).

Без WeasyPrint нельзя молча подсунуть HTML с расширением .pdf — покупательница
получит битый файл. Проверяем, что `render_pdf` отдаёт `.html`-путь и пишет
тот самый HTML, а `to_pdf_bytes` прямо падает.
"""
from __future__ import annotations

import math
import xml.etree.ElementTree as ET

import pytest

from app.pdfgen import render


def test_to_pdf_bytes_raises_when_unavailable(monkeypatch):
    monkeypatch.setattr(render, "available", lambda: False)
    with pytest.raises(render.PdfUnavailable):
        render.to_pdf_bytes("<p>hello</p>")


def test_render_pdf_falls_back_to_html(monkeypatch, tmp_path):
    monkeypatch.setattr(render, "available", lambda: False)
    out = tmp_path / "разбор.pdf"

    actual = render.render_pdf("<p>привет</p>", out)

    assert actual.suffix == ".html", "молчаливый .pdf вместо HTML запрещён"
    assert actual.name == out.with_suffix(".html").name
    assert actual.read_text() == "<p>привет</p>"


@pytest.mark.asyncio
async def test_full_natal_report_contains_extended_chart_and_mobile_viewport(monkeypatch):
    from app.pdfgen import builder

    async def fake_geo(*_args, **_kwargs):
        return 55.79, 49.12, "Europe/Moscow"

    monkeypatch.setattr(builder.geo, "resolve_city_async", fake_geo)
    monkeypatch.setattr(builder.llm, "enabled", lambda: False)
    order = builder.Order(
        name="Анна", birth_date="1990-06-21", birth_time="14:30", birth_city="Казань"
    )

    html = await builder.generate(None, order, concurrency=1)

    assert 'name="viewport"' in html
    assert "Раху" in html and "Кету" in html
    assert "Хирон" in html and "Джуно" in html
    assert "Куспиды домов" in html and "Ключевые аспекты" in html
    assert "Placidus" in html and "Tropical" in html
    assert "https://github.com/astartv1ai-del/oracleAI" in html
    assert 'class="cover-wheel"' in html
    assert html.count('<svg viewBox="0 0 300 300"') >= 2
    assert "Анна" in html and "21.06.1990 · 14:30 · Казань" in html
    assert 'content: "OracleAI · " counter(page)' in html



def test_pdf_wheel_separates_extreme_close_degree_cluster():
    from app.pdfgen import layout

    names = ["Солнце", "Луна", "Меркурий", "Венера", "Марс", "Юпитер",
             "Сатурн", "Уран", "Нептун", "Плутон"]
    chart = {
        "sun": {"symbol": "☉", "sign": "Овен"},
        "planets": [
            {"name": name, "sign": "Овен", "abs_deg": 12 + i * .55}
            for i, name in enumerate(names)
        ],
        "nodes": [
            {"name": "Раху (Северный узел)", "sign": "Овен", "abs_deg": 12.2},
            {"name": "Кету (Южный узел)", "sign": "Овен", "abs_deg": 12.7},
        ],
        "houses": [], "aspects": [],
    }
    root = ET.fromstring(layout.wheel_svg(chart, size=260))
    marker_circles = [
        (float(node.attrib["cx"]), float(node.attrib["cy"]), float(node.attrib["r"]))
        for node in root.iter()
        if node.tag.endswith("circle") and float(node.attrib.get("r", 0)) in {10.9, 8.8}
    ]
    assert len(marker_circles) == 12
    minimum_clearance = min(
        math.hypot(a[0] - b[0], a[1] - b[1]) - a[2] - b[2]
        for i, a in enumerate(marker_circles)
        for b in marker_circles[i + 1:]
    )
    assert minimum_clearance > 0


@pytest.mark.asyncio
async def test_english_natal_report_is_localized(monkeypatch):
    from app.pdfgen import builder

    async def fake_geo(*_args, **_kwargs):
        return 55.79, 49.12, "Europe/Moscow"

    monkeypatch.setattr(builder.geo, "resolve_city_async", fake_geo)
    monkeypatch.setattr(builder.llm, "enabled", lambda: False)
    order = builder.Order(
        name="Anna", birth_date="1990-06-21", birth_time="14:30",
        birth_city="Kazan", lang="en",
    )

    html = await builder.generate(None, order, concurrency=1)

    assert '<html lang="en">' in html
    assert "Full natal chart and Destiny Matrix report" in html
    assert "Your chart in numbers" in html
    assert "Lunar nodes: Rahu and Ketu" in html
    assert "Additional points" in html
    assert "Chiron" in html and "Juno" in html
    assert "Destiny Matrix" in html
    assert "https://github.com/astartv1ai-del/oracleAI" in html
    assert 'class="cover-wheel"' in html
    assert "Anna" in html and "21.06.1990 · 14:30 · Kazan" in html
    assert 'content: "OracleAI · " counter(page)' in html
    assert "Натальная карта: полный расчёт" not in html
    assert "Кто ты по своей карте" not in html
