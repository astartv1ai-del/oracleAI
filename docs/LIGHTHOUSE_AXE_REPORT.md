# OracleAI — Lighthouse, axe-core и контрастность тёмной темы

**Дата проверки:** 27 августа 2026 года.
**Проверенные локали:** RU и EN через существующую visual QA-матрицу.
**Финальная accessibility-матрица:** 10 SPA-состояний на desktop viewport 1440×900.
**Состояния:** Home, Guides, четыре чата (`oracle`, `astro`, `tarot`, `chiromant`) и четыре вкладки Profile (`summary`, `chart`, `history`, `memory`).

## 1. Итог автоматического прогона

Приложение является SPA, поэтому «все страницы» проверялись как все пользовательские экранные состояния, доступные через QA-only URL-параметры. QA-параметры не влияют на обычный production flow: они только пропускают onboarding/age overlay, выбирают экран и замораживают декоративную motion-графику для воспроизводимого Lighthouse capture.

| Проверка | Результат |
|---|---:|
| Lighthouse accessibility, финальный прогон | **100/100 на всех 10 состояниях** |
| axe-core violations | **0 на всех 10 состояниях** |
| axe-core passes | **30–40 на состояние** |
| axe-core incomplete | Только `color-contrast`, **1 manual-review record на состояние** |
| Unnamed interactive controls | **0** |
| Inputs without accessible label | **0** |
| Images without `alt` | **0** |
| Design contract | **PASS** |
| JS syntax check | **PASS** |
| Semantic token contrast check | **PASS** |

Полный Lighthouse-прогон с категориями Performance, Accessibility, Best Practices и SEO также выполнен. Для всех состояний Accessibility составила 100, Best Practices — 96, SEO — 100. Performance category в локальном dev-окружении не получила итоговый score: Lighthouse не смог завершить `NO_TTI_CPU_IDLE_PERIOD`, а для части chat-состояний дополнительно возникал DevTools `ResponseCompression` protocol timeout. Это ограничение режима измерения локального приложения, а не зафиксированная accessibility-ошибка интерфейса. В QA-режиме motion теперь замораживается, чтобы следующий performance-прогон на staging/production был стабильнее.

## 2. Исправления, которые привели к нулю axe violations

Первоначальный axe-прогон выявил три группы shared-shell проблем: отсутствовал landmark `<main>`, у Home/Profile/Chat не было корректного level-one heading, а generic `div` использовали `aria-label` без подходящей роли. Дополнительно Guides нарушал heading order из-за перехода с `h1` сразу на `h3`.

| Проблема | Исправление |
|---|---|
| Нет главного landmark | `#app-main` заменён на `<main id="app-main" tabindex="-1">`. |
| Нет `h1` на Home | `.hero-title` стал `<h1>`, визуальный стиль сохранён. |
| Нет `h1` на Profile | `.profile-name` стал `<h1>`. |
| Нет `h1` в Chat | `.cname` стал `<h1>`. |
| Некорректный порядок заголовков Guides | Vedic heading изменён с `h3` на `h2`; CSS поддерживает оба уровня. |
| `aria-label` на generic brand div | `.brand-lockup` получил `role="img"`. |
| `aria-label` на score div | `.daily-ritual-score` преобразован в `<output>`. |
| `aria-label` на proof/suggestion containers | `.agent-proof-row`, `.chat-proof-strip` и `.suggest-chips` получили `role="group"`. |

После этих изменений повторный axe-core matrix показал **0 violations на Home, Guides, всех четырёх чатах и всех четырёх вкладках Profile**.

## 3. Почему axe помечает `color-contrast` как incomplete

`color-contrast` остаётся в секции `incomplete`, а не `violations`. На страницах используются декоративные градиенты, полупрозрачные surfaces, pseudo-elements и starfield/orb artwork. axe-core намеренно не утверждает контраст, когда не может надёжно вычислить фактический backdrop текста из CSS-градиента или pseudo-element. В отчётах это проявляется как `bgGradient`/`pseudoContent`, а не как рассчитанный ratio ниже порога.

Это не заменено игнорированием правила. Для deterministic части проверки создан и запущен `scripts/check_visual_contrast.py`, который вычисляет контраст semantic tokens на фактическом базовом тёмном фоне и выполняет отдельную проверку UI-индикаторов. Поэтому автоматическая интерпретация такая: **axe violations отсутствуют; color-contrast требует ручного review сложных composited surfaces; core token pairs проходят численную проверку**.

## 4. Текстовый контраст в dark theme

