# Natal chart visual variants — 2026-08-26

All variants use the same synthetic exact chart and identical canonical calculations. Only Kerykeion theme/style/ring presentation changes.

## Selected production variant

**A — Classic dark · clean** was selected for production because it has the clearest separation of outer and inner circles, lower visual density, and better readability of aspect lines. Production configuration is Kerykeion `theme="dark"`, `style="classic"`, `show_zodiac_background_ring=False`, rendered by resvg onto `#0c0a1d`.

The selected style is applied through `app/core/chart_rendering.py`, which is shared by the authenticated Mini App image endpoint and the PDF print path. Cache namespace was bumped to invalidate prior modern-style raster images.

## Comparison files

| File | Variant |
|---|---|
| `A.png` | Classic dark, clean |
| `B.png` | Classic dark, high contrast |
| `C.png` | Modern dark, clean |
| `D.png` | Modern dark, zodiac ring |
| `E.png` | Modern dark, high contrast ring |
| `F.png` | Classic warm, editorial |
| `comparison_sheet.png` | Labeled comparison sheet |
| `selected_A_full.png` | Selected style at 1200×1200 full-view render |

Synthetic RU/EN PDFs were regenerated after selection; the RU artifact is 10 pages and the house-cusp page remains a dedicated larger-type page.
