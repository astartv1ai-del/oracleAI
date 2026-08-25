from pathlib import Path
from kerykeion import AstrologicalSubjectFactory
from kerykeion.chart_data_factory import ChartDataFactory
from kerykeion.charts.chart_drawer import ChartDrawer
import resvg_py

out = Path('/home/ubuntu/oracleAI/docs/audit/chart_engine_smoke/style_compare')
out.mkdir(parents=True, exist_ok=True)
subject = AstrologicalSubjectFactory.from_birth_data(
    name='oracle', year=1990, month=6, day=21, hour=14, minute=30,
    city='-', lat=55.79, lng=49.12, tz_str='Europe/Moscow', online=False,
    zodiac_type='Tropical', houses_system_identifier='P',
    perspective_type='Apparent Geocentric',
)
data = ChartDataFactory.create_natal_chart_data(subject)
for style in ('classic', 'modern'):
    svg = ChartDrawer(chart_data=data, chart_language='RU', theme='dark', style=style).generate_wheel_only_svg_string(
        remove_css_variables=True, style=style, show_zodiac_background_ring=False,
    )
    png = resvg_py.svg_to_bytes(svg_string=svg, background='#0c0a1d', width=1200, height=1200)
    (out / f'{style}.png').write_bytes(png)
    print(style, len(svg), len(png))
