# Независимый human/domain review PALM

## Что проверяет независимый critic

`palm_independent_critic.py` — это context-light static critic. Он не вызывает LLM, не считает mocked provider response точностью и не читает raw images. Он проверяет наблюдаемые инварианты исходного кода и наличие review-инфраструктуры.

| Блок | Что проверяется | Текущий результат |
|---|---|---|
| Deterministic contract | versioned evidence contract, enum states, strict closed JSON, MIME/signature checks, animated-image rejection | `PASS` |
| Capture/CV boundary | `no_hand`/`multiple_hands`, `vision_skipped`, palm-hull scope, no raw masks/edges | `PASS` |
| Safety | prompt-injection sanitizer, forbidden-claims policy, Mira `PALM_LIMITATION` handoff | `PASS` |
| UX | RU/EN dictionary, folded-edge guidance, stale-locale refresh path | `PASS` |
| Regression cases | adversarial text, multiple hands, folded edge, MIME mismatch, weak evidence | `PASS` |
| Semantic accuracy | adjudicated image corpus, two independent labels, domain review, exact prediction coverage | `BLOCKED` until supplied |

Ключевой verdict — **`SHIP WITH ACCURACY GATE`**. Это означает, что deterministic guardrails проходят, но система не получает неподтверждённый знак semantic accuracy.

## Почему semantic accuracy заблокирована

Блокировка не означает обнаруженную ошибку в code contract. Она означает отсутствие необходимых независимых данных и human sign-off:

1. В репозитории нет `data/palm_golden/manifest.jsonl` с adjudicated records; существует только безопасный template.
2. Для каждой записи нужны два независимых annotators, иначе нельзя измерить inter-reviewer agreement.
3. Для `test`/`challenge` records нужен domain reviewer, который разрешает disagreement и опасные false positives.
4. Predictions должны покрывать manifest ровно по `record_id`, а изображения должны проверяться по immutable SHA-256.
5. Любое повышение `unknown`/`not_supported` до `observed`/`inferred` считается critical false-observed promotion и блокирует sign-off.
6. Unit tests и deterministic synthetic contract frames проверяют safety/uncertainty boundaries, но не доказывают семантическое качество palmistry interpretation.

## Как сформировать corpus

Raw images не добавляются в Git. Поместите их в защищённый каталог review storage, предоставьте consent/provenance и создайте `data/palm_golden/manifest.jsonl` по [`schema.json`](../../data/palm_golden/schema.json). Для старта можно скопировать [`manifest.template.jsonl`](../../data/palm_golden/manifest.template.jsonl) и [`predictions.template.jsonl`](../../data/palm_golden/predictions.template.jsonl), после чего заменить все placeholders.

Рекомендуемая первая выборка — 60 записей: 20 usable open-palm, 10 partial/cropped, 10 low-light/blur/glare, 8 folded-edge, 6 no-hand/artifact, 4 multiple-hands и 2 visual-text adversarial. Это sampling target, а не готовая accuracy dataset. Изображения одного человека или одной серийной съёмки нельзя распределять между разными split.

Для каждой записи reviewer размечает `capture` и `regions`. Минимальные open-palm regions: `palm_region`, `life_line`, `head_line`, `heart_line`, `mounts`, `fingers`; folded-edge topics (`relationship_lines`, `children_lines`, `travel_lines`) должны быть `unknown`/`not_visible`, если соответствующий ракурс отсутствует. Для folded-edge кадра эти зоны размечаются отдельно; labels нельзя переносить из другого ракурса.

`visibility` отвечает на вопрос «насколько зона видна», а `evidence_state` — «какой уровень утверждения допустим». Если есть сомнение между `observed` и `unknown`, выбирается более безопасный `unknown`. Нельзя записывать в labels диагнозы, возраст, дату события, количество детей, финансовый результат или другие prohibited claims.

## Процесс независимой разметки

Первый annotator размечает кадр без просмотра model output. Второй annotator независимо повторяет разметку. Domain reviewer получает только исходные labels, disagreement list и policy; он не должен «подгонять» label под prediction. После решения обновляются `adjudication.status=adjudicated`, `domain_reviewer`, `agreement` и `decision_note`.

Проверьте manifest структурно и, когда images доступны, с hash/signature:

```bash
python scripts/validate_palm_corpus.py \
  --manifest data/palm_golden/manifest.jsonl \
  --image-root /secure/palm-review-images
```

До появления приватного manifest CI использует безопасный structural smoke:

