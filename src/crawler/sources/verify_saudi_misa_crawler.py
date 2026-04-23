from __future__ import annotations

import asyncio

from src.crawler.sources.saudi_misa_crawler import (
    SaudiMisaCrawlerError,
    run_saudi_misa_crawl,
)


def _truncate(value: str | None, *, limit: int = 160) -> str:
    """Return a compact deterministic preview for verifier output."""
    if value is None:
        return "None"
    cleaned = value.strip()
    if len(cleaned) <= limit:
        return cleaned
    return f"{cleaned[:limit]}..."


def run() -> None:
    """Execute live Saudi MISA procurements crawl verification."""
    try:
        result = asyncio.run(run_saudi_misa_crawl())
    except SaudiMisaCrawlerError as exc:
        print(f"SAUDI_MISA CRAWLER VERIFICATION FAILED: {exc}")
        return

    if result.total_items == 0:
        raise ValueError("expected at least one Saudi MISA procurement row, got zero")

    first_item = result.items[0]

    print(f"verify_saudi_misa_source_name={result.source_name}")
    print(f"verify_saudi_misa_listing_url={result.listing_url}")
    print(f"verify_saudi_misa_final_url={result.final_url}")
    print(f"verify_saudi_misa_page_title={result.page_title}")
    print(f"verify_saudi_misa_extracted_at={result.extracted_at.isoformat()}")
    print(f"verify_saudi_misa_total_items={result.total_items}")
    print(f"verify_saudi_misa_first_item_title={first_item.title_text}")
    print(f"verify_saudi_misa_first_item_href={first_item.detail_url}")
    print(
        "verify_saudi_misa_first_item_reference_number="
        f"{first_item.visible_reference_number}"
    )
    print(
        "verify_saudi_misa_first_item_offering_date="
        f"{first_item.visible_offering_date}"
    )
    print(
        "verify_saudi_misa_first_item_inquiry_deadline="
        f"{first_item.visible_inquiry_deadline}"
    )
    print(
        "verify_saudi_misa_first_item_bid_deadline="
        f"{first_item.visible_bid_deadline}"
    )
    print(
        "verify_saudi_misa_first_item_status_link_text="
        f"{first_item.visible_status_link_text}"
    )
    print(
        "verify_saudi_misa_first_item_raw_preview="
        f"{_truncate(first_item.raw_text)}"
    )

    for item in result.items[:3]:
        print(f"verify_saudi_misa_sample_{item.item_index}_title={item.title_text}")
        print(f"verify_saudi_misa_sample_{item.item_index}_href={item.detail_url}")
        print(
            "verify_saudi_misa_sample_"
            f"{item.item_index}_reference_number={item.visible_reference_number}"
        )
        print(
            "verify_saudi_misa_sample_"
            f"{item.item_index}_offering_date={item.visible_offering_date}"
        )
        print(
            "verify_saudi_misa_sample_"
            f"{item.item_index}_inquiry_deadline={item.visible_inquiry_deadline}"
        )
        print(
            "verify_saudi_misa_sample_"
            f"{item.item_index}_bid_deadline={item.visible_bid_deadline}"
        )
        print(
            "verify_saudi_misa_sample_"
            f"{item.item_index}_status_link_text={item.visible_status_link_text}"
        )


if __name__ == "__main__":
    run()
