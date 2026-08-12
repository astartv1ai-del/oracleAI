"""Живая проверка LLM-слоя через настроенный провайдер (OmniRouter).

Прогоняет главную фишку целиком — память, скиллы (tool-use), прогноз дня —
против реальной модели и печатает латентность, токены и модели каждого шага.

Запуск:
    python -m scripts.live_llm_probe

Требуется запущенный шлюз: по умолчанию OmniRouter на
http://localhost:20128/v1 (см. CUSTOM_LLM_* в .env). Если шлюз выключен,
скрипт честно скажет об этом и упадёт с подсказкой.

Провайдер, модель и ключ берутся из app.config → .env. Расход пишется в
`llm_usage` (как в проде). Финалом печатаются сводные токены по моделям.
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.config import settings  # noqa: E402
from app.core import agent as agent_core  # noqa: E402
from app.core import astro, llm, memory  # noqa: E402
from app.core.agents.runtime import answer  # noqa: E402
from app.data.session import connect, utcnow  # noqa: E402
from app.repo import users  # noqa: E402

logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(name)s: %(message)s")

FAILS: list[str] = []


def mark(ok: bool, label: str) -> bool:
    FAILS.append(label) if not ok else None
    print(f"    {'OK' if ok else 'FAIL'} — {label}")
    return ok


async def _seed_user(db):
    """Клиентка с построенной картой, как после онбординга (тезис в тестах)."""
    tg_id = 7770001
    await users.ensure(db, tg_id, "Проба")
    chart = await astro.compute_chart_async("1990-06-21", "14:30", "Казань",
                                            55.79, 49.12, "Europe/Moscow")
    await users.update(db, tg_id, onboarded=1, birth_date="1990-06-21",
                       birth_time="14:30", birth_time_known=1,
                       birth_city="Казань", tz="Europe/Moscow", sub_level="vip",
                       chart_json=json.dumps(chart, ensure_ascii=False))
    return await users.get(db, tg_id)


async def _usage(db, since: str) -> None:
    cur = await db.execute(
        "SELECT model, purpose, "
        "SUM(prompt_tokens) pt, SUM(completion_tokens) ct, MAX(latency_ms) lat "
        "FROM llm_usage WHERE created_at >= ? GROUP BY model, purpose ORDER BY model",
        (since,))
    rows = await cur.fetchall()
    if not rows:
        return
    print("  ── расход (llm_usage) ──")
    for r in rows:
        print(f"  {r['model']} [{r['purpose']}] prompt {r['pt']} · comp {r['ct']} · "
              f"макс {r['lat']} мс")


async def probe() -> int:
    if not settings.provider_chain:
        print("Нет доступного LLM-провайдера.")
        print("Открой .env: LLM_PROVIDER=auto, CUSTOM_LLM_BASE_URL=http://localhost:20128/v1,")
        print("CUSTOM_LLM_MODEL=oc/claude-sonnet-5, CUSTOM_LLM_API_KEY=sk-…")
        print("и запусти OmniRouter. Проверка: curl -s http://localhost:20128/v1/models")
        return 1

    print(f"Провайдер: {settings.provider} | цепочка: {settings.provider_chain}")
    print(f"main={llm._models(settings.provider, 'main')}  lite={llm._models(settings.provider, 'lite')}")
    if "custom" in settings.provider_chain and settings.custom_base_url:
        from urllib.parse import urlparse
        import socket
        u = urlparse(settings.custom_base_url)
        try:
            socket.create_connection((u.hostname or "localhost", u.port or 80),
                                     timeout=2).close()
            print(f"  шлюз {settings.custom_base_url} доступен")
        except OSError as e:
            print(f"  ! не достучался до {settings.custom_base_url}: {e}")
            print("    запусти OmniRouter и повтори: python -m scripts.live_llm_probe")
            return 1
    print()

    since = utcnow()
    db = await connect(os.path.join(tempfile.mkdtemp(), "probe.db"), seed=False)
    user = await _seed_user(db)

    # ── 1. LITE: короткое сообщение дёшевой моделью ──────────────────────────
    t0 = time.monotonic()
    x = await llm.complete("Ты — Лилит, астролог. Отвечай одной строкой.",
                           "Привет! Что сегодня обещает мне звёзды?", tier="lite",
                           purpose="probe", tg_id=user["tg_id"], db=db)
    print(f"[{time.monotonic()-t0:5.2f}s] lite → {x[:140]!r}")
    mark(bool(x and len(x) > 5), "lite-complete")

    # ── 2. ПАМЯТЬ: запись + семантический всплыв в recall ─────────────────────
    t0 = time.monotonic()
    await memory.remember(db, user["tg_id"], "Клиентка переезжает в Берлин в сентябре")
    recalled = await memory.recall(db, user["tg_id"], "переезд в Берлин", limit=5)
    print(f"[{time.monotonic()-t0:5.2f}s] память → {recalled}")
    mark(any("Берлин" in m for m in recalled), "memory-add+recall")

    # ── 3. СКИЛЛЫ + ПАМЯТЬ: полный answer() — tool-use цикл ───────────────────
    t0 = time.monotonic()
    text = await answer(db, user,
                        "Что у меня по карте и транзитам на сегодня? Коротко.")
    print(f"[{time.monotonic()-t0:5.2f}s] answer() → {len(text)} симв")
    print("    " + " ".join(text.split())[:260])
    mark(len(text) >= 120, "answer-skill-memory")

    # ── 4. ПРОГНОЗ ДНЯ: daily_forecast_cached (main, генеративная) ────────────
    t0 = time.monotonic()
    forecast = await agent_core.daily_forecast_cached(db, user)
    print(f"[{time.monotonic()-t0:5.2f}s] прогноз → {len(forecast)} симв")
    print("    " + " ".join(forecast.split())[:260])
    mark(bool(forecast and forecast.startswith("🌅")), "daily-forecast")

    await _usage(db, since)
    await db.close()

    print("\n" + "=" * 44)
    if FAILS:
        print(f"ПРОВАЛЕНЫ шаги: {', '.join(FAILS)}")
        return 1
    print("Все шаги LLM-слоя прошли.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(asyncio.run(probe()))
    except KeyboardInterrupt:
        sys.exit(130)