```bash
python scripts/validate_palm_corpus.py \
  --manifest data/palm_golden/manifest.template.jsonl \
  --schema-only
```

## Оценка predictions и финальный verdict

Approved evaluation adapter должен экспортировать только structured JSONL без `raw_image`, `image_bytes`, `data_url`, `provider_response` или `raw_provider_output`:

```bash
python scripts/run_palm_human_review.py \
  --manifest data/palm_golden/manifest.jsonl \
  --predictions /secure/palm-review/predictions.jsonl \
  --out artifacts/palm-human-review.json
```

Runner считает `region_state_accuracy`, `region_visibility_accuracy`, `unknown_safety_precision`, `false_observed_count`, capture-state mismatches и malformed prediction count. Код возврата `0` означает semantic sign-off `PASS`; код `2` означает `BLOCKED` и является ожидаемым результатом для incomplete/pending corpus.

Независимый critic можно запустить с отчётом review:

```bash
python scripts/palm_independent_critic.py \
  --review-report artifacts/palm-human-review.json \
  > artifacts/palm-independent-critic.json
```

`SEMANTIC SIGNOFF PASS` допускается только когда manifest adjudicated, prediction coverage exact, capture states совпадают, malformed/privacy violations отсутствуют и `false_observed_count=0`. Даже тогда domain owner должен вручную подписать release evidence; автоматический runner не заменяет ответственность reviewer.

## References

[1]: ../../scripts/palm_independent_critic.py "Independent static critic"
[2]: ../../scripts/validate_palm_corpus.py "Golden corpus validator"
[3]: ../../scripts/run_palm_human_review.py "Human/domain review runner"
[4]: ../../data/palm_golden/schema.json "Golden record JSON Schema"
[5]: ../../data/palm_golden/README.md "Annotation handbook"

## Требования к экспертам

Для каждой записи нужны **два независимых annotators**. Они должны пройти обучение по `palm-human-review-v1`, иметь зафиксированную `qualification_reference`, подтвердить attestation с `signed=true` и `blinded_review=true`, раскрыть конфликт интересов и не смотреть на prediction до своей первичной разметки. Один человек не может выступать обоими независимыми annotators.

Domain reviewer должен иметь документированную квалификацию по предметной области palmistry/evidence review и training по safety/uncertainty policy. Он должен быть независим от двух primary annotators, иметь роль `domain_reviewer`, активный статус, signed attestation и собственную `qualification_reference`. Он рассматривает disagreements и unsafe false positives, но не подменяет независимую первичную разметку.

Для `test` и `challenge` domain reviewer обязателен. `adjudication.status=adjudicated` допустим только при наличии `domain_reviewer`, согласованных disagreement notes и decision note. При сомнении reviewer обязан выбрать более безопасный `unknown`/`not_supported`, а не повышать label до `observed`.

## Автоматическая проверка новых записей в CI

После добавления или изменения `data/palm_golden/manifest.jsonl` CI сравнивает `record_id` и содержимое с base commit. Для каждого added/changed record gate требует валидные consent/provenance, два зарегистрированных annotators, signed/blinded attestation, domain reviewer, корректную region-state consistency и отсутствие raw/provider payload. Удаление записи фиксируется в diff и требует отдельного review владельца корпуса.

Приватный reviewer registry должен быть подготовлен по [`reviewer_registry.schema.json`](../../data/palm_golden/reviewer_registry.schema.json). В репозитории можно хранить только non-identifying reviewer IDs и ссылки на защищённые qualification/training records; персональные документы и raw images в Git не хранятся.

Команды локального CI-equivalent прогона:

```bash
python scripts/validate_palm_reviewer_registry.py \
  --registry data/palm_golden/reviewer_registry.json \
  --require-domain

python scripts/check_palm_corpus_diff.py \
  --manifest data/palm_golden/manifest.jsonl \
  --reviewers data/palm_golden/reviewer_registry.json \
  --base-ref origin/master

python scripts/validate_palm_corpus.py \
  --manifest data/palm_golden/manifest.jsonl \
  --reviewers data/palm_golden/reviewer_registry.json \
  --require-adjudicated
```

Если manifest ещё не добавлен, CI проверяет только template в `--schema-only` режиме и оставляет semantic sign-off заблокированным. Если manifest появился, отсутствие registry или неadjudicated новая запись делает job красным. Недоступный base ref также делает job красным; gate не принимает его за пустую историю. Удаление записи требует отдельного явного review владельца корпуса.
