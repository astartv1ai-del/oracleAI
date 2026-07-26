"""Единый LLM-слой: Anthropic, OpenAI и любой OpenAI-совместимый сервер
(MiniMax, vLLM, LM Studio...) за одним интерфейсом.

- complete(system, user_text, tier)        — простой ответ без инструментов
- run_agent(system, messages, tools, exec) — tool-use цикл (скиллы)
- transcribe(bytes)                        — голос → текст (Whisper)
- speak(text)                              — текст → голос (TTS)

Надёжность:
- цепочка провайдеров из settings.provider_chain: упал основной → резервный;
- 2 попытки на провайдера с паузой; таймауты на каждый вызов;
- если модель не умеет tool-use (некоторые локальные) — автоматический
  фолбэк: скиллы выполняются заранее, ответ генерируется одним запросом.

OpenAI-совместимые серверы читаются ТОЛЬКО потоком (stream=True): многие прокси
и локальные раннеры отвечают SSE независимо от запроса, и тогда обычный разбор
даёт пустой content. Reasoning-модели пишут размышления в reasoning_content —
их отбрасываем, в ответ идёт только content.

Каждый вызов пишется в `llm_usage`: токены, латентность и оценка стоимости.
Без этого себестоимость платящей клиентки — догадка, а вся юнит-экономика
продукта построена на цифре «≤ $2.5 в месяц».

Формат tools — как у Anthropic: {name, description, input_schema}.
"""
from __future__ import annotations

import asyncio
import json
import logging
import time
from typing import Awaitable, Callable

from ..config import settings

log = logging.getLogger("oracle.llm")

ToolExecutor = Callable[[str, dict], Awaitable[str]]

MAX_ITERS = 6
RETRIES = 2
TIMEOUT = 180.0
# Reasoning-модели тратят часть лимита на размышления: если потолок низкий,
# ответ не успевает родиться. max_tokens — это кап, а не цель, поднять безопасно.
MIN_OPENAI_TOKENS = 2500

#: $ за миллион токенов (вход, выход). Локальные модели считаем бесплатными.
#: Цифры приблизительные и нужны для порядка величины, а не для бухгалтерии —
#: точные суммы всё равно приходят от провайдера в счёте.
PRICING = {
    "claude-sonnet-5": (3.0, 15.0),
    "claude-haiku-4-5": (1.0, 5.0),
    "claude-opus": (15.0, 75.0),
    "gpt-4o": (2.5, 10.0),
    "gpt-4o-mini": (0.15, 0.6),
    "text-embedding-3-small": (0.02, 0.0),
}


def enabled() -> bool:
    """Есть ли хоть один рабочий провайдер. Иначе продукт идёт в офлайн-режим."""
    return settings.llm_enabled


def _models(provider: str, tier: str) -> str:
    if provider == "anthropic":
        return settings.anthropic_main if tier == "main" else settings.anthropic_lite
    if provider == "openai":
        return settings.openai_main if tier == "main" else settings.openai_lite
    return settings.custom_model_main if tier == "main" else settings.custom_model_lite


def estimate_cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    """Оценка стоимости вызова в долларах. 0 — модель не из прайса (локальная)."""
    for prefix, (price_in, price_out) in PRICING.items():
        if model.startswith(prefix):
            return (prompt_tokens * price_in + completion_tokens * price_out) / 1e6
    return 0.0


# ──────────────────────────── журнал расходов ─────────────────────────────────

async def record_usage(db, *, provider: str, model: str, purpose: str,
                       prompt_tokens: int = 0, completion_tokens: int = 0,
                       latency_ms: int = 0, ok: bool = True,
                       tg_id: int | None = None) -> None:
    """Пишет вызов в `llm_usage`. Сбой журнала не должен ронять ответ клиентке."""
    if db is None:
        return
    try:
        from ..data.session import transaction, utcnow
        now = utcnow()
        async with transaction(db):
            await db.execute(
                "INSERT INTO llm_usage(tg_id, provider, model, purpose, "
                "prompt_tokens, completion_tokens, cost_usd, latency_ms, ok, day, "
                "created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                (tg_id, provider, model, purpose, prompt_tokens, completion_tokens,
                 estimate_cost(model, prompt_tokens, completion_tokens),
                 latency_ms, int(ok), now[:10], now))
    except Exception as e:  # noqa: BLE001
        log.debug("расход LLM не записан: %s", e)


