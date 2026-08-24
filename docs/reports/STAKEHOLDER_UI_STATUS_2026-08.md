# OracleAI — краткий статус для стейкхолдеров

**Срез:** commit `ab24f35` на ветке `feat/agent-first-harness`  
**Статус:** UI/QA demo-ready, production deployment не подтверждён.

## Что реально сделано

За последние итерации исправлены ключевые cross-platform проблемы Mini App: desktop shell получил отдельную sidebar/workspace-композицию, mobile — drawer и safe-area поведение; Home и Hub получили собственные desktop layouts вместо растянутой мобильной колонки; header, toast, chat composer, history search и archived read-only flow выровнены по единой системе.

Критическая Tarot-регрессия разобрана по первопричине. Slot имел несогласованный ratio с реальными вертикальными scans, а `object-fit: cover` дополнительно усиливал crop; grid items также сжимались относительно tracks. Сейчас spread/day-card/widget используют единый ratio `330 / 568`, карта заполняет slot, а grid изолирован от соседних элементов. 3D flip работает через CSS `perspective`/`preserve-3d`/`rotateY`, с backface isolation, GPU hint и reduced-motion fallback.

Полностью удалена mantra functionality: catalog, UI, routing copy, seed/settings, diary keyword и legacy DB exposure. Добавлены серверные и тестовые guardrails, чтобы старые database overrides не вернули удалённую функцию.

## Что подтверждено

| Контроль | Результат |
|---|---|
| Mobile 320×844, 375×812, 390×844 | Без document horizontal overflow |
| Desktop 1024×768 и 1280×800 | Root/canvas/sidebar geometry в пределах viewport |
| Tarot 3-card live flow | Полный artwork, одинаковые slot/card размеры, ghost-сосед отсутствует |
| Full pytest с offline LLM | PASS |
| Ruff и JS syntax | PASS |
| Cache-busting | PASS, v109 |
| Agent quality | PASS; safety-critical failures 0 |

## Отрезвляющие ограничения

Это **не означает**, что продукт готов к production launch. В текущем репозитории нет настроенного внешнего staging target: отсутствуют staging domain, SSH/deploy target, CI/CD workflow или подключённый hosting project. Production deployment также требует реальных Telegram/LLM/payment/back-up secrets, домена, TLS, backup drill и проверки webhook. Эти вещи нельзя безопасно имитировать из локального sandbox.

Локальное демо использует `DEV_MODE=1` и `dev_user=1`; такой режим предназначен только для просмотра и QA. Его нельзя публиковать как staging для клиента без закрытого доступа и production auth.

## Решение для демонстрации

Для клиентского просмотра подготовлен временный demo-сервис на текущем commit. Он показывает фактическую версию UI, но является ephemeral preview, а не постоянным staging environment. После завершения sandbox-сессии его доступность может прекратиться.

## Следующий обязательный шаг до staging

Нужны конкретные параметры целевого контура: hostname/domain, способ доступа к серверу или подключённый hosting project, значения deployment secrets через защищённый секрет-хранилище и ответственный за acceptance. После этого можно выполнить deploy, `/api/health` smoke test и закрытую client demo ссылку.
