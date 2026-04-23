"""add_user_operator_role

Revision ID: 20260419_000016
Revises: 20260419_000015
Create Date: 2026-04-19 20:50:00
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '20260419_000016'
down_revision = '20260419_000015'
branch_labels = None
depends_on = None


def upgrade() -> None:
	op.add_column(
		'users',
		sa.Column('is_operator', sa.Boolean(), nullable=False, server_default='false'),
	)
	op.alter_column('users', 'is_operator', server_default=None)


def downgrade() -> None:
	op.drop_column('users', 'is_operator')
