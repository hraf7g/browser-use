from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from datetime import UTC, datetime

from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select
from sqlalchemy.orm import Session

from browser_use.llm.messages import BaseMessage, SystemMessage, UserMessage
from src.ai.control_service import resolve_ai_enrichment_policy
from src.ai.factory import AIRuntime, build_ai_runtime
from src.ai.usage_budget_service import (
	AIDailyBudgetExceededError,
	record_ai_invoke_completion,
	record_ai_invoke_failure,
	reserve_ai_budget_for_messages,
)
from src.db.models.tender import Tender
from src.ingestion.tender_derived_fields import (
	build_primary_industry_code,
	build_tender_industry_codes,
	build_tender_search_text,
)
from src.shared.config.settings import Settings, get_settings
from src.shared.logging.logger import get_logger

AI_SUMMARY_ERROR_MAX_LENGTH = 2000
logger = get_logger(__name__)


class TenderSummaryOutput(BaseModel):
	"""Structured Bedrock response for a short tender summary."""

	bullets: list[str] = Field(min_length=3, max_length=3)

	@field_validator('bullets')
	@classmethod
	def validate_bullets(cls, value: list[str]) -> list[str]:
		normalized: list[str] = []
		for bullet in value:
			cleaned = bullet.strip().lstrip('-').lstrip('*').strip()
			if not cleaned:
				raise ValueError('summary bullets must not be empty')
			if len(cleaned) > 220:
				raise ValueError('summary bullets must be concise')
			normalized.append(cleaned)
		return normalized


@dataclass(frozen=True)
class TenderEnrichmentResult:
	"""Structured result for one enrichment batch."""

	attempted_count: int
	enriched_count: int
	failed_count: int
	skipped_count: int


def enrich_tenders_updated_since(
	session: Session,
	*,
	since: datetime,
	settings: Settings | None = None,
) -> TenderEnrichmentResult:
	"""
	Enrich recent tenders with AI summaries using the app-owned runtime contract.

	Notes:
		- This function does not commit the transaction.
		- When AI is disabled it returns a zero-result without raising.
		- Repeated failures are bounded by ai_summary_max_attempts.
	"""
	cfg = settings or get_settings()
	policy = resolve_ai_enrichment_policy(
		session,
		settings=cfg,
	)
	if not policy.enabled:
		logger.warning(
			'tender_ai_enrichment_skipped '
			f'reason={policy.reason} '
			f'ai_provider={policy.ai_provider} '
			f'ai_enrichment_enabled={policy.ai_enrichment_enabled} '
			f'emergency_stop_enabled={policy.emergency_stop_enabled}'
		)
		return TenderEnrichmentResult(
			attempted_count=0,
			enriched_count=0,
			failed_count=0,
			skipped_count=0,
		)
	runtime = build_ai_runtime(cfg)
	if runtime.provider == 'disabled':
		logger.info('tender_ai_enrichment_skipped ai_provider=disabled')
		return TenderEnrichmentResult(
			attempted_count=0,
			enriched_count=0,
			failed_count=0,
			skipped_count=0,
		)

	tenders = (
		session.execute(
			select(Tender)
			.where(
				Tender.updated_at >= since,
				Tender.ai_summary.is_(None),
				Tender.ai_summary_attempt_count < cfg.ai_summary_max_attempts,
			)
			.order_by(Tender.updated_at.asc(), Tender.id.asc())
			.limit(policy.effective_batch_size)
		)
		.scalars()
		.all()
	)

	if not tenders:
		logger.info(
			'tender_ai_enrichment_noop '
			f'since={since.isoformat()} '
			f'batch_size={policy.effective_batch_size} '
			f'max_attempts={cfg.ai_summary_max_attempts}'
		)
		return TenderEnrichmentResult(
			attempted_count=0,
			enriched_count=0,
			failed_count=0,
			skipped_count=0,
		)

	attempted_count = 0
	enriched_count = 0
	failed_count = 0
	skipped_count = 0

	for index, tender in enumerate(tenders):
		if tender.ai_summary:
			skipped_count += 1
			continue

		try:
			_apply_tender_summary(
				session=session,
				tender=tender,
				runtime=runtime,
				settings=cfg,
			)
			attempted_count += 1
			enriched_count += 1
		except AIDailyBudgetExceededError as exc:
			skipped_count += len(tenders) - index
			logger.warning(
				f'tender_ai_enrichment_budget_blocked reason={str(exc)!r} skipped_remaining_count={len(tenders) - index}'
			)
			break
		except Exception as exc:
			attempted_count += 1
			failed_count += 1
			_record_enrichment_failure(tender=tender, error=exc)
			logger.warning(
				'tender_ai_enrichment_failed '
				f'tender_id={tender.id} '
				f'attempt_count={tender.ai_summary_attempt_count} '
				f'error={_truncate_error(str(exc))!r}'
			)

	session.flush()
	logger.info(
		'tender_ai_enrichment_completed '
		f'since={since.isoformat()} '
		f'attempted_count={attempted_count} '
		f'enriched_count={enriched_count} '
		f'failed_count={failed_count} '
		f'skipped_count={skipped_count}'
	)
	return TenderEnrichmentResult(
		attempted_count=attempted_count,
		enriched_count=enriched_count,
		failed_count=failed_count,
		skipped_count=skipped_count,
	)


