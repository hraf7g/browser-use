"""add_ai_daily_budget_controls

Revision ID: 20260419_000017
Revises: 20260419_000016
Create Date: 2026-04-19 21:20:00
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '20260419_000017'
down_revision = '20260419_000016'
branch_labels = None
depends_on = None


def upgrade() -> None:
	op.add_column(
		'ai_control_state',
		sa.Column('max_daily_requests_override', sa.Integer(), nullable=True),
	)
	op.add_column(
		'ai_control_state',
		sa.Column('max_daily_reserved_tokens_override', sa.Integer(), nullable=True),
	)
	op.create_check_constraint(
		'ck_ai_control_state_daily_requests_override_positive',
		'ai_control_state',
		'max_daily_requests_override IS NULL OR max_daily_requests_override >= 1',
	)
	op.create_check_constraint(
		'ck_ai_control_state_daily_reserved_tokens_override_positive',
		'ai_control_state',
		'max_daily_reserved_tokens_override IS NULL OR max_daily_reserved_tokens_override >= 1',
	)
	op.create_table(
		'ai_daily_usage',
		sa.Column('usage_date', sa.Date(), nullable=False),
		sa.Column('request_count', sa.Integer(), nullable=False, server_default='0'),
		sa.Column('blocked_request_count', sa.Integer(), nullable=False, server_default='0'),
		sa.Column('throttled_request_count', sa.Integer(), nullable=False, server_default='0'),
		sa.Column('provider_error_count', sa.Integer(), nullable=False, server_default='0'),
		sa.Column('estimated_input_tokens', sa.Integer(), nullable=False, server_default='0'),
		sa.Column('reserved_total_tokens', sa.Integer(), nullable=False, server_default='0'),
		sa.Column('actual_prompt_tokens', sa.Integer(), nullable=False, server_default='0'),
		sa.Column('actual_completion_tokens', sa.Integer(), nullable=False, server_default='0'),
		sa.Column('actual_total_tokens', sa.Integer(), nullable=False, server_default='0'),
		sa.Column('last_model', sa.String(length=255), nullable=True),
		sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
		sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
		sa.CheckConstraint('request_count >= 0', name='ck_ai_daily_usage_request_count_nonnegative'),
		sa.CheckConstraint('blocked_request_count >= 0', name='ck_ai_daily_usage_blocked_count_nonnegative'),
		sa.CheckConstraint('throttled_request_count >= 0', name='ck_ai_daily_usage_throttled_count_nonnegative'),
		sa.CheckConstraint('provider_error_count >= 0', name='ck_ai_daily_usage_provider_error_count_nonnegative'),
		sa.CheckConstraint('estimated_input_tokens >= 0', name='ck_ai_daily_usage_estimated_input_nonnegative'),
		sa.CheckConstraint('reserved_total_tokens >= 0', name='ck_ai_daily_usage_reserved_total_nonnegative'),
		sa.CheckConstraint('actual_prompt_tokens >= 0', name='ck_ai_daily_usage_actual_prompt_nonnegative'),
		sa.CheckConstraint(
			'actual_completion_tokens >= 0',
			name='ck_ai_daily_usage_actual_completion_nonnegative',
		),
		sa.CheckConstraint('actual_total_tokens >= 0', name='ck_ai_daily_usage_actual_total_nonnegative'),
		sa.PrimaryKeyConstraint('usage_date'),
	)
	for column_name in (
		'request_count',
		'blocked_request_count',
		'throttled_request_count',
		'provider_error_count',
		'estimated_input_tokens',
		'reserved_total_tokens',
		'actual_prompt_tokens',
		'actual_completion_tokens',
		'actual_total_tokens',
	):
		op.alter_column('ai_daily_usage', column_name, server_default=None)


def downgrade() -> None:
	op.drop_table('ai_daily_usage')
	op.drop_constraint(
		'ck_ai_control_state_daily_reserved_tokens_override_positive',
		'ai_control_state',
		type_='check',
	)
	op.drop_constraint(
		'ck_ai_control_state_daily_requests_override_positive',
		'ai_control_state',
		type_='check',
	)
	op.drop_column('ai_control_state', 'max_daily_reserved_tokens_override')
	op.drop_column('ai_control_state', 'max_daily_requests_override')
