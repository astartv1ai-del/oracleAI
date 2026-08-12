# QA — final-polish

## Метод: Playwright DOM-аудит (viewport 390×844, dev_user 555000001)

### Скриншоты экранов — overflow
- home / hub / profile / chat / sheet: все чисты, декор (.galaxy/.lilith-sil) отфильтрован
- composer: tool-btn left=73, send right=369, input top=648 → всё в ряд, без наложений
- Sheet: open=true при клике tool-toggle, closes_after_pick=true, te-av=3 (с `<img>`), te-grid=2 колонки

### Инструменты (реальный путь: чип в шите)
9/9 открываются с ожидаемым pending: moon, matrix, career, tarot(→pick), compat, chart, today, practices, diary. widget_shown=true у всех. toolbar_removed=true.

### Интеракции (клики, «применяются ли»)
| Флоу | Результат |
|---|---|
| Таро draw → 3 карты → флип всех → interpret | form исчезает, вопрос в w-sub, interp_btn после всех 3, AI-ответ приходит, виджет остаётся |
| Карта дня flip | `.dc-card.flipped`, смысл `.dc-mean` показан |
| Матрица select node | `.m-node.on` ×3 после клика |
| Луна expand | `p.exp=0`, совет `.moon-adv` показан |
| Карьера select day | `p.sel=0`, `.cw-cell.sel` ×1 |
| Практика done | API 200, статус repeat-иден (already отмечено — не баг) |
| Compat full | result_widget=true, pending_after=null, errors: [] |

### Backend-фиксы, найденные аудитом
- `_synastry_fresh`: `cached["created_at"]` вместо `cached.get` (sqlite3.Row) — compat 500 → 200
- cheer-крэш: `(last.text || '').startsWith` — виджет без text после doCompat больше не падает

### Статическая верификация
- `node --check`: 13/13 JS OK
- CSS скобки: 16/16 сбалансированы
- pytest: 289 passed. 4 env-fail (aiogram/openai не установлены в dev) — не код.

## Не проверено
- Реальные LLM-потоки через openai (модуль отсутствует) — интерпретации протестированы через dev-fallback
- Экран ввода Intro (SKIP_INTRO обойдён в аудите)