class _Meter:
    """Считает токены и время одного логического вызова (со всеми итерациями)."""

    def __init__(self) -> None:
        self.prompt = 0
        self.completion = 0
        self.started = time.monotonic()

    def add(self, usage) -> None:
        if not usage:
            return
        self.prompt += (getattr(usage, "input_tokens", None)
                        or getattr(usage, "prompt_tokens", None) or 0)
        self.completion += (getattr(usage, "output_tokens", None)
                            or getattr(usage, "completion_tokens", None) or 0)

    @property
    def ms(self) -> int:
        return int((time.monotonic() - self.started) * 1000)


# ──────────────────────────── клиенты провайдеров ─────────────────────────────

def _openai_client(provider: str):
    from openai import AsyncOpenAI
    if provider == "custom":
        return AsyncOpenAI(base_url=settings.custom_base_url,
                           api_key=settings.custom_api_key or "sk-local",
                           timeout=TIMEOUT)
    return AsyncOpenAI(api_key=settings.openai_key, timeout=TIMEOUT)


def _anthropic_client():
    import anthropic
    return anthropic.AsyncAnthropic(api_key=settings.anthropic_key, timeout=TIMEOUT)


async def _stream_chat(client, model: str, messages: list[dict], max_tokens: int,
                       tools: list[dict] | None = None,
                       meter: "_Meter | None" = None) -> tuple[str, list[dict]]:
    """Читает ответ потоком и собирает (текст, вызовы инструментов).

    tool_calls приходят фрагментами: имя в одном чанке, аргументы по кусочкам —
    склеиваем их по index. reasoning_content не попадает в ответ, но если модель
    выдала ТОЛЬКО размышления, честно сообщаем об этом (кончился лимит токенов).
    """
    kwargs: dict = {"model": model, "messages": messages, "stream": True,
                    "max_tokens": max(max_tokens, MIN_OPENAI_TOKENS)}
    if tools:
        kwargs["tools"] = tools
    # Просим сервер вернуть расход токенов. Многие локальные раннеры и прокси
    # этого параметра не знают и отвечают TypeError или 400 — тогда считаем
    # без учёта: журнал расходов не стоит того, чтобы уронить ответ клиентке.
    try:
        stream = await client.chat.completions.create(
            **kwargs, stream_options={"include_usage": True})
    except Exception as e:  # noqa: BLE001
        if "stream_options" not in str(e) and not isinstance(e, TypeError):
            raise
        log.debug("сервер не знает stream_options — расход не посчитаю: %s", e)
        stream = await client.chat.completions.create(**kwargs)

    parts: list[str] = []
    slots: dict[int, dict] = {}
    reasoned = 0
    async for chunk in stream:
        if meter is not None:
            meter.add(getattr(chunk, "usage", None))
        if not chunk.choices:
            continue
        delta = chunk.choices[0].delta
        if delta is None:
            continue
        if delta.content:
            parts.append(delta.content)
        thought = (getattr(delta, "reasoning_content", None)
                   or getattr(delta, "reasoning", None))
        if thought:
            reasoned += len(thought)
        for tc in (delta.tool_calls or []):
            slot = slots.setdefault(tc.index, {"id": "", "name": "", "args": ""})
            if tc.id:
                slot["id"] = tc.id
            if tc.function:
                if tc.function.name:
                    slot["name"] = tc.function.name
                if tc.function.arguments:
                    slot["args"] += tc.function.arguments

    text = "".join(parts).strip()
    calls = [slots[i] for i in sorted(slots) if slots[i]["name"]]
    for n, call in enumerate(calls):          # некоторые серверы не шлют id
        call["id"] = call["id"] or f"call_{n}"
    if not text and not calls:
        raise RuntimeError("модель отдала только размышления без ответа"
                           if reasoned else "пустой ответ модели")
    return text, calls


async def _with_retries(coro_factory, provider: str, what: str):
    last = None
    for attempt in range(RETRIES):
        try:
            return await coro_factory()
        except Exception as e:  # noqa: BLE001
            last = e
            log.warning("%s/%s попытка %d: %s", provider, what, attempt + 1, e)
            await asyncio.sleep(0.8 * (attempt + 1))
    raise last


# ---------------------------------------------------------------- complete

async def complete(system: str, user_text: str, tier: str = "lite",
                   max_tokens: int = 600, *, purpose: str = "complete",
                   tg_id: int | None = None, db=None) -> str:
    errors = []
    for provider in settings.provider_chain:
        meter = _Meter()
        model = _models(provider, tier)
        try:
            text = await _with_retries(
                lambda p=provider: _complete_with(p, system, user_text, tier,
                                                  max_tokens, meter),
                provider, "complete")
        except Exception as e:  # noqa: BLE001
            errors.append(f"{provider}: {e}")
            await record_usage(db, provider=provider, model=model, purpose=purpose,
                               prompt_tokens=meter.prompt,
                               completion_tokens=meter.completion,
                               latency_ms=meter.ms, ok=False, tg_id=tg_id)
            continue
        await record_usage(db, provider=provider, model=model, purpose=purpose,
                           prompt_tokens=meter.prompt,
                           completion_tokens=meter.completion,
                           latency_ms=meter.ms, ok=True, tg_id=tg_id)
        return text
    raise RuntimeError("Все LLM-провайдеры недоступны: " + "; ".join(errors))


