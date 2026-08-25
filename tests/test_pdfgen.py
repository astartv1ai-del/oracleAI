"""PDF-разборы: честный фолбэк на HTML, когда WeasyPrint не установлен (G28).

Без WeasyPrint нельзя молча подсунуть HTML с расширением .pdf — покупательница
получит битый файл. Проверяем, что `render_pdf` отдаёт `.html`-путь и пишет
тот самый HTML, а `to_pdf_bytes` прямо падает.
"""
from __future__ import annotations

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
    assert 'class="natal-print-image"' in html
    assert 'data:image/png;base64,' in html
    assert 'width="2400" height="2400"' in html
    assert "data-contract-version=\"1\"" not in html
    assert "Линии аспектов" in html
    assert "Print image rendered by the mature chart engine" not in html
    assert "source SVG never leaves the server render pipeline" not in html
    assert "house-reference" in html
    assert "aspect-reference" in html
    assert "https://github.com/astartv1ai-del/oracleAI" in html


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
    assert "Aspect lines" in html
    assert 'class="natal-print-image"' in html
    assert 'data:image/png;base64,' in html
    assert 'width="2400" height="2400"' in html
    assert "data-contract-version=\"1\"" not in html
    assert "Calculation contract" in html
    assert "Print image rendered by the mature chart engine" not in html
    assert "source SVG never leaves the server render pipeline" not in html
    assert "house-reference" in html
    assert "aspect-reference" in html
    assert "https://github.com/astartv1ai-del/oracleAI" in html
    assert "Натальная карта: полный расчёт" not in html
    assert "Кто ты по своей карте" not in html
