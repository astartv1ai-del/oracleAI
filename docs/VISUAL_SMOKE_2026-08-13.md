# Visual smoke — 2026-08-13

Local dev route: `http://127.0.0.1:8080/?dev_user=1001`.

Observed states:

| Surface | Result |
|---|---|
| Home / Today | Rendered without blank screen; hero, daily ritual 0/2, agent cards and bottom dock visible. |
| Chat / Lilith | Chat shell, agent tabs, sessions control, composer and suggestions rendered. |
| Tool entry | One visible composer tool entry (`Инструменты`); no duplicate command tray or other-agent tool list. |
| Session list | `МОИ ЧАТЫ 1 из 5` and `Новый` controls visible; recovery card gives human-readable retry action when history request is unavailable in local smoke state. |
| Bottom navigation | Quiet floating dock with one active section and labels `Сегодня`, `Диалоги`, `Моё`. |
| Cache version | v82 assets loaded after Stage 3 frontend change. |

Screenshot paths from the browser smoke are stored by the sandbox under `/home/ubuntu/screenshots/` for the task session. This is synthetic dev smoke only; staging QA still needs 360/390/430 px, RU/EN, keyboard-open, large text and reduced-motion checks from `docs/DESIGN_COMPONENT_INVENTORY.md`.

## v83 reload

After the one-column mobile tool-sheet CSS change, the local v83 route reloaded successfully and the Home screen remained intact with no blank/error state. The previous chat screenshot showed the tool drawer metadata as readable controls; the one-column rule is now intended to keep those rows readable at narrow widths. A full interaction smoke remains synthetic because the local dev session can return the history recovery card when its API state is unavailable.
