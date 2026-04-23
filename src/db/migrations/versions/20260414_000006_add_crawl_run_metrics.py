from __future__ import annotations

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "20260414_000006"
down_revision = "20260412_000005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("crawl_runs", sa.Column("crawled_row_count", sa.Integer(), nullable=True))
    op.add_column("crawl_runs", sa.Column("normalized_row_count", sa.Integer(), nullable=True))
    op.add_column("crawl_runs", sa.Column("accepted_row_count", sa.Integer(), nullable=True))
    op.add_column("crawl_runs", sa.Column("review_required_row_count", sa.Integer(), nullable=True))
    op.add_column("crawl_runs", sa.Column("updated_tender_count", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("crawl_runs", "updated_tender_count")
    op.drop_column("crawl_runs", "review_required_row_count")
    op.drop_column("crawl_runs", "accepted_row_count")
    op.drop_column("crawl_runs", "normalized_row_count")
    op.drop_column("crawl_runs", "crawled_row_count")
