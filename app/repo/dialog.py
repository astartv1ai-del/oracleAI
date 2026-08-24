"""Диалоги: треды по агентам, сообщения, память, дневник."""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

from ..data.session import transaction, utcnow
from . import users as users_repo

# ─────────────────────────────── треды ────────────────────────────────────────


def auto_thread_title(text: str, agent: str = "oracle") -> str:
    """Returns a short non-quoting category for the first user message.

    The title intentionally does not copy personal text into a more visible
    session label; it is a reversible UI convenience, not a memory feature.
    """
    lower = (text or "").casefold()
    if any(word in lower for word in ("любов", "отношен", "партн", "relationship", "love")):
        return "Отношения"
    if any(word in lower for word in ("работ", "карьер", "деньг", "work", "career")):
        return "Дело и ресурсы"
    if any(word in lower for word in ("тревог", "устал", "чувств", "страш", "anxious", "tired")):
        return "Состояние"
    if agent == "tarot":
        return "Вопрос к картам"
    if agent == "astro":
        return "Ориентир по карте"
    return "Разговор о важном"


async def ensure_thread(db, tg_id: int, agent: str = "oracle", title: str | None = None):
    """Возвращает активный тред пользователя с этим агентом, создавая при нужде.

    Один живой тред на агента: в мессенджере у собеседника один диалог, а не
    список. Архивные треды (`archived=1`) остаются в истории и не мешают.
    """
    cur = await db.execute(
        "SELECT * FROM threads WHERE tg_id=? AND agent=? AND archived=0 "
        "ORDER BY id DESC LIMIT 1", (tg_id, agent))
    row = await cur.fetchone()
    if row:
        return row
    async with transaction(db):
        await db.execute(
            "INSERT INTO threads(tg_id, agent, title, created_at, last_at) "
            "VALUES(?,?,?,?,?)", (tg_id, agent, title, utcnow(), utcnow()))
    cur = await db.execute(
        "SELECT * FROM threads WHERE tg_id=? AND agent=? AND archived=0 "
        "ORDER BY id DESC LIMIT 1", (tg_id, agent))
    return await cur.fetchone()


async def create_thread(db, tg_id: int, agent: str = "oracle",
                        title: str | None = None) -> dict:
    """Создаёт НОВЫЙ тред (не переиспользует активный). Для многочатовых сессий.

    В отличие от `ensure_thread` (один живой тред на агента) — здесь каждый
    вызов даёт отдельный чат, чтобы в Mini App можно было вести несколько
    параллельных диалогов, как в ChatGPT.
    """
    async with transaction(db):
        cur = await db.execute(
            "INSERT INTO threads(tg_id, agent, title, created_at, last_at) "
            "VALUES(?,?,?,?,?)", (tg_id, agent, title, utcnow(), utcnow()))
        thread_id = cur.lastrowid
    cur = await db.execute("SELECT * FROM threads WHERE id=? AND tg_id=?",
                           (thread_id, tg_id))
    return dict(await cur.fetchone())


async def get_thread(db, thread_id: int, tg_id: int):
    cur = await db.execute(
        "SELECT * FROM threads WHERE id=? AND tg_id=?", (thread_id, tg_id))
    return await cur.fetchone()


async def list_threads(db, tg_id: int, limit: int = 30) -> list[dict]:
    cur = await db.execute(
        "SELECT * FROM threads WHERE tg_id=? AND archived=0 "
        "ORDER BY COALESCE(last_at, created_at) DESC LIMIT ?", (tg_id, limit))
    return [dict(r) for r in await cur.fetchall()]


async def search_threads(db, tg_id: int, query: str = "", limit: int = 50) -> list[dict]:
    """Ищет активные треды пользователя по заголовку, превью и сообщениям.

    Поиск остаётся scoped по tg_id и archived=0. Текст совпадения используется
    только для локального результата интерфейса и не меняет title или память.
    """
    query = " ".join((query or "").split())[:120]
    if not query:
        return await list_threads(db, tg_id, limit=limit)
    like = f"%{query}%"
    cur = await db.execute(
        "SELECT t.*, "
        "CASE WHEN t.title LIKE ? THEN t.title "
        "WHEN t.last_text LIKE ? THEN t.last_text "
        "ELSE (SELECT m.text FROM messages m WHERE m.thread_id=t.id "
        "AND m.text LIKE ? ORDER BY m.id DESC LIMIT 1) END AS match_text "
        "FROM threads t WHERE t.tg_id=? AND "
        "(t.title LIKE ? OR t.last_text LIKE ? OR EXISTS "
        "(SELECT 1 FROM messages m2 WHERE m2.thread_id=t.id AND m2.text LIKE ?)) "
        "ORDER BY COALESCE(t.last_at, t.created_at) DESC LIMIT ?",
        (like, like, like, tg_id, like, like, like, max(1, min(limit, 100))),
    )
    return [dict(row) for row in await cur.fetchall()]


