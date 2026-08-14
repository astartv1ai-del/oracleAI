"""Исполнение агента: сборка контекста, tool-use цикл, офлайн-подстраховка.

Продукт обязан отвечать всегда. Поэтому у каждого вызова есть три уровня:
    1. агентный цикл с инструментами (полноценный ответ);
    2. цепочка резервных LLM-провайдеров внутри `core.llm`;
    3. офлайн-трактовка на реальных расчётах — если недоступны все провайдеры.

Третий уровень не заглушка: карты, знак Солнца и арканы в нём настоящие, просто
текст собран шаблоном. Клиентка получает осмысленный ответ, а не «сервис недоступен».
"""
from __future__ import annotations

import json
import logging
import random

from ...repo import billing as billing_repo
from ...repo import content as content_repo
from ...repo import dialog as dialog_repo
from ...repo import users as users_repo
from .. import astro, llm, memory, skills, tarot
from .. import matrix as mx
from ..personas import persona_style
from ..stable import stable_seed
from .base import build_system_prompt
from .context import build_bounded_history
from ..interpretation import validate_nonfatal_text
from .specs import DEFAULT_AGENT, REGISTRY, get

log = logging.getLogger("oracle.agents")

# Ответ агента — это несколько абзацев. Всё, что короче, — обрывок: модели
# иногда возвращают заглушку вроде «Готова услышать твои мысли».
MIN_ANSWER_LEN = 120


async def resolve(db, code: str | None):
    """Агент по коду с переопределениями из админки (`content_items`).

    Правится образ, название и подпись — то, что относится к бренду. Набор
    скиллов остаётся в коде: это логика, а не текст.
    """
    spec = get(code)
    if db is None:
        return spec, spec.style, spec.rules
    try:
        item = await content_repo.get_content(db, "agent", spec.code)
    except Exception as e:  # noqa: BLE001
        log.warning("настройки агента %s недоступны: %s", spec.code, e)
        item = None
    if not item:
        return spec, spec.style, spec.rules
    meta = content_repo.content_meta(item)
    return spec, item.get("body") or spec.style, meta.get("rules") or spec.rules


async def _context(db, user, spec, question: str = ""):
    """Контекст клиентки: карта, арканы, память — с глубиной по тарифу.

    Память подбирается под вопрос (семантический поиск), а не берётся «сверху
    списка»: иначе на вопрос о работе в промпт уходили факты про бывшего.
    Часть слотов всегда отдана самым весомым фактам — они про неё в целом.
    """
    chart = users_repo.chart_of(user)
    brief = (astro.chart_brief(chart, time_known=bool(user["birth_time_known"]))
             if chart else "карта ещё не построена")
    matrix_brief = "-"
    if user["birth_date"]:
        try:
            matrix_brief = mx.matrix_brief(mx.compute_matrix(user["birth_date"]))
        except (ValueError, KeyError) as e:
            log.warning("матрица для %s не посчиталась: %s", user["tg_id"], e)

    plan = await billing_repo.get_plan(db, user["sub_level"] or "free")
    depth = plan.get("memory_depth") or 20
    if not users_repo.sub_active(user):
        # «Память заморожена» на бесплатном уровне — это и есть причина продлить
        free = await billing_repo.get_plan(db, "free")
        depth = free.get("memory_depth") or 5

    if not bool(user["memory_enabled"]):
        return brief, matrix_brief, [], ""
    memories = await memory.recall(db, user["tg_id"], question, limit=depth)
    summary = await memory.get_summary(db, user["tg_id"]) if depth > 5 else ""
    return brief, matrix_brief, memories, summary


