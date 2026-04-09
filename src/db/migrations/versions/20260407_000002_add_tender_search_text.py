from __future__ import annotations

import re
import unicodedata

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "20260407_000002"
down_revision = "20260406_000001"
branch_labels = None
depends_on = None

ARABIC_DIACRITICS_PATTERN = re.compile(
    "[" "\u0610-\u061A" "\u064B-\u065F" "\u0670" "\u06D6-\u06ED" "]"
)
MULTISPACE_PATTERN = re.compile(r"\s+")


def upgrade() -> None:
    op.add_column(
        "tenders",
        sa.Column(
            "search_text",
            sa.Text(),
            nullable=False,
            server_default=sa.text("''"),
        ),
    )

    _backfill_tender_search_text()

    op.create_index(
        "ix_tenders_search_text",
        "tenders",
        ["search_text"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_tenders_search_text", table_name="tenders")
    op.drop_column("tenders", "search_text")


def _backfill_tender_search_text() -> None:
    """
    Backfill search_text deterministically for existing tenders.

    Notes:
        - keeps migration self-contained
        - does not import application modules
        - uses conservative Arabic/English normalization only
    """
    bind = op.get_bind()
    rows = bind.execute(
        sa.text(
            """
        SELECT id, title, issuing_entity, category, ai_summary, tender_ref
        FROM tenders
        """
        )
    ).mappings()

    batch: list[dict[str, object]] = []
    for row in rows:
        search_text = _build_search_text(
            title=row["title"],
            issuing_entity=row["issuing_entity"],
            category=row["category"],
            ai_summary=row["ai_summary"],
            tender_ref=row["tender_ref"],
        )
        batch.append(
            {
                "id": row["id"],
                "search_text": search_text,
            }
        )

        if len(batch) >= 500:
            _flush_backfill_batch(bind, batch)
            batch = []

    if batch:
        _flush_backfill_batch(bind, batch)


def _flush_backfill_batch(
    bind: sa.engine.Connection,
    batch: list[dict[str, object]],
) -> None:
    """Write one backfill batch to the database."""
    bind.execute(
        sa.text(
            """
        UPDATE tenders
        SET search_text = :search_text
        WHERE id = :id
        """
        ),
        batch,
    )


def _build_search_text(
    *,
    title: str | None,
    issuing_entity: str | None,
    category: str | None,
    ai_summary: str | None,
    tender_ref: str | None,
) -> str:
    """Build deterministic multilingual-normalized search text."""
    parts = [
        title,
        issuing_entity,
        category,
        ai_summary,
        tender_ref,
    ]
    normalized_parts = [
        _normalize_multilingual_text(part)
        for part in parts
        if isinstance(part, str) and part.strip()
    ]
    return " ".join(part for part in normalized_parts if part)


def _normalize_multilingual_text(value: str) -> str:
    """
    Apply conservative multilingual normalization for search backfill.

    Included:
        - Unicode NFKC normalization
        - Arabic diacritic removal
        - tatweel removal
        - conservative Arabic variant normalization
        - Latin casefold
        - whitespace collapse
    """
    unicode_normalized = unicodedata.normalize("NFKC", value)
    without_diacritics = ARABIC_DIACRITICS_PATTERN.sub("", unicode_normalized)
    without_tatweel = without_diacritics.replace("ـ", "")

    translation_table = str.maketrans(
        {
            "أ": "ا",
            "إ": "ا",
            "آ": "ا",
            "ٱ": "ا",
            "ى": "ي",
            "ی": "ي",
            "ې": "ي",
            "ک": "ك",
        }
    )
    arabic_normalized = without_tatweel.translate(translation_table)
    casefolded = arabic_normalized.casefold()

    return MULTISPACE_PATTERN.sub(" ", casefolded.strip())
