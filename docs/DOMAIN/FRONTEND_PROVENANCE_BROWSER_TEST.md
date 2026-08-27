# Frontend provenance browser test notes

**Run:** 2026-08-27, local `APP_ENV=dev DEV_MODE=1` FastAPI on `127.0.0.1:8080`

**QA users:** synthetic RU user `10001`; EN user `10002` seeded by `scripts/seed_visual_user.py`

## Observed states

The first attempt with `dev_user=10001` failed at the auth gate because the seeded user did not yet exist. After seeding the disposable QA users, the Mini App loaded successfully. The RU chat route rendered the Astrology guide and its chart question controls. Clicking the chart suggestion filled the question, and clicking send produced the bounded offline response; this did not automatically insert a chart card into chat because the chat interpretation path returned “Ответ пока не пришёл”. That is a service/LLM smoke limitation, not a provenance rendering failure.

The RU profile chart route loaded the saved exact chart. Clicking “Полная карта” opened the full-chart modal. The collapsed provenance summary appeared as `Источник расчёта · Технические сведения`; clicking its native `<summary>` expanded the block and rendered `OracleAI Engine`, `Kerykeion`, `oracleai-kerykeion-engine-v2` and `Swiss Ephemeris`. The native `<details>` interaction is keyboard-addressable in the DOM.

## Finding

The provenance block is present and visually readable, but the backend `license_notice` value is displayed as a raw English sentence in the RU interface. The next patch must use localized frontend copy for the license explanation while retaining the backend field only as provenance input/availability. Backend-provided values must continue to be escaped and bounded.

## Second pass after localization patch

The seeded RU profile/full-chart flow again opened successfully, and the native provenance `<details>` block appeared and expanded on click. The DOM still showed the old English `license_notice` sentence after the source patch intended to use `provenanceLicenseCopy`. This indicates either a cached/old frontend source response or that the running process/bundle is serving a different source path. The next step is to inspect the browser function source and network response, then hard-refresh or restart the local server before marking the localized result as passed.

## Cache-bust diagnosis

Browser inspection confirmed that the loaded helper still used `value('license_notice', 220)` and did not contain `provenanceLicenseCopy`, so the first localization patch was not loaded. The source uses script query `?v=103`; bumping all Mini App asset query versions in `miniapp/index.html` to `v=104` was necessary to invalidate the cached scripts. After the v=104 navigation, the seeded RU profile chart surface loaded cleanly and the “Полная карта” action remained available for the final localized assertion.

## Final RU assertion

After the v=104 cache bust, the full-chart modal showed the localized license text: `Использование backend регулируется AGPL-3.0 или коммерческой лицензией выбранной модели распространения.` The block displayed the expected product engine, backend, adapter version and ephemeris. Clicking the native summary expanded the details and kept the values visible. The browser screenshots and extracted DOM confirmed that the earlier English leakage was a cache-busting issue, not a remaining localization path.

## EN assertion

The seeded EN profile/full-chart route loaded successfully. The modal showed `Calculation source`, `Technical details`, `Product engine`, `Backend`, `Adapter version`, `Ephemeris` and the localized English license copy: `The backend is covered by AGPL-3.0 or a commercial license under the selected distribution model.` The provenance details were visible in the full chart and the native summary remained interactive.

The browser test therefore covers both localized values and the cache-busting fix. The chat route itself loaded the Astrology guide and accepted a chart question; its suggestion action filled the chat input, while the local offline/LLM path returned a bounded “answer not arrived” state rather than rendering an inline chart card. The `chartHtml` source path is statically verified by the frontend contract checker and shares the same helper as the full-chart modal.

## Chat helper assertion

The RU chat route was opened with the seeded user and a real `/api/chart?dev_user=10001` payload was fetched in the browser context. Calling the production `app.chartHtml(c)` helper returned HTML containing `.chart-provenance`, `OracleAI Engine`, the Russian localized license copy, no raw English license sentence, and no `open` attribute on `<details>` (collapsed by default). This confirms the chat rendering path independently of the local offline/LLM answer response.

## Final v2 browser smoke — 2026-08-27

After the engine v2 contract changes, the browser QA route was opened again with synthetic RU user `10001` and synthetic EN user `10002` on cache-bust `v105`. Clicking the full-chart control opened the modal in both locales. Clicking the native `Calculation source`/`Источник расчёта` summary expanded the details. The DOM showed `OracleAI Engine`, `Kerykeion`, adapter `oracleai-kerykeion-engine-v2`, `Swiss Ephemeris`, and localized AGPL/commercial license copy. The full-chart copy showed the resolved localized Ascendant label (`Асцендент Весы` / `Ascendant Весы`) and no literal `{sign}` placeholder. The browser found the placeholder once before the fix; the source was corrected in `miniapp/js/12-misc.js`, the static checker was strengthened, and asset query versions were bumped from `v104` to `v105` to bypass the already-cached module.

The final frontend build emitted the deterministic hashed artifacts recorded by `miniapp/dist/manifest.json`. The local server's `/api/chart?dev_user=10001` response remained HTTP 200 and retained the v2 calculation contract with configuration fingerprint and coordinate/timezone evidence. No real personal data was used.
