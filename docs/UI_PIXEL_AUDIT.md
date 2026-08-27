# OracleAI — UI Pixel Audit

**Дата baseline:** 2026-08-27  
**Ветка:** `master`  
**Состояние:** до текущего visual reconstruction pass  
**Источник:** локальный dev API, synthetic user `10001`, без production credentials.

## Baseline scope

Проверены две фактические runtime-сцены: защищённый recovery screen без валидной Telegram-сессии и authenticated home screen с seeded synthetic user. Дополнительно существующий Playwright standards harness подтвердил отсутствие horizontal overflow, unnamed focusables и images without alt в доступных seeded states.

## Recovery screen observations

На viewport browser screenshot примерно `895×768` центральный application frame занимает около `336px` по ширине и визуально центрирован на космическом фоне. Header содержит profile pill, OracleAI wordmark и notification control. Recovery card находится в верхней части frame и содержит один primary CTA «Повторить».

Сильные стороны: контент остаётся сфокусированным, основной CTA заметен, background сохраняет брендовый образ, recovery state не маскируется под полноценный продуктовый home.

Дефекты baseline: в первом screenshot frame выглядит чрезмерно высоким относительно короткого recovery content; большая часть viewport остаётся пустой. Header controls и CTA используют разные визуальные веса, а при первом переходе часть страницы могла быть снята во время loading transition. Для recovery state нужен более компактный content-driven card и предсказуемая стабилизация layout перед visual capture.

## Authenticated home observations

После seed synthetic user home содержит: top chrome с profile/notifications, daily ritual header, lunar context, primary daily sign CTA, diary/practice cards, lunar calendar, sign-of-the-day reading, compatibility CTA, agent selection cards и fixed bottom navigation (`Сегодня`, `Диалоги`, `Оплата`, `Моё`).

Базовая информационная архитектура сохраняет правильную продуктовую идентичность: сначала мягкий daily ritual, затем personal reading, затем tools/agents. В DOM обнаружены доступные labels для основных actions, а в standards audit не найдено горизонтального переполнения.

Дефекты baseline, требующие screen-by-screen measurement: home перегружен вертикально и смешивает feature cards, reading content и navigation без достаточно выраженного ритма секций; большая часть typography и card spacing задана локальными значениями в нескольких CSS-файлах; desktop frame требует проверки максимальной ширины и line length; agent cards и bottom navigation должны быть сопоставлены по touch target, icon scale и active-state contrast.

## Initial acceptance baseline

| Check | Baseline result | Interpretation |
|---|---|---|
| Mobile 360 / reference 390 / large 430 | `scrollWidth == viewportWidth` in existing harness | No horizontal overflow detected in covered states. |
| Focusable labels | `unnamedFocusableCount == 0` in existing harness | Covered controls have accessible names. |
| Image alternative text | `imagesWithoutAltCount == 0` in existing harness | Covered images have alt attributes. |
| Reduced motion | Reference 390 run uses reduced-motion context | Must preserve this behavior after CSS changes. |
| Recovery layout | Runtime screenshot captured | Content is correct, but vertical frame has excessive empty space. |
| Authenticated home | Runtime DOM/content captured after synthetic seed | Requires geometry reconstruction and broader state capture. |

## Measurement protocol

The next pass must record, for each major screen, viewport width/height, safe-area padding, frame width, side margins, top chrome height, content width, section gaps, card padding/radius, CTA min-height, icon size, navigation height, heading line length and horizontal overflow. Measurements must be taken from rendered DOM rectangles at `320`, `360`, `375`, `390`, `430`, `768`, `1024`, `1440` and `1920` CSS pixels where the runtime supports the state.

## Baseline conclusion

The existing UI is structurally healthy but not yet pixel-precise. The primary reconstruction target is **geometry and hierarchy**, not a wholesale palette change: establish one content frame, spacing scale, typography scale, card families, button/touch-target rules, responsive breakpoints and state-specific layout behavior, then validate every change with rendered screenshots and DOM measurements.

