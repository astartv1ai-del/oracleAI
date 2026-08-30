"""Async SQLAlchemy/asyncpg backend behind the existing repository DB protocol."""
from __future__ import annotations

import logging
import os
import re
from contextlib import asynccontextmanager
from contextvars import ContextVar
from decimal import Decimal
from typing import Any, Iterable

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

log = logging.getLogger("oracle.db.shim")


class LegacyShimUsageError(RuntimeError):
    """Raised when SHIM_ENFORCED=1 and a call site still needs SQLite→PG translation.

    See ADR-0003 (docs/ADR/ADR-0003-shim-removal.md) for policy: the flag defaults to
    off in production (silent translate + WARNING log), on in CI + staging (fail fast).
    """

_ID_TABLES = {
    "admin_audit", "broadcasts", "content_items", "crystal_ledger",
    "crystal_lots", "diary", "entitlements", "events", "llm_usage", "memories",
    "messages", "monetization_usage", "orders", "palm_readings", "partners",
    "payment_webhook_failures", "payments", "practices", "price_book_items",
    "product_cost_events", "promo_redemptions", "referrals", "reports",
    "safety_events", "shared_context_events", "shared_context_snapshots",
    "synastry_cache", "tarot_readings", "threads", "user_notes",
    "user_notifications",
}
_INSERT_TABLE_RE = re.compile(r"^\s*INSERT(?:\s+OR\s+IGNORE)?\s+INTO\s+([\w]+)", re.I)


def _split_script(script: str) -> list[str]:
    """Split DDL without treating semicolons in comments/strings as separators."""
    statements: list[str] = []
    start = 0
    quote: str | None = None
    line_comment = False
    i = 0
    while i < len(script):
        char = script[i]
        nxt = script[i + 1] if i + 1 < len(script) else ""
        if line_comment:
            if char == "\n":
                line_comment = False
            i += 1
            continue
        if quote:
            if char == quote:
                if nxt == quote:
                    i += 2
                    continue
                quote = None
            i += 1
            continue
        if char == "-" and nxt == "-":
            line_comment = True
            i += 2
            continue
        if char in ("'", '"'):
            quote = char
        elif char == ";":
            statement = script[start:i].strip()
            if statement:
                statements.append(statement)
            start = i + 1
        i += 1
    tail = script[start:].strip()
    if tail:
        statements.append(tail)
    return statements


def _env_int(name: str, default: int, *, minimum: int = 1) -> int:
    try:
        return max(int(os.getenv(name, str(default))), minimum)
    except (TypeError, ValueError):
        return default


def _shim_enforced() -> bool:
    """SHIM_ENFORCED gate (ADR-0003).

    ``SHIM_ENFORCED=1`` (CI + staging): translation is forbidden — legacy SQL raises
    ``LegacyShimUsageError`` on the first call. ``0`` (production default): the shim
    still translates but the call site is logged at WARNING for offline auditing.
    """
    return os.getenv("SHIM_ENFORCED", "0") == "1"


def _needs_translation(sql: str) -> bool:
    """Structural heuristic — see ADR-0003."""
    stripped = sql.lstrip()
    if stripped.upper().startswith("INSERT OR IGNORE"):
        return True
    # ? outside of any string literal counts as a legacy positional placeholder.
    in_single = False
    in_double = False
    i = 0
    while i < len(sql):
        ch = sql[i]
        if in_single:
            if ch == "'":
                in_single = False
            i += 1
            continue
        if in_double:
            if ch == '"':
                in_double = False
            i += 1
            continue
        if ch == "'":
            in_single = True
        elif ch == '"':
            in_double = True
        elif ch == "?":
            return True
        i += 1
    return False


def _translate_sql(sql: str) -> tuple[str, list[str]]:
    """Convert the small SQLite SQL dialect used by repositories to PostgreSQL.

    Files that have already been ported to the native PostgreSQL dialect
    (named :param placeholders, ON CONFLICT (<col>) DO NOTHING, explicit
    RETURNING id) pass through this function unchanged:
      - No '?' → the re.sub loop produces names=[] and returns sql as-is.
      - No 'INSERT OR IGNORE' prefix → the first branch is skipped.
    _bind_params then returns the caller-supplied dict directly (isinstance
    check), so execute() works correctly for both ported and legacy files.

    When ``SHIM_ENFORCED=1`` and the SQL still requires translation, this
    raises ``LegacyShimUsageError`` to fail the test/CI/staging boot fast.
    See ``docs/ADR/ADR-0003-shim-removal.md``.
    """
    sql = sql.strip().rstrip(";")
    if _needs_translation(sql):
        if _shim_enforced():
            raise LegacyShimUsageError(
                "SHIM_ENFORCED=1 rejected legacy SQL — port this call site to native "
                "PostgreSQL dialect per ADR-0001 (named :params + ON CONFLICT (<col>) "
                f"DO NOTHING + explicit RETURNING id):\n{sql}"
            )
        log.warning("legacy SQL still using shim (see ADR-0003): %s", sql[:400])

    if sql.upper().startswith("INSERT OR IGNORE"):
        sql = re.sub(r"^INSERT\s+OR\s+IGNORE", "INSERT", sql, count=1, flags=re.I)
        sql += " ON CONFLICT DO NOTHING"

    names: list[str] = []

    def replace_placeholder(_match) -> str:
        name = f"p{len(names)}"
        names.append(name)
        return f":{name}"

    sql = re.sub(r"\?", replace_placeholder, sql)
    return sql, names


def _coerce_pg(value):
    """PostgreSQL NUMERIC arrives as Decimal; repositories expect int/float."""
    if isinstance(value, Decimal):
        return int(value) if value == value.to_integral_value() else float(value)
    return value


