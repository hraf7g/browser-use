"""create_ai_control_state

Revision ID: 20260419_000015
Revises: 20260419_000014
Create Date: 2026-04-19 20:05:00
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '20260419_000015'
down_revision = '20260419_000014'
branch_labels = None
depends_on = None


def upgrade() -> None:
	op.create_table(
		'ai_control_state',
		sa.Column('id', sa.Integer(), nullable=False),
		sa.Column('ai_enrichment_enabled', sa.Boolean(), nullable=False, server_default=sa.text('true')),
		sa.Column('emergency_stop_enabled', sa.Boolean(), nullable=False, server_default=sa.text('false')),
		sa.Column('emergency_stop_reason', sa.Text(), nullable=True),
		sa.Column('max_enrichment_batch_size_override', sa.Integer(), nullable=True),
		sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
		sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
		sa.CheckConstraint('id = 1', name='ck_ai_control_state_singleton'),
		sa.CheckConstraint(
			'max_enrichment_batch_size_override IS NULL OR max_enrichment_batch_size_override >= 1',
			name='ck_ai_control_state_batch_override_positive',
		),
		sa.PrimaryKeyConstraint('id'),
	)
	op.execute(
		sa.text(
			"""
			INSERT INTO ai_control_state (
				id,
				ai_enrichment_enabled,
				emergency_stop_enabled,
				emergency_stop_reason,
				max_enrichment_batch_size_override
			) VALUES (
				1,
				true,
				false,
				NULL,
				NULL
			)
			"""
		)
	)
	op.alter_column('ai_control_state', 'ai_enrichment_enabled', server_default=None)
	op.alter_column('ai_control_state', 'emergency_stop_enabled', server_default=None)


def downgrade() -> None:
	op.drop_table('ai_control_state')
