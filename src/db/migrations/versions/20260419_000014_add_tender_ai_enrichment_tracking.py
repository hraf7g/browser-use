"""add_tender_ai_enrichment_tracking

Revision ID: 20260419_000014
Revises: 20260418_000013
Create Date: 2026-04-19 17:35:00
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '20260419_000014'
down_revision = '20260418_000013'
branch_labels = None
depends_on = None


def upgrade() -> None:
	op.add_column(
		'tenders',
		sa.Column('ai_summary_attempt_count', sa.Integer(), nullable=False, server_default='0'),
	)
	op.add_column(
		'tenders',
		sa.Column('ai_summary_generated_at', sa.DateTime(timezone=True), nullable=True),
	)
	op.add_column(
		'tenders',
		sa.Column('ai_summary_last_attempted_at', sa.DateTime(timezone=True), nullable=True),
	)
	op.add_column(
		'tenders',
		sa.Column('ai_summary_last_error', sa.Text(), nullable=True),
	)
	op.add_column(
		'tenders',
		sa.Column('ai_summary_model', sa.String(length=255), nullable=True),
	)

	connection = op.get_bind()
	connection.execute(
		sa.text(
			"""
			UPDATE tenders
			SET ai_summary_attempt_count = CASE
				WHEN ai_summary IS NULL OR btrim(ai_summary) = '' THEN 0
				ELSE 1
			END,
				ai_summary_generated_at = CASE
					WHEN ai_summary IS NULL OR btrim(ai_summary) = '' THEN NULL
					ELSE updated_at
				END,
				ai_summary_last_attempted_at = CASE
					WHEN ai_summary IS NULL OR btrim(ai_summary) = '' THEN NULL
					ELSE updated_at
				END
			"""
		)
	)

	op.alter_column('tenders', 'ai_summary_attempt_count', server_default=None)


def downgrade() -> None:
	op.drop_column('tenders', 'ai_summary_model')
	op.drop_column('tenders', 'ai_summary_last_error')
	op.drop_column('tenders', 'ai_summary_last_attempted_at')
	op.drop_column('tenders', 'ai_summary_generated_at')
	op.drop_column('tenders', 'ai_summary_attempt_count')