Для обычного текста применён порог **4.5:1**. Для крупного текста допускается 3:1, но система использует более строгий normal-text threshold для основных пар.

| Текстовая пара | Расчётный контраст | Статус |
|---|---:|---|
| `--color-text-primary` `#FAF8FF` на `--color-bg-primary` `#0A0920` | **18.58:1** | PASS |
| `--color-text-secondary` `#D4CEE7` на `#0A0920` | **12.85:1** | PASS |
| `--color-text-muted` `#A39BBD` на `#0A0920` | **7.44:1** | PASS |
| Primary text `#FAF8FF` на `--color-bg-secondary` `#100E29` | **17.85:1** | PASS |
| Primary text `#FAF8FF` на `--color-bg-elevated` `#19153A` | **16.48:1** | PASS |
| `--color-on-accent` `#251D39` на `--color-accent-strong` `#FFE9B4` | **13.37:1** | PASS |
| `--color-on-accent` `#251D39` на `--color-accent-deep` `#EABF68` | **9.25:1** | PASS |

Проблема решалась не ручной заменой отдельных цветов в компонентах, а централизацией палитры: все основные text/background/CTA aliases теперь ссылаются на semantic tokens. Это предотвращает расхождение между Home, Chat, Profile, Tarot и Vedic surfaces.

## 5. Нетекстовый контраст и focus indicators

Для графических объектов, границ, selected states и focus indicators применялся порог **3:1**. Это относится к элементам, которые пользователь должен различать независимо от текста: активным границам, focus outlines, status colors и цветным UI-индикаторам.

| Нетекстовый элемент | Цвет / composited result | Контраст | Статус |
|---|---|---:|---|
| Strong accent | `#FFE9B4` на `#0A0920` | **16.37:1** | PASS |
| Deep accent | `#EABF68` на `#0A0920` | **11.33:1** | PASS |
| Secondary accent | `#B9A6FF` на `#0A0920` | **9.29:1** | PASS |
| Success indicator | `#7BE0C5` на `#0A0920` | **12.41:1** | PASS |
| Warning indicator | `#F5D48B` на `#0A0920` | **13.68:1** | PASS |
| Error indicator | `#F5A9C7` на `#0A0920` | **10.61:1** | PASS |
| Info indicator | `#B9A6FF` на `#0A0920` | **9.29:1** | PASS |
| Strong border / selected outline | `rgba(245,212,139,.50)` composited over `#0A0920` | **3.99:1** | PASS |
| Solid focus outline | `--color-accent-strong` на `--color-bg-primary` | **16.37:1** | PASS |

В ходе этого прогона была дополнительно найдена и исправлена слабая граница `--color-border-strong`: прежняя opacity `.38` давала около **2.76:1**, что было ниже целевого 3:1 для non-text indicator. Значение повышено до `.50`, после чего composited ratio стал **3.99:1**. Мягкий `box-shadow` focus ring остаётся дополнительным halo; единственным индикатором фокуса он не является — компонент всегда получает сплошной 2px `outline` с offset.

Цвет не используется как единственный канал статуса: active/selected/success/error states дополнительно используют текст, iconography, border, fill или изменение структуры. Это защищает пользователей с цветовой недостаточностью и одновременно делает состояния понятными в high-contrast окружениях.

## 6. Что осталось проверить вне sandbox

Автоматические результаты не заменяют ручной end-to-end accessibility pass. Перед production рекомендуется прогнать клавиатурный сценарий Tab/Shift+Tab/Escape, проверить focus return после modal/sheet, пройти NVDA на Windows и VoiceOver на iOS/macOS, а также проверить Telegram iOS/Android с реальными `safeAreaInset`, `contentSafeAreaInset`, dynamic viewport, keyboard, BackButton и BottomButton. Отдельно стоит открыть сложные gradient surfaces на реальных устройствах и проверить контраст текста поверх artwork в разных яркостях экрана.

## References

[1]: https://www.w3.org/TR/WCAG21/#contrast-minimum — W3C WCAG 2.1, Success Criterion 1.4.3 Contrast (Minimum).
[2]: https://www.w3.org/TR/WCAG21/#non-text-contrast — W3C WCAG 2.1, Success Criterion 1.4.11 Non-text Contrast.
[3]: https://github.com/dequelabs/axe-core — axe-core, automated accessibility engine and rule documentation.
[4]: https://developer.chrome.com/docs/lighthouse/accessibility — Chrome Lighthouse accessibility audits.
[5]: https://core.telegram.org/bots/webapps — Telegram Mini Apps official documentation.
