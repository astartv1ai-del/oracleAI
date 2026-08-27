# OracleAI — детальный отчёт по мобильной/десктопной версии, контрастности и a11y

**Дата проверки:** 27 августа 2026 года.  
**Базовый коммит:** `0323801` — `feat: complete visual QA polish pass`.
**Расширенный аудит:** `f435951` — `feat: extend wcag and desktop visual QA`.
**Проверенные локали:** RU и EN.  
**Проверенные ширины:** 375px, 768px, 1440px и 1920px.  
**Проверенные состояния:** age gate, onboarding, Сегодня, Диалоги, чат проводника, Профиль, вкладки Chart/History/Memory, memory modal и Tarot entry.

## 1. Краткий вывод

Основная проблема проекта была не в отсутствии визуального направления: космический фон, шампань-акцент и редакционная типографика уже формировали узнаваемый стиль. Проблема заключалась в **расхождении правил между слоями**: legacy-токены и поздний ritual-слой задавали разные палитры, размеры и состояния компонентов. На мобильном это проявлялось в сжатом header, плотной типографике и риске переполнения длинных RU/EN labels. На ПК интерфейс был намеренно узким и центрированным, но декоративный фон выступал за границы canvas и попадал в необогащённую overflow-проверку.

В исправленной версии эти риски сведены к единому контракту. Добавлены семантические токены, единая type scale, 4px spacing scale, минимальные 44px touch targets, общие focus/disabled/active states, safe-area правила и отдельный final CSS layer. После исправлений финальный capture охватил 48 DOM-состояний; реальные UI overflow, unnamed focusable и изображения без `alt` не обнаружены.

## 2. Мобильная версия: основные проблемы и исправления

| Проблема | Как проявлялась | Как исправили | Результат |
|---|---|---|---|
| Сжатый header на 375px | Имя пользователя обрезалось слишком рано; рядом конкурировали pill, центральный бренд и bell. | Зафиксировали симметричную grid-шапку, `max-width` для pill, ellipsis только для имени и минимум 44px для controls. | Header сохраняет структуру и не создаёт layout overflow. |
| Непредсказуемая типографика | В проекте одновременно встречались значения вроде 10.5px, 11.5px, 12.5px, 13.5px, 15px и 17.5px без единой шкалы. | Добавили H1–H6, body, caption, label и button tokens; для заголовков включили `text-wrap: balance`, для чтения — ограничение около 68ch. | Заголовки и вторичный текст имеют предсказуемый ритм. |
| Плотный hero на узком экране | Заголовок, сообщение дня и CTA конкурировали за пространство; особенно заметно в RU/EN с разной длиной строк. | Согласовали `screen padding`, bounded copy и responsive overrides для hero-title/hero message. | Hero сохраняет один визуальный фокус и не обрезает основную мысль. |
| Разрозненные состояния controls | Hover/active были заметнее, чем keyboard focus или disabled. | Добавили единый focus ring, active scale, disabled opacity и transition contract для кнопок, tabs, chips, inputs и навигации. | Состояния читаются не только по цвету и одинаковы между экранами. |
| Разные размеры touch targets | Часть действий была меньше комфортной зоны пальца. | Введён `--touch-target: 44px`; он применяется к buttons, nav, tabs, chips, inputs и интерактивным cards. | Минимальный интерактивный target — 44px. |
| Safe-area и клавиатура | Header, composer, sheets и нижняя навигация использовали safe-area не как общий контракт. | Зафиксировали `env(safe-area-inset-top/bottom)` в shell, composer, modal/sheet и app navigation. | Контент не должен заезжать под системные зоны Telegram/WebView. |
| RU/EN labels | Длинные подписи в tabs, header и навигации требовали отдельной проверки. | Capture запускается в обеих локалях; введены bounded labels, ellipsis только там, где допустимо, и balanced headings. | 375px и 768px проверяются автоматически для RU/EN. |
| Декоративные элементы | Hero orb и starfield намеренно выходят за собственные границы; наивный DOM-check мог считать это ошибкой. | UI overflow отделён от decorative bleed; `html/body` получили `overflow-x: hidden`, clipped artwork не учитывается как layout overflow. | Реальный горизонтальный scroll отсутствует. |

