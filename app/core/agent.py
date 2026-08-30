"""Thin compatibility facade over the scenario modules.

Свободный диалог всегда идёт через `app.core.agents.runtime.answer`
(re-exported ниже как ``ask_oracle``). Готовые сценарии — из
`app.core.scenarios.*`. Этот модуль оставлен как публичная точка входа для
внешних скриптов, планировщика, тестов и бот-хендлеров, которые исторически
писали ``from app.core import agent`` — новых бизнес-правил или promt-строк
здесь НЕТ.

Никакого дублирования логики: каждая функция ниже — это re-export канонической
реализации из `agents.runtime` или `scenarios/*`.
"""
from __future__ import annotations

import logging

# ── canonical free-form dialog entrypoint ────────────────────────────────
from . import agents
from . import tool_registry as skills  # noqa: F401  # tests may monkeypatch this attribute
# ── canonical scenario modules ───────────────────────────────────────────
from .scenarios import compat as _compat_scn
from .scenarios import forecast as _forecast_scn
from .scenarios import memory as _memory_scn
from .scenarios import report as _report_scn
from .scenarios import tarot as _tarot_scn

log = logging.getLogger("oracle.agent")


async def ask_oracle(db, user, question: str, *, agent: str = "oracle",
                     thread_id: int | None = None,
                     allowance_line: str = "",
                     extra_rules: str = "",
                     trace: list[str] | None = None) -> str:
    """Свободный вопрос агенту.

    Compatibility entrypoint. Единственная реализация живёт в
    `app.core.agents.runtime.answer`; здесь только прокси, чтобы старые
    call-site'ы (``from app.core import agent``) продолжали работать.
    """
    return await agents.answer(
        db, user, question, agent=agent, thread_id=thread_id,
        allowance_line=allowance_line, extra_rules=extra_rules, trace=trace)


# ── re-exports for legacy imports ────────────────────────────────────────
# Свободный диалог: см. ask_oracle выше.
# Готовые сценарии живут в scenarios.*; они экспортируются здесь под их
# историческими именами, чтобы `agent.<func>` продолжал работать.
interpret_reading = _tarot_scn.interpret_reading
daily_forecast = _forecast_scn.daily_forecast
daily_forecast_cached = _forecast_scn.daily_forecast_cached
card_of_day = _forecast_scn.card_of_day
daily_sphere = _forecast_scn.daily_sphere
interpret_compat = _compat_scn.interpret_compat
interpret_chart = _report_scn.interpret_chart
build_report = _report_scn.build_report
monthly_report = _report_scn.monthly_report
extract_memory_llm = _memory_scn.extract_memory_llm

# Историческая совместимость для тестов, которые правят внутренние helpers:
from .scenarios._impl import (  # noqa: E402, F401
    _chart_brief,
    _chart_required_coverage,
    _forecast_offline,
    _full_chart_fallback,
    _memory_extract_prompt,
    _parse_facts,
    _reading_offline,
    _report_offline,
)

__all__ = [
    "ask_oracle",
    "interpret_reading",
    "daily_forecast",
    "daily_forecast_cached",
    "card_of_day",
    "daily_sphere",
    "interpret_compat",
    "interpret_chart",
    "build_report",
    "monthly_report",
    "extract_memory_llm",
]