## Reference screenshot observations

### Home — `390×844`

The visual language is already strong: dark cosmic canvas, warm gold CTA, restrained violet surfaces and a clear daily ritual hierarchy. The dominant hero card is approximately `358px` wide with `16px` side margins and an intentionally prominent height. The top profile pill truncates the synthetic user name, which is acceptable for production only if the truncation preserves the profile affordance and does not collide with the centered wordmark. The fixed bottom navigation is approximately `69px` high and overlays the lower viewport; the page needs enough bottom padding so the final content card never ends underneath it.

The main visual risks are **vertical density and content length**, not color. The hero title occupies three lines and remains readable, while the next section begins close to the hero card. The seasonal card uses a distinct compact family and should not inherit the hero’s larger padding. The rhythm between hero, seasonal sign, rhythm card and bottom nav should be tokenized rather than adjusted per screen.

### Chat / agent hub — `390×844`

The screen has a clear editorial header, a single featured agent card and a compact list of suggested actions. The featured card’s inner layout is close to the minimum comfortable width: portrait, copy and CTA share one row. The CTA height is visually comfortable and the quick prompt pills are discoverable, but the lower action list is partially hidden behind the fixed bottom navigation in the screenshot. The chat surface therefore needs explicit `padding-bottom: calc(nav-height + safe-area)` and a consistent scroll inset.

The chat heading and subheading form a strong hierarchy, but the body copy is close to the full frame width. A reading measure around `32rem` on desktop and `calc(100% - 32px)` on mobile should be enforced for long explanatory text. Agent cards should use one medium-card family, while quick actions should remain visibly subordinate.

### Immediate reconstruction priorities

1. Define global geometry tokens for frame width, mobile gutter, section gap, card padding, control height, radius families and bottom-nav height.
2. Add safe-area-aware bottom content padding to every scrollable main surface.
3. Prevent desktop wide-screen stretching with a consistent `max-width` content frame while preserving the cosmic background outside it.
4. Normalize button/touch targets to at least `44px` and avoid shrinking icon-only controls below that target.
5. Keep the existing brand palette and imagery; make the premium improvement through optical spacing, hierarchy and responsive geometry.

## Post-reconstruction findings

После подключения `18-pixel-reconstruction.css` и обновления cache-busting до `v103` повторный harness прошёл на `ru/en` в `360×800`, `390×844` и `430×932`: horizontal overflow отсутствует, unnamed focusables отсутствуют, images without alt отсутствуют, reduced-motion reference сохраняется.

### Home retest — `390×844`

Hero title стал компактнее и держит две строки вместо трёх, CTA получил симметричный внутренний ритм и предсказуемую ширину, seasonal card визуально отделён как medium card, а daily ritual card получил больше воздуха между progress bar и action row. Нижняя навигация остаётся отдельной floating capsule; content padding предотвращает потерю нижнего action card под nav.

### Chat retest — `390×844`

Featured agent card теперь лучше удерживает горизонтальный баланс portrait/copy/CTA, suggested actions выстроены в один понятный вертикальный ритм, а нижний список не обрывается непосредственно на границе nav capsule. Header, body copy и action list сохраняют одну content frame шириной viewport минус токенизированные gutters.

### Remaining visual gate

Покрытые screenshots подтверждают local visual contract, но не заменяют ручную проверку всех screens из плана (landing, onboarding, compatibility, astrology, palm, history, diary, memory, profile, shop и admin dashboard) в реальном Telegram WebView. Эти screens требуют отдельного seeded route matrix и device review, даже при зелёном automated harness.

## Admin Dashboard baseline — local desktop

Authenticated synthetic owner state is available locally when the API runs with `ADMIN_ID=10001`. At the observed desktop viewport, the dashboard uses a left sidebar of approximately `160px`, a main analytics region and a top-right period/control row. Metric cards form a dense grid and the payment-control card spans the content width. The dashboard is operationally information-rich and visually consistent with the dark/violet product language.

