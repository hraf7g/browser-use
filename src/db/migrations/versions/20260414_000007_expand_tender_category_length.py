from __future__ import annotations

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "20260414_000007"
down_revision = "20260414_000006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "tenders",
        "category",
        existing_type=sa.String(length=100),
        type_=sa.String(length=500),
        existing_nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "tenders",
        "category",
        existing_type=sa.String(length=500),
        type_=sa.String(length=100),
        existing_nullable=True,
    )
