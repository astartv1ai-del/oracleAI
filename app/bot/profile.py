"""Профиль: состояние доступа, память, рефералка, образ Оракула, разборы."""
from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.types import CallbackQuery

from ..core.personas import persona_list
from ..repo import admin as admin_repo
from ..repo import billing, dialog, readings, users
from ..services import analytics, limits, referrals
from .chat import _send_long
from .keyboards import (back_menu, main_menu, personas_kb, profile_kb,
                        report_kb, share_kb)

log = logging.getLogger("oracle.bot.profile")
router = Router()


async def _menu(db, tg_id: int):
    return main_menu(is_admin=bool(await admin_repo.resolve_role(db, tg_id)))


@router.callback_query(F.data == "profile")
async def profile(cb: CallbackQuery, db):
    user = await users.get(db, cb.from_user.id)
    allowance = await limits.allowance(db, user, check_followup=False)
    active = users.sub_active(user)
    streak = await dialog.diary_streak(db, cb.from_user.id)
    memories = await dialog.get_memories(db, cb.from_user.id, limit=5)
    ref = await referrals.stats(db, cb.from_user.id)
    entitlements = await billing.list_entitlements(db, cb.from_user.id)

    sub_line = (f"{allowance.plan['title']} · осталось "
                f"{users.sub_days_left(user)} дн." if active else "доступ завершён")
    unit = "сегодня" if allowance.period == "day" else "на неделе"
    mem_block = ("\n".join(f"• {m}" for m in memories) if memories
                 else "<i>я только начинаю узнавать тебя</i>")

    lines = [
        f"👤 <b>{user['name']}</b>",
        f"🔮 Твой Оракул: {user['oracle_name']}",
        f"💫 Доступ: {sub_line}",
        f"✦ Кристаллы: <b>{user['crystals']}</b>",
        f"💬 Вопросов {unit}: {allowance.left} из {allowance.limit}"
        + (f" (+{allowance.extra_questions} купленных)"
           if allowance.extra_questions else ""),
        f"📖 Стрик дневника: {streak} дн. {'🔥' if streak >= 3 else ''}",
    ]
    if ref["level1"]:
        lines.append(f"🌟 Приглашено людей: {ref['level1']}"
                     + (f" · из них платят: {ref['paying']}" if ref["paying"] else ""))
    if entitlements:
        names = {"spread": "расклады", "report": "разборы", "question": "вопросы"}
        opened = ", ".join(
            f"{names.get(e['kind'], e['kind'])} ×{e['qty_total'] - e['qty_used']}"
            for e in entitlements[:4])
        lines.append(f"🎁 Открыто: {opened}")
    lines += ["", "<b>Что я о тебе знаю:</b>", mem_block]

    await cb.message.answer("\n".join(lines),
                            reply_markup=profile_kb(
                                push_on=bool(user["morning_push"]),
                                sub_active=active))
    await cb.answer()


@router.callback_query(F.data == "toggle_push")
async def toggle_push(cb: CallbackQuery, db):
    user = await users.get(db, cb.from_user.id)
    new_value = 0 if user["morning_push"] else 1
    await users.update(db, cb.from_user.id, morning_push=new_value)
    await analytics.track(db, "toggle_push", cb.from_user.id,
                          props={"on": bool(new_value)})
    await cb.answer("Утренний прогноз включён 🌅" if new_value
                    else "Утренний прогноз выключен 🌙")
    await profile(cb, db)


@router.callback_query(F.data == "change_persona")
async def change_persona(cb: CallbackQuery, db):
    await cb.message.answer(
        "🔮 <b>Кем мне быть для тебя?</b>\n"
        "<i>Меняется только манера речи — память и карта останутся.</i>",
        reply_markup=personas_kb(await persona_list(db)))
    await cb.answer()


