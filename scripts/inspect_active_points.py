from __future__ import annotations

from app.core.astro import ACTIVE_POINTS
from kerykeion import AstrologicalSubjectFactory

model = AstrologicalSubjectFactory.from_birth_data(
    name="points", year=1990, month=6, day=21, hour=14, minute=30,
    city="Kazan", lat=55.79, lng=49.12, tz_str="Europe/Moscow", online=False,
    active_points=ACTIVE_POINTS,
)
for point in ACTIVE_POINTS:
    attr = point.lower()
    value = getattr(model, attr, None)
    print(point, "->", attr, type(value).__name__ if value is not None else "MISSING")
