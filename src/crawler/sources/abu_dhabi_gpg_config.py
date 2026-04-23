from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AbuDhabiGPGConfig:
    """
    Configuration inventory for the Abu Dhabi Government Procurement Gate source.

    Notes:
        - This file is configuration-only.
        - Selectors are intentionally narrow and deterministic.
        - Live verification happens in the crawler verification step.
        - The dedicated public-tenders routes are request-rejected from this environment,
          so this first discovery slice targets the official public homepage widget that
          exposes live active-tender cards and public detail links.
    """

    source_name: str = "Abu Dhabi GPG"
    source_base_url: str = "https://www.adgpg.gov.ae"
    listing_url: str = "https://www.adgpg.gov.ae/"

    page_load_timeout_ms: int = 120_000
    default_wait_after_navigation_ms: int = 5_000
    min_jitter_ms: int = 4_000
    max_jitter_ms: int = 8_000

    page_body: str = "body"
    page_title: str = "title"
    tender_cards: str = 'a[href*="/For-Suppliers/Public-Tenders?id="]'
    card_type_label: str = ".card-type-label"
    card_date: str = ".field-date"
    card_title: str = ".field-title"
    card_short_description: str = ".field-shortdescription"

    expected_page_text_markers: tuple[str, ...] = (
        "Abu Dhabi Government Procurement Gate",
        "Active Tenders",
        "Public Tenders",
        "VIEW ALL",
    )

    anti_bot_text_markers: tuple[str, ...] = (
        "request rejected",
        "support id",
        "access denied",
        "please consult with your administrator",
        "verify you are human",
        "captcha",
    )


ABU_DHABI_GPG_CONFIG = AbuDhabiGPGConfig()
