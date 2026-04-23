from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.db.models.source import Source
from src.db.models.tender import Tender
from src.db.models.tender_match import TenderMatch
from src.db.models.user import User
from src.shared.industry_taxonomy import get_industry_label
from src.shared.schemas.email import EmailMessage
from src.shared.source_registry import MONITORED_COUNTRIES


class DailyBriefError(ValueError):
	"""Base class for daily brief build errors."""


class DailyBriefUserNotFoundError(DailyBriefError):
	"""Raised when the target user does not exist."""


class DailyBriefInactiveUserError(DailyBriefError):
	"""Raised when the target user is inactive."""


@dataclass(frozen=True)
class DailyBriefBuildResult:
	"""Deterministic daily brief payload for one user."""

	user_id: UUID
	match_ids: list[UUID]
	tender_ids: list[UUID]
	email_message: EmailMessage


def build_daily_brief_for_user(
	session: Session,
	*,
	user_id: UUID,
) -> DailyBriefBuildResult | None:
	"""
	Build a daily brief email for one user from unsent tender matches.

	Returns:
	    DailyBriefBuildResult | None:
	        - returns None when there are no unsent matches
	        - otherwise returns the rendered email payload and matched IDs

	Notes:
	    - This function does not send email.
	    - This function does not mark matches as sent.
	    - This function does not commit the transaction.
	"""
	user = session.get(User, user_id)
	if user is None:
		raise DailyBriefUserNotFoundError(f"user '{user_id}' was not found")

	if not user.is_active:
		raise DailyBriefInactiveUserError(f"user '{user_id}' is inactive")

	rows = session.execute(
		select(TenderMatch, Tender, Source)
		.join(Tender, Tender.id == TenderMatch.tender_id)
		.join(Source, Source.id == Tender.source_id)
		.where(
			TenderMatch.user_id == user_id,
			TenderMatch.sent_at.is_(None),
			TenderMatch.daily_brief_queued_at.is_(None),
		)
		.order_by(
			Tender.closing_date.asc().nulls_last(),
			Tender.created_at.desc(),
			Tender.id.asc(),
		)
	).all()

	if not rows:
		return None

	match_ids: list[UUID] = []
	tender_ids: list[UUID] = []
	rendered_items: list[str] = []

	for index, row in enumerate(rows, start=1):
		tender_match, tender, source = row
		match_ids.append(tender_match.id)
		tender_ids.append(tender.id)
		rendered_items.append(
			_render_tender_match_block(
				position=index,
				tender=tender,
				source=source,
				tender_match=tender_match,
			)
		)

	match_count = len(rows)
	subject = _build_subject(match_count)
	body_text = _build_body(rendered_items)

	return DailyBriefBuildResult(
		user_id=user.id,
		match_ids=match_ids,
		tender_ids=tender_ids,
		email_message=EmailMessage(
			to=user.email,
			subject=subject,
			body_text=body_text,
		),
	)


def _build_subject(match_count: int) -> str:
	"""Build a deterministic email subject line."""
	if match_count == 1:
		return 'UAE Tender Watch — 1 new tender match'
	return f'UAE Tender Watch — {match_count} new tender matches'


def _build_body(rendered_items: list[str]) -> str:
	"""Build the plain-text email body."""
	lines = [
		'Your latest UAE Tender Watch brief is ready.',
		'',
		'New matching tenders:',
		'',
		*rendered_items,
		'Open the dashboard to review, prioritize, and act on these opportunities.',
	]
	return '\n'.join(lines).strip()


def _render_tender_match_block(
	*,
	position: int,
	tender: Tender,
	source: Source,
	tender_match: TenderMatch,
) -> str:
	"""Render one matched tender entry for the daily brief."""
	matched_keywords = ', '.join(tender_match.matched_keywords or [])
	matched_countries = _render_matched_countries(list(tender_match.matched_country_codes or []))
	matched_industries = _render_matched_industries(list(tender_match.matched_industry_codes or []))
	lines = [
		f'{position}. {tender.title}',
		f'   Entity: {tender.issuing_entity}',
		f'   Source: {source.name}',
		(
			f'   Closing Date: {tender.closing_date.isoformat()}'
			if tender.closing_date is not None
			else '   Closing Date: Unknown'
		),
	]

	if tender.tender_ref:
		lines.append(f'   Reference: {tender.tender_ref}')

	if tender.category:
		lines.append(f'   Category: {tender.category}')

	if matched_keywords:
		lines.append(f'   Matched Keywords: {matched_keywords}')
	if matched_countries:
		lines.append(f'   Matched Countries: {matched_countries}')
	if matched_industries:
		lines.append(f'   Matched Industries: {matched_industries}')

	if tender.ai_summary:
		lines.append(f'   Summary: {tender.ai_summary}')

	lines.append(f'   Source Link: {tender.source_url}')
	lines.append('')

	return '\n'.join(lines)


def _render_matched_countries(country_codes: list[str]) -> str:
	"""Render persisted matched country codes into a compact display string."""
	if not country_codes:
		return ''

	country_name_by_code = {country.code: country.name for country in MONITORED_COUNTRIES}
	return ', '.join(country_name_by_code.get(country_code, country_code) for country_code in country_codes)


def _render_matched_industries(industry_codes: list[str]) -> str:
	"""Render persisted matched industry codes into a compact display string."""
	if not industry_codes:
		return ''

	return ', '.join(get_industry_label(industry_code) for industry_code in industry_codes)
