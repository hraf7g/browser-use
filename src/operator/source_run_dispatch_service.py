from __future__ import annotations

from sqlalchemy.orm import Session

from src.crawler.sources.abu_dhabi_gpg_run_service import run_abu_dhabi_gpg_source
from src.crawler.sources.bahrain_tender_board_run_service import (
	run_bahrain_tender_board_source,
)
from src.crawler.sources.dubai_esupply_run_service import run_dubai_esupply_source
from src.crawler.sources.federal_mof_run_service import run_federal_mof_source
from src.crawler.sources.oman_tender_board_run_service import (
	run_oman_tender_board_source,
)
from src.crawler.sources.qatar_monaqasat_run_service import (
	run_qatar_monaqasat_source,
)
from src.crawler.sources.saudi_etimad_run_service import run_saudi_etimad_source
from src.crawler.sources.saudi_misa_run_service import run_saudi_misa_source
from src.shared.schemas.operator_run import (
	OperatorRunSourceResponse,
)
from src.shared.source_registry import supported_source_names_text


class SourceRunDispatchError(ValueError):
	"""Raised when a manual source run cannot be dispatched safely."""


RUN_SERVICE_HANDLERS = {
	'Dubai eSupply': run_dubai_esupply_source,
	'Federal MOF': run_federal_mof_source,
	'Saudi Etimad': run_saudi_etimad_source,
	'Saudi MISA Procurements': run_saudi_misa_source,
	'Oman Tender Board': run_oman_tender_board_source,
	'Abu Dhabi GPG': run_abu_dhabi_gpg_source,
	'Bahrain Tender Board': run_bahrain_tender_board_source,
	'Qatar Monaqasat': run_qatar_monaqasat_source,
}


def dispatch_source_run(
	*,
	session: Session,
	source_name: str,
) -> OperatorRunSourceResponse:
	"""
	Dispatch one supported manual source run and normalize the result.

	Notes:
	    - This service does not commit the transaction.
	    - The caller owns transaction boundaries.
	    - Only explicitly supported sources can be triggered.
	    - Source-specific run services remain authoritative for crawl logic.
	"""
	normalized_source_name = source_name.strip()

	run_handler = RUN_SERVICE_HANDLERS.get(normalized_source_name)
	if run_handler is None:
		raise SourceRunDispatchError(
			'unsupported source_name for manual operator run: '
			f'{normalized_source_name!r}; supported values are '
			f'{supported_source_names_text()}'
		)

	result = run_handler(session=session)
	normalized_row_count = getattr(
		result,
		'normalized_row_count',
		getattr(result, 'enriched_normalized_row_count', 0),
	)
	crawled_row_count = getattr(
		result,
		'crawled_row_count',
		getattr(result, 'widget_crawled_row_count', 0),
	)

	return OperatorRunSourceResponse(
		source_name=normalized_source_name,
		source_id=result.source_id,
		crawl_run_id=result.crawl_run_id,
		run_identifier=result.run_identifier,
		status=result.status,
		started_at=result.started_at,
		finished_at=result.finished_at,
		crawled_row_count=crawled_row_count,
		normalized_row_count=normalized_row_count,
		accepted_row_count=result.accepted_row_count,
		review_required_row_count=result.review_required_row_count,
		created_tender_count=result.created_tender_count,
		updated_tender_count=result.updated_tender_count,
		failure_step=result.failure_step,
		failure_reason=result.failure_reason,
	)
