"""Натальная карта, Матрица Судьбы, совместимость, партнёры, разборы."""
from __future__ import annotations

import json
import re
from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from ...core import agent as agent_core
from ...core import astro, geo, memory, skills
from ...core.matrix import compute_matrix
from ...repo import billing, dialog, readings, users
from ...services import analytics
from ..deps import active_user, current_user, get_db, rate_limit

router = APIRouter(prefix="/api", tags=["chart"])


def _parse_date(value: str) -> str:
    """Принимаем YYYY-MM-DD и ДД.ММ.ГГГГ — интерфейс и бот дают разный формат."""
    value = (value or "").strip()
    for fmt in ("%Y-%m-%d", "%d.%m.%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(value, fmt).date().isoformat()
        except ValueError:
            continue
    raise HTTPException(400, "нужна дата в формате ДД.ММ.ГГГГ")


@router.get("/chart")
async def chart(user=Depends(current_user), db=Depends(get_db)):
    """Карта целиком: планеты, дома, аспекты — для колеса и списков."""
    data = users.chart_of(user)
    if not data:
        raise HTTPException(400, "карта ещё не построена — пройди знакомство в боте")
    return {
        "mode": data.get("mode", "lite"),
        "sun": data.get("sun"),
        "ascendant": data.get("ascendant"),
        "mc": data.get("mc"),
        "planets": data.get("planets", []),
        "houses": data.get("houses", []),
        "aspects": data.get("aspects", []),
        "nodes": data.get("nodes", []),
        "note": data.get("note"),
        "birth": {"date": user["birth_date"], "time": user["birth_time"],
                  "city": user["birth_city"],
                  "time_known": bool(user["birth_time_known"])},
    }


_TIME_RE = re.compile(r"^\d{1,2}:\d{2}$")


class ChartBuildIn(BaseModel):
    birth_time: str | None = None
    birth_city: str | None = Field(default=None, max_length=60)


@router.post("/chart", dependencies=[Depends(rate_limit("write"))])
async def build_chart(item: ChartBuildIn | None = None, user=Depends(current_user),
                      db=Depends(get_db)):
    """Строит и сохраняет натальную карту — тот же путь, что в онбординге бота.

    Нужно для сценария «собери карту прямо здесь»: у астролога в чате клиентка
    может заполнить/уточнить время и город, не заходя в бота. Если карта уже
    построена — возвращает её без пересчёта.
    """
    if not user["birth_date"]:
        raise HTTPException(400, "нет даты рождения — заполни её в боте")

    existing = users.chart_of(user)
    if existing and not (item and (item.birth_time or item.birth_city)):
        return {"ok": True, "cached": True, "mode": existing.get("mode"),
                "sun": existing.get("sun"), "ascendant": existing.get("ascendant"),
                "planets": existing.get("planets", []),
                "houses": existing.get("houses", []),
                "nodes": existing.get("nodes", []), "mc": existing.get("mc"),
                "aspects": existing.get("aspects", [])}

    item = item or ChartBuildIn()
    city = (item.birth_city or user["birth_city"] or "").strip()
    if not city:
        raise HTTPException(400, "укажи город рождения")
    time = item.birth_time or user["birth_time"] or "12:00"
    if item.birth_time and not _TIME_RE.match(item.birth_time):
        raise HTTPException(400, "время в формате ЧЧ:ММ, например 14:30")

    lat, lon, tz = await geo.resolve_city_async(city, db)
    chart = await astro.compute_chart_async(user["birth_date"], time, city, lat, lon, tz)
    await users.update(db, user["tg_id"], birth_city=city, birth_lat=lat,
                       birth_lon=lon, tz=tz, birth_time=time,
                       birth_time_known=1 if item.birth_time else user["birth_time_known"],
                       chart_json=json.dumps(chart, ensure_ascii=False))
    return {"ok": True, "cached": False, "mode": chart.get("mode"),
            "sun": chart.get("sun"), "ascendant": chart.get("ascendant"),
            "planets": chart.get("planets", []), "houses": chart.get("houses", []),
            "nodes": chart.get("nodes", []), "mc": chart.get("mc"),
            "aspects": chart.get("aspects", [])}


@router.post("/chart/interpret", dependencies=[Depends(rate_limit("write"))])
async def chart_interpret(user=Depends(current_user), db=Depends(get_db)):
    """Бесплатный ИИ-разбор построенной карты простыми словами (кэш в chart_json).

    Для людей без астрологических знаний: кто ты, характер, сильные/слабые
    стороны, страхи, предназначение (Раху) и кармический багаж (Кету).
    """
    if not user["birth_date"]:
        raise HTTPException(400, "нет даты рождения")
    chart = users.chart_of(user)
    if not chart:
        raise HTTPException(400, "карта ещё не построена")
    text = chart.get("interpretation")
    if not text:
        text, live = await agent_core.interpret_chart(db, user, chart)
        # Кэшируем только LLM-генерацию: офлайн-заглушка не должна «залипать».
        if live:
            chart["interpretation"] = text
            await users.update(db, user["tg_id"],
                               chart_json=json.dumps(chart, ensure_ascii=False))
    return {"text": text}


@router.get("/matrix")
async def matrix(user=Depends(current_user)):
    if not user["birth_date"]:
        raise HTTPException(400, "нет даты рождения")
    return compute_matrix(user["birth_date"])


# ─────────────────────────────── совместимость ────────────────────────────────

class CompatIn(BaseModel):
    partner_date: str
    partner_name: str = Field(default="", max_length=30)
    save: bool = False
    relation: Literal["love", "friend", "work", "family"] = "love"


@router.post("/compat", dependencies=[Depends(rate_limit("write"))])
async def compat(item: CompatIn, user=Depends(current_user), db=Depends(get_db)):
    """«Спидометр любви»: балл и его разбор считает сервер.

    Формула живёт в одном месте специально: раньше у клиента была своя копия, и
    Mini App показывал балл, не совпадающий с ответом Оракула в чате.
    """
    if not user["birth_date"]:
        raise HTTPException(400, "нет даты рождения")
    partner_date = _parse_date(item.partner_date)
    # Полные карты обеих сохранились (партнёр с городом и временем) — синастрия
    # пары учесться в балле; иначе остаётся балл по датам (лёгкий путь).
    aspects = await skills._pair_aspects(db, user, partner_date)
    data = skills._compat(user["birth_date"], partner_date, relation=item.relation,
                          aspects=aspects)
    if item.save and item.partner_name:
        await readings.add_partner(db, user["tg_id"], item.partner_name.strip(),
                                   partner_date)
    return {**data, "partner_date": partner_date}


@router.post("/compat/full", dependencies=[Depends(rate_limit("llm"))])
async def compat_full(item: CompatIn, user=Depends(active_user), db=Depends(get_db)):
    """Разбор пары Астрологом — расходует вопрос дня."""
    from ...services import limits
    from .chat import _deny

    if not user["birth_date"]:
        raise HTTPException(400, "нет даты рождения")
    partner_date = _parse_date(item.partner_date)
    name = item.partner_name.strip()[:30]

    verdict = await limits.check(db, user)
    if not verdict.allowed:
        raise _deny(verdict)
    if not await limits.consume(db, user, verdict):
        raise _deny(verdict)

    thread = await dialog.ensure_thread(db, user["tg_id"], "astro")
    await dialog.save_message(
        db, user["tg_id"], "user", f"Совместимость с {name or 'партнёром'}",
        is_question=limits.counts_toward_limit(verdict), thread_id=thread["id"],
        agent="astro", surface="miniapp")
    text = await agent_core.interpret_compat(db, user, partner_date, name)
    await dialog.save_message(db, user["tg_id"], "assistant", text,
                              thread_id=thread["id"], agent="astro",
                              surface="miniapp")
    if name:
        await memory.remember(db, user["tg_id"],
                              f"Партнёр {name}, дата рождения {partner_date}",
                              kind="person")
        if item.save:
            await readings.add_partner(db, user["tg_id"], name, partner_date)
    await analytics.track(db, "compat_full", user["tg_id"], surface="miniapp")
    scores = skills._compat(user["birth_date"], partner_date, relation=item.relation)
    return {"answer": text, "scores": scores}


# ──────────────────────────────── партнёры ────────────────────────────────────

class PartnerIn(BaseModel):
    name: str = Field(min_length=1, max_length=40)
    birth_date: str
    relation: str = Field(default="partner", max_length=20)
    birth_time: str | None = None
    birth_city: str | None = Field(default=None, max_length=60)


@router.get("/partners")
async def partners(user=Depends(current_user), db=Depends(get_db)):
    return await readings.list_partners(db, user["tg_id"])


@router.post("/partners", dependencies=[Depends(rate_limit("write"))])
async def add_partner(item: PartnerIn, user=Depends(current_user),
                      db=Depends(get_db)):
    """Сохраняет человека из окружения — чтобы агент понимал «он»/«она»."""
    birth_date = _parse_date(item.birth_date)
    lat = lon = tz = None
    chart_data = None
    if item.birth_city:
        lat, lon, tz = await geo.resolve_city_async(item.birth_city, db)
        chart_data = await astro.compute_chart_async(birth_date, item.birth_time,
                                                     item.birth_city, lat, lon, tz)
    partner_id = await readings.add_partner(
        db, user["tg_id"], item.name.strip(), birth_date,
        relation=item.relation, birth_time=item.birth_time,
        birth_city=item.birth_city, lat=lat, lon=lon, tz=tz, chart=chart_data)
    await memory.remember(db, user["tg_id"],
                          f"{item.relation}: {item.name} ({birth_date})",
                          kind="person")
    return {"id": partner_id, "ok": True}


@router.delete("/partners/{partner_id}", dependencies=[Depends(rate_limit("write"))])
async def delete_partner(partner_id: int, user=Depends(current_user),
                         db=Depends(get_db)):
    await readings.delete_partner(db, partner_id, user["tg_id"])
    return {"ok": True}


# ───────────────────────────── купленные разборы ──────────────────────────────

class ReportIn(BaseModel):
    partner_date: str | None = None
    partner_name: str = Field(default="", max_length=30)


@router.get("/reports")
async def reports(user=Depends(current_user), db=Depends(get_db)):
    """Список готовых разборов + права на ещё не собранные."""
    return {
        "ready": await readings.list_reports(db, user["tg_id"]),
        "available": [e for e in await billing.list_entitlements(db, user["tg_id"])
                      if e["kind"] == "report"],
    }


@router.get("/reports/{kind}")
async def get_report(kind: str, period: str | None = None,
                     user=Depends(current_user), db=Depends(get_db)):
    row = await readings.get_report(db, user["tg_id"], kind, period)
    if not row:
        raise HTTPException(404, "такого разбора пока нет")
    return {"kind": row["kind"], "title": row["title"], "body": row["body"],
            "period": row["period"], "created_at": row["created_at"]}


@router.post("/reports/{kind}", dependencies=[Depends(rate_limit("llm"))])
async def build_report(kind: str, item: ReportIn | None = None,
                       user=Depends(current_user), db=Depends(get_db)):
    """Собирает купленный разбор. Право списывается только после успеха."""
    if kind not in agent_core.REPORTS:
        raise HTTPException(404, "неизвестный разбор")
    item = item or ReportIn()

    existing = await readings.get_report(db, user["tg_id"], kind,
                                        item.partner_date if kind == "synastry" else None)
    if existing and existing["body"]:
        return {"kind": kind, "title": existing["title"], "body": existing["body"],
                "cached": True}

    if not await billing.available_entitlements(db, user["tg_id"], "report", kind):
        raise HTTPException(402, "этот разбор нужно открыть в лавке 💎")

    partner_date = _parse_date(item.partner_date) if item.partner_date else None
    if kind == "synastry" and not partner_date:
        raise HTTPException(400, "для синастрии нужна дата партнёра")

    result = await agent_core.build_report(db, user, kind, partner_date=partner_date,
                                          partner_name=item.partner_name)
    if not await billing.consume_entitlement(db, user["tg_id"], "report", kind):
        # право исчезло между проверкой и списанием (второе устройство) —
        # отчёт уже сохранён, отдаём его, повторно не спишем
        pass
    await analytics.track(db, "report_built", user["tg_id"],
                          props={"kind": kind}, surface="miniapp")
    return result
