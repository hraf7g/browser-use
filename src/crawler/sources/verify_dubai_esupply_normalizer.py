from __future__ import annotations

import asyncio

from sqlalchemy import select

from src.crawler.sources.dubai_esupply_crawler import run_dubai_esupply_crawl
from src.crawler.sources.dubai_esupply_normalizer import (
    _canonicalize_dubai_source_url,
    _split_tender_ref_and_title,
    normalize_dubai_esupply_rows,
)
from src.db.models.source import Source
from src.db.session import get_session_factory

SOURCE_NAME = "Dubai eSupply"


async def _run() -> None:
    """
    Perform an isolated production-grade verification of the Dubai eSupply normalization layer.

    This script verifies:
    - live crawl execution succeeds
    - the Dubai eSupply source exists in the database
    - extracted rows can be normalized into TenderIngestionInput payloads
    - key normalized fields are populated deterministically
    """
    session_factory = get_session_factory()
    crawl_result = await run_dubai_esupply_crawl()

    if crawl_result.total_rows < 1:
        raise ValueError("expected at least one crawled row, got zero")

    with session_factory() as session:
        source = session.execute(
            select(Source).where(Source.name == SOURCE_NAME)
        ).scalar_one_or_none()

        if source is None:
            raise ValueError(
                f"source '{SOURCE_NAME}' was not found; seed sources first"
            )

        normalized_rows = normalize_dubai_esupply_rows(
            source_id=source.id,
            rows=crawl_result.rows,
        )

        if not normalized_rows:
            raise ValueError("expected at least one normalized row, got zero")

        first_item = normalized_rows[0]

        if not first_item.title.strip():
            raise ValueError("first normalized item has empty title")

        if not first_item.issuing_entity.strip():
            raise ValueError("first normalized item has empty issuing_entity")

        if not first_item.dedupe_key.strip():
            raise ValueError("first normalized item has empty dedupe_key")

        if first_item.source_id is None:
            raise ValueError("first normalized item has no source_id")

        expected_canonical_source_url = _canonicalize_dubai_source_url(
            crawl_result.listing_url
        )
        if first_item.source_url != expected_canonical_source_url:
            raise ValueError("normalized source_url is not canonicalized as expected")
        if "_ncp=" in first_item.source_url:
            raise ValueError("normalized source_url still contains volatile _ncp")

        deterministic_examples = (
            ("12607621 / vor", "12607621", "vor"),
            ("12607620-IVECO TRUCK", "12607620", "IVECO TRUCK"),
            (
                "12607439 Transportation Maintenance Dept",
                "12607439",
                "Transportation Maintenance Dept",
            ),
            (
                "REQ 12607678 / 12607610 -VOR- W.O# INS-26-896914",
                "REQ 12607678 / 12607610",
                "VOR- W.O# INS-26-896914",
            ),
        )
        for raw_value, expected_ref, expected_title in deterministic_examples:
            actual_ref, actual_title = _split_tender_ref_and_title(raw_value)
            if actual_ref != expected_ref or actual_title != expected_title:
                raise ValueError(
                    "deterministic title/ref split regressed for "
                    f"{raw_value!r}: got ref={actual_ref!r}, title={actual_title!r}"
                )

        low_confidence_raw = (
            "Med.Equip / BME/Telemetry Units/SOQ:22600821/HKM/IPR/126032997-HH"
        )
        low_confidence_ref, low_confidence_title = _split_tender_ref_and_title(
            low_confidence_raw
        )
        if low_confidence_ref is not None:
            raise ValueError(
                "low-confidence Dubai eSupply token was persisted as tender_ref: "
                f"{low_confidence_ref!r}"
            )
        if low_confidence_title != low_confidence_raw:
            raise ValueError("low-confidence title preservation regressed unexpectedly")

        suspicious_pairs = [
            (raw_row.cells[2].strip(), normalized_row.tender_ref, normalized_row.title)
            for raw_row, normalized_row in zip(crawl_result.rows, normalized_rows, strict=False)
            if "/" in raw_row.cells[2] and normalized_row.tender_ref is None
        ]
        suspicious_sample = suspicious_pairs[:5]

        print(f"verify_normalizer_source_name={crawl_result.source_name}")
        print(f"verify_normalizer_listing_url={crawl_result.listing_url}")
        print(f"verify_normalizer_total_crawled_rows={crawl_result.total_rows}")
        print(f"verify_normalizer_total_normalized_rows={len(normalized_rows)}")
        print(f"verify_normalizer_first_title={first_item.title}")
        print(f"verify_normalizer_first_issuing_entity={first_item.issuing_entity}")
        print(f"verify_normalizer_first_closing_date={first_item.closing_date.isoformat()}")
        print(f"verify_normalizer_first_tender_ref={first_item.tender_ref}")
        print(f"verify_normalizer_first_category={first_item.category}")
        print(f"verify_normalizer_first_dedupe_key={first_item.dedupe_key}")
        print(f"verify_normalizer_first_source_url={first_item.source_url}")
        print(
            "verify_normalizer_first_source_url_is_canonical="
            f"{first_item.source_url == expected_canonical_source_url}"
        )
        print(f"verify_normalizer_low_confidence_ref={low_confidence_ref}")
        print(
            "verify_normalizer_low_confidence_title_preserved="
            f"{low_confidence_title == low_confidence_raw}"
        )
        print(f"verify_normalizer_suspicious_pair_count={len(suspicious_pairs)}")

        for index, (raw_title, tender_ref, title) in enumerate(
            suspicious_sample,
            start=1,
        ):
            print(f"verify_normalizer_suspicious_{index}_raw_title={raw_title}")
            print(f"verify_normalizer_suspicious_{index}_tender_ref={tender_ref}")
            print(f"verify_normalizer_suspicious_{index}_title={title}")


def run() -> None:
    """Synchronous module entrypoint."""
    asyncio.run(_run())


if __name__ == "__main__":
    run()
