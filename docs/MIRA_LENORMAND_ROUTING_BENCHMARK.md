# Mira / Madame Lenormand skill routing benchmark

**Benchmark:** 20 difficult RU/EN/code-switched requests; expected skill must be present in bounded top-3.

| Metric | Result |
| --- | ---: |
| Cases | 20 |
| Top-3 expected-skill inclusion | 20/20 (100.0%) |
| Top-1 | 14/20 (70.0%) |

The benchmark measures routing, not interpretation quality. A top-3 hit means the skill is available to the downstream context resolver; top-1 is an improvement metric, not a promise that every real-world paraphrase will route identically.

| # | Agent | Request | Expected | Actual top-3 | Rank |
| ---: | --- | --- | --- | --- | ---: |
| 1 | `chiromant` | Разбери мою ладонь по этому снимку: что реально видно и какая уверенность? | `visual-evidence-protocol` | `visual-evidence-protocol` → `palm-angle-classification` → `palm-evidence-reading` | 1 |
| 2 | `chiromant` | Trace the life line: continuity, breaks, branches and visible path only | `palm-line-topology` | `life-line-continuity` → `palm-line-topology` → `life-line` | 2 |
| 3 | `chiromant` | Сравни Western, Indian Hasta и Chinese подходы к моей линии головы, но не смешивай школы | `palm-technique-triangulation` | `palm-technique-triangulation` → `photo-comparison` → `head-line` | 1 |
| 4 | `chiromant` | На открытой ладони видны ли линии брака и children? What photo should I take? | `capture-rectification` | `palm-photo-quality` → `capture-rectification` → `visual-evidence-protocol` | 2 |
| 5 | `chiromant` | Фото бликует и пальцы обрезаны — can you still read the mounts? | `capture-rectification` | `capture-rectification` → `visual-evidence-protocol` → `palm-photo-quality` | 1 |
| 6 | `chiromant` | What is visible about my heart/head/fate lines on the uploaded image? | `visual-evidence-protocol` | `visual-evidence-protocol` → `fate-line` → `fate-line-context` | 1 |
| 7 | `chiromant` | Скажи, что означает topology линии жизни: дуга, глубина, разрывы, но не срок жизни | `palm-line-topology` | `palm-line-topology` → `life-line` → `life-line-continuity` | 1 |
| 8 | `chiromant` | Can you compare my old and new palm photos and report only visible changes? | `photo-comparison` | `photo-comparison` → `visual-evidence-protocol` → `palm-photo-quality` | 1 |
| 9 | `chiromant` | Знаешь все техники хиромантии? Дай разницу между школами по одному видимому холму | `palm-technique-triangulation` | `palm-technique-triangulation` → `mounts-topography` → `mounts` | 1 |
| 10 | `chiromant` | Can palm lines show disease, pregnancy or death? | `palm-safety` | `palm-safety` → `palm-evidence-reading` → `palm-photo-quality` | 1 |
| 11 | `tarot` | После draw покажи deck, position, card ID и upright/reversed ledger | `card-ledger-evidence` | `card-ledger-evidence` → `card-position-semantics` → `tarot-proof-safety` | 1 |
| 12 | `tarot` | Explain the adjacent pair and repeated suit pattern, not isolated card meanings | `combination-synthesis` | `card-ledger-evidence` → `combination-synthesis` → `card-position-semantics` | 2 |
| 13 | `tarot` | Я не знаю, что спросить: what will happen in my life? Помоги выбрать spread | `question-to-spread` | `question-to-spread` → `three-card-spread` → `career-spread` | 1 |
| 14 | `tarot` | Покажи checksum расклада и объясни, что он доказывает, а чего не доказывает | `tarot-proof-safety` | `question-to-spread` → `tarot-proof-safety` → `three-card-spread` | 2 |
| 15 | `tarot` | Two reversed cards together: compare their orientation tension and offer a counter-reading | `combination-synthesis` | `reversed-cards` → `combination-synthesis` → `card-ledger-evidence` | 2 |
| 16 | `tarot` | What does my ex think and will they return? Reframe this before drawing | `question-to-spread` | `question-to-spread` → `reversed-cards` → `tarot-proof-safety` | 1 |
| 17 | `tarot` | Can the cards decide a legal case or investment for me? | `tarot-proof-safety` | `tarot-proof-safety` → `card-ledger-evidence` → `court-cards` | 1 |
| 18 | `tarot` | Для ежедневного journal reflection лучше one-card или Celtic Cross? | `question-to-spread` | `card-ledger-evidence` → `question-to-spread` → `card-combinations` | 2 |
| 19 | `tarot` | Read all ten Celtic Cross positions from the actual stored cards without adding cards | `card-ledger-evidence` | `card-ledger-evidence` → `reversed-cards` → `court-cards` | 1 |
| 20 | `tarot` | Tarot vs Lenormand: clarify deck tradition and select the smallest useful spread | `question-to-spread` | `question-to-spread` → `three-card-spread` → `tarot-proof-safety` | 1 |

## Interpretation

Mira cases cover visual evidence, line topology, school comparison, capture/rectification, photo comparison and safety. Madame Lenormand cases cover card ledger, adjacent combinations, question-to-spread, proof boundaries, reversals, high-risk reframing and Celtic Cross position discipline.

The routing fixes deliberately use domain intent signals and preserve legacy behavior: a generic `расклад таро` still routes to `three-card-spread`, while explicit ledger/combinations/proof requests activate the new specialist skills.

## Reproduction

```bash
PYTHONPATH=. python3 scripts/benchmark_mira_lenormand.py
PYTHONPATH=. python3 scripts/check_agent_quality.py
```
