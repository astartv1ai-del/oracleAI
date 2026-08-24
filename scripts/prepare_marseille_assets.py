from __future__ import annotations

import json
import urllib.request
from pathlib import Path

from PIL import Image

OUTPUT = Path('miniapp/img/marseille')
RAW_ROOT = 'https://raw.githubusercontent.com/mixvlad/TarotCards/main/tarot/marseille/full'
REPO_ROOT = 'https://github.com/mixvlad/TarotCards/tree/main/tarot/marseille'

MAJORS = [
    ('m00', '00_Le_Mat.png', 'The Fool'), ('m01', '01_Le_Bateleur.png', 'The Magician'),
    ('m02', '02_La_Papesse.png', 'The High Priestess'), ('m03', '03_L_Imperatrice.png', 'The Empress'),
    ('m04', '04_L_Empereur.png', 'The Emperor'), ('m05', '05_Le_Pape.png', 'The Hierophant'),
    ('m06', '06_L_Amoureux.png', 'The Lovers'), ('m07', '07_Le_Chariot.png', 'The Chariot'),
    ('m08', '08_La_Justice.png', 'Justice'), ('m09', '09_L_Ermite.png', 'The Hermit'),
    ('m10', '10_La_Roue_de_Fortune.png', 'Wheel of Fortune'), ('m11', '11_La_Force.png', 'Strength'),
    ('m12', '12_Le_Pendu.png', 'The Hanged Man'), ('m13', '13_La_Mort.png', 'Death'),
    ('m14', '14_Temperance.png', 'Temperance'), ('m15', '15_Le_Diable.png', 'The Devil'),
    ('m16', '16_La_Maison_Dieu.png', 'The Tower'), ('m17', '17_L_Etoile.png', 'The Star'),
    ('m18', '18_La_Lune.png', 'The Moon'), ('m19', '19_Le_Soleil.png', 'The Sun'),
    ('m20', '20_Le_Jugement.png', 'Judgement'), ('m21', '21_Le_Monde.png', 'The World'),
]
SUITS = {
    'cups': 'Cups', 'pents': 'Pents', 'swords': 'Swords', 'wands': 'Wands',
}


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    entries = []
    specs = list(MAJORS)
    for suit_slug, suit_name in SUITS.items():
        for number in range(1, 15):
            specs.append((f'{suit_slug}{number:02d}', f'{suit_name}{number:02d}.png', f'{suit_name} {number}'))
    for slug, filename, label in specs:
        url = f'{RAW_ROOT}/{filename}'
        target = OUTPUT / f'{slug}.jpg'
        with urllib.request.urlopen(url, timeout=30) as response:
            image = Image.open(response).convert('RGB')
            image.save(target, quality=90, optimize=True, progressive=True)
        entries.append({
            'card_id': slug, 'source_file': filename, 'source_url': f'{REPO_ROOT}/full/{filename}',
            'raw_url': url, 'license': 'Public domain (source metadata in mixvlad/TarotCards)',
            'label_en': label, 'asset': f'/static/img/marseille/{slug}.jpg', 'pixel_size': list(image.size),
        })
    manifest = {
        'deck_id': 'marseille-78-conver-v1',
        'label': 'Tarot de Marseille · historical public-domain reference',
        'card_count': len(entries), 'source_repo': REPO_ROOT,
        'license_note': 'Each source entry is marked public domain in the repository metadata; preserve source URLs and re-check jurisdiction before redistribution.',
        'cards': entries,
    }
    (OUTPUT / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    (OUTPUT / 'README.md').write_text(
        '# Tarot de Marseille — reference assets\n\n'
        '78 cards normalized from the historical/public-domain reference files in '
        f'[mixvlad/TarotCards]({REPO_ROOT}). Keep the manifest source URLs and license note. '
        'This deck has its own majors/minors visual tradition and must not inherit RWS meanings silently.\n',
        encoding='utf-8',
    )
    print(json.dumps({'deck_id': manifest['deck_id'], 'cards': len(entries), 'output': str(OUTPUT)}))


if __name__ == '__main__':
    main()
