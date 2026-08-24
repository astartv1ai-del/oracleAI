from __future__ import annotations

import json
from pathlib import Path

from PIL import Image

SOURCE = Path('/tmp/oracleai-lenormand-source/game-of-hope.png')
OUTPUT = Path('miniapp/img/lenormand')
SOURCE_URL = 'https://commons.wikimedia.org/wiki/File:Das_Spiel_der_Hofnung_(The_Game_of_Hope).png'
SOURCE_LICENSE = 'Public domain status as stated on the Wikimedia Commons file page; preserve source attribution and re-check jurisdiction before redistribution.'

NAMES = [
    ('rider', 'Rider', 'Всадник'), ('clover', 'Clover', 'Клевер'), ('ship', 'Ship', 'Корабль'),
    ('house', 'House', 'Дом'), ('tree', 'Tree', 'Дерево'), ('clouds', 'Clouds', 'Облака'),
    ('snake', 'Snake', 'Змея'), ('coffin', 'Coffin', 'Гроб'), ('bouquet', 'Bouquet', 'Букет'),
    ('scythe', 'Scythe', 'Коса'), ('whip', 'Whip', 'Метла'), ('birds', 'Birds', 'Птицы'),
    ('child', 'Child', 'Ребёнок'), ('fox', 'Fox', 'Лиса'), ('bear', 'Bear', 'Медведь'),
    ('stars', 'Stars', 'Звёзды'), ('stork', 'Stork', 'Аист'), ('dog', 'Dog', 'Собака'),
    ('tower', 'Tower', 'Башня'), ('garden', 'Garden', 'Сад'), ('mountain', 'Mountain', 'Гора'),
    ('crossroads', 'Crossroads', 'Развилка'), ('mice', 'Mice', 'Мыши'), ('heart', 'Heart', 'Сердце'),
    ('ring', 'Ring', 'Кольцо'), ('book', 'Book', 'Книга'), ('letter', 'Letter', 'Письмо'),
    ('man', 'Man', 'Мужчина'), ('woman', 'Woman', 'Женщина'), ('lily', 'Lily', 'Лилии'),
    ('sun', 'Sun', 'Солнце'), ('moon', 'Moon', 'Луна'), ('key', 'Key', 'Ключ'),
    ('fish', 'Fish', 'Рыбы'), ('anchor', 'Anchor', 'Якорь'), ('cross', 'Cross', 'Крест'),
]

X_BOUNDS = [(135, 677), (730, 1282), (1350, 1906), (1969, 2517), (2580, 3129), (3208, 3761)]
Y_BOUNDS = [(115, 846), (914, 1642), (1703, 2430), (2495, 3212), (3270, 3988), (4063, 4769)]


def main() -> None:
    if not SOURCE.exists():
        raise SystemExit(f'Missing source: {SOURCE}')
    OUTPUT.mkdir(parents=True, exist_ok=True)
    image = Image.open(SOURCE).convert('RGB')
    if image.size != (3900, 4900):
        raise SystemExit(f'Unexpected source size: {image.size}')
    manifest_cards = []
    for index, (slug, en, ru) in enumerate(NAMES, 1):
        row, col = divmod(index - 1, 6)
        x0, x1 = X_BOUNDS[col]
        y0, y1 = Y_BOUNDS[row]
        # Keep a small amount of the historical border; remove only white gutter.
        crop = image.crop((x0 - 4, y0 - 4, x1 + 4, y1 + 4))
        target = OUTPUT / f'{index:02d}-{slug}.jpg'
        crop.save(target, quality=90, optimize=True, progressive=True)
        manifest_cards.append({
            'number': index, 'slug': slug, 'name_en': en, 'name_ru': ru,
            'file': str(target), 'pixel_size': list(crop.size), 'source_board_number': index,
        })
    manifest = {
        'deck_id': 'lenormand-36-game-of-hope-v1',
        'deck_name': 'Das Spiel der Hofnung / The Game of Hope',
        'card_count': 36,
        'asset_status': 'historical-reference-assets',
        'source_url': SOURCE_URL,
        'license': SOURCE_LICENSE,
        'source_dimensions': [3900, 4900],
        'grid': '6x6 row-major, manually verified with overlapping tiles',
        'cards': manifest_cards,
    }
    (OUTPUT / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    (OUTPUT / 'README.md').write_text(
        '# Lenormand 36 — historical reference assets\n\n'
        'These card images are conservative crops from the public-domain historical board '
        '“Das Spiel der Hofnung / The Game of Hope”. Keep the source URL and license note in '
        'the manifest when redistributing. This is a historical visual reference deck, not '
        'a claim that every modern Lenormand school uses identical artwork or meanings.\n\n'
        f'Source: {SOURCE_URL}\n\nLicense note: {SOURCE_LICENSE}\n',
        encoding='utf-8',
    )
    print(json.dumps({'deck_id': manifest['deck_id'], 'cards': len(manifest_cards), 'output': str(OUTPUT)}, ensure_ascii=False))


if __name__ == '__main__':
    main()
