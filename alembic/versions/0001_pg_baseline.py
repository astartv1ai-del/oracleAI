"""Create the OracleAI PostgreSQL baseline schema.

Revision ID: 0001_pg_baseline
Revises:
"""
from __future__ import annotations

from alembic import op

from app.data.pg_schema import (
    POSTGRES_BOOTSTRAP,
    POSTGRES_EXTENSION_SETUP,
    POSTGRES_INDEXES,
    POSTGRES_TABLES,
)

revision = "0001_pg_baseline"
down_revision = None
branch_labels = None
depends_on = None


def _statements(*scripts: str) -> list[str]:
    from app.data.postgres import _split_script
    return [part for script in scripts for part in _split_script(script)]


def upgrade() -> None:
    for statement in _statements(
        POSTGRES_EXTENSION_SETUP, POSTGRES_BOOTSTRAP, POSTGRES_TABLES, POSTGRES_INDEXES):
        op.execute(statement)


def downgrade() -> None:
    # Downgrade is intentionally conservative: dropping a production database
    # from a migration is unsafe. Restore a backup instead of deleting data.
    raise RuntimeError("PostgreSQL baseline downgrade is destructive; restore a backup")
