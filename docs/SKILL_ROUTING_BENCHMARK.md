# Подробный отчёт: multilingual skill routing

> Это benchmark маршрутизации skills, а не тест качества финального LLM-ответа. Успех означает, что expected skill попал в детерминированный top-3 контекст.

## Итог

На curated-наборе из **20** запросов top-3 pass: **20/20 (100.0%)**; top-1: **20/20 (100.0%)**; MRR: **1.000**.

Исторический результат до targeted fixes составлял 15/20 (75%). Финальная версия улучшилась на **+25 процентных пунктов top-3**. Это доказательство на 20 заданных случаях, а не универсальная production accuracy.

| Срез | Cases | Top-1 | Top-3 | Accuracy top-3 |
|---|---:|---:|---:|---:|
| Urania / astro | 10 | 10/10 | 10/10 | 100.0% |
| Lilith / oracle | 10 | 10/10 | 10/10 | 100.0% |
| Русский | 2 | 2/2 | 2/2 | 100.0% |
| English | 9 | 9/9 | 9/9 | 100.0% |
| Mixed/code-switched | 9 | 9/9 | 9/9 | 100.0% |

## Все 20 запросов

| # | Agent | Язык | Intent | Запрос | Expected | Фактический top-3 | Rank | Top-3 | Signals | Anti-Barnum/dependency |
|---:|---|---|---|---|---|---|---:|---|---|---|
| 1 | `astro` | `ru` | nodes/Rahu-Ketu | Покажи Раху и Кету и объясни их ось | `lunar-nodes` | `lunar-nodes` → `lunar-phases` → `chart-synthesis` | 1 | PASS | `lunar_node` | yes |
| 2 | `astro` | `en` | synastry | Can you compare our synastry aspects without mind-reading? | `compatibility-synastry` | `compatibility-synastry` → `synastry-boundaries` → `aspects` | 1 | PASS | `compare`, `synastry`, `mind`, `reading`, `without`, `aspects` | yes |
| 3 | `astro` | `mixed` | houses and angles | my natal chart: Асцендент, MC and houses | `houses-and-angles` | `houses-and-angles` → `natal-chart-foundations` → `chart-synthesis` | 1 | PASS | `ascendant`, `houses`, `chart`, `natal` | yes |
| 4 | `astro` | `mixed` | retrogrades | Ретроградный Меркурий и practical checks | `retrogrades` | `retrogrades` → `aspects` → `astrology-history` | 1 | PASS | `retrograde` | yes |
| 5 | `astro` | `en` | Western transits | What are the current transits of Saturn for my chart? | `transits` | `transits` → `chart-synthesis` → `saturn-and-boundaries` | 1 | PASS | `current`, `transits`, `chart`, `saturn` | yes |
| 6 | `astro` | `mixed` | expanded points | Что показывают Хирон, Джуно и expanded points? | `chart-synthesis` | `chart-synthesis` → `lunar-nodes` → `nakshatra-pada` | 1 | PASS | `chiron`, `expanded`, `juno`, `points` | yes |
| 7 | `astro` | `en` | date-only safety | No birth time: can you name the house of Rahu? | `date-only-mode` | `date-only-mode` → `houses-and-angles` → `lunar-nodes` | 1 | PASS | `birth`, `house`, `rahu`, `time` | no |
| 8 | `astro` | `en` | date comparison | Compare two launch dates using my criteria, not a guarantee | `electional-reflection` | `electional-reflection` → `anti-barnum-protocol` → `career-symbolism` | 1 | PASS | `compare`, `criteria`, `dates`, `using` | yes |
| 9 | `astro` | `mixed` | career timing | career timing по карте — give criteria, not certainty | `career-symbolism` | `career-symbolism` → `electional-reflection` → `anti-barnum-protocol` | 1 | PASS | `career`, `criteria`, `timing`, `certainty` | yes |
| 10 | `astro` | `ru` | lunar phases/journal | Лунные фазы и дневник наблюдений на неделю | `lunar-phases` | `lunar-phases` | 1 | PASS | `diary`, `дневник`, `лунные`, `фазы` | yes |
| 11 | `oracle` | `mixed` | Matrix reading | Разбери мой аркан судьбы: ресурс, тень и choice | `matrix-reading` | `matrix-reading` → `emotion-naming` → `matrix-lines` | 1 | PASS | `arcana`, `choice`, `fate` | yes |
| 12 | `oracle` | `en` | emotion naming | Help me name what I feel after that conversation | `emotion-naming` | `emotion-naming` → `conversation-rehearsal` → `answer-structure` | 1 | PASS | `after`, `conversation`, `feel`, `name`, `what` | yes |
| 13 | `oracle` | `mixed` | boundary design | Мне нужно design a boundary в переписке | `boundary-design` | `boundary-design` → `answer-structure` → `career-reflection` | 1 | PASS | `boundary`, `design` | yes |
| 14 | `oracle` | `mixed` | memory privacy | Что ты помнишь обо мне, если memory disabled? | `memory-recall` | `memory-recall` → `memory-save-decision` → `answer-structure` | 1 | PASS | `memory` | no |
| 15 | `oracle` | `en` | habit loop | Why do I keep scrolling at night? Find the habit loop | `habit-loop` | `habit-loop` → `emotion-naming` → `matrix-reading` | 1 | PASS | `habit`, `loop` | yes |
| 16 | `oracle` | `mixed` | relationship pattern | Что я могу наблюдать в repeated relationship pattern? | `relationship-reflection` | `relationship-reflection` → `pattern-mapping` → `anti-barnum-protocol` | 1 | PASS | `relationship`, `pattern` | yes |
| 17 | `oracle` | `en` | values conflict | I am choosing stability or an exciting project | `values-conflict` | `values-conflict` → `matrix-reading` | 1 | PASS | `exciting`, `project`, `stability` | yes |
| 18 | `oracle` | `mixed` | practice selection | Подбери gentle practice for more спокойствия | `practice-selection` | `practice-selection` → `practice-follow-through` → `matrix-reading` | 1 | PASS | `practice` | no |
| 19 | `oracle` | `en` | diary review | Review my diary themes this month | `diary-dynamics` | `diary-dynamics` → `monthly-review` → `matrix-reading` | 1 | PASS | `diary`, `themes`, `this`, `review` | yes |
| 20 | `oracle` | `en` | conversation rehearsal | Help me rehearse a difficult conversation | `conversation-rehearsal` | `conversation-rehearsal` → `emotion-naming` → `pattern-mapping` | 1 | PASS | `conversation`, `difficult`, `rehearse` | yes |

## Method and interpretation

The generator calls the same `select_skills(profile, query, 3)` function used by the harness. The selected order is the actual deterministic top-3 order. Signals are lexical/tag overlaps used to make the result reviewable; they are not hidden reasoning. `anti_barnum_or_dependency` flags when the selected context contains the shared safety skill or a skill with declared dependencies.

The current router is intentionally bounded and deterministic. The benchmark does not test response truthfulness, chart calculation correctness, latency or live LLM behavior. The next routing phase should add adversarial paraphrases, top-1/MRR release thresholds and safety-critical date-only cases.

## Reproducibility

```bash
PYTHONPATH=. python3 scripts/benchmark_skill_routing.py
PYTHONPATH=. python3 scripts/report_skill_routing.py
```

Source files: `scripts/benchmark_skill_routing.py`, `scripts/report_skill_routing.py`, `tests/test_agent_file_harness.py`, `scripts/check_agent_quality.py`. 
