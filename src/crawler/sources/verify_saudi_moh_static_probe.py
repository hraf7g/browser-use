from __future__ import annotations

from src.crawler.sources.saudi_moh_static_probe import (
    SaudiMohStaticFetchError,
    run_saudi_moh_static_probe,
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
    """Execute live Saudi MOH static-feasibility verification."""
    try:
        result = run_saudi_moh_static_probe()
    except SaudiMohStaticFetchError as exc:
        print(f'SAUDI_MOH STATIC PROBE FAILED: {exc}')
        return

    print(f'verify_saudi_moh_static_source_name={result.source_name}')
    print(f'verify_saudi_moh_static_listing_url={result.listing_url}')
    print(f'verify_saudi_moh_static_final_url={result.final_url}')
    print(f'verify_saudi_moh_static_fetched_at={result.fetched_at.isoformat()}')
    print(f'verify_saudi_moh_static_fetch_status={result.fetch_status}')
    print(f'verify_saudi_moh_static_status_code={result.status_code}')
    print(f'verify_saudi_moh_static_content_type={result.content_type}')
    print(f'verify_saudi_moh_static_page_title={result.page_title}')
    print(f'verify_saudi_moh_static_html_returned={result.html_returned}')
    print(f'verify_saudi_moh_static_redirected={result.redirected}')
    print(f'verify_saudi_moh_static_blocked={result.blocked}')
    print(f'verify_saudi_moh_static_empty={result.empty}')
    print(f'verify_saudi_moh_static_js_shell_only={result.js_shell_only}')
    print(
        'verify_saudi_moh_static_tender_list_data_present='
        f'{result.tender_list_data_present}'
    )
    print(
        'verify_saudi_moh_static_embedded_json_present='
        f'{result.embedded_json_present}'
    )
    print(
        'verify_saudi_moh_static_visible_api_endpoints_present='
        f'{result.visible_api_endpoints_present}'
    )
    print(
        'verify_saudi_moh_static_feasible_static_scraping='
        f'{result.feasible_static_scraping}'
    )
    print(f'verify_saudi_moh_static_blocker_reason={result.blocker_reason}')
    print(f'verify_saudi_moh_static_tender_link_count={result.tender_link_count}')
    print(f'verify_saudi_moh_static_embedded_json_count={result.embedded_json_count}')
    print(
        'verify_saudi_moh_static_visible_api_endpoint_count='
        f'{result.visible_api_endpoint_count}'
    )

    for item in result.items[:3]:
        print(f'verify_saudi_moh_static_sample_{item.item_index}_title={item.title_text}')
        print(f'verify_saudi_moh_static_sample_{item.item_index}_href={item.href}')
        print(
            'verify_saudi_moh_static_sample_'
            f'{item.item_index}_tender_number={item.visible_tender_number}'
        )
        print(
            'verify_saudi_moh_static_sample_'
            f'{item.item_index}_tendering_date={item.visible_tendering_date}'
        )
        print(
            'verify_saudi_moh_static_sample_'
            f'{item.item_index}_bidding_deadline={item.visible_bidding_deadline}'
        )
        print(
            'verify_saudi_moh_static_sample_'
            f'{item.item_index}_opening_date={item.visible_opening_date}'
        )
        print(
            'verify_saudi_moh_static_sample_'
            f'{item.item_index}_status={_truncate(item.visible_status)}'
        )


if __name__ == '__main__':
    run()
