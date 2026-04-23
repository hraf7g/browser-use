from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20260417_000008"
down_revision = "20260414_000007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "tender_matches",
        sa.Column("daily_brief_queued_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "tender_matches",
        sa.Column("instant_alert_queued_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.add_column(
        "email_deliveries",
        sa.Column("recipient_email", sa.String(length=320), nullable=True),
    )
    op.add_column(
        "email_deliveries",
        sa.Column("subject", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "email_deliveries",
        sa.Column("body_text", sa.Text(), nullable=True),
    )
    op.add_column(
        "email_deliveries",
        sa.Column(
            "match_ids",
            postgresql.ARRAY(postgresql.UUID(as_uuid=True)),
            nullable=True,
        ),
    )
    op.add_column(
        "email_deliveries",
        sa.Column(
            "tender_ids",
            postgresql.ARRAY(postgresql.UUID(as_uuid=True)),
            nullable=True,
        ),
    )
    op.add_column(
        "email_deliveries",
        sa.Column("backend_message_id", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "email_deliveries",
        sa.Column("backend_output_path", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("email_deliveries", "backend_output_path")
    op.drop_column("email_deliveries", "backend_message_id")
    op.drop_column("email_deliveries", "tender_ids")
    op.drop_column("email_deliveries", "match_ids")
    op.drop_column("email_deliveries", "body_text")
    op.drop_column("email_deliveries", "subject")
    op.drop_column("email_deliveries", "recipient_email")
    op.drop_column("tender_matches", "instant_alert_queued_at")
    op.drop_column("tender_matches", "daily_brief_queued_at")
