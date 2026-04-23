"""Persist deterministic country and industry scope evidence on tender matches."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20260418_000013'
down_revision = '20260418_000012'
branch_labels = None
depends_on = None


def upgrade() -> None:
	op.add_column(
		'tender_matches',
		sa.Column(
			'matched_country_codes',
			postgresql.ARRAY(sa.String(length=2)),
			nullable=False,
			server_default='{}',
		),
	)
	op.add_column(
		'tender_matches',
		sa.Column(
			'matched_industry_codes',
			postgresql.ARRAY(sa.String(length=64)),
			nullable=False,
			server_default='{}',
		),
	)

	op.execute(
		sa.text(
			"""
            UPDATE tender_matches AS tm
            SET matched_country_codes = ARRAY[src.country_code]
            FROM tenders AS t
            JOIN sources AS src ON src.id = t.source_id
            WHERE tm.tender_id = t.id
              AND src.country_code IS NOT NULL
            """
		)
	)
	op.execute(
		sa.text(
			"""
            UPDATE tender_matches AS tm
            SET matched_industry_codes = COALESCE(t.industry_codes, '{}')
            FROM tenders AS t
            WHERE tm.tender_id = t.id
            """
		)
	)

	op.alter_column('tender_matches', 'matched_country_codes', server_default=None)
	op.alter_column('tender_matches', 'matched_industry_codes', server_default=None)


def downgrade() -> None:
	op.drop_column('tender_matches', 'matched_industry_codes')
	op.drop_column('tender_matches', 'matched_country_codes')
