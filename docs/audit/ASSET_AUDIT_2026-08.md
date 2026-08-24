# OracleAI — asset audit, 2026-08

## Initial findings

The current Tarot JPEGs are full card scans. Their light outer paper/card surface is part of the source artwork rather than a transparent cutout; simply applying `mix-blend-mode` would damage the card colors and legibility. The correct product treatment is a dark stage/container with a controlled neutral card shadow, not aggressive blending. A representative Rider–Waite–Smith card was visually inspected at `miniapp/img/tarot/m00.jpg`.

The existing `miniapp/img/og-card.jpg` is already a dark, gold-on-midnight composition with no accidental white rectangle. It can remain the public social preview asset while the in-product hero should use a new CSS/SVG visual rather than the decorative image as a sticker.

The deterministic corner audit found many Tarot JPEGs with light corners because of their physical card border, while `tarot-back.png` has dark opaque corners. This is an asset treatment issue, not evidence that every light pixel must be removed. Follow-up work should focus on locating actual UI wrappers that expose the card as an isolated white rectangle, then fix the stage/background/radius/shadow or replace only genuinely foreign label assets.


## v105 follow-up

The home hero now uses a concise value proposition — `Твоя точка опоры на сегодня` / `A clear point of support for today` — while the personal greeting is a secondary line. The phase renderer now outputs a reusable SVG moon with radial shading, rim and restrained glow; the same primitive is used in hero and lunar list contexts, so the visual language is consistent across scales.

The Tarot card white paper edge was retained intentionally because it belongs to the Rider–Waite–Smith scan and is necessary for card legibility. Its surrounding stage is dark, neutral and shadow-controlled; no white label/background asset was introduced. The current v105 mobile runner again reports `horizontalOverflow: false` for all checked widths and surfaces.
