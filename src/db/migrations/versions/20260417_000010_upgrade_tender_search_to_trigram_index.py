from __future__ import annotations

from alembic import op

# revision identifiers, used by Alembic.
revision = "20260417_000010"
down_revision = "20260417_000009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    op.drop_index("ix_tenders_search_text", table_name="tenders")
    op.create_index(
        "ix_tenders_search_text_trgm",
        "tenders",
        ["search_text"],
        unique=False,
        postgresql_using="gin",
        postgresql_ops={"search_text": "gin_trgm_ops"},
    )


def downgrade() -> None:
    op.drop_index("ix_tenders_search_text_trgm", table_name="tenders")
    op.create_index(
        "ix_tenders_search_text",
        "tenders",
        ["search_text"],
        unique=False,
    )