class PostgresRow:
    """A row-compatible view over a SQLAlchemy Row (supports row["col"])."""

    __slots__ = ("_values", "_mapping")

    def __init__(self, row):
        mapping = {key: _coerce_pg(value) for key, value in row._mapping.items()}
        self._values = tuple(mapping.values())
        self._mapping = mapping

    def __getitem__(self, key):
        if isinstance(key, int):
            return self._values[key]
        return self._mapping[key]

    def __iter__(self):
        # `dict(row)` is used throughout the existing repositories.
        return iter(self._mapping.items())

    def keys(self):
        return self._mapping.keys()

    def get(self, key, default=None):
        return self._mapping.get(key, default)

    def __repr__(self) -> str:
        return repr(self._mapping)


class PostgresCursor:
    def __init__(self, rows: Iterable[PostgresRow] = (), *, rowcount: int = -1,
                 lastrowid: int | None = None):
        self._rows = list(rows)
        self._position = 0
        self.rowcount = rowcount
        self.lastrowid = lastrowid

    async def fetchone(self):
        if self._position >= len(self._rows):
            return None
        row = self._rows[self._position]
        self._position += 1
        return row

    async def fetchall(self):
        rows = self._rows[self._position:]
        self._position = len(self._rows)
        return rows

    async def fetchmany(self, size: int | None = None):
        end = self._position + (size or 1)
        rows = self._rows[self._position:end]
        self._position += len(rows)
        return rows


class PostgresDatabase:
    """Connection-pool backed async DB object used by current repositories."""

    is_postgres = True

    def __init__(self, url: str):
        self.url = url
        self.engine: AsyncEngine = create_async_engine(
            url,
            pool_pre_ping=True,
            pool_size=_env_int("PG_POOL_SIZE", 10),
            max_overflow=_env_int("PG_MAX_OVERFLOW", 10, minimum=0),
            pool_timeout=_env_int("PG_POOL_TIMEOUT", 30),
            # Recycle idle connections to survive NAT/PgBouncer silent timeouts.
            pool_recycle=_env_int("PG_POOL_RECYCLE", 1800),
        )
        self._connection: ContextVar[Any] = ContextVar(
            "oracle_pg_connection", default=None)

    def _bind_params(self, names: list[str], params: Any) -> dict[str, Any]:
        if isinstance(params, dict):
            return params
        values = tuple(params or ())
        return dict(zip(names, values))

    async def execute(self, sql: str, params: Any = ()) -> PostgresCursor:
        sql, names = _translate_sql(sql)
        bind = self._bind_params(names, params)
        connection = self._connection.get()
        match = _INSERT_TABLE_RE.match(sql)
        table = match.group(1).lower() if match else ""
        needs_id = table in _ID_TABLES and sql.upper().startswith("INSERT")
        if needs_id and " RETURNING " not in sql.upper():
            sql += " RETURNING id"

        if connection is not None:
            result = await connection.execute(text(sql), bind)
            return self._cursor_from_result(result, needs_id)

        if sql.upper().startswith(("SELECT", "WITH", "SHOW", "EXPLAIN")):
            async with self.engine.connect() as connection:
                result = await connection.execute(text(sql), bind)
                return self._cursor_from_result(result, needs_id)
        async with self.engine.begin() as connection:
            result = await connection.execute(text(sql), bind)
            return self._cursor_from_result(result, needs_id)

    @staticmethod
    def _cursor_from_result(result, needs_id: bool) -> PostgresCursor:
        rows = [PostgresRow(row) for row in result.fetchall()] if result.returns_rows else []
        lastrowid = rows[0][0] if needs_id and rows else None
        return PostgresCursor(rows, rowcount=result.rowcount, lastrowid=lastrowid)

    async def executemany(self, sql: str, rows: Iterable[Any]) -> PostgresCursor:
        sql, names = _translate_sql(sql)
        bind_rows = [self._bind_params(names, row) for row in rows]
        if not bind_rows:
            return PostgresCursor([], rowcount=0)
        connection = self._connection.get()
        if connection is not None:
            result = await connection.execute(text(sql), bind_rows)
        else:
            async with self.engine.begin() as connection:
                result = await connection.execute(text(sql), bind_rows)
        return PostgresCursor([], rowcount=result.rowcount)

    async def executescript(self, script: str) -> None:
        statements = _split_script(script)
        async with self.engine.begin() as connection:
            for statement in statements:
                await connection.execute(text(statement))

    async def commit(self) -> None:
        # Non-transactional statements use engine.begin() and are committed already.
        return None

    async def rollback(self) -> None:
        return None

    @asynccontextmanager
    async def transaction(self):
        current = self._connection.get()
        if current is not None:
            yield self
            return
        async with self.engine.begin() as connection:
            token = self._connection.set(connection)
            try:
                yield self
            finally:
                self._connection.reset(token)

    async def healthcheck(self) -> dict:
        cur = await self.execute("SELECT current_database(), current_setting('server_version')")
        row = await cur.fetchone()
        tables = await self.execute(
            "SELECT COUNT(*) FROM information_schema.tables "
            "WHERE table_schema='public'")
        users = await self.execute("SELECT COUNT(*) FROM users")
        return {
            "ok": True,
            "integrity": "ok",
            "database": row[0] if row else None,
            "server_version": row[1] if row else None,
            "journal_mode": "postgresql",
            "page_count": None,
            "users": (await users.fetchone())[0],
            "schema_tables": (await tables.fetchone())[0],
        }

    async def close(self) -> None:
        await self.engine.dispose()
