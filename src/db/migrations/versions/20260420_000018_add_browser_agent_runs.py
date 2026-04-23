"""add browser agent runs

Revision ID: 20260420_000018
Revises: 20260419_000017
Create Date: 2026-04-20 12:00:00.000000
"""
# pyright: reportMissingImports=false

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = '20260420_000018'
down_revision = '20260419_000017'
branch_labels = None
depends_on = None


def upgrade() -> None:
	op.create_table(
		'browser_agent_runs',
		sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
		sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
		sa.Column('status', sa.String(length=32), nullable=False, server_default='queued'),
		sa.Column('task_prompt', sa.Text(), nullable=False),
		sa.Column('start_url', sa.String(length=2048), nullable=True),
		sa.Column('allowed_domains', sa.JSON(), nullable=True),
		sa.Column('max_steps', sa.Integer(), nullable=False),
		sa.Column('step_timeout_seconds', sa.Integer(), nullable=False),
		sa.Column('llm_timeout_seconds', sa.Integer(), nullable=False),
		sa.Column('queued_at', sa.DateTime(timezone=True), nullable=False),
		sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
		sa.Column('finished_at', sa.DateTime(timezone=True), nullable=True),
		sa.Column('cancel_requested_at', sa.DateTime(timezone=True), nullable=True),
		sa.Column('last_heartbeat_at', sa.DateTime(timezone=True), nullable=True),
		sa.Column('error_message', sa.Text(), nullable=True),
		sa.Column('final_result_text', sa.Text(), nullable=True),
		sa.Column('llm_provider', sa.String(length=64), nullable=False, server_default='bedrock_anthropic'),
		sa.Column('llm_model', sa.String(length=255), nullable=False),
		sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
		sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
		sa.CheckConstraint(
			"status IN ('queued','running','cancelling','cancelled','completed','failed')",
			name='ck_browser_agent_runs_status_valid',
		),
		sa.CheckConstraint('max_steps >= 1', name='ck_browser_agent_runs_max_steps_positive'),
		sa.CheckConstraint('step_timeout_seconds >= 30', name='ck_browser_agent_runs_step_timeout_minimum'),
		sa.CheckConstraint('llm_timeout_seconds >= 15', name='ck_browser_agent_runs_llm_timeout_minimum'),
		sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
		sa.PrimaryKeyConstraint('id'),
	)
	op.create_index('ix_browser_agent_runs_status', 'browser_agent_runs', ['status'])
	op.create_index('ix_browser_agent_runs_user_id', 'browser_agent_runs', ['user_id'])
	op.create_index('ix_browser_agent_runs_user_status', 'browser_agent_runs', ['user_id', 'status'])
	op.create_index('ix_browser_agent_runs_status_created_at', 'browser_agent_runs', ['status', 'created_at'])
	op.alter_column('browser_agent_runs', 'status', server_default=None)
	op.alter_column('browser_agent_runs', 'llm_provider', server_default=None)


def downgrade() -> None:
	op.drop_index('ix_browser_agent_runs_status_created_at', table_name='browser_agent_runs')
	op.drop_index('ix_browser_agent_runs_user_status', table_name='browser_agent_runs')
	op.drop_index('ix_browser_agent_runs_user_id', table_name='browser_agent_runs')
	op.drop_index('ix_browser_agent_runs_status', table_name='browser_agent_runs')
	op.drop_table('browser_agent_runs')
