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