@router.callback_query(F.data == "invite")
async def invite(cb: CallbackQuery, db):
    me = await cb.bot.get_me()
    link = referrals.link_for(me.username, cb.from_user.id)
    stats = await referrals.stats(db, cb.from_user.id)

    lines = [
        "🌟 <b>Поделись встречей с Оракулом</b>",
        "",
        f"Твоя личная ссылка:\n<code>{link}</code>",
        "",
        f"За каждого приглашённого — по ✦{stats['bonus_per_invite']} каждому.",
        f"Когда приглашённый оформит доступ — тебе ещё ✦{stats['revenue_share']}. ✨",
    ]
    if stats["level1"]:
        lines += ["",
                  f"Уже пришло по твоей ссылке: <b>{stats['level1']}</b>"
                  + (f" · второй уровень: {stats['level2']}" if stats["level2"] else ""),
                  f"Из них оформили доступ: <b>{stats['paying']}</b>",
                  f"Начислено всего: ✦{stats['bonus_total']}"]

    await cb.message.answer(
        "\n".join(lines),
        reply_markup=share_kb(link, referrals.share_text(stats["bonus_per_invite"]),
                              label="💌 Поделиться ссылкой"))
    await cb.answer()


@router.callback_query(F.data == "my_reports")
async def my_reports(cb: CallbackQuery, db):
    ready = await readings.list_reports(db, cb.from_user.id)
    available = [e for e in await billing.list_entitlements(db, cb.from_user.id)
                 if e["kind"] == "report"]
    if not ready and not available:
        await cb.answer()
        await cb.message.answer(
            "📜 Больших разборов пока нет.\n\n"
            "Разбор натальной карты, Матрицы, пары или соляр — это длинный текст, "
            "который остаётся у тебя навсегда. Взять можно в 💎 Лавке.",
            reply_markup=back_menu())
        return

    lines = ["📜 <b>Твои разборы</b>", ""]
    if available:
        lines.append("<i>Оплачено и ждёт сборки:</i>")
        for item in available:
            lines.append(f"• {item['code']} ×{item['qty_total'] - item['qty_used']}")
        lines.append("<i>Собрать разбор можно в Mini App — раздел «Карта».</i>")
        lines.append("")
    if ready:
        lines.append("<i>Готовые:</i>")
    await cb.message.answer("\n".join(lines), reply_markup=report_kb(ready))
    await cb.answer()


@router.callback_query(F.data.startswith("report:"))
async def show_report(cb: CallbackQuery, db):
    parts = cb.data.split(":")
    kind = parts[1]
    period = parts[2] if len(parts) > 2 and parts[2] else None
    row = await readings.get_report(db, cb.from_user.id, kind, period)
    if not row:
        await cb.answer("Разбор не найден", show_alert=True)
        return
    await cb.answer()
    await _send_long(cb.message, f"<b>{row['title']}</b>\n\n{row['body']}",
                     reply_markup=back_menu())


@router.callback_query(F.data == "admin_stats")
async def admin_stats_cb(cb: CallbackQuery, db):
    """Резерв, когда WEBAPP_URL не задан и веб-панель недоступна."""
    role = await admin_repo.resolve_role(db, cb.from_user.id)
    if not role:
        await cb.answer("Нет доступа")
        return
    from ..repo import analytics as analytics_repo
    o = await analytics_repo.overview(db)
    funnel = await analytics_repo.funnel(db, 30)
    lines = ["📊 <b>Оракул за 30 дней</b>", ""]
    for step in funnel:
        lines.append(f"{step['step']}: <b>{step['value']}</b> ({step['of_total']}%)")
    lines += ["",
              f"⭐ Stars: {o['stars_total']} всего · {o['stars_30d']} за месяц",
              f"💫 Живых подписок: {o['subs_active']}",
              f"✦ Кристаллов у клиенток: {o['crystals_outstanding']}",
              "",
              "<i>Полная панель открывается, когда задан WEBAPP_URL.</i>"]
    await cb.message.answer("\n".join(lines),
                            reply_markup=await _menu(db, cb.from_user.id))
    await cb.answer()
