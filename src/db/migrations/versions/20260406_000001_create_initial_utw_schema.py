"""create_initial_utw_schema

Revision ID: 20260406_000001
Revises: None
Create Date: 2026-04-06 00:00:00
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "20260406_000001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "sources",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("base_url", sa.String(length=500), nullable=False),
        sa.Column("status", sa.String(length=20), server_default="healthy", nullable=False),
        sa.Column("last_successful_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_failed_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("failure_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("base_url", name="uq_sources_base_url"),
        sa.UniqueConstraint("name", name="uq_sources_name"),
    )

    op.create_table(
        "keyword_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("keywords", postgresql.ARRAY(sa.Text()), nullable=False),
        sa.Column("alert_enabled", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("industry_label", sa.String(length=120), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", name="uq_keyword_profiles_user_id"),
    )

    op.create_table(
        "tenders",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tender_ref", sa.String(length=255), nullable=True),
        sa.Column("source_url", sa.String(length=1000), nullable=False),
        sa.Column("title", sa.String(length=1000), nullable=False),
        sa.Column("issuing_entity", sa.String(length=500), nullable=False),
        sa.Column("closing_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("opening_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("category", sa.String(length=255), nullable=True),
        sa.Column("ai_summary", sa.Text(), nullable=True),
        sa.Column("dedupe_key", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["source_id"], ["sources.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("source_id", "dedupe_key", name="uq_tenders_source_id_dedupe_key"),
    )
    op.create_index("ix_tenders_source_id", "tenders", ["source_id"], unique=False)
    op.create_index("ix_tenders_closing_date", "tenders", ["closing_date"], unique=False)
    op.create_index("ix_tenders_created_at", "tenders", ["created_at"], unique=False)
    op.create_index(
        "ux_tenders_source_id_tender_ref_not_null",
        "tenders",
        ["source_id", "tender_ref"],
        unique=True,
        postgresql_where=sa.text("tender_ref IS NOT NULL"),
    )

    op.create_table(
        "tender_matches",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tender_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("matched_keywords", postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["tender_id"], ["tenders.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "tender_id", name="uq_tender_matches_user_id_tender_id"),
    )
    op.create_index(
        "ix_tender_matches_user_id_sent_at",
        "tender_matches",
        ["user_id", "sent_at"],
        unique=False,
    )

    op.create_table(
        "crawl_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("new_tenders_count", sa.Integer(), nullable=True),
        sa.Column("failure_reason", sa.Text(), nullable=True),
        sa.Column("failure_step", sa.String(length=100), nullable=True),
        sa.Column("run_identifier", sa.String(length=100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["source_id"], ["sources.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_crawl_runs_source_id", "crawl_runs", ["source_id"], unique=False)
    op.create_index("ix_crawl_runs_started_at", "crawl_runs", ["started_at"], unique=False)

    op.create_table(
        "email_deliveries",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("delivery_type", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("attempted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("match_count", sa.Integer(), nullable=True),
        sa.Column("failure_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_email_deliveries_user_id", "email_deliveries", ["user_id"], unique=False)
    op.create_index("ix_email_deliveries_attempted_at", "email_deliveries", ["attempted_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_email_deliveries_attempted_at", table_name="email_deliveries")
    op.drop_index("ix_email_deliveries_user_id", table_name="email_deliveries")
    op.drop_table("email_deliveries")

    op.drop_index("ix_crawl_runs_started_at", table_name="crawl_runs")
    op.drop_index("ix_crawl_runs_source_id", table_name="crawl_runs")
    op.drop_table("crawl_runs")

    op.drop_index("ix_tender_matches_user_id_sent_at", table_name="tender_matches")
    op.drop_table("tender_matches")

    op.drop_index("ux_tenders_source_id_tender_ref_not_null", table_name="tenders")
    op.drop_index("ix_tenders_created_at", table_name="tenders")
    op.drop_index("ix_tenders_closing_date", table_name="tenders")
    op.drop_index("ix_tenders_source_id", table_name="tenders")
    op.drop_table("tenders")

    op.drop_table("keyword_profiles")
    op.drop_table("sources")

    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