### Что осталось осознанным исключением на мобильном

Emoji и контентные символы всё ещё встречаются внутри данных чтения и некоторых non-interactive контекстов. Для controls нормативом теперь является SVG sigil-набор; замена всех контентных glyphs на SVG не выполнялась, поскольку это затронуло бы смысловые данные Tarot/астрологии, а не UI-иконографику.

## 3. ПК-версия: основные проблемы и исправления

| Проблема | Как проявлялась на 1440/1920px | Как исправили | Результат |
|---|---|---|---|
| Слишком узкая колонка без явного объяснения | App frame около 480px мог выглядеть как случайное ограничение, хотя продукт — Telegram Mini App. | Ограничение 480px закрепили как осознанный Telegram-first contract и описали в Design System. | Canvas остаётся сфокусированным и не растягивает чат/карточки. |
| Фоновый bleed попадал в overflow-метрику | Nebula, galaxy и Lilith выступали за внутренний app frame. | Добавили overflow guard для html/body/starfield и разделили real UI overflow от decorative overflow в harness. | `scrollWidth` равен viewport; layout overflow не обнаружен. |
| Палитра была двойной | Legacy `--bg-*`, `--gold`, `--text-*` конфликтовали с `--ink-*`, `--champagne-*`, `--lilac-*`. | Legacy aliases теперь разрешаются через семантические `--color-*`; ritual слой использует те же значения. | Менять палитру можно из одного token source. |
| Разные карточки и sheets | Card radius, border и elevation отличались между feature-модулями. | Зафиксированы card radius 20px, sheet/modal radius 24px, semantic borders и общие surface rules. | Профиль, чат, Tarot и compatibility выглядят как части одной системы. |
| Слишком много поздних override-правил | Большой `15-ritual-redesign.css` повышал риск каскадных конфликтов. | Добавлен отдельный `16-visual-qa.css` только для cross-screen invariants; переменные aliases разрешают неопределённые custom properties. | Финальный слой стал явной точкой QA-контрактов. |
| Не было фиксированного desktop QA | Предыдущий baseline покрывал только 360/390/430px. | Добавлен capture для 375/768/1440/1920px и RU/EN. | ПК и широкие мониторы входят в регулярную проверку. |

## 4. Проверка контрастности

Проверка выполнена скриптом [`scripts/check_visual_contrast.py`](../scripts/check_visual_contrast.py) для основных непрозрачных token-пар. Коэффициент считается по формуле относительной яркости WCAG; целевой порог для обычного текста — **4.5:1**.[1]

| Foreground | Background | Коэффициент | Требование | Статус |
|---|---|---:|---:|---|
| `--color-text-primary` `#faf8ff` | `--color-bg-primary` `#0a0920` | **18.58:1** | 4.5:1 | PASS |
| `--color-text-secondary` `#d4cee7` | `--color-bg-primary` `#0a0920` | **12.85:1** | 4.5:1 | PASS |
| `--color-text-muted` `#a39bbd` | `--color-bg-primary` `#0a0920` | **7.44:1** | 4.5:1 | PASS |
| `--color-on-accent` `#251d39` | `--color-accent-strong` `#ffe9b4` | **13.37:1** | 4.5:1 | PASS |

### Интерпретация

Основной белый текст имеет большой запас контраста на глубоком canvas. Вторичный и muted-текст также проходят AA на базовом фоне; при этом `--color-text-subtle` зарезервирован только для несущественных подсказок и не должен применяться к основному copy. Тёмный текст на светлой CTA-поверхности также проходит с большим запасом, поэтому шампань-кнопки не зависят от тонкого начертания или свечения для читаемости.