async def _complete_with(provider, system, user_text, tier, max_tokens,
                         meter: _Meter) -> str:
    if provider == "anthropic":
        client = _anthropic_client()
        resp = await client.messages.create(
            model=_models(provider, tier), max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user_text}],
        )
        meter.add(getattr(resp, "usage", None))
        return "".join(b.text for b in resp.content if b.type == "text").strip()

    client = _openai_client(provider)
    text, _ = await _stream_chat(
        client, _models(provider, tier),
        [{"role": "system", "content": system}, {"role": "user", "content": user_text}],
        max_tokens, meter=meter,
    )
    return text


# ---------------------------------------------------------------- run_agent

async def run_agent(system: str, messages: list[dict], tools: list[dict],
                    execute: ToolExecutor, tier: str = "main",
                    max_tokens: int = 1500, *, purpose: str = "answer",
                    tg_id: int | None = None, db=None) -> str:
    """Агентный цикл: модель вызывает скиллы, мы исполняем, модель отвечает."""
    errors = []
    for provider in settings.provider_chain:
        meter = _Meter()
        model = _models(provider, tier)
        try:
            if provider == "anthropic":
                text = await _run_anthropic(system, messages, tools, execute,
                                            tier, max_tokens, meter)
            else:
                text = await _run_openai_like(provider, system, messages, tools,
                                              execute, tier, max_tokens, meter)
        except Exception as e:  # noqa: BLE001
            errors.append(f"{provider}: {e}")
            log.warning("run_agent %s: %s", provider, e)
            await record_usage(db, provider=provider, model=model, purpose=purpose,
                               prompt_tokens=meter.prompt,
                               completion_tokens=meter.completion,
                               latency_ms=meter.ms, ok=False, tg_id=tg_id)
            continue
        await record_usage(db, provider=provider, model=model, purpose=purpose,
                           prompt_tokens=meter.prompt,
                           completion_tokens=meter.completion,
                           latency_ms=meter.ms, ok=True, tg_id=tg_id)
        return text
    raise RuntimeError("Все LLM-провайдеры недоступны: " + "; ".join(errors))


async def _gather_tools(execute: ToolExecutor, calls: list[tuple[str, dict]]
                        ) -> list[str]:
    """Исполняет запрошенные скиллы параллельно.

    Модель часто просит сразу карту и транзиты; последовательное исполнение
    складывало задержки, а скиллы независимы и почти все — обращения к БД.
    """
    async def one(name: str, args: dict) -> str:
        try:
            return await execute(name, args)
        except Exception as e:  # noqa: BLE001
            log.warning("скилл %s упал в цикле агента: %s", name, e)
            return f"ошибка инструмента {name}: {e}"

    return list(await asyncio.gather(*(one(n, a) for n, a in calls)))


async def _run_anthropic(system, messages, tools, execute, tier, max_tokens,
                         meter: _Meter) -> str:
    client = _anthropic_client()
    sys_block = [{"type": "text", "text": system,
                  "cache_control": {"type": "ephemeral"}}]
    msgs = [dict(m) for m in messages]

    for _ in range(MAX_ITERS):
        resp = await _with_retries(
            lambda: client.messages.create(
                model=_models("anthropic", tier), max_tokens=max_tokens,
                system=sys_block, tools=tools, messages=msgs),
            "anthropic", "agent")
        meter.add(getattr(resp, "usage", None))
        if resp.stop_reason != "tool_use":
            return "".join(b.text for b in resp.content if b.type == "text").strip()
        msgs.append({"role": "assistant", "content": resp.content})
        blocks = [b for b in resp.content if b.type == "tool_use"]
        outputs = await _gather_tools(
            execute, [(b.name, dict(b.input or {})) for b in blocks])
        msgs.append({"role": "user", "content": [
            {"type": "tool_result", "tool_use_id": b.id, "content": out}
            for b, out in zip(blocks, outputs)]})
    return _fallback_text()


def _to_openai_tools(tools: list[dict]) -> list[dict]:
    return [{
        "type": "function",
        "function": {
            "name": t["name"],
            "description": t["description"],
            "parameters": t.get("input_schema", {"type": "object", "properties": {}}),
        },
    } for t in tools]


