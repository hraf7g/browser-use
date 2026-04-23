"""add_source_country_metadata_and_profile_country_scope

Revision ID: 20260418_000011
Revises: 20260417_000010
Create Date: 2026-04-18 00:00:00
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20260418_000011'
down_revision = '20260417_000010'
branch_labels = None
depends_on = None


def upgrade() -> None:
	op.add_column(
		'sources',
		sa.Column('country_code', sa.String(length=2), nullable=True),
	)
	op.add_column(
		'sources',
		sa.Column('country_name', sa.String(length=120), nullable=True),
	)
	op.add_column(
		'sources',
		sa.Column('lifecycle', sa.String(length=20), server_default='live', nullable=False),
	)

	op.execute(
		"""
		UPDATE sources
		SET country_code = CASE name
			WHEN 'Dubai eSupply' THEN 'AE'
			WHEN 'Federal MOF' THEN 'AE'
			WHEN 'Saudi Etimad' THEN 'SA'
			WHEN 'Saudi MISA Procurements' THEN 'SA'
			WHEN 'Oman Tender Board' THEN 'OM'
			WHEN 'Abu Dhabi GPG' THEN 'AE'
			WHEN 'Bahrain Tender Board' THEN 'BH'
			WHEN 'Qatar Monaqasat' THEN 'QA'
			ELSE 'AE'
		END,
		country_name = CASE name
			WHEN 'Dubai eSupply' THEN 'United Arab Emirates'
			WHEN 'Federal MOF' THEN 'United Arab Emirates'
			WHEN 'Saudi Etimad' THEN 'Saudi Arabia'
			WHEN 'Saudi MISA Procurements' THEN 'Saudi Arabia'
			WHEN 'Oman Tender Board' THEN 'Oman'
			WHEN 'Abu Dhabi GPG' THEN 'United Arab Emirates'
			WHEN 'Bahrain Tender Board' THEN 'Bahrain'
			WHEN 'Qatar Monaqasat' THEN 'Qatar'
			ELSE 'United Arab Emirates'
		END,
		lifecycle = 'live'
		"""
	)

	op.alter_column('sources', 'country_code', nullable=False)
	op.alter_column('sources', 'country_name', nullable=False)

	op.add_column(
		'keyword_profiles',
		sa.Column(
			'country_codes',
			postgresql.ARRAY(sa.String(length=2)),
			server_default='{}',
			nullable=False,
		),
	)


def downgrade() -> None:
	op.drop_column('keyword_profiles', 'country_codes')
	op.drop_column('sources', 'lifecycle')
	op.drop_column('sources', 'country_name')
	op.drop_column('sources', 'country_code')
