from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from typing import TYPE_CHECKING, cast
from uuid import uuid4

from sqlalchemy import select

from src.ai.factory import AIRuntime
from src.db.models.source import Source
from src.db.models.tender import Tender
from src.db.session import get_session_factory
from src.ingestion.tender_ingestion_service import ingest_tender
from src.jobs.enrich_recent_tenders_job_service import run_enrich_recent_tenders_job
from src.shared.config.settings import get_settings
from src.shared.schemas.tender_ingestion import TenderIngestionInput

if TYPE_CHECKING:
	from browser_use.llm.base import BaseChatModel

SOURCE_NAME = 'Dubai eSupply'


class _VerificationLLM:
	"""Deterministic in-process LLM stub for persisted enrichment verification."""

	provider = 'anthropic_bedrock'

	def __init__(self, *, model: str):
		self.model = model
		self._attempts_by_title: dict[str, int] = {}

	async def ainvoke(self, messages, output_format=None, **kwargs):
		if output_format is None:
			raise ValueError('output_format is required for enrichment verification')

		payload = json.loads(messages[-1].content)
		title = str(payload['title'])
		attempt_count = self._attempts_by_title.get(title, 0) + 1
		self._attempts_by_title[title] = attempt_count

		if 'RETRY-ONCE' in title and attempt_count == 1:
			raise RuntimeError('simulated transient Bedrock verification failure')

		if 'SUCCESS' not in title and 'RETRY-ONCE' not in title:
			raise RuntimeError(f'unexpected verification title: {title}')

		return SimpleNamespace(
			completion=output_format(
				bullets=[
					f'Scope inferred from title: {title}.',
					f'Issuer is {payload["issuing_entity"]}.',
					'Timing cues come from the persisted listing fields.',
				]
			)
		)


