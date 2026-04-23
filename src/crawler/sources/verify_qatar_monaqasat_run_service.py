from __future__ import annotations

from sqlalchemy import func, select

from src.crawler.sources.qatar_monaqasat_run_service import (
	run_qatar_monaqasat_source,
)
from src.db.models.crawl_run import CrawlRun
from src.db.models.source import Source
from src.db.models.tender import Tender
from src.db.session import get_session_factory

SOURCE_NAME = 'Qatar Monaqasat'


def run() -> None:
	"""
	Perform a production-grade persisted verification of the Qatar run service.
	"""
	session_factory = get_session_factory()

	with session_factory() as session:
		source_before = session.execute(select(Source).where(Source.name == SOURCE_NAME)).scalar_one_or_none()

		if source_before is None:
			raise ValueError(f"source '{SOURCE_NAME}' was not found; seed sources first")

		before_tender_count = len(session.execute(select(Tender).where(Tender.source_id == source_before.id)).scalars().all())

		result = run_qatar_monaqasat_source(session=session)
		session.commit()

	with session_factory() as session:
		source_after = session.execute(select(Source).where(Source.name == SOURCE_NAME)).scalar_one_or_none()
		if source_after is None:
			raise ValueError('source disappeared after run')

		crawl_run = session.get(CrawlRun, result.crawl_run_id)
		if crawl_run is None:
			raise ValueError('expected persisted CrawlRun row was not found')

		tenders_after = session.execute(select(Tender).where(Tender.source_id == source_after.id)).scalars().all()
		after_tender_count = len(tenders_after)
		populated_search_text_count = sum(
			1 for tender in tenders_after if isinstance(tender.search_text, str) and tender.search_text.strip()
		)
		duplicate_tender_refs = session.execute(
			select(Tender.tender_ref, func.count(Tender.id))
			.where(Tender.source_id == source_after.id)
			.where(Tender.tender_ref.is_not(None))
			.group_by(Tender.tender_ref)
			.having(func.count(Tender.id) > 1)
			.order_by(Tender.tender_ref.asc())
		).all()

		if result.status not in {'success', 'failed'}:
			raise ValueError(f'unexpected source run status {result.status}')

		if crawl_run.status != result.status:
			raise ValueError(f'persisted crawl_run.status={crawl_run.status} does not match result {result.status}')

		if result.accepted_row_count != (result.created_tender_count + result.updated_tender_count):
			raise ValueError('accepted_row_count does not equal created_tender_count + updated_tender_count')

		if populated_search_text_count == 0 and result.accepted_row_count > 0:
			raise ValueError('accepted rows were reported but no persisted tenders have populated search_text')

		if duplicate_tender_refs:
			raise ValueError(f'expected no persisted duplicate tender_ref values, got {duplicate_tender_refs[:5]!r}')

		if result.status == 'success':
			if source_after.status != 'healthy':
				raise ValueError(f"expected source status 'healthy', got {source_after.status}")
			if source_after.failure_count != 0:
				raise ValueError(f'expected source failure_count=0, got {source_after.failure_count}')
			if source_after.last_successful_run_at is None:
				raise ValueError('expected source.last_successful_run_at to be populated')
			if after_tender_count < before_tender_count:
				raise ValueError('tender count decreased unexpectedly after successful run')
		else:
			if source_after.status != 'degraded':
				raise ValueError(f"expected source status 'degraded', got {source_after.status}")
			if source_after.failure_count < 1:
				raise ValueError('expected source failure_count to increment after failed run')
			if source_after.last_failed_run_at is None:
				raise ValueError('expected source.last_failed_run_at to be populated')

		print(f'verify_run_result_status={result.status}')
		print(f'verify_run_result_run_identifier={result.run_identifier}')
		print(f'verify_run_result_crawled_row_count={result.crawled_row_count}')
		print(f'verify_run_result_detail_sampled_row_count={result.detail_sampled_row_count}')
		print(f'verify_run_result_normalized_row_count={result.normalized_row_count}')
		print(f'verify_run_result_accepted_row_count={result.accepted_row_count}')
		print(f'verify_run_result_review_required_row_count={result.review_required_row_count}')
		print(f'verify_run_result_created_tender_count={result.created_tender_count}')
		print(f'verify_run_result_updated_tender_count={result.updated_tender_count}')
		print(f'verify_run_crawl_run_status={crawl_run.status}')
		print(f'verify_run_crawl_run_failure_step={crawl_run.failure_step}')
		print(f'verify_run_crawl_run_failure_reason={crawl_run.failure_reason}')
		print(f'verify_run_source_after_status={source_after.status}')
		print(f'verify_run_source_after_failure_count={source_after.failure_count}')
		print(f'verify_run_before_tender_count={before_tender_count}')
		print(f'verify_run_after_tender_count={after_tender_count}')
		print(f'verify_run_populated_search_text_count={populated_search_text_count}')
		print(f'verify_run_duplicate_tender_ref_count={len(duplicate_tender_refs)}')


if __name__ == '__main__':
	run()
