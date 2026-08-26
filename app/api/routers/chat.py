"""Чаты с агентами: список, история, вопрос."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from ...core import agents
from ...repo import dialog
from ...services import chat as chat_svc
from ..common.errors import access_denied
from ..contracts.chat import AskIn
from ..deps import confirmed_age_user, get_db, rate_limit

router = APIRouter(prefix="/api", tags=["chat"])

@router.get("/agents")
async def agent_list(user=Depends(confirmed_age_user), db=Depends(get_db)):
    """Список чатов: агент, превью последнего сообщения, подсказки."""
    return await chat_svc.threads_view(db, user)


@router.get("/chat")
async def chat_history_default(user=Depends(confirmed_age_user), db=Depends(get_db)):
    """Совместимость: общая лента диалога с Оракулом."""
    messages = await dialog.history(db, user["tg_id"], limit=30)
    return {"messages": messages}


@router.get("/chat/{agent}")
async def chat_history(agent: str, user=Depends(confirmed_age_user), db=Depends(get_db)):
    if agent not in agents.codes():
        raise HTTPException(404, "нет такого собеседника")
    return await chat_svc.thread_history(db, user, agent)


@router.post("/chat/{agent}", dependencies=[Depends(rate_limit("llm"))])
async def ask_agent(agent: str, item: AskIn, user=Depends(confirmed_age_user),
                    db=Depends(get_db)):
    if agent not in agents.codes():
        raise HTTPException(404, "нет такого собеседника")
    try:
        return await chat_svc.ask(db, user, item.text, agent=agent,
                                  surface="miniapp", allow_paid=item.allow_paid)
    except chat_svc.ChatDenied as e:
        raise access_denied(e.verdict) from e
    except ValueError as e:
        raise HTTPException(400, str(e)) from e


@router.post("/ask", dependencies=[Depends(rate_limit("llm"))])
async def ask(item: AskIn, user=Depends(confirmed_age_user), db=Depends(get_db)):
    """Совместимость: вопрос главному Оракулу."""
    try:
        result = await chat_svc.ask(db, user, item.text,
                                   agent=agents.DEFAULT_AGENT, surface="miniapp")
    except chat_svc.ChatDenied as e:
        raise access_denied(e.verdict) from e
    return {"answer": result["answer"],
            "questions_left": result["allowance"]["left"],
            "allowance": result["allowance"]}


@router.delete("/chat/{agent}", dependencies=[Depends(rate_limit("write"))])
async def clear_thread(agent: str, user=Depends(confirmed_age_user), db=Depends(get_db)):
    """Архивирует переписку: новый чат начнётся с чистого листа.

    Сообщения не удаляются — память о клиентке и история для поддержки остаются.
    """
    if agent not in agents.codes():
        raise HTTPException(404, "нет такого собеседника")
    thread = await dialog.ensure_thread(db, user["tg_id"], agent)
    await dialog.archive_thread(db, thread["id"], user["tg_id"])
    return {"ok": True}


# ─────────────────── многочатовые сессии (как ChatGPT) ───────────────────────

MAX_SESSIONS = 5


@router.get("/chat/{agent}/sessions")
async def list_sessions(agent: str, user=Depends(confirmed_age_user), db=Depends(get_db)):
    """Чаты-сессии агента (до MAX_SESSIONS) — новые впереди."""
    if agent not in agents.codes():
        raise HTTPException(404, "нет такого собеседника")
    rows = [dict(r) for r in await dialog.list_threads(db, user["tg_id"])
            if r["agent"] == agent][:MAX_SESSIONS]
    return rows


@router.post("/chat/{agent}/sessions", dependencies=[Depends(rate_limit("write"))])
async def new_session(agent: str, user=Depends(confirmed_age_user), db=Depends(get_db)):
    if agent not in agents.codes():
        raise HTTPException(404, "нет такого собеседника")
    rows = [r for r in await dialog.list_threads(db, user["tg_id"])
            if r["agent"] == agent]
    if len(rows) >= MAX_SESSIONS:
        raise HTTPException(400,
                            f"максимум {MAX_SESSIONS} чатов — заверши один или удали")
    spec = agents.get(agent)
    thread = await dialog.create_thread(db, user["tg_id"], spec.code,
                                        title=spec.title)
    return {"thread_id": thread["id"], "title": spec.title}


@router.get("/chat/{agent}/sessions/{thread_id}")
async def session_history(agent: str, thread_id: int, user=Depends(confirmed_age_user),
                          db=Depends(get_db)):
    if agent not in agents.codes():
        raise HTTPException(404, "нет такого собеседника")
    thread = await dialog.get_thread(db, thread_id, user["tg_id"])
    if not thread or thread["agent"] != agent or thread["archived"]:
        raise HTTPException(404, "нет такого чата")
    messages = await dialog.thread_messages(db, thread_id, limit=60)
    return {"agent": agents.get(agent).as_dict(user), "thread_id": thread_id,
            "messages": messages}


@router.post("/chat/{agent}/sessions/{thread_id}",
             dependencies=[Depends(rate_limit("llm"))])
async def ask_session(agent: str, thread_id: int, item: AskIn,
                      user=Depends(confirmed_age_user), db=Depends(get_db)):
    if agent not in agents.codes():
        raise HTTPException(404, "нет такого собеседника")
    try:
        return await chat_svc.ask(db, user, item.text, agent=agent,
                                  surface="miniapp", allow_paid=item.allow_paid,
                                  thread_id=thread_id)
    except chat_svc.ChatDenied as e:
        raise access_denied(e.verdict) from e
    except ValueError as e:
        raise HTTPException(400, str(e)) from e


@router.delete("/chat/{agent}/sessions/{thread_id}",
               dependencies=[Depends(rate_limit("write"))])
async def delete_session(agent: str, thread_id: int, user=Depends(confirmed_age_user),
                         db=Depends(get_db)):
    thread = await dialog.get_thread(db, thread_id, user["tg_id"])
    if not thread or thread["agent"] != agent:
        raise HTTPException(404, "нет такого чата")
    await dialog.archive_thread(db, thread_id, user["tg_id"])
    return {"ok": True}
