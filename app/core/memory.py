"""Долгая память об одной клиентке: запись, поиск по смыслу, сводка «кто она».

Память — главный крючок удержания продукта: через две недели Оракул знает о
клиентке больше подруг, и уйти становится эмоционально дорого. Значит, память
должна быть не «списком последних фраз», а тем, что реально всплывает к месту.

Три механики:

1. **Дедупликация.** Экстракция фактов идёт после каждого ответа, и без
   дедупликации «работает дизайнером» попадало в промпт десять раз, вытесняя
   всё остальное. Сначала точное совпадение (дёшево), затем — близость векторов:
   «его зовут Дима» и «моего парня зовут Дима» это один факт.
2. **Поиск по смыслу.** В промпт уходит не «топ по весу», а то, что относится к
   ЭТОМУ вопросу. Иначе на вопрос про работу приезжали факты про бывшего.
3. **Сводка профиля.** Раз в неделю дешёвая модель собирает абзац «кто она» —
   он занимает в промпте меньше места, чем сорок фактов, и читается моделью
   лучше.

Эмбеддинги — необязательный слой. Нет ключа, нет сети, выключен флаг — модуль
молча возвращается к поиску по словам, и продукт работает как раньше.
"""
from __future__ import annotations

import array
import logging
import math
import re

from ..config import settings
from ..repo import dialog as dialog_repo

log = logging.getLogger("oracle.memory")

#: Порог близости, выше которого два факта считаются одним. Подобран так, чтобы
#: переформулировки склеивались, а «люблю кофе» и «люблю Диму» — нет.
DUPLICATE_THRESHOLD = 0.90
#: Ниже этого сходства факт не относится к вопросу — в промпт его не берём.
RELEVANCE_FLOOR = 0.25
#: Сколько слотов промпта всегда отдано самым весомым фактам (её «константы»).
ANCHOR_SHARE = 0.4

EMBED_DIM_LIMIT = 3072


# ─────────────────────────────── эмбеддинги ───────────────────────────────────

def embed_model() -> str:
    return settings.embed_model


def embeddings_enabled() -> bool:
    """Есть ли, чем считать векторы. Без этого работает поиск по словам."""
    return bool(settings.embed_model) and bool(
        settings.openai_key or (settings.custom_base_url and settings.embed_via_custom))


async def embed(texts: list[str]) -> list[list[float]] | None:
    """Векторы для списка строк. None — эмбеддинги недоступны, это не ошибка."""
    texts = [t for t in (texts or []) if t and t.strip()]
    if not texts or not embeddings_enabled():
        return None
    try:
        from openai import AsyncOpenAI
        if settings.openai_key:
            client = AsyncOpenAI(api_key=settings.openai_key, timeout=30)
        else:
            client = AsyncOpenAI(base_url=settings.custom_base_url,
                                 api_key=settings.custom_api_key or "sk-local",
                                 timeout=30)
        resp = await client.embeddings.create(model=settings.embed_model,
                                              input=texts)
        return [item.embedding for item in resp.data]
    except Exception as e:  # noqa: BLE001
        log.info("эмбеддинги недоступны (%s) — работаю по словам", e)
        return None


def pack(vector: list[float]) -> bytes:
    """float32-массив: в четыре раза компактнее JSON и читается без разбора."""
    return array.array("f", vector[:EMBED_DIM_LIMIT]).tobytes()


def unpack(blob) -> list[float]:
    if not blob:
        return []
    arr = array.array("f")
    try:
        arr.frombytes(bytes(blob))
    except (ValueError, TypeError):
        return []
    return list(arr)


