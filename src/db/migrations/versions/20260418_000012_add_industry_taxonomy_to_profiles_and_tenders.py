"""add_industry_taxonomy_to_profiles_and_tenders

Revision ID: 20260418_000012
Revises: 20260418_000011
Create Date: 2026-04-18 00:30:00
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

from src.shared.industry_taxonomy import (
	classify_industry_codes,
	classify_profile_industry_codes,
)

# revision identifiers, used by Alembic.
revision = '20260418_000012'
down_revision = '20260418_000011'
branch_labels = None
depends_on = None


def upgrade() -> None:
	op.add_column(
		'keyword_profiles',
		sa.Column(
			'industry_codes',
			postgresql.ARRAY(sa.String(length=64)),
			server_default='{}',
			nullable=False,
		),
	)
	op.add_column(
		'tenders',
		sa.Column(
			'industry_codes',
			postgresql.ARRAY(sa.String(length=64)),
			server_default='{}',
			nullable=False,
		),
	)
	op.add_column(
		'tenders',
		sa.Column('primary_industry_code', sa.String(length=64), nullable=True),
	)

	connection = op.get_bind()
	rows = connection.execute(sa.text('SELECT id, category, title, issuing_entity, ai_summary FROM tenders')).mappings()

	for row in rows:
		industry_codes = classify_industry_codes(
			category=row['category'],
			title=row['title'],
			issuing_entity=row['issuing_entity'],
			ai_summary=row['ai_summary'],
		)
		connection.execute(
			sa.text(
				"""
				UPDATE tenders
				SET industry_codes = :industry_codes,
					primary_industry_code = :primary_industry_code
				WHERE id = :tender_id
				"""
			),
			{
				'tender_id': row['id'],
				'industry_codes': industry_codes,
				'primary_industry_code': None if not industry_codes else industry_codes[0],
			},
		)

	profile_rows = connection.execute(sa.text('SELECT id, industry_label, keywords FROM keyword_profiles')).mappings()

	for row in profile_rows:
		industry_codes = classify_profile_industry_codes(
			industry_label=row['industry_label'],
			keywords=list(row['keywords'] or []),
		)
		connection.execute(
			sa.text(
				"""
				UPDATE keyword_profiles
				SET industry_codes = :industry_codes
				WHERE id = :profile_id
				"""
			),
			{
				'profile_id': row['id'],
				'industry_codes': industry_codes,
			},
		)


def downgrade() -> None:
	op.drop_column('tenders', 'primary_industry_code')
	op.drop_column('tenders', 'industry_codes')
	op.drop_column('keyword_profiles', 'industry_codes')
