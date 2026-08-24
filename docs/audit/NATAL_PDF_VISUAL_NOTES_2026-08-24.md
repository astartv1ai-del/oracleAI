# Natal PDF visual notes — 2026-08-24

## Scope
Visual inspection of regenerated natal PDFs after the premium wheel, cover-wheel, and branded footer changes.

## Files checked
- `/tmp/oracleai-natal-cases/алексей-1990-03-21.pdf`
- `/home/ubuntu/Downloads/oracle-natal-report.pdf`

## Confirmed findings
1. **Cover page now includes a centered natal wheel** and remains a single readable A4 page.
2. **Birth metadata on cover now includes time when known**. Verified on Alexey case: `21.03.1990 · 08:15 · Москва`.
3. **Footer is branded** and visible as `OracleAI · N` on every inspected page, replacing the anonymous page number.
4. **Reference/overview page remains readable** after moving one wheel to the cover. Facts card, wheel, and matrix stay visually separated with no clipping.
5. **Pages 3–7 are not blank**. They contain tables and structured report sections; no empty filler pages were observed in the inspected Alexey PDF.
6. **No visible text-overlap or clipping** was observed on inspected pages 1–7 of the Alexey PDF.
7. Live browser-triggered export created a real binary PDF in Downloads:
   - `/home/ubuntu/Downloads/oracle-natal-report.pdf`
   - `file`: PDF document, version 1.7
   - `pdfinfo`: 7 pages, A4, producer WeasyPrint 69.0

## Remaining caveat to keep in final report
- The cover wheel is visually premium and centered, but literal geometry sharing between web and PDF is still implemented as **parallel replicated contracts**, not a single imported geometry module. Final report should describe this honestly.
