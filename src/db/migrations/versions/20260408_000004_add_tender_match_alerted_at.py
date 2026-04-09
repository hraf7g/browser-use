from __future__ import annotations

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "20260408_000004"
down_revision = "20260408_000003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "tender_matches",
        sa.Column("alerted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_tender_matches_user_id_alerted_at",
        "tender_matches",
        ["user_id", "alerted_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_tender_matches_user_id_alerted_at", table_name="tender_matches")
    op.drop_column("tender_matches", "alerted_at")
