# P2 Quality Gate

Этот документ фиксирует локальный quality gate для продуктовых P2-рисков. Он не заменяет ручную проверку клавиатуры, screen reader, Telegram WebView, production upload storage или внешний payment review. Его задача — не дать репозиторию потерять проверяемые контракты при последующих изменениях.

## Автоматические проверки

Из корня репозитория запускается:

```bash
LLM_PROVIDER=off EMBED_MODEL='' python3 scripts/check_p2_quality.py
```

Gate проверяет наличие tracked visual/accessibility evidence, отсутствие битых Markdown-ссылок, RU/EN key parity, наличие report-template contract, воспроизводимость offline performance benchmark и то, что Visual QA ссылается на tracked summaries.

| Check | Contract |
|---|---|
| Tracked evidence | Visual QA, localization, report-template и palm-upload документы существуют в репозитории. |
| Markdown hygiene | Локальные ссылки разрешаются в существующие файлы; внешние URL не проверяются как локальные. |
| Locale parity | Ключи основных RU/EN словарей Mini App совпадают. |
| Report templates | Каталог описывает natal, synastry, Tarot, localization и snapshot inputs. |
| Benchmark reproducibility | Synthetic benchmark запускается с отключённым LLM и возвращает JSON с `pass=true`. |
| Visual evidence | Narrative QA ссылается только на tracked summaries, а не на отсутствующие raw artifacts. |

## Acceptance criteria

P2 quality gate считается пройденным только если все checks имеют `pass=true`, Python и JavaScript syntax checks проходят, `pytest -q` не имеет unexpected failures, а `git diff --check` не сообщает о нарушениях. Скриншоты, screen-reader результаты, touch-target review, storage-retention drill и provider sandbox evidence сохраняются отдельными owner-led артефактами и не имитируются локальным synthetic gate.

## Rollback

Скрипт read-only и не меняет базу, deployment или пользовательские данные. При регрессии откатывается только commit, который изменил соответствующий contract/documentation или benchmark, после чего gate запускается повторно.
