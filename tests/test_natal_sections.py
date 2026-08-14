from __future__ import annotations

from app.core import astro


def _chart(*, exact: bool) -> dict:
    planets = [
        {"name": "Солнце", "sign": "Лев", "deg": 10.0, "abs_deg": 130.0, "house": 1 if exact else None, "retro": False},
        {"name": "Луна", "sign": "Рак", "deg": 8.0, "abs_deg": 98.0, "house": 12 if exact else None, "retro": False},
        {"name": "Меркурий", "sign": "Дева", "deg": 4.0, "abs_deg": 154.0, "house": 2 if exact else None, "retro": False},
        {"name": "Венера", "sign": "Весы", "deg": 16.0, "abs_deg": 196.0, "house": 3 if exact else None, "retro": False},
        {"name": "Марс", "sign": "Скорпион", "deg": 2.0, "abs_deg": 212.0, "house": 4 if exact else None, "retro": False},
    ]
    return {
        "mode": "full",
        "precision": "exact" if exact else "date_only",
        "sun": {"sign": "Лев", "symbol": "☉", "element": "огонь"},
        "ascendant": {"sign": "Рак", "deg": 12.0, "abs_deg": 102.0} if exact else None,
        "mc": {"sign": "Овен", "deg": 4.0} if exact else None,
        "planets": planets,
        "houses": ([
            {"n": 2, "sign": "Лев", "deg": 1.0},
            {"n": 6, "sign": "Стрелец", "deg": 7.0},
            {"n": 7, "sign": "Козерог", "deg": 13.0},
            {"n": 10, "sign": "Овен", "deg": 4.0},
        ] if exact else []),
        "aspects": [],
        "nodes": [
            {"name": "Раху (Северный узел)", "sign": "Близнецы", "deg": 22.0},
            {"name": "Кету (Южный узел)", "sign": "Стрелец", "deg": 22.0},
        ],
    }


def test_chart_sections_cover_required_user_topics() -> None:
    result = astro.chart_sections(_chart(exact=True), time_known=True)
    sections = result["sections"]
    assert result["exact"] is True
    assert set(sections) == {"identity", "mind_career", "relationships", "nodes"}
    labels = {item["label"] for section in sections.values() for item in section["items"]}
    assert {"Солнце", "Луна", "Асцендент", "Меркурий", "Марс", "Карьера", "Финансы", "Венера", "7-й дом", "Кету · Южный узел", "Раху · Северный узел"} <= labels
    assert "буквальную прошлую жизнь" in sections["nodes"]["intro"]
    assert sections["mind_career"]["items"][-1]["available"] is True


def test_chart_sections_hide_unreliable_houses_without_birth_time() -> None:
    result = astro.chart_sections(_chart(exact=False), time_known=False)
    sections = result["sections"]
    assert result["exact"] is False
    identity = {item["label"]: item for item in sections["identity"]["items"]}
    assert identity["Солнце"]["available"] is True
    assert identity["Асцендент"]["available"] is False
    career = {item["label"]: item for item in sections["mind_career"]["items"]}
    assert career["Карьера"]["available"] is False
    assert career["Финансы"]["available"] is False
    assert "точные дома" in sections["mind_career"]["note"]