async def _run_openai_like(provider, system, messages, tools, execute,
                           tier, max_tokens, meter: _Meter) -> str:
    """OpenAI и OpenAI-совместимые серверы (custom/MiniMax).

    Если сервер не поддерживает function calling — падаем в pre-tool режим:
    выполняем базовые скиллы заранее и отвечаем одним запросом.
    """
    client = _openai_client(provider)
    model = _models(provider, tier)
    msgs: list[dict] = [{"role": "system", "content": system}]
    msgs += [{"role": m["role"], "content": m["content"]} for m in messages]
    oa_tools = _to_openai_tools(tools)

    try:
        for _ in range(MAX_ITERS):
            text, calls = await _with_retries(
                lambda: _stream_chat(client, model, msgs, max_tokens, oa_tools,
                                     meter=meter),
                provider, "agent")
            if not calls:
                return text
            msgs.append({
                "role": "assistant",
                "content": text,
                "tool_calls": [{
                    "id": c["id"], "type": "function",
                    "function": {"name": c["name"], "arguments": c["args"] or "{}"},
                } for c in calls],
            })
            parsed = []
            for c in calls:
                try:
                    parsed.append((c["name"], json.loads(c["args"] or "{}")))
                except json.JSONDecodeError:
                    parsed.append((c["name"], {}))
            outputs = await _gather_tools(execute, parsed)
            for c, out in zip(calls, outputs):
                msgs.append({"role": "tool", "tool_call_id": c["id"], "content": out})
        return _fallback_text()
    except Exception as e:  # noqa: BLE001
        # сервер не умеет tools (400/устаревший API) → pre-tool режим
        if "tool" not in str(e).lower() and "function" not in str(e).lower():
            raise
        log.info("%s без tool-use, включаю pre-tool режим", provider)
        return await _run_pretool(client, model, system, messages,
                                  execute, max_tokens, meter)


async def _run_pretool(client, model, system, messages, execute,
                       max_tokens, meter: _Meter) -> str:
    """Скиллы выполняются заранее (карта + транзиты + таро при намёке на расклад),
    результат кладётся в контекст, модель отвечает одним запросом."""
    last = messages[-1]["content"] if messages else ""
    lower = str(last).lower()
    wanted: list[tuple[str, dict]] = [("get_chart", {}), ("get_transits", {})]
    if any(w in lower for w in ("таро", "карт", "расклад", "будет", "стоит ли")):
        wanted.append(("draw_tarot", {"n": 3}))
    if any(w in lower for w in ("матриц", "предназнач", "карм")):
        wanted.append(("get_matrix", {}))
    context_parts = await _gather_tools(execute, wanted)
    system2 = (system + "\n\n[Данные твоих инструментов для этого ответа]\n"
               + "\n\n".join(context_parts))
    msgs = [{"role": "system", "content": system2}]
    msgs += [{"role": m["role"], "content": m["content"]} for m in messages]
    text, _ = await _stream_chat(client, model, msgs, max_tokens, meter=meter)
    return text


def _fallback_text() -> str:
    return "Звёзды сегодня говорят тихо... задай вопрос ещё раз, милая. 🌙"


# ---------------------------------------------------------------- голос

async def transcribe(file_bytes: bytes, filename: str = "voice.ogg") -> str | None:
    """Расшифровка голосового (Whisper, только настоящий OpenAI)."""
    if not settings.openai_key:
        return None
    try:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=settings.openai_key, timeout=60)
        resp = await client.audio.transcriptions.create(
            model="whisper-1", file=(filename, file_bytes), language="ru",
        )
        return (resp.text or "").strip() or None
    except Exception:
        return None


def tts_enabled() -> bool:
    return bool(settings.openai_key and settings.tts_model)


async def speak(text: str, *, voice: str | None = None) -> bytes | None:
    """Текст → голос Оракула (OGG/Opus для голосового сообщения Telegram).

    None означает «озвучки не будет» — тариф с аудио должен деградировать до
    текста, а не отдавать ошибку.
    """
    if not tts_enabled() or not (text or "").strip():
        return None
    try:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=settings.openai_key, timeout=120)
        resp = await client.audio.speech.create(
            model=settings.tts_model,
            voice=voice or settings.tts_voice,
            input=text[:4000],
            response_format="opus",
        )
        return resp.read() if hasattr(resp, "read") else bytes(resp.content)
    except Exception as e:  # noqa: BLE001
        log.info("озвучка не удалась: %s", e)
        return None