def _apply_tender_summary(
	*,
	session: Session,
	tender: Tender,
	runtime: AIRuntime,
	settings: Settings,
) -> None:
	previous_attempt_count = tender.ai_summary_attempt_count
	previous_last_attempted_at = tender.ai_summary_last_attempted_at
	tender.ai_summary_attempt_count += 1
	tender.ai_summary_last_attempted_at = datetime.now(UTC)
	try:
		summary_text, model_name = asyncio.run(
			_generate_tender_summary(
				session=session,
				tender=tender,
				runtime=runtime,
				settings=settings,
			)
		)
	except AIDailyBudgetExceededError:
		tender.ai_summary_attempt_count = previous_attempt_count
		tender.ai_summary_last_attempted_at = previous_last_attempted_at
		raise

	tender.ai_summary = summary_text
	tender.ai_summary_generated_at = datetime.now(UTC)
	tender.ai_summary_last_error = None
	tender.ai_summary_model = model_name

	industry_codes = build_tender_industry_codes(
		category=tender.category,
		title=tender.title,
		issuing_entity=tender.issuing_entity,
		ai_summary=tender.ai_summary,
	)
	tender.industry_codes = industry_codes
	tender.primary_industry_code = build_primary_industry_code(industry_codes)
	tender.search_text = build_tender_search_text(
		title=tender.title,
		issuing_entity=tender.issuing_entity,
		category=tender.category,
		ai_summary=tender.ai_summary,
		tender_ref=tender.tender_ref,
	)


def _record_enrichment_failure(*, tender: Tender, error: Exception) -> None:
	tender.ai_summary_last_error = _truncate_error(str(error))


async def _generate_tender_summary(
	*,
	session: Session,
	tender: Tender,
	runtime: AIRuntime,
	settings: Settings,
) -> tuple[str, str]:
	messages: list[BaseMessage] = [
		SystemMessage(
			content=(
				'You summarize public tender listings using only the provided source fields. '
				'Do not invent facts, budgets, eligibility rules, or timelines that are not stated. '
				'Return exactly three concise bullets covering scope, buyer/context, and timing or category cues.'
			)
		),
		UserMessage(
			content=json.dumps(
				{
					'title': tender.title,
					'issuing_entity': tender.issuing_entity,
					'closing_date': None if tender.closing_date is None else tender.closing_date.isoformat(),
					'opening_date': None if tender.opening_date is None else tender.opening_date.isoformat(),
					'published_at': None if tender.published_at is None else tender.published_at.isoformat(),
					'category': tender.category,
					'tender_ref': tender.tender_ref,
					'source_url': tender.source_url,
				},
				ensure_ascii=False,
				sort_keys=True,
			)
		),
	]

	primary_llm = runtime.llm
	if primary_llm is None:
		raise RuntimeError('AI runtime did not provide a primary llm')

	completion = None
	model_name = str(getattr(primary_llm, 'model', ''))

	try:
		completion = await _invoke_summary_llm(
			session=session,
			llm=primary_llm,
			messages=messages,
			settings=settings,
		)
	except Exception:
		if runtime.fallback_llm is None:
			raise
		fallback_llm = runtime.fallback_llm
		model_name = str(getattr(fallback_llm, 'model', ''))
		completion = await _invoke_summary_llm(
			session=session,
			llm=fallback_llm,
			messages=messages,
			settings=settings,
		)

	output = completion.completion
	summary_text = '\n'.join(f'• {bullet}' for bullet in output.bullets)
	return summary_text, model_name


async def _invoke_summary_llm(
	*,
	session: Session,
	llm,
	messages: list[BaseMessage],
	settings: Settings,
):
	model_id = str(getattr(llm, 'model', ''))
	reservation = reserve_ai_budget_for_messages(
		session,
		model_id=model_id,
		messages=messages,
		settings=settings,
	)
	try:
		completion = await llm.ainvoke(messages, output_format=TenderSummaryOutput)
	except Exception as exc:
		record_ai_invoke_failure(
			session,
			error=exc,
			model_id=model_id,
			usage_date=reservation.usage_date,
		)
		raise

	if completion.usage is not None:
		record_ai_invoke_completion(
			session,
			usage=completion.usage,
			model_id=model_id,
			usage_date=reservation.usage_date,
		)
	return completion


def _truncate_error(value: str) -> str:
	cleaned = value.strip()
	if len(cleaned) <= AI_SUMMARY_ERROR_MAX_LENGTH:
		return cleaned
	return cleaned[:AI_SUMMARY_ERROR_MAX_LENGTH]
