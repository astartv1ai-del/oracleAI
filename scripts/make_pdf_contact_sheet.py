from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

source = Path('/home/ubuntu/oracleAI/docs/audit/chart_engine_smoke/pdf_pages/final_clean')
files = sorted(source.glob('ru-*.png'))
thumb_w = 300
margin = 24
label_h = 34
with Image.open(files[0]) as sample:
    ratio = sample.height / sample.width
thumb_h = int(thumb_w * ratio)
cols = 3
rows = (len(files) + cols - 1) // cols
sheet = Image.new('RGB', (cols * (thumb_w + margin) + margin, rows * (thumb_h + label_h + margin) + margin), '#0c0a1d')
draw = ImageDraw.Draw(sheet)
font = ImageFont.load_default()
for index, path in enumerate(files):
    with Image.open(path).convert('RGB') as image:
        image.thumbnail((thumb_w, thumb_h), Image.Resampling.LANCZOS)
        x = margin + (index % cols) * (thumb_w + margin)
        y = margin + (index // cols) * (thumb_h + label_h + margin)
        sheet.paste(image, (x, y))
        draw.text((x, y + thumb_h + 8), path.stem, fill='#f4d88b', font=font)
out = source / 'contact_sheet.png'
sheet.save(out, optimize=True)
print(out)
