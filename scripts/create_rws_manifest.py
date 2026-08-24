from __future__ import annotations

import hashlib
import json
from pathlib import Path

from PIL import Image

from app.core.tarot import DECK

ROOT = Path('miniapp/img/tarot')
CATEGORY_URL = 'https://commons.wikimedia.org/wiki/Category:Rider-Waite-Smith_tarot_deck_(Geldard)'


def main() -> None:
    cards = []
    for card in DECK:
        path = ROOT / f"{card['img']}.jpg"
        if not path.is_file():
            raise SystemExit(f'missing RWS asset: {path}')
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        with Image.open(path) as image:
            size = list(image.size)
        cards.append({
            'card_id': card['img'], 'name': card['name'], 'arcana': card['arcana'],
            'suit': card['suit'], 'asset': f'/static/img/tarot/{path.name}',
            'sha256': digest, 'pixel_size': size,
        })
    manifest = {
        'deck_id': 'rws-78-geldard-v1',
        'label': 'Rider–Waite–Smith · Geldard', 'card_count': len(cards),
        'requested_source_category': CATEGORY_URL,
        'source_verification': 'asset_id_complete_individual_provenance_pending',
        'verification_note': 'All 78 canonical OracleAI card IDs have local readable assets and stable hashes. The repository does not yet prove that each local file was downloaded from its corresponding Geldard Commons file; do not represent this as per-file provenance.',
        'cards': cards,
    }
    (ROOT / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'deck_id': manifest['deck_id'], 'card_count': len(cards), 'status': manifest['source_verification']}))


if __name__ == '__main__':
    main()
