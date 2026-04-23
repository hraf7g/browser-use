from __future__ import annotations

import asyncio

from src.crawler.sources.saudi_moh_crawler import (
    SaudiMohCrawlerError,
    run_saudi_moh_crawl,
)


def _truncate(value: str | None, *, limit: int = 160) -> str:
    """Return a compact deterministic preview for verifier output."""
    if value is None:
        return 'None'
    cleaned = value.strip()
    if len(cleaned) <= limit:
        return cleaned
    return f'{cleaned[:limit]}...'


def run() -> None:
    """Execute live Saudi MOH tenders crawl verification."""
    try:
        result = asyncio.run(run_saudi_moh_crawl())
    except SaudiMohCrawlerError as exc:
        print(f'SAUDI_MOH CRAWLER VERIFICATION FAILED: {exc}')
        return

    if result.total_items == 0:
        raise ValueError('expected at least one Saudi MOH tender row, got zero')

    first_item = result.items[0]

    print(f'verify_saudi_moh_source_name={result.source_name}')
    print(f'verify_saudi_moh_listing_url={result.listing_url}')
    print(f'verify_saudi_moh_final_url={result.final_url}')
    print(f'verify_saudi_moh_page_title={result.page_title}')
    print(f'verify_saudi_moh_extracted_at={result.extracted_at.isoformat()}')
    print(f'verify_saudi_moh_total_items={result.total_items}')
    print(f'verify_saudi_moh_first_item_title={first_item.title_text}')
    print(f'verify_saudi_moh_first_item_href={first_item.detail_url}')
    print(
        'verify_saudi_moh_first_item_tender_number='
        f'{first_item.visible_tender_number}'
    )
    print(
        'verify_saudi_moh_first_item_tendering_date='
        f'{first_item.visible_tendering_date}'
    )
    print(
        'verify_saudi_moh_first_item_bidding_deadline='
        f'{first_item.visible_bidding_deadline}'
    )
    print(
        'verify_saudi_moh_first_item_opening_date='
        f'{first_item.visible_opening_date}'
    )
    print(f'verify_saudi_moh_first_item_status={first_item.visible_status}')
    print(
        'verify_saudi_moh_first_item_raw_preview='
        f'{_truncate(first_item.raw_text)}'
    )

    for item in result.items[:3]:
        print(f'verify_saudi_moh_sample_{item.item_index}_title={item.title_text}')
        print(f'verify_saudi_moh_sample_{item.item_index}_href={item.detail_url}')
        print(
            'verify_saudi_moh_sample_'
            f'{item.item_index}_tender_number={item.visible_tender_number}'
        )
        print(
            'verify_saudi_moh_sample_'
            f'{item.item_index}_tendering_date={item.visible_tendering_date}'
        )
        print(
            'verify_saudi_moh_sample_'
            f'{item.item_index}_bidding_deadline={item.visible_bidding_deadline}'
        )
        print(
            'verify_saudi_moh_sample_'
            f'{item.item_index}_opening_date={item.visible_opening_date}'
        )
        print(
            'verify_saudi_moh_sample_'
            f'{item.item_index}_status={item.visible_status}'
        )


if __name__ == '__main__':
    run()