async def system_for(db, user, spec=None, *, allowance_line: str = "",
                     question: str = "", extra_rules: str = "") -> str:
    """Системный промпт агента для этой клиентки."""
    spec = spec or get(DEFAULT_AGENT)
    spec, style, rules = await resolve(db, spec.code)
    if spec.uses_persona:
        style = await persona_style(db, user)
    brief, matrix_brief, memories, summary = await _context(db, user, spec, question)
    language_rule = ("Reply in clear, warm English. Keep card and calculation names "
                     "recognisable; never pretend a translation is an exact calculation."
                     if user["lang"] == "en" else "")
    combined_extra_rules = "\n".join(rule for rule in (extra_rules, language_rule) if rule)
    return build_system_prompt(
        spec, user=user, agent_name=spec.display_name(user), chart_brief=brief,
        matrix_brief=matrix_brief, memories=memories,
        allowance_line=allowance_line, style=style, rules=rules,
        profile_summary=summary, extra_rules=combined_extra_rules)


async def answer(db, user, question: str, *, agent: str = DEFAULT_AGENT,
                 thread_id: int | None = None, allowance_line: str = "",
                 extra_rules: str = "") -> str:
    """Ответ агента на вопрос. Никогда не поднимает исключение наружу."""
    spec = get(agent)
    if llm.enabled():
        try:
            system = await system_for(db, user, spec, allowance_line=allowance_line,
                                      question=question, extra_rules=extra_rules)
            # Активная подписка оплачивает более глубокий разбор: больше итераций
            # на многошаговый «план + разбор + совет» и длиннее тред в контексте.
            premium = users_repo.sub_active(user) if db else False
            history_limit = (max(spec.history_limit, 20)
                             if premium else spec.history_limit)
            # Берём небольшой запас для детерминированной выжимки ранней части
            # текущего треда. Новый тред не имеет истории, поэтому это и есть
            # явный сброс краткосрочного контекста без затрагивания памяти.
            history = await dialog_repo.history(
                db, user["tg_id"], limit=history_limit * 3, thread_id=thread_id)
            messages = build_bounded_history(history, question,
                                              recent_limit=history_limit)

            async def executor(name: str, args: dict) -> str:
                return await skills.execute(db, user, name, args)

            text = await llm.run_agent(
                system, messages, skills.tools_for(spec.skills), executor,
                tier=spec.tier, max_tokens=spec.max_tokens,
                purpose=f"answer:{spec.code}", tg_id=user["tg_id"], db=db,
                max_iters=10 if premium else None)
            quality = validate_nonfatal_text(text)
            if not quality.ok:
                log.warning("агент %s не прошёл safety gate: %s — офлайн",
                            spec.code, "; ".join(quality.issues))
            elif len(text.strip()) >= MIN_ANSWER_LEN:
                return text
            else:
                log.info("агент %s вернул слишком короткий ответ (%d симв) — офлайн",
                         spec.code, len(text.strip()))
        except Exception as e:  # noqa: BLE001
            log.warning("агент %s не ответил (%s) — офлайн", spec.code, e)

    chart = users_repo.chart_of(user)
    memories = (await dialog_repo.get_memories(db, user["tg_id"], limit=5)
                if bool(user["memory_enabled"]) else [])
    return offline_answer(user, question, chart, memories, spec)


# ─────────────────────────── офлайн-трактовка ─────────────────────────────────

_OPENINGS = [
    "Я слышу твой вопрос, {name}... Нити уже задрожали.",
    "{name}, я всмотрелась в твою карту, прежде чем ответить.",
    "Звёзды наклонились ближе, {name}. Слушай.",
]
_CLOSINGS = [
    "Запиши это в дневник — через неделю поймёшь, о чём я. 🌙",
    "Доверься этому знаку. Я рядом, когда захочешь спросить ещё. ✨",
    "И помни: карты показывают дорогу, но идёшь по ней ты. 💫",
]
_ADVICE_BY_ELEMENT = {
    "огонь": "действуй смело, твоя стихия — огонь, промедление гасит его",
    "вода": "слушай чувства, твоя стихия — вода: она всегда знает, куда течь",
    "воздух": "поговори об этом вслух — воздуху нужно движение слов",
    "земля": "сделай один маленький практический шаг — земля любит опору",
}


