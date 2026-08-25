from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from kerykeion import AstrologicalSubjectFactory
from kerykeion.chart_data_factory import ChartDataFactory
from kerykeion.charts.chart_drawer import ChartDrawer
import resvg_py

OUT = Path('/home/ubuntu/oracleAI/docs/audit/chart_engine_variants_2026-08-26')
OUT.mkdir(parents=True, exist_ok=True)
BG = '#0c0a1d'

VARIANTS = [
    ('A', 'Classic dark · clean', 'dark', 'classic', False),
    ('B', 'Classic dark · contrast', 'dark-high-contrast', 'classic', False),
    ('C', 'Modern dark · clean', 'dark', 'modern', False),
    ('D', 'Modern dark · zodiac ring', 'dark', 'modern', True),
    ('E', 'Modern dark · contrast ring', 'dark-high-contrast', 'modern', True),
    ('F', 'Classic warm · editorial', 'classic', 'classic', False),
]

subject = AstrologicalSubjectFactory.from_birth_data(
    name='oracle', year=1990, month=6, day=21, hour=14, minute=30,
    city='-', lat=55.79, lng=49.12, tz_str='Europe/Moscow', online=False,
    zodiac_type='Tropical', houses_system_identifier='P',
    perspective_type='Apparent Geocentric',
)
data = ChartDataFactory.create_natal_chart_data(subject)

font_candidates = [
    '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
    '/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf',
]
font_path = next((p for p in font_candidates if Path(p).exists()), None)
font = ImageFont.truetype(font_path, 30) if font_path else ImageFont.load_default()
small = ImageFont.truetype(font_path, 21) if font_path else ImageFont.load_default()

cards = []
for code, label, theme, style, ring in VARIANTS:
    svg = ChartDrawer(chart_data=data, chart_language='RU', theme=theme, style=style).generate_wheel_only_svg_string(
        remove_css_variables=True, style=style, show_zodiac_background_ring=ring,
    )
    png = resvg_py.svg_to_bytes(svg_string=svg, background=BG, width=1000, height=1000)
    path = OUT / f'{code}.png'
    path.write_bytes(png)
    with Image.open(path).convert('RGB') as image:
        image.thumbnail((560, 560), Image.Resampling.LANCZOS)
        card = Image.new('RGB', (600, 690), '#15112c')
        card.paste(image, ((600 - image.width) // 2, 24))
        draw = ImageDraw.Draw(card)
        draw.text((24, 590), f'{code}  {label}', fill='#f4d88b', font=font)
        draw.text((24, 635), f'theme={theme}  style={style}  zodiac_ring={ring}', fill='#b8add4', font=small)
        cards.append(card)

sheet = Image.new('RGB', (1200, 2190), '#0c0a1d')
draw = ImageDraw.Draw(sheet)
draw.text((40, 28), 'OracleAI natal chart — visual variants', fill='#f4d88b', font=font)
draw.text((40, 72), 'Same synthetic chart, same calculations; choose by letter.', fill='#b8add4', font=small)
for i, card in enumerate(cards):
    x = (i % 2) * 600
    y = 120 + (i // 2) * 690
    sheet.paste(card, (x, y))
sheet.save(OUT / 'comparison_sheet.png', optimize=True)
print(f'created {len(cards)} variants in {OUT}')
