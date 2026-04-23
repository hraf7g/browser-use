from __future__ import annotations

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "20260417_000009"
down_revision = "20260417_000008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "tenders",
        "closing_date",
        existing_type=sa.DateTime(timezone=True),
        nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "tenders",
        "closing_date",
        existing_type=sa.DateTime(timezone=True),
        nullable=False,
    )
