from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Literal

SourceHealthStatus = Literal['healthy', 'degraded']
SourceLifecycle = Literal['live', 'in_progress', 'disabled']


@dataclass(frozen=True)
class MonitoringCountry:
	"""Canonical country metadata used across monitored sources and profiles."""

	code: str
	name: str


@dataclass(frozen=True)
class SourceRegistryEntry:
	"""Canonical definition for one monitored source."""

	name: str
	base_url: str
	country_code: str
	country_name: str
	lifecycle: SourceLifecycle
	status: SourceHealthStatus
	notes: str


SOURCE_REGISTRY: tuple[SourceRegistryEntry, ...] = (
	SourceRegistryEntry(
		name='Dubai eSupply',
		base_url='https://esupply.dubai.gov.ae',
		country_code='AE',
		country_name='United Arab Emirates',
		lifecycle='live',
		status='healthy',
		notes=('Seeded v1 source; verification status managed operationally outside seed data.'),
	),
	SourceRegistryEntry(
		name='Federal MOF',
		base_url='https://mprocurement.mof.gov.ae/',
		country_code='AE',
		country_name='United Arab Emirates',
		lifecycle='live',
		status='healthy',
		notes=('Seeded v1 source; public listing accessibility must be validated separately.'),
	),
	SourceRegistryEntry(
		name='Saudi Etimad',
		base_url='https://tenders.etimad.sa',
		country_code='SA',
		country_name='Saudi Arabia',
		lifecycle='live',
		status='healthy',
		notes=('Seeded v1 source; public listing verification is deterministic but listing-only records may require review.'),
	),
	SourceRegistryEntry(
		name='Saudi MISA Procurements',
		base_url='https://misa.gov.sa',
		country_code='SA',
		country_name='Saudi Arabia',
		lifecycle='live',
		status='healthy',
		notes=(
			'Seeded v1 source; official competitions-table verification is '
			'deterministic while Etimad visitor detail accessibility is not '
			'required for the stronger table-driven path.'
		),
	),
	SourceRegistryEntry(
		name='Oman Tender Board',
		base_url='https://etendering.tenderboard.gov.om',
		country_code='OM',
		country_name='Oman',
		lifecycle='live',
		status='healthy',
		notes=(
			'Seeded v1 source; public NewTenders listing verification is '
			'deterministic while detail-page and run-service behavior are '
			'validated separately.'
		),
	),
	SourceRegistryEntry(
		name='Abu Dhabi GPG',
		base_url='https://www.adgpg.gov.ae/',
		country_code='AE',
		country_name='United Arab Emirates',
		lifecycle='live',
		status='healthy',
		notes=(
			'Seeded v1 source; homepage-widget discovery and public detail-page '
			'enrichment are validated separately before run-service integration.'
		),
	),
	SourceRegistryEntry(
		name='Bahrain Tender Board',
		base_url='https://etendering.tenderboard.gov.bh',
		country_code='BH',
		country_name='Bahrain',
		lifecycle='live',
		status='healthy',
		notes=(
			'Seeded source; dashboard crawl plus detail-page enrichment are '
			'validated separately before and during run-service integration.'
		),
	),
	SourceRegistryEntry(
		name='Qatar Monaqasat',
		base_url='https://monaqasat.mof.gov.qa',
		country_code='QA',
		country_name='Qatar',
		lifecycle='live',
		status='healthy',
		notes=(
			'Seeded source; public technically-opened listing plus detail-page '
			'enrichment are validated separately before and during run-service integration.'
		),
	),
)

MONITORED_SOURCE_NAMES: tuple[str, ...] = tuple(entry.name for entry in SOURCE_REGISTRY)

MONITORED_SOURCE_ORDER: dict[str, int] = {source_name: index for index, source_name in enumerate(MONITORED_SOURCE_NAMES)}

MONITORED_COUNTRIES: tuple[MonitoringCountry, ...] = tuple(
	MonitoringCountry(code=country_code, name=country_name)
	for country_code, country_name in {entry.country_code: entry.country_name for entry in SOURCE_REGISTRY}.items()
)
MONITORED_COUNTRY_CODES: tuple[str, ...] = tuple(country.code for country in MONITORED_COUNTRIES)


def is_supported_source_name(source_name: str) -> bool:
	"""Return whether a source name belongs to the canonical registry."""
	return source_name in MONITORED_SOURCE_ORDER


def supported_source_names_text() -> str:
	"""Return the canonical source names for diagnostics."""
	return ', '.join(f"'{name}'" for name in MONITORED_SOURCE_NAMES)


def normalize_source_health_status(status: str | None) -> SourceHealthStatus:
	"""Map persisted or legacy source health values into the canonical vocabulary."""
	if (status or '').strip().lower() == 'healthy':
		return 'healthy'
	return 'degraded'


def is_supported_country_code(country_code: str) -> bool:
	"""Return whether a country code belongs to the monitored source registry."""
	return country_code in MONITORED_COUNTRY_CODES


def build_seed_source_rows() -> tuple[dict[str, str], ...]:
	"""Return canonical seed rows derived from the registry."""
	return tuple(asdict(entry) for entry in SOURCE_REGISTRY)
