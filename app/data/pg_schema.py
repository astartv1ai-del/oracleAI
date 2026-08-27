"""PostgreSQL rendering of the canonical application schema.

The repository layer still speaks the project's small async DB protocol. This module
keeps one source of truth for tables/indexes while translating SQLite-only storage
choices to PostgreSQL equivalents for the production backend.
"""
from __future__ import annotations

import os

from .schema import INDEXES, TABLES

PGVECTOR_ENABLED = os.getenv("PGVECTOR_ENABLED", "1") == "1"


def _render_tables() -> str:
    rendered = TABLES.replace(
        "INTEGER PRIMARY KEY AUTOINCREMENT", "BIGSERIAL PRIMARY KEY")
    rendered = rendered.replace("BLOB", "vector" if PGVECTOR_ENABLED else "BYTEA")
    return rendered


POSTGRES_TABLES = _render_tables()
POSTGRES_INDEXES = INDEXES
POSTGRES_EXTENSION_SETUP = (
    "CREATE EXTENSION IF NOT EXISTS vector;" if PGVECTOR_ENABLED else ""
)
# Runtime uses the application role and should not require superuser privilege.
POSTGRES_BOOTSTRAP = "CREATE TABLE IF NOT EXISTS alembic_version (version_num VARCHAR(255) PRIMARY KEY);"
