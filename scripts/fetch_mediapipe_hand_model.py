from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path
from urllib.request import urlopen

MODEL_URL = 'https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task'
MODEL_SHA256 = 'fbc2a30080c3c557093b5ddfc334698132eb341044ccee322ccf8bcf3607cde1'
MODEL_SIZE = 7819105
DEFAULT_PATH = Path('models/hand_landmarker.task')
MANIFEST_PATH = Path('models/hand_landmarker.manifest.json')


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    target = Path(os.environ.get('ORACLEAI_MEDIAPIPE_MODEL', DEFAULT_PATH))
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.is_file() and target.stat().st_size == MODEL_SIZE and sha256(target) == MODEL_SHA256:
        print(json.dumps({'path': str(target), 'status': 'already_verified', 'sha256': MODEL_SHA256}))
        return
    fd, tmp_name = tempfile.mkstemp(prefix='.hand_landmarker.', dir=target.parent)
    os.close(fd)
    tmp = Path(tmp_name)
    try:
        with urlopen(MODEL_URL, timeout=60) as response, tmp.open('wb') as out:
            while chunk := response.read(1024 * 1024):
                out.write(chunk)
        actual_size = tmp.stat().st_size
        actual_sha = sha256(tmp)
        if actual_size != MODEL_SIZE or actual_sha != MODEL_SHA256:
            raise RuntimeError(f'model integrity check failed: size={actual_size}, sha256={actual_sha}')
        tmp.replace(target)
    finally:
        tmp.unlink(missing_ok=True)
    manifest = {
        'model': 'MediaPipe Hand Landmarker', 'url': MODEL_URL,
        'sha256': MODEL_SHA256, 'size_bytes': MODEL_SIZE,
        'license_note': 'Use under the MediaPipe/Google model terms applicable to this bundle; keep this provenance with the artifact.',
    }
    MANIFEST_PATH.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'path': str(target), 'status': 'downloaded_and_verified', 'sha256': MODEL_SHA256}))


if __name__ == '__main__':
    main()