Эта проверка не пытается математически представить каждый пиксель полупрозрачного градиента, фоновой фотографии или blur-слоя. Поэтому для градиентных hero, сообщений на artwork и декоративных surfaces дополнительно применяются визуальный capture, bounded copy и ручная проверка. Это важное ограничение: token-level PASS не означает автоматическую сертификацию каждого возможного композиционного сочетания.

## 5. Accessibility / a11y отчёт

| Проверка | Метод | Результат |
|---|---|---|
| Именованные интерактивные элементы | DOM harness ищет `button`, links, inputs, selects, textarea и tabindex-элементы без `aria-label`, visible text или value. | **0** unnamed focusable в 48 состояниях. |
| Изображения | DOM harness считает `<img>` без атрибута `alt`. | **0** изображений без `alt`. Декоративные изображения имеют пустой `alt` и `aria-hidden`. |
| Keyboard focus | CSS contract проверяет `:focus-visible` для buttons, data-actions, inputs и dock navigation. | **PASS по стилевому контракту:** 2px outline, 3px offset; в интерактивном ручном тесте следует пройти Tab-flow в реальном Telegram WebView перед production release. |
| Touch targets | Общий `--touch-target: 44px` применяется к controls и navigation. | **PASS по CSS contract**; критические controls не должны быть меньше 44px. |
| Reduced motion | `prefers-reduced-motion: reduce` отключает практически все transitions/animations и переводит scroll behavior в `auto`; capture запускает reduced-motion контекст на 768px. | **PASS**; декоративная атмосфера и swipe transition отключаются/смягчаются. |
| Цвет как единственный сигнал | Error/success/info имеют semantic token, но также предусматриваются текст, icon, badge или recovery copy. | **PASS по component contract**; ошибка не должна отображаться только красной рамкой. |
| Горизонтальный overflow | Сравнение `body.scrollWidth`/`documentElement.scrollWidth` с viewport во всех captures; decorative bleed считается отдельно. | **0 состояний** с реальным UI overflow. |
| Safe area | Проверены CSS-правила для header, composer, sheets и bottom nav с `env(safe-area-inset-*)`. | **PASS по CSS contract**. Требует финальной проверки на физическом iPhone/Telegram WebView. |
| Modal focus | Overlay имеет `role="dialog"`, `aria-modal`, close action и focus-visible стили там, где присутствует. | **PASS по покрытым модальным состояниям**; production smoke-test должен проверить возврат фокуса после закрытия. |
| Long text/localization | RU/EN capture на 375/768px для home, hub, chat, profile и tabs. | **PASS визуального capture**; необрезание нестандартно длинных пользовательских имён требует отдельного ручного теста. |

## 6. Что именно считать исправленным, а что — проверенным частично

Исправлены кодом семантическая палитра, типографическая шкала, spacing/radius/touch tokens, карточки, controls, focus/disabled/active states, overlay geometry, responsive guardrails, safe-area contract, reduced-motion contract, contrast checker и four-breakpoint capture. Проверены автоматически 48 states, отсутствие overflow, отсутствие unnamed focusable и отсутствие `img` без `alt`.

Частично автоматизированными остаются пиксельный контраст поверх сложных фотографических/градиентных композиций, фактический screen-reader порядок, возврат фокуса в Telegram WebView после закрытия modal и поведение системной клавиатуры на физических устройствах. Эти проверки описаны в Design System как обязательный production smoke-test, но не могут быть полностью доказаны headless DOM capture.

## 7. Команды воспроизведения

```bash
python3 scripts/check_design_contract.py
python3 scripts/check_visual_contrast.py
python3 scripts/visual_qa_capture.py
for f in miniapp/js/*.js; do node --check "$f"; done
pytest -q -rA
git diff --check
```

## References