async def archive_thread(db, thread_id: int, tg_id: int) -> None:
    async with transaction(db):
        await db.execute("UPDATE threads SET archived=1 WHERE id=? AND tg_id=?",
                         (thread_id, tg_id))


# ────────────────────────────── сообщения ─────────────────────────────────────

async def save_message(db, tg_id: int, role: str, text: str,
                       is_question: bool = False, *, thread_id: int | None = None,
                       agent: str = "oracle", surface: str = "bot",
                       tokens: int | None = None) -> int:
    """Пишет сообщение и обновляет превью треда одной транзакцией."""
    async with transaction(db):
        cur = await db.execute(
            "INSERT INTO messages(tg_id, thread_id, agent, role, text, is_question, "
            "surface, tokens, created_at) VALUES(?,?,?,?,?,?,?,?,?)",
            (tg_id, thread_id, agent, role, text, int(is_question), surface,
             tokens, utcnow()))
        msg_id = cur.lastrowid
        if thread_id and role == "user":
            await db.execute(
                "UPDATE threads SET msg_count=msg_count+1, last_text=?, last_at=?, "
                "title=CASE WHEN msg_count=0 THEN ? ELSE title END WHERE id=?",
                (text[:160], utcnow(), auto_thread_title(text, agent), thread_id),
            )
        elif thread_id:
            await db.execute(
                "UPDATE threads SET msg_count=msg_count+1, last_text=?, last_at=? "
                "WHERE id=?", (text[:160], utcnow(), thread_id))
    return msg_id


async def history(db, tg_id: int, limit: int = 16, *,
                  thread_id: int | None = None) -> list[dict]:
    """Последние сообщения в формате LLM ({role, content}), в прямом порядке.

    Без thread_id берём общую ленту пользователя — так исторические сообщения
    бота (созданные до появления тредов, с `thread_id IS NULL`) не теряются.
    """
    if thread_id:
        cur = await db.execute(
            "SELECT role, text FROM messages WHERE thread_id=? ORDER BY id DESC LIMIT ?",
            (thread_id, limit))
    else:
        cur = await db.execute(
            "SELECT role, text FROM messages WHERE tg_id=? ORDER BY id DESC LIMIT ?",
            (tg_id, limit))
    rows = await cur.fetchall()
    return [{"role": r["role"], "content": r["text"]} for r in reversed(rows)]


async def thread_messages(db, thread_id: int, limit: int = 100) -> list[dict]:
    cur = await db.execute(
        "SELECT id, role, text, created_at FROM messages WHERE thread_id=? "
        "ORDER BY id DESC LIMIT ?", (thread_id, limit))
    rows = [dict(r) for r in await cur.fetchall()]
    rows.reverse()
    return rows


async def questions_used_today(db, user) -> int:
    cur = await db.execute(
        "SELECT COUNT(*) c FROM messages WHERE tg_id=? AND is_question=1 AND created_at>=?",
        (user["tg_id"], users_repo.day_start_utc(user)))
    return (await cur.fetchone())["c"]


async def questions_used_since(db, tg_id: int, since_iso: str) -> int:
    cur = await db.execute(
        "SELECT COUNT(*) c FROM messages WHERE tg_id=? AND is_question=1 AND created_at>=?",
        (tg_id, since_iso))
    return (await cur.fetchone())["c"]


async def followups_since(db, tg_id: int, since_iso: str) -> int:
    """Сообщений клиентки после указанного момента, не помеченных вопросом."""
    cur = await db.execute(
        "SELECT COUNT(*) c FROM messages WHERE tg_id=? AND role='user' "
        "AND is_question=0 AND created_at > ?", (tg_id, since_iso))
    return (await cur.fetchone())["c"]


async def last_question_at(db, tg_id: int) -> str | None:
    cur = await db.execute(
        "SELECT created_at FROM messages WHERE tg_id=? AND is_question=1 "
        "ORDER BY id DESC LIMIT 1", (tg_id,))
    row = await cur.fetchone()
    return row["created_at"] if row else None


# ─────────────────────────────── память ───────────────────────────────────────

def dedup_key(fact: str) -> str:
    """Ключ сравнения фактов: регистр, «ё» и лишние пробелы не различаем."""
    return " ".join((fact or "").lower().replace("ё", "е").split())


