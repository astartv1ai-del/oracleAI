import inspect
from kerykeion.charts.chart_drawer import ChartDrawer
from kerykeion import AstrologicalSubjectFactory

print("ChartDrawer", inspect.signature(ChartDrawer))
for name in ["generate_wheel_only_svg_string", "generate_svg_string", "save_wheel_only_svg_file"]:
    print(name, inspect.signature(getattr(ChartDrawer, name)))
subject = AstrologicalSubjectFactory.from_birth_data(
    name="fixture", year=1990, month=7, day=15, hour=10, minute=30,
    lat=41.9028, lng=12.4964, tz_str="Europe/Rome", online=False,
)
print("subject", type(subject).__name__)
