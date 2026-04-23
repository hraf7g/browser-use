from __future__ import annotations

from sqlalchemy import select

from src.db.models.source import Source
from src.db.session import get_session_factory
from src.shared.source_registry import build_seed_source_rows

SEED_SOURCES: tuple[dict[str, str], ...] = build_seed_source_rows()


def seed_sources() -> int:
    """Insert the v1 monitored sources if they do not already exist."""
    session_factory = get_session_factory()

    with session_factory() as session:
        inserted_count = 0

        for source_data in SEED_SOURCES:
            existing = session.execute(
                select(Source).where(Source.name == source_data["name"])
            ).scalar_one_or_none()

            if existing is not None:
                continue

            session.add(Source(**source_data))
            inserted_count += 1

        session.commit()
        return inserted_count


if __name__ == "__main__":
    inserted = seed_sources()
    print(f"seeded_sources={inserted}")