[1]: [W3C, WCAG 2.2 — Contrast (Minimum)](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html)
[2]: [MDN, `prefers-reduced-motion`](https://developer.mozilla.org/en-US/docs/Web/CSS/@media/prefers-reduced-motion)
[3]: [`docs/DESIGN_SYSTEM.md`](DESIGN_SYSTEM.md)
[4]: [`docs/VISUAL_QA.md`](VISUAL_QA.md)

## 8. Дополнительные проверки, которые целесообразно выполнить

Ниже приведены проверки, которые расширяют текущий DOM/CSS-аудит до полноценного pre-production accessibility и Telegram Mini Apps review. Они разделены на **WCAG 2.1 AA**, дополнительные критерии WCAG 2.2 и платформенные проверки Telegram. Это важно, потому что Target Size (Minimum) относится к WCAG 2.2, а не к WCAG 2.1 AA.[5]

| Область | Стандарт / критерий | Что проверять в OracleAI | Приоритет |
|---|---|---|---|
| Keyboard | WCAG 2.1 2.1.1, 2.1.2 | Полный Tab/Shift+Tab маршрут через header, nav, cards, tabs, composer, tool sheet и modal; отсутствие keyboard trap; Enter/Space не должны вызывать неожиданные действия. | P0 |
| Focus order | WCAG 2.1 2.4.3 | DOM-порядок должен совпадать с визуальным: header → content → modal/sheet → close/action; после закрытия modal фокус возвращается к trigger. | P0 |
| Focus visible | WCAG 2.1 2.4.7; дополнительно WCAG 2.2 2.4.11/2.4.13 | Проверить реальный `:focus-visible` в Chromium и Telegram WebView, включая focus на тёмной карточке, активном tab и светлой CTA. | P0 |
| Reflow / zoom | WCAG 2.1 1.4.4, 1.4.10 | Проверить 200% zoom и CSS text-only zoom; контент не должен требовать горизонтального scroll при ширине 320 CSS px и не должен терять controls. | P0 |
| Text spacing | WCAG 2.1 1.4.12 | Подменить line-height 1.5, paragraph spacing 2em, letter-spacing .12em, word-spacing .16em; проверить отсутствие обрезания и наложений в RU/EN. | P1 |
| Non-text contrast | WCAG 2.1 1.4.11 | Измерить contrast 3:1 для borders, focus rings, icons, active tab indicator, progress track/fill и error controls на фактических поверхностях, а не только на base token. | P0 |
| Hover/focus content | WCAG 2.1 1.4.13 | Проверить tooltip/title-like UI: его можно dismiss, он не закрывается при перемещении курсора к нему и не перекрывает обязательный контент. | P1 |
| Input purpose | WCAG 2.1 1.3.5 и 3.3.2 | Добавить/проверить `autocomplete`, programmatic labels и инструкции для даты рождения, времени, города, вопроса и memory input. | P1 |
| Label in name | WCAG 2.1 2.5.3 | Accessible name кнопки должен содержать видимый label; особенно проверить icon-only share, close, bell, send, delete и back controls. | P0 |
| Errors | WCAG 2.1 3.3.1–3.3.3 | Проверить inline error с `aria-describedby`, `aria-invalid`, понятной причиной и retry; текст формы не должен исчезать после ошибки сети. | P0 |
| Live updates | WCAG 2.1 4.1.2; практический ARIA review | Для toast, loading, chat response и success state определить `role=status`/`role=alert` только там, где это нужно, без повторного чтения всей страницы. | P1 |
| Language | WCAG 2.1 3.1.1/3.1.2 | Проверить `html[lang]` и language of parts для смешанных RU/EN labels; runtime locale switch должен обновлять metadata. | P0 |
| Reduced motion | WCAG 2.1 2.3.3 и platform review | Проверить не только CSS, но и JS-driven swipe, haptic, card flip, chart draw и loading loops при reduced-motion. | P1 |
| Pointer input | WCAG 2.1 2.5.2/2.5.3 | Проверить pointer cancellation, label-in-name, отсутствие действий только через drag/swipe, корректную работу tap/click на cards и tabs. | P0 |
| Screen reader semantics | WCAG 2.1 1.3.1/4.1.2 | NVDA/VoiceOver/TalkBack pass: landmark structure, headings, dialog naming, tab selection, button names, progress semantics, image alternatives. | P0 |
| Telegram theme | Telegram Mini Apps | Проверить runtime `themeParams`, синхронизацию `bg_color`, `secondary_bg_color`, `text_color`, `button_color`, `button_text_color`, `bottom_bar_bg_color`; проверить light/dark themes. | P0 |
| Telegram viewport | Telegram Mini Apps | Проверить `viewportHeight`, `viewportStableHeight`, `viewportChanged`, fullscreen and keyboard transitions; composer/nav не должны прыгать. | P0 |
| Telegram safe area | Telegram Mini Apps | Проверить `safeAreaInset` и `contentSafeAreaInset` в fullscreen portrait/landscape на iOS и Android, включая home indicator и notch. | P0 |
| Native controls | Telegram Mini Apps | Проверить `BackButton`, `BottomButton`/MainButton, close confirmation, haptic feedback and whether native controls duplicate in-app CTA. | P1 |
| Platform QA | Telegram clients | Прогнать Telegram iOS, Android, macOS/Windows desktop WebView; проверить long press, text selection, keyboard, orientation and network recovery. | P0 |

## 9. Реестр компонентов с обновлёнными touch targets и focus states

Размеры ниже реализованы в `miniapp/css/16-visual-qa.css` и токенах `miniapp/css/00-tokens.css`. Базовый токен `--touch-target` равен **44px**. Для компонентов, у которых явно задана ширина/высота меньше 44px ради визуального glyph-box, действует глобальный `min-height: var(--touch-target)`; перед production release такие icon-only элементы всё равно следует подтвердить измерением реального bounding box.

| Компонент / селекторы | Touch target после обновления | Focus behavior после обновления | Состояния |
|---|---:|---|---|
| Header profile pill `.user-pill` | `min-height: 44px`; width fluid, name ellipsis | Global `button:focus-visible`, 2px outline, 3px offset | default, compact, long name, focus, disabled |
| Header notifications `.bell` | `44 × 44px` | Same visible outline plus semantic `aria-label` | default, hover, active, focus |
| Bottom navigation `.nav-btn` | `min-height: 54px` | Focus ring on full nav item, active state uses contrast + fill | default, active, pressed, focus |
| Primary/secondary buttons `.btn`, `.btn-primary`, `.btn-ghost` | `min-height: 44px` | Focus ring plus hover/active/disabled transition contract | hover, active, focus, disabled, loading |
| Ritual CTA `.ritual-cta` | `min-height: 46px` | Inherits focus-visible, preserves high-contrast dark label on champagne | default, active, focus |
| Inputs `.ipt`, `input`, `textarea`, `select` | `min-height: 44px`, radius 14px | Border changes to strong semantic border plus `--focus-ring`; placeholder uses muted token | default, focus, error, success, disabled |
| Profile tabs `.ptab` | `min-height: 44px` | Focus ring; selected state has fill, contrast and active tab semantics | default, selected, focus |
| Chat tabs `.atab` | `min-height: 44px` | Focus ring on tab button; active state not color-only | default, active, focus |
| Chips `.chip`, `.ask-chip`, `.rel-chip` | `min-height: 44px` through shared rule; compact visual padding retained | Focus ring and active scale; selected state uses border/background | default, selected, disabled, focus |
| Agent cards `.agent-card`, home cards `.dock-item` | `min-height: 44px`; full card click surface | Focus ring on card action surface; active scale limited to .985 | default, hover/active, focus |
| Tool rows `.tool`, `.te-chip` | `min-height: 44px`; tool sheet row uses 60px | Focus ring on full row and no gesture-only dependency | default, open, selected, focus |
| Chat composer `.tool-btn`, `.send-btn` | `44 × 44px` | Focus ring and `focus-within` border on composer | empty, typing, sending, error, focus |
| Chat header `.back`, `.chat-reset` | CSS min-height 44px despite compact glyph box | Visible outline and semantic label/title | default, active, focus |
| Modal close `.m-close`, `.te-close` | Global button min-height 44px; sheet close zone target preserved | Outline offset kept inside visible overlay and close action named | enter, active, focus, exit |
| Memory actions `.memory-open`, `.mem-del`, `.memory-add` | Shared button min-height 44px; delete/send icon actions require runtime bounding-box verification | Visible focus outline and accessible name | default, add, delete, success, error |
| Toast/status `.toast`, status badges | Not pointer targets by default; dismiss action follows `.btn` contract | Status color paired with text/icon; no color-only message | success, error, info, warning |

## 10. Дополнительные desktop-исправления в текущем проходе

В рамках этой дополнительной проверки исправлены три конкретных desktop/mobile-webview риска. Во-первых, `.screen` на tablet/desktop получил дополнительный bottom clearance до 144px и `scrollbar-gutter: stable`, поэтому последняя карточка или секция не должны визуально упираться в нижнюю навигацию. Во-вторых, `#app-root` на desktop получил тонкую semantic frame border, контролируемый фон и мягкую тень; это отделяет 480px Mini App canvas от фонового artwork, не растягивая контент. В-третьих, runtime теперь синхронизирует `document.documentElement.lang`, `dir` и `document.title` с выбранным RU/EN языком. В ходе проверки обнаружен и исправлен реальный accessibility-дефект: `.user-pill` имел высоту 42px и был поднят до 44px.

## 11. Ограничения текущего automated pass

Текущий harness доказывает отсутствие ряда структурных ошибок, но не заменяет полный ручной accessibility pass. В частности, необходимо отдельно пройти NVDA/VoiceOver/TalkBack, проверить реальное отображение `:focus-visible` при Tab, keyboard trap и возврат фокуса после закрытия modal, проверить контраст non-text borders на каждом gradient surface, а также открыть приложение внутри реальных Telegram iOS/Android WebView с dynamic viewport, fullscreen и ThemeParams. Эти проверки включены в таблицу выше как P0/P1, но требуют соответствующих клиентов и устройств.

## References

[5]: [W3C, Web Content Accessibility Guidelines (WCAG) 2.1](https://www.w3.org/TR/WCAG21/)
[6]: [Telegram, Telegram Mini Apps — official documentation](https://core.telegram.org/bots/webapps)

## 12. Итог расширенного прохода после исправлений

После дополнительного прохода standards harness зафиксировал **24 проверенных DOM-состояния** в RU/EN на 375px и 1440px. Итог: `small_targets=0`, `unnamed=0`, `images_without_alt=0`, `inputs_without_label=0`, `positiveTabindex=0`; для английской локали установлены `html[lang]=en` и заголовок `OracleAI — your gentle daily ritual`, для русской — `html[lang]=ru` и русскоязычный title. Telegram WebApp-мок присутствует, `isExpanded=true`, а viewport height корректно доступен runtime-слою.

Desktop capture дополнительно проверил 1440px и 1920px в top/bottom scroll states для Home, Guides и Profile. App frame сохраняет 480px Telegram-first ширину, горизонтальный scroll отсутствует, а `screen` получает 144px bottom clearance и способен прокрутиться до terminal content. Это устраняет риск того, что последний card/section окажется недоступен из-за нижней навигации.

## 13. Что требуется проверить на реальных клиентах перед production

Headless-проверка не может сама доказать корректность системного screen reader, фактический возврат фокуса после закрытия modal или поведение iOS/Android WebView при клавиатуре и fullscreen. Перед production рекомендуется выполнить короткий smoke-test на Telegram iOS и Android: пройти Tab/VoiceOver/TalkBack эквивалентный focus-flow, открыть/закрыть modal, вызвать composer с клавиатурой, изменить тему Telegram, включить fullscreen portrait/landscape и проверить `safeAreaInset`/`contentSafeAreaInset`. Это не найденные ошибки текущего прохода, а следующий уровень platform validation согласно официальной документации Telegram.[6]