def cosine(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if not na or not nb:
        return 0.0
    return dot / (na * nb)


# ─────────────────────────────── запись ───────────────────────────────────────

def _normalize(fact: str) -> str:
    return re.sub(r"\s+", " ", (fact or "").strip().lower().replace("ё", "е"))


async def remember(db, tg_id: int, fact: str, kind: str = "fact") -> bool:
    """Сохраняет факт. False — это дубликат, вес существующего усилен.

    Порядок проверок — от дешёвой к дорогой: точное совпадение ловит большинство
    повторов бесплатно, вектор считаем только для того, что прошло дальше.
    """
    fact = (fact or "").strip()
    if len(fact) < 3:
        return False
    if len(fact) > 300:
        fact = fact[:300].rsplit(" ", 1)[0]

    exact = await _find_exact(db, tg_id, fact)
    if exact:
        await _bump(db, exact)
        return False

    vectors = await embed([fact])
    vector = vectors[0] if vectors else None
    if vector:
        twin = await _find_similar(db, tg_id, vector)
        if twin:
            await _bump(db, twin)
            return False

    await _insert(db, tg_id, fact, kind, vector)
    return True


async def _find_exact(db, tg_id: int, fact: str) -> int | None:
    """Точный повтор с точностью до регистра, «ё» и пробелов.

    Сравнение в Python: `lower()` в SQLite покрывает только ASCII, из-за чего
    «Работает дизайнером» и «работает дизайнером» считались разными фактами.
    """
    from ..repo.dialog import dedup_key

    key = dedup_key(fact)
    cur = await db.execute("SELECT id, fact FROM memories WHERE tg_id=?", (tg_id,))
    return next((r["id"] for r in await cur.fetchall()
                 if dedup_key(r["fact"]) == key), None)


async def _find_similar(db, tg_id: int, vector: list[float]) -> int | None:
    cur = await db.execute(
        "SELECT id, embedding FROM memories WHERE tg_id=? AND embedding IS NOT NULL",
        (tg_id,))
    for row in await cur.fetchall():
        if cosine(vector, unpack(row["embedding"])) >= DUPLICATE_THRESHOLD:
            return row["id"]
    return None


async def _bump(db, memory_id: int) -> None:
    from ..data.session import transaction, utcnow
    async with transaction(db):
        await db.execute(
            "UPDATE memories SET weight=weight+1, last_used=? WHERE id=?",
            (utcnow(), memory_id))


async def _insert(db, tg_id: int, fact: str, kind: str,
                  vector: list[float] | None) -> None:
    from ..data.session import transaction, utcnow
    async with transaction(db):
        await db.execute(
            "INSERT INTO memories(tg_id, fact, kind, weight, embedding, embed_model, "
            "created_at) VALUES(?,?,?,1,?,?,?)",
            (tg_id, fact, kind, pack(vector) if vector else None,
             embed_model() if vector else None, utcnow()))


# ─────────────────────────────── поиск ────────────────────────────────────────

async def recall(db, tg_id: int, query: str = "", limit: int = 20) -> list[str]:
    """Факты для промпта: часть — самые весомые, часть — по смыслу вопроса."""
    limit = max(1, limit)
    if not query.strip():
        return await dialog_repo.get_memories(db, tg_id, limit=limit)

    anchors_n = max(1, int(limit * ANCHOR_SHARE))
    anchors = await dialog_repo.get_memories(db, tg_id, limit=anchors_n)
    rest = limit - len(anchors)
    if rest <= 0:
        return anchors

    relevant = await _semantic(db, tg_id, query, rest * 3)
    if relevant is None:
        relevant = await dialog_repo.search_memories(db, tg_id, query, limit=rest * 3)

    seen = {_normalize(a) for a in anchors}
    out = list(anchors)
    for fact in relevant:
        key = _normalize(fact)
        if key in seen:
            continue
        seen.add(key)
        out.append(fact)
        if len(out) >= limit:
            break
    return out


async def _semantic(db, tg_id: int, query: str, limit: int) -> list[str] | None:
    """Факты, отсортированные по близости к вопросу. None — векторов нет."""
    vectors = await embed([query])
    if not vectors:
        return None
    qv = vectors[0]
    cur = await db.execute(
        "SELECT id, fact, weight, embedding FROM memories "
        "WHERE tg_id=? AND embedding IS NOT NULL", (tg_id,))
    rows = await cur.fetchall()
    if not rows:
        return None
    scored = []
    for row in rows:
        score = cosine(qv, unpack(row["embedding"]))
        if score < RELEVANCE_FLOOR:
            continue
        # вес слегка поднимает то, что она повторяла: это её постоянные темы
        scored.append((score + 0.02 * min(row["weight"] or 1, 5), row["fact"]))
    scored.sort(reverse=True)
    return [fact for _, fact in scored[:limit]]


async def backfill_embeddings(db, tg_id: int, limit: int = 50) -> int:
    """Досчитывает векторы для фактов, сохранённых до включения эмбеддингов."""
    if not embeddings_enabled():
        return 0
    cur = await db.execute(
        "SELECT id, fact FROM memories WHERE tg_id=? AND embedding IS NULL "
        "ORDER BY weight DESC, id DESC LIMIT ?", (tg_id, limit))
    rows = await cur.fetchall()
    if not rows:
        return 0
    vectors = await embed([r["fact"] for r in rows])
    if not vectors:
        return 0
    from ..data.session import transaction
    async with transaction(db):
        for row, vector in zip(rows, vectors):
            await db.execute(
                "UPDATE memories SET embedding=?, embed_model=? WHERE id=?",
                (pack(vector), embed_model(), row["id"]))
    return len(rows)


# ──────────────────────────── сводка профиля ──────────────────────────────────

SUMMARY_MIN_FACTS = 8
SUMMARY_REBUILD_AFTER = 10          # новых фактов с прошлой сборки


async def get_summary(db, tg_id: int) -> str:
    try:
        cur = await db.execute(
            "SELECT summary FROM profile_summaries WHERE tg_id=?", (tg_id,))
        row = await cur.fetchone()
    except Exception as e:  # noqa: BLE001
        log.debug("сводка профиля недоступна: %s", e)
        return ""
    return (row["summary"] or "") if row else ""


async def _facts_count(db, tg_id: int) -> int:
    cur = await db.execute("SELECT COUNT(*) c FROM memories WHERE tg_id=?", (tg_id,))
    return (await cur.fetchone())["c"]


async def needs_summary(db, tg_id: int) -> bool:
    total = await _facts_count(db, tg_id)
    if total < SUMMARY_MIN_FACTS:
        return False
    cur = await db.execute(
        "SELECT facts_count FROM profile_summaries WHERE tg_id=?", (tg_id,))
    row = await cur.fetchone()
    if not row:
        return True
    return total - (row["facts_count"] or 0) >= SUMMARY_REBUILD_AFTER


async def build_summary(db, user) -> str:
    """Пересобирает абзац «кто она» дешёвой моделью. Пустая строка — не вышло."""
    from . import llm

    tg_id = user["tg_id"]
    facts = await dialog_repo.get_memories(db, tg_id, limit=60)
    if len(facts) < SUMMARY_MIN_FACTS or not llm.enabled():
        return ""
    joined = "\n".join(f"- {f}" for f in facts)
    try:
        text = await llm.complete(
            ("Ты собираешь досье для личного астролога. По списку фактов о "
             "клиентке напиши ОДИН абзац (до 60 слов) в третьем лице: кто она, "
             "что для неё важно, что болит, чего хочет. Только то, что следует "
             "из фактов. Без вступлений и списков."),
            joined, tier="lite", max_tokens=220,
            purpose="memory_summary", tg_id=tg_id, db=db)
    except Exception as e:  # noqa: BLE001
        log.info("сводка профиля не собралась: %s", e)
        return ""
    text = (text or "").strip()
    if len(text) < 40:
        return ""

    from ..data.session import transaction, utcnow
    async with transaction(db):
        await db.execute(
            "INSERT OR REPLACE INTO profile_summaries(tg_id, summary, facts_count, "
            "built_at) VALUES(?,?,?,?)",
            (tg_id, text, await _facts_count(db, tg_id), utcnow()))
    return text