def run() -> None:
	"""
	Perform a persisted verification of the recent-tender AI enrichment job.

	This script verifies:
	    - newly staged tenders are selected by the enrichment job
	    - a successful enrichment persists ai_summary and model metadata
	    - a transient failure is retried on a later job run
	    - exhausted tenders are not retried past the configured max attempts
	"""
	session_factory = get_session_factory()
	settings = get_settings()
	unique_marker = f'utw-enrich-job-{uuid4().hex}'
	since = datetime.now(UTC) - timedelta(minutes=5)

	with session_factory() as session:
		source = session.execute(select(Source).where(Source.name == SOURCE_NAME)).scalar_one_or_none()
		if source is None:
			raise ValueError(f"source '{SOURCE_NAME}' was not found; seed sources first")

		success_tender, _ = ingest_tender(
			session=session,
			payload=_build_tender_payload(
				source_id=source.id,
				source_url_suffix=f'{unique_marker}/success',
				title=f'{unique_marker} SUCCESS enterprise infrastructure procurement',
				tender_ref=f'VERIFY-ENRICH-SUCCESS-{uuid4().hex[:10].upper()}',
				dedupe_key=f'{unique_marker}-success',
			),
		)
		retry_tender, _ = ingest_tender(
			session=session,
			payload=_build_tender_payload(
				source_id=source.id,
				source_url_suffix=f'{unique_marker}/retry',
				title=f'{unique_marker} RETRY-ONCE secure platform procurement',
				tender_ref=f'VERIFY-ENRICH-RETRY-{uuid4().hex[:10].upper()}',
				dedupe_key=f'{unique_marker}-retry',
			),
		)
		exhausted_tender, _ = ingest_tender(
			session=session,
			payload=_build_tender_payload(
				source_id=source.id,
				source_url_suffix=f'{unique_marker}/exhausted',
				title=f'{unique_marker} exhausted tender verification',
				tender_ref=f'VERIFY-ENRICH-EXHAUSTED-{uuid4().hex[:10].upper()}',
				dedupe_key=f'{unique_marker}-exhausted',
			),
		)
		exhausted_tender.ai_summary_attempt_count = settings.ai_summary_max_attempts
		exhausted_tender.ai_summary_last_attempted_at = datetime.now(UTC)
		exhausted_tender.ai_summary_last_error = 'previous enrichment failure'
		session.commit()

		success_tender_id = success_tender.id
		retry_tender_id = retry_tender.id
		exhausted_tender_id = exhausted_tender.id

	verification_llm = _VerificationLLM(model='bedrock-verification-claude-sonnet')

	from src.ai import tender_enrichment_service as enrichment_module

	original_build_ai_runtime = enrichment_module.build_ai_runtime
	enrichment_module.build_ai_runtime = lambda _: AIRuntime(
		provider='bedrock_anthropic',
		llm=cast('BaseChatModel', verification_llm),
		fallback_llm=None,
	)
	try:
		first_result = run_enrich_recent_tenders_job(since=since)
		second_result = run_enrich_recent_tenders_job(since=since)
	finally:
		enrichment_module.build_ai_runtime = original_build_ai_runtime

	if first_result.attempted_count != 2:
		raise ValueError(f'expected first attempted_count=2, got {first_result.attempted_count}')
	if first_result.enriched_count != 1:
		raise ValueError(f'expected first enriched_count=1, got {first_result.enriched_count}')
	if first_result.failed_count != 1:
		raise ValueError(f'expected first failed_count=1, got {first_result.failed_count}')

	if second_result.attempted_count != 1:
		raise ValueError(f'expected second attempted_count=1, got {second_result.attempted_count}')
	if second_result.enriched_count != 1:
		raise ValueError(f'expected second enriched_count=1, got {second_result.enriched_count}')
	if second_result.failed_count != 0:
		raise ValueError(f'expected second failed_count=0, got {second_result.failed_count}')

	with session_factory() as session:
		success_tender = session.get(Tender, success_tender_id)
		retry_tender = session.get(Tender, retry_tender_id)
		exhausted_tender = session.get(Tender, exhausted_tender_id)

		if success_tender is None or retry_tender is None or exhausted_tender is None:
			raise ValueError('expected verification tenders to remain persisted after job runs')

		if success_tender.ai_summary is None:
			raise ValueError('expected success tender ai_summary to be populated')
		if success_tender.ai_summary_attempt_count != 1:
			raise ValueError('expected success tender ai_summary_attempt_count to remain 1 after rerun')
		if success_tender.ai_summary_model != verification_llm.model:
			raise ValueError('expected success tender ai_summary_model to match verification model')
		if success_tender.ai_summary_generated_at is None:
			raise ValueError('expected success tender ai_summary_generated_at to be populated')

		if retry_tender.ai_summary is None:
			raise ValueError('expected retry tender ai_summary to be populated on the second run')
		if retry_tender.ai_summary_attempt_count != 2:
			raise ValueError(f'expected retry tender ai_summary_attempt_count=2, got {retry_tender.ai_summary_attempt_count}')
		if retry_tender.ai_summary_last_error is not None:
			raise ValueError('expected retry tender ai_summary_last_error to be cleared after success')
		if retry_tender.ai_summary_generated_at is None:
			raise ValueError('expected retry tender ai_summary_generated_at to be populated')

		if exhausted_tender.ai_summary is not None:
			raise ValueError('expected exhausted tender ai_summary to remain empty')
		if exhausted_tender.ai_summary_attempt_count != settings.ai_summary_max_attempts:
			raise ValueError('expected exhausted tender attempt count to remain unchanged')
		if exhausted_tender.ai_summary_last_error != 'previous enrichment failure':
			raise ValueError('expected exhausted tender last_error to remain unchanged')

	print(f'verify_enrich_recent_tenders_job_since={since.isoformat()}')
	print(f'verify_enrich_recent_tenders_job_first_attempted_count={first_result.attempted_count}')
	print(f'verify_enrich_recent_tenders_job_first_enriched_count={first_result.enriched_count}')
	print(f'verify_enrich_recent_tenders_job_first_failed_count={first_result.failed_count}')
	print(f'verify_enrich_recent_tenders_job_second_attempted_count={second_result.attempted_count}')
	print(f'verify_enrich_recent_tenders_job_second_enriched_count={second_result.enriched_count}')
	print(f'verify_enrich_recent_tenders_job_success_tender_id={success_tender_id}')
	print(f'verify_enrich_recent_tenders_job_retry_tender_id={retry_tender_id}')
	print(f'verify_enrich_recent_tenders_job_exhausted_tender_id={exhausted_tender_id}')
	print(f'verify_enrich_recent_tenders_job_success_model={verification_llm.model}')


def _build_tender_payload(
	*,
	source_id,
	source_url_suffix: str,
	title: str,
	tender_ref: str,
	dedupe_key: str,
) -> TenderIngestionInput:
	now = datetime.now(UTC)
	return TenderIngestionInput(
		source_id=source_id,
		source_url=f'https://esupply.dubai.gov.ae/{source_url_suffix}',
		title=title,
		issuing_entity='Dubai eSupply',
		closing_date=now + timedelta(days=30),
		dedupe_key=dedupe_key,
		tender_ref=tender_ref,
		opening_date=now - timedelta(days=1),
		published_at=now - timedelta(days=2),
		category='Technology',
		ai_summary=None,
	)


if __name__ == '__main__':
	run()
