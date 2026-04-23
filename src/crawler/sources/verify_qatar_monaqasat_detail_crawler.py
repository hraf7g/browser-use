from __future__ import annotations

import asyncio
import sys

from src.crawler.sources.qatar_monaqasat_detail_crawler import (
	QatarMonaqasatDetailCrawlerError,
	QatarMonaqasatDetailCrawlResult,
	run_qatar_monaqasat_detail_crawl,
)


def _truncate(value: str | None, limit: int = 160) -> str:
	"""Return a compact one-line preview for verification output."""
	if value is None:
		return 'None'
	compact = value.replace('\n', ' | ').strip()
	if len(compact) <= limit:
		return compact
	return f'{compact[: limit - 3]}...'


def _print_summary(result: QatarMonaqasatDetailCrawlResult) -> None:
	"""Print a compact deterministic summary of sampled detail-page inspection."""
	print(f'verify_qatar_monaqasat_detail_source_name={result.source_name}')
	print(f'verify_qatar_monaqasat_detail_listing_url={result.listing_url}')
	print(f'verify_qatar_monaqasat_detail_final_listing_url={result.final_listing_url}')
	print(f'verify_qatar_monaqasat_detail_sample_count={result.sample_count}')
	print(f'verify_qatar_monaqasat_detail_successful_detail_pages={result.successful_detail_pages}')
	print(f'verify_qatar_monaqasat_detail_enrichment_supported={result.successful_detail_pages > 0}')

	sample_count = min(5, len(result.items))
	for index in range(sample_count):
		item = result.items[index]
		print(f'verify_qatar_monaqasat_detail_item_{index}_dashboard_title={_truncate(item.dashboard_title_text)}')
		print(f'verify_qatar_monaqasat_detail_item_{index}_detail_url={item.detail_url}')
		print(f'verify_qatar_monaqasat_detail_item_{index}_detail_page_title={_truncate(item.detail_page_title)}')
		print(f'verify_qatar_monaqasat_detail_item_{index}_access_status={item.access_status}')
		print(f'verify_qatar_monaqasat_detail_item_{index}_detail_title={_truncate(item.detail_title)}')
		print(f'verify_qatar_monaqasat_detail_item_{index}_detail_publish_date_raw={_truncate(item.detail_publish_date_raw)}')
		print(f'verify_qatar_monaqasat_detail_item_{index}_detail_closing_date_raw={_truncate(item.detail_closing_date_raw)}')
		print(f'verify_qatar_monaqasat_detail_item_{index}_detail_tender_type={_truncate(item.detail_tender_type)}')
		print(f'verify_qatar_monaqasat_detail_item_{index}_stronger_fields={item.stronger_fields}')


async def _run() -> None:
	"""Execute the live Qatar detail-page inspection and validate the result shape."""
	result = await run_qatar_monaqasat_detail_crawl()

	if result.sample_count < 1:
		raise ValueError('expected at least one sampled detail page, got zero')

	for item in result.items:
		if not item.detail_url.strip():
			raise ValueError(f'detail sample {item.item_index} has empty detail_url')
		if not item.detail_page_title.strip():
			raise ValueError(f'detail sample {item.item_index} has empty detail_page_title')
		if not item.raw_text.strip():
			raise ValueError(f'detail sample {item.item_index} has empty raw_text')
		if item.access_status != 'detail_page':
			raise ValueError(f'detail sample {item.item_index} has unexpected access_status={item.access_status}')

	_print_summary(result)


def run() -> None:
	"""Synchronous entrypoint for module execution."""
	try:
		asyncio.run(_run())
	except QatarMonaqasatDetailCrawlerError as exc:
		print(f'QATAR_MONAQASAT DETAIL VERIFICATION FAILED: {exc}', file=sys.stderr)
		sys.exit(1)
	except Exception as exc:
		print(f'UNEXPECTED ERROR: {exc}', file=sys.stderr)
		sys.exit(1)


if __name__ == '__main__':
	run()