The main admin visual risks are **density and scanability**: many small uppercase labels, compact cards and a long dashboard body create a high cognitive load; the sidebar should remain visually subordinate to the data canvas, and controls need a consistent minimum height. Responsive behavior below desktop requires explicit wrapping/stacking rules rather than relying on the desktop grid. Because this state is authenticated and owner-scoped, it was included in the local audit but not exposed to public routes.

## Admin post-reconstruction measurements

На локальном owner dashboard после нового admin layer измерен desktop layout: sidebar `216px`, main canvas `1049px`, content width `987.6px`, gutter `30.72px`, KPI grid gap `16px`, первые KPI cards `151.3×132.5px`, payment health card `987.6×289px`, стандартный nav item `44px` высотой. Внешний document scroll не создаёт горизонтального переполнения (`scrollWidth 1265px` при viewport `1280px`).

Эти значения подтверждают, что dashboard использует bounded wide canvas и единый minimum control target. Для узких viewport остаётся обязательным отдельный mobile run, поскольку sidebar меняет режим с fixed column на horizontal navigation.

## Profile and Tarot observations

### Profile / payments — `390×844`

The profile/payment surface has a strong compact hero, a readable crystal balance card and clearly separated payment method controls. The subscription card is visually dominant without becoming an oversized empty panel. The primary payment CTA is wide and comfortable. Remaining polish is mostly consistency: payment tabs, plan cards and the bottom nav should share the same focus ring and vertical clearance tokens as home/chat.

### Tarot / first-run overlay — `390×844`

The capture enters the Tarot journey through the first-run onboarding overlay. The overlay is intentionally modal, centered and readable, with a clear two-action hierarchy: secondary «Пропустить» and primary «Дальше». This is a valid product state rather than a rendering failure. The overlay has sufficient contrast and comfortable controls; its final manual gate is to verify that long English/Russian headings remain balanced and that the modal remains within the safe area at `320px` width.

## Screen coverage status

| Screen family | Local visual evidence | Current assessment |
|---|---|---|
| Landing / recovery | Browser runtime screenshot | Compactness and CTA hierarchy reviewed. |
| Age gate / intro | Existing visual harness and CSS contract | Accessible, safe-area-aware; manual long-copy review remains. |
| Today / home | `ru-reference-390-home.png`, RU/EN harness | Improved geometry and nav clearance. |
| Agent selection / chat hub | `ru-reference-390-chat.png`, RU/EN harness | Improved featured-card and list rhythm. |
| Tarot | `ru-reference-390-tarot.png`, RU/EN harness | First-run modal state reviewed; post-onboarding reading state needs manual device run. |
| Profile / shop | `ru-reference-390-profile.png`, RU/EN harness | Strong hierarchy; final payment interaction review remains. |
| Astrology / compatibility / palm | Existing API/visual contracts, no current screenshot in this run | Requires dedicated seeded action journey. |
| History / diary / memory | Existing API/visual contracts, no current screenshot in this run | Requires dedicated seeded tab/modal journey. |
| Admin Dashboard | Local owner browser screenshot and DOM measurements | Desktop geometry improved; mobile sidebar run remains. |

## Admin responsive retest

Одноразовый Playwright probe подтвердил admin contract в двух viewport sizes:

| Viewport | Sidebar | Main height | Horizontal overflow | Unnamed focusables | Controls below 44px |
|---|---:|---:|---|---:|---:|
| `1280×900` | `216×900` | `1706.75px` | No | 0 | 0 |
| `390×844` | `390×66` | `2999.5px` | No | 0 | 0 |

Для получения zero unnamed focusables к dynamic search, segment, promo, broadcast, admin и horoscope controls добавлены явные `aria-label`. Nested visible labels сохранены; бизнес-логика и permissions не менялись.
