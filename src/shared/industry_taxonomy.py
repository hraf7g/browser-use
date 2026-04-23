from __future__ import annotations

from dataclasses import dataclass

from src.shared.text.multilingual import build_multilingual_snapshot

IndustryCode = str


@dataclass(frozen=True)
class IndustryTaxonomyEntry:
	"""Canonical normalized industry entry used across profiles and tenders."""

	code: IndustryCode
	label: str
	aliases: tuple[str, ...]


INDUSTRY_TAXONOMY: tuple[IndustryTaxonomyEntry, ...] = (
	IndustryTaxonomyEntry(
		code='construction',
		label='Construction',
		aliases=(
			'construction',
			'civil works',
			'building',
			'infrastructure',
			'roads',
			'mep',
			'contracting',
			'engineering works',
			'مقاولات',
			'إنشاءات',
			'بنية تحتية',
		),
	),
	IndustryTaxonomyEntry(
		code='facilities',
		label='Facilities Management',
		aliases=(
			'facility management',
			'facilities',
			'maintenance',
			'cleaning',
			'janitorial',
			'landscaping',
			'hvac',
			'building services',
			'إدارة مرافق',
			'صيانة',
			'نظافة',
		),
	),
	IndustryTaxonomyEntry(
		code='technology',
		label='Technology',
		aliases=(
			'technology',
			'information technology',
			'ict',
			'software',
			'hardware',
			'cybersecurity',
			'network',
			'data center',
			'digital',
			'تقنية',
			'تقنية المعلومات',
			'أمن سيبراني',
		),
	),
	IndustryTaxonomyEntry(
		code='security',
		label='Security & Safety',
		aliases=(
			'security',
			'safety',
			'fire alarm',
			'cctv',
			'guarding',
			'access control',
			'منظومة أمن',
			'أمن',
			'سلامة',
			'مراقبة',
		),
	),
	IndustryTaxonomyEntry(
		code='healthcare',
		label='Healthcare',
		aliases=(
			'healthcare',
			'medical',
			'hospital',
			'clinic',
			'pharmaceutical',
			'lab',
			'medical equipment',
			'صحي',
			'طبي',
			'مستشفى',
		),
	),
	IndustryTaxonomyEntry(
		code='transport_logistics',
		label='Transport & Logistics',
		aliases=(
			'transport',
			'transportation',
			'logistics',
			'fleet',
			'shipping',
			'warehouse',
			'mobility',
			'ports',
			'aviation',
			'نقل',
			'لوجستيات',
			'شحن',
		),
	),
	IndustryTaxonomyEntry(
		code='energy_utilities',
		label='Energy & Utilities',
		aliases=(
			'energy',
			'utilities',
			'electricity',
			'power',
			'solar',
			'water',
			'wastewater',
			'oil',
			'gas',
			'طاقة',
			'كهرباء',
			'مياه',
		),
	),
	IndustryTaxonomyEntry(
		code='industrial',
		label='Industrial & Manufacturing',
		aliases=(
			'manufacturing',
			'industrial',
			'factory',
			'machinery',
			'plant',
			'production',
			'تصنيع',
			'صناعي',
			'معدات',
		),
	),
	IndustryTaxonomyEntry(
		code='professional_services',
		label='Professional Services',
		aliases=(
			'consulting',
			'professional services',
			'legal',
			'audit',
			'training',
			'advisory',
			'design',
			'project management',
			'استشارات',
			'خدمات مهنية',
			'تدريب',
		),
	),
)

INDUSTRY_CODE_SET: frozenset[str] = frozenset(entry.code for entry in INDUSTRY_TAXONOMY)
INDUSTRY_CODE_MAX_ITEMS = 10


def is_supported_industry_code(industry_code: str) -> bool:
	"""Return whether the given industry code exists in the canonical taxonomy."""
	return industry_code in INDUSTRY_CODE_SET


def classify_industry_codes(
	*,
	category: str | None,
	title: str,
	issuing_entity: str,
	ai_summary: str | None,
) -> list[IndustryCode]:
	"""Classify a tender into one or more normalized industries using persisted text fields."""
	search_text = ' '.join(
		part.strip() for part in (category, title, issuing_entity, ai_summary) if isinstance(part, str) and part.strip()
	)
	if not search_text:
		return []

	search_snapshot = build_multilingual_snapshot(search_text)
	search_tokens = set(search_snapshot.tokens)
	search_collapsed = search_snapshot.collapsed

	matched_codes: list[IndustryCode] = []
	for entry in INDUSTRY_TAXONOMY:
		if _entry_matches(entry=entry, search_tokens=search_tokens, search_collapsed=search_collapsed):
			matched_codes.append(entry.code)

	return matched_codes


def classify_profile_industry_codes(
	*,
	industry_label: str | None,
	keywords: list[str],
) -> list[IndustryCode]:
	"""Classify a profile into normalized industries using display label and saved keywords."""
	return classify_industry_codes(
		category=industry_label,
		title=' '.join(keywords),
		issuing_entity='',
		ai_summary=None,
	)


def get_industry_label(industry_code: IndustryCode) -> str:
	"""Return the display label for a normalized industry code."""
	for entry in INDUSTRY_TAXONOMY:
		if entry.code == industry_code:
			return entry.label
	return industry_code


def _entry_matches(
	*,
	entry: IndustryTaxonomyEntry,
	search_tokens: set[str],
	search_collapsed: str,
) -> bool:
	for alias in entry.aliases:
		alias_snapshot = build_multilingual_snapshot(alias)
		if not alias_snapshot.collapsed:
			continue

		if alias_snapshot.tokens and all(token in search_tokens for token in alias_snapshot.tokens):
			return True

	return False