def offline_answer(user, question: str, chart: dict, memories: list[str],
                   spec=None) -> str:
    """Ответ на реальных расчётах, собранный без модели.

    Сид детерминирован вопросом и клиенткой: повторный запрос того же вопроса не
    выдаёт другую судьбу — иначе офлайн-режим выглядел бы как обман.
    """
    spec = spec or get(DEFAULT_AGENT)
    if spec.code == "chiromant":
        return (
            "Я Мира, Проводник ладони. Для ответа мне нужно сохранённое evidence-чтение "
            "по фотографии ладони.\n\n"
            "Загрузи одну ладонь целиком при ровном свете — я проверю качество кадра, "
            "покажу только различимые зоны и предложу один вопрос для саморефлексии. "
            "Это не медицинская диагностика и не предсказание."
        )
    rnd = random.Random(stable_seed(question, user["tg_id"]))
    name = user["name"] or "милая"
    sun = (chart.get("sun") or {})
    sign = sun.get("sign", "твоём знаке")
    element = sun.get("element", "")

    cards = tarot.draw(3)
    positions = ["Прошлое", "Настоящее", "Будущее"]
    cards_block = tarot.cards_text(cards, positions)

    destiny = ""
    if user["birth_date"]:
        try:
            m = mx.compute_matrix(user["birth_date"])
            destiny = (f"Твой аркан судьбы — {m['destiny']['n']} "
                       f"({m['destiny']['arcana']}): {m['destiny']['meaning']}.")
        except (ValueError, KeyError):
            destiny = ""

    mem_line = ""
    if memories:
        mem_line = (f"Я помню, что ты говорила мне: «{memories[0]}» — "
                    f"держу это в сердце, отвечая тебе.")

    key = cards[1]
    advice = _ADVICE_BY_ELEMENT.get(element, "слушай себя — ответ уже внутри")
    if user["lang"] == "en":
        english_memory = ("I will keep in mind something you shared with me — "
                          "only because your memory setting is on. " if memories else "")
        return (
            f"I hear your question, {name}. Let’s look at it gently.\n\n"
            f"Your Sun sign ({sign}) is one point of reflection here. {english_memory}\n\n"
            f"The three-card spread is:\n{cards_block}\n\n"
            f"At the centre is {key['emoji']} {key['name']}: {key['meaning']}. "
            "Treat this as a reflective prompt, not a fixed prediction. "
            "Choose one small, kind action that feels possible today."
        )
    return (
        f"{rnd.choice(_OPENINGS).format(name=name)}\n\n"
        f"Солнце в {sign} даёт тебе больше силы, чем ты себе разрешаешь. {destiny}\n"
        f"{mem_line}\n\n"
        f"Я разложила для тебя три карты:\n{cards_block}\n\n"
        f"Сердце расклада — {key['emoji']} {key['name']}: {key['meaning']}. "
        f"На твой вопрос это отвечает так: {advice}.\n\n"
        f"{rnd.choice(_CLOSINGS)}"
    ).replace("\n\n\n", "\n\n")


# ─────────────────────────── витрина агентов ─────────────────────────────────

async def agent_list(db, user) -> list[dict]:
    """Список агентов для интерфейса, с описаниями из админки."""
    out = []
    for code in REGISTRY:
        spec, style, _ = await resolve(db, code)
        item = spec.as_dict(user)
        try:
            content = await content_repo.get_content(db, "agent", code)
        except Exception:  # noqa: BLE001
            content = None
        if content:
            meta = content_repo.content_meta(content)
            item["title"] = content.get("title") or item["title"]
            item["tagline"] = meta.get("tagline") or item["tagline"]
        out.append(item)
    return out


def as_json(user, code: str) -> str:
    return json.dumps(get(code).as_dict(user), ensure_ascii=False)
