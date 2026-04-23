from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class QatarMonaqasatConfig:
    """
    Configuration inventory for the Qatar Monaqasat public tenders source.

    Notes:
        - This file is configuration-only.
        - Selectors are intentionally narrow and deterministic.
        - Live verification happens in the crawler verification step.
        - This source currently targets the official public "Technically Opened Tenders"
          listing because it exposes stable public tender cards with detail links.
    """

    source_name: str = "Qatar Monaqasat"
    source_base_url: str = "https://monaqasat.mof.gov.qa"
    listing_url: str = (
        "https://monaqasat.mof.gov.qa/TendersOnlineServices/TechnicallyOpenedTenders/63"
    )

    page_load_timeout_ms: int = 120_000
    default_wait_after_navigation_ms: int = 5_000
    min_jitter_ms: int = 4_000
    max_jitter_ms: int = 8_000

    page_body: str = "body"
    page_title: str = "title"
    detail_links: str = 'a[href*="/TendersOnlineServices/TenderDetails/"], a[href*="/TenderDetails/"]'

    expected_page_text_markers: tuple[str, ...] = (
        "Technically Opened Tenders",
        "Publish date",
        "Ministry",
        "Type",
        "Total number of records",
    )

    anti_bot_text_markers: tuple[str, ...] = (
        "please enable javascript",
        "access denied",
        "reference id",
        "support id",
        "verify you are human",
        "captcha",
    )

    generic_link_labels: tuple[str, ...] = (
        "companies",
        "report",
        "details",
        "view",
    )


QATAR_MONAQASAT_CONFIG = QatarMonaqasatConfig()
