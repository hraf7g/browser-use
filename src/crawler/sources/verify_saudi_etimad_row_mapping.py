from __future__ import annotations

import asyncio
import sys
from urllib.parse import parse_qsl, urlparse

from src.crawler.sources.saudi_etimad_crawler import (
    SaudiEtimadCrawlerError,
    SaudiEtimadCrawlResult,
    run_saudi_etimad_crawl,
)


def _truncate(value: str | None, limit: int = 140) -> str:
    """Return a compact one-line preview for verification output."""
    if value is None:
        return "None"
    compact = value.replace("\n", " | ").strip()
    if len(compact) <= limit:
        return compact
    return f"{compact[: limit - 3]}..."


def _print_summary(result: SaudiEtimadCrawlResult) -> None:
    """Print a compact verification summary of mapped listing fields."""
    print(f"verify_saudi_etimad_mapping_source_name={result.source_name}")
    print(f"verify_saudi_etimad_mapping_listing_url={result.listing_url}")
    print(f"verify_saudi_etimad_mapping_final_url={result.final_url}")
    print(f"verify_saudi_etimad_mapping_page_title={result.page_title}")
    print(f"verify_saudi_etimad_mapping_total_items={result.total_items}")

    sample_count = min(5, len(result.items))
    for index in range(sample_count):
        item = result.items[index]
        print(f"verify_saudi_etimad_mapping_item_{index}_title={_truncate(item.title_text)}")
        print(
            f"verify_saudi_etimad_mapping_item_{index}_issuing_entity="
            f"{_truncate(item.issuing_entity)}"
        )
        print(
            f"verify_saudi_etimad_mapping_item_{index}_publication_date="
            f"{_truncate(item.publication_date)}"
        )
        print(
            f"verify_saudi_etimad_mapping_item_{index}_procurement_type_label="
            f"{_truncate(item.procurement_type_label)}"
        )
        print(
            f"verify_saudi_etimad_mapping_item_{index}_visible_reference="
            f"{_truncate(item.visible_reference)}"
        )
        print(f"verify_saudi_etimad_mapping_item_{index}_detail_url={item.detail_url}")


def _validate_item(item_index: int, result: SaudiEtimadCrawlResult) -> None:
    """Validate deterministic mapping expectations for a single item."""
    item = result.items[item_index]

    if not item.title_text.strip():
        raise ValueError(f"item {item.item_index} has empty title_text")
    if not item.detail_url.strip():
        raise ValueError(f"item {item.item_index} has empty detail_url")

    parsed = urlparse(item.detail_url)
    if parsed.scheme != "https" or parsed.netloc != "tenders.etimad.sa":
        raise ValueError(f"item {item.item_index} detail_url is not on the expected host")
    if parsed.path != "/Tender/DetailsForVisitor":
        raise ValueError(f"item {item.item_index} detail_url path is unexpected")

    query_pairs = dict(parse_qsl(parsed.query, keep_blank_values=True))
    if not query_pairs.get("STenderId"):
        raise ValueError(f"item {item.item_index} detail_url has no non-empty STenderId")

    if "تاريخ النشر" in item.raw_text and item.publication_date is None:
        raise ValueError(f"item {item.item_index} is missing publication_date despite visible listing text")

    raw_lines = item.raw_text.splitlines()

    if len(raw_lines) >= 2 and not raw_lines[1].startswith("تاريخ النشر"):
        expected_type_line = raw_lines[1]
        if expected_type_line not in {"التفاصيل", item.title_text} and item.procurement_type_label != expected_type_line:
            raise ValueError(
                f"item {item.item_index} procurement_type_label did not match the visible listing line"
            )

    if len(raw_lines) >= 4 and raw_lines[3] not in {"التفاصيل", item.title_text} and item.issuing_entity != raw_lines[3]:
        raise ValueError(
            f"item {item.item_index} issuing_entity did not match the visible listing line"
        )

    if item.visible_reference is not None and item.visible_reference not in item.title_text and not any(
        item.visible_reference in line for line in item.reference_fields
    ):
        raise ValueError(
            f"item {item.item_index} visible_reference was not actually found in visible listing text"
        )


async def _run() -> None:
    """Execute row-mapping verification against the live Saudi Etimad listing."""
    result = await run_saudi_etimad_crawl()

    if result.total_items < 1:
        raise ValueError("expected at least one mapped item, got zero")

    for item_index in range(min(5, result.total_items)):
        _validate_item(item_index, result)

    _print_summary(result)


def run() -> None:
    """Synchronous entrypoint for module execution."""
    try:
        asyncio.run(_run())
    except SaudiEtimadCrawlerError as exc:
        print(f"SAUDI_ETIMAD ROW MAPPING VERIFICATION FAILED: {exc}", file=sys.stderr)
        sys.exit(1)
    except Exception as exc:
        print(f"UNEXPECTED ERROR: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    run()