async def save_memory(db, tg_id: int, fact: str, kind: str = "fact",
                      weight: int = 1) -> bool:
    """Сохраняет факт, отбрасывая дубликаты.

    Экстракция памяти запускается после каждого ответа, и без дедупликации
    «Работает дизайнером» попадало в промпт по десять раз, вытесняя остальное.
    Сравниваем по нормализованному тексту — точных повторов это ловит, а на
    смысловые дубликаты нужны эмбеддинги (следующий шаг, см. ТЗ §5).
    """
    fact = (fact or "").strip()
    if len(fact) < 3:
        return False
    # Сравниваем в Python, а не через SQL lower(): встроенный lower() в SQLite
    # работает только с ASCII, поэтому «Работает» и «работает» для него разные
    # строки — на кириллице дедупликация молча не срабатывала.
    key = dedup_key(fact)
    cur = await db.execute("SELECT id, fact FROM memories WHERE tg_id=?", (tg_id,))
    twin = next((r["id"] for r in await cur.fetchall()
                 if dedup_key(r["fact"]) == key), None)
    if twin is not None:
        async with transaction(db):
            await db.execute(
                "UPDATE memories SET weight=weight+1 WHERE id=?", (twin,))
        return False
    async with transaction(db):
        await db.execute(
            "INSERT INTO memories(tg_id, fact, kind, weight, created_at) "
            "VALUES(?,?,?,?,?)", (tg_id, fact, kind, weight, utcnow()))
    return True


async def get_memories(db, tg_id: int, limit: int = 20) -> list[str]:
    """Самые весомые и свежие факты: вес важнее давности."""
    cur = await db.execute(
        "SELECT fact FROM memories WHERE tg_id=? ORDER BY weight DESC, id DESC LIMIT ?",
        (tg_id, limit))
    return [r["fact"] for r in await cur.fetchall()]


async def memories_full(db, tg_id: int, limit: int = 100) -> list[dict]:
    cur = await db.execute(
        "SELECT * FROM memories WHERE tg_id=? ORDER BY weight DESC, id DESC LIMIT ?",
        (tg_id, limit))
    return [dict(r) for r in await cur.fetchall()]


async def search_memories(db, tg_id: int, query: str, limit: int = 10) -> list[str]:
    words = [w for w in (query or "").lower().split() if len(w) > 2]
    if not words:
        return await get_memories(db, tg_id, limit)
    clause = " OR ".join(["lower(fact) LIKE ?"] * len(words))
    params = [tg_id] + [f"%{w}%" for w in words] + [limit]
    cur = await db.execute(
        f"SELECT fact FROM memories WHERE tg_id=? AND ({clause}) "
        f"ORDER BY weight DESC, id DESC LIMIT ?", params)
    hits = [r["fact"] for r in await cur.fetchall()]
    return hits or await get_memories(db, tg_id, limit)


async def forget_memory(db, memory_id: int, tg_id: int) -> None:
    async with transaction(db):
        await db.execute("DELETE FROM memories WHERE id=? AND tg_id=?",
                         (memory_id, tg_id))


# ─────────────────────────────── дневник ──────────────────────────────────────

async def add_diary(db, tg_id: int, text: str, mood: str | None = None) -> None:
    async with transaction(db):
        await db.execute(
            "INSERT INTO diary(tg_id, text, mood, created_at) VALUES(?,?,?,?)",
            (tg_id, text, mood, utcnow()))


async def get_diary(db, tg_id: int, limit: int = 30) -> list[dict]:
    cur = await db.execute(
        "SELECT id, text, mood, created_at FROM diary WHERE tg_id=? "
        "ORDER BY id DESC LIMIT ?", (tg_id, limit))
    return [dict(r) for r in await cur.fetchall()]


async def diary_entries_between(db, tg_id: int, start_iso: str,
                                end_iso: str) -> list[dict]:
    """Записи в окне [start, end) по UTC — для месячной сводки.

    `created_at` лежит в UTC, месяц у клиентки «на сутки вперёд» Владивостока
    только сползает по краям — для сводки это приемлемо.
    """
    cur = await db.execute(
        "SELECT id, text, mood, created_at FROM diary WHERE tg_id=? "
        "AND created_at>=? AND created_at<? ORDER BY id", (tg_id, start_iso, end_iso))
    return [dict(r) for r in await cur.fetchall()]


async def diary_streak(db, tg_id: int) -> int:
    """Дней подряд с записями. Сегодня ещё не писала — считаем от вчера."""
    cur = await db.execute(
        "SELECT DISTINCT substr(created_at, 1, 10) d FROM diary WHERE tg_id=? "
        "ORDER BY d DESC LIMIT 400", (tg_id,))
    dayset = {r["d"] for r in await cur.fetchall()}
    if not dayset:
        return 0
    cursor = date.today()
    if cursor.isoformat() not in dayset:
        cursor -= timedelta(days=1)
    streak = 0
    while cursor.isoformat() in dayset:
        streak += 1
        cursor -= timedelta(days=1)
    return streak


async def diary_count_since(db, tg_id: int, days: int) -> int:
    since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    cur = await db.execute(
        "SELECT COUNT(*) c FROM diary WHERE tg_id=? AND created_at>=?", (tg_id, since))
    return (await cur.fetchone())["c"]
