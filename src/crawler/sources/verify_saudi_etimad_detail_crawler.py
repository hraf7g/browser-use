from __future__ import annotations

import asyncio

from src.crawler.sources.saudi_etimad_detail_crawler import run_saudi_etimad_detail_crawl


def _truncate(value: str | None, *, limit: int = 120) -> str:
	"""Return a stable printable preview of optional text."""
	if value is None:
		return 'None'
	cleaned = value.strip()
	if len(cleaned) <= limit:
		return cleaned
	return f'{cleaned[:limit]}...'


async def _run() -> None:
	result = await run_saudi_etimad_detail_crawl(sample_size=3)

	print(f'verify_saudi_etimad_detail_source_name={result.source_name}')
	print(f'verify_saudi_etimad_detail_listing_url={result.listing_url}')
	print(f'verify_saudi_etimad_detail_final_listing_url={result.final_listing_url}')
	print(f'verify_saudi_etimad_detail_sample_count={result.sample_count}')
	print(f'verify_saudi_etimad_detail_successful_detail_pages={result.successful_detail_pages}')

	for index, item in enumerate(result.items):
		print(f'verify_saudi_etimad_detail_item_{index}_detail_url={item.detail_url}')
		print(f'verify_saudi_etimad_detail_item_{index}_access_status={item.access_status}')
		print(f'verify_saudi_etimad_detail_item_{index}_detail_title={_truncate(item.detail_title)}')
		print(f'verify_saudi_etimad_detail_item_{index}_detail_issuing_entity={_truncate(item.detail_issuing_entity)}')
		print(f'verify_saudi_etimad_detail_item_{index}_detail_competition_number={_truncate(item.detail_competition_number)}')
		print(f'verify_saudi_etimad_detail_item_{index}_detail_reference_number={_truncate(item.detail_reference_number)}')
		print(f'verify_saudi_etimad_detail_item_{index}_detail_procurement_type={_truncate(item.detail_procurement_type)}')
		print(f'verify_saudi_etimad_detail_item_{index}_detail_remaining_time_raw={_truncate(item.detail_remaining_time_raw)}')
		print(f'verify_saudi_etimad_detail_item_{index}_stronger_fields={item.stronger_fields}')


if __name__ == '__main__':
	asyncio.run(_run())
