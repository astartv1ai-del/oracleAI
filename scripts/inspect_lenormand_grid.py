from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image

SOURCE = Path('/tmp/oracleai-lenormand-source/game-of-hope.png')


def intervals(values: np.ndarray, minimum: int) -> list[tuple[int, int]]:
    active = values >= minimum
    points = np.flatnonzero(active)
    if len(points) == 0:
        return []
    groups = []
    start = prev = int(points[0])
    for point in points[1:]:
        point = int(point)
        if point > prev + 1:
            groups.append((start, prev + 1))
            start = point
        prev = point
    groups.append((start, prev + 1))
    return groups


def main() -> None:
    image = np.asarray(Image.open(SOURCE).convert('RGB'))
    gray = image.mean(axis=2)
    ink = gray < 240
    x_counts = ink.sum(axis=0)
    y_counts = ink.sum(axis=1)
    print('shape', image.shape)
    print('x intervals', intervals(x_counts, int(image.shape[0] * 0.12)))
    print('y intervals', intervals(y_counts, int(image.shape[1] * 0.12)))
    # Report lower thresholds as a cross-check around the six-column/six-row grid.
    print('x intervals loose', intervals(x_counts, int(image.shape[0] * 0.04)))
    print('y intervals loose', intervals(y_counts, int(image.shape[1] * 0.04)))


if __name__ == '__main__':
    main()
