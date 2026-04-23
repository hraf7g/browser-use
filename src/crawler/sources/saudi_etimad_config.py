from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SaudiEtimadConfig:
    """
    Configuration inventory for the Saudi Etimad public competitions source.

    Notes:
        - This file is configuration-only.
        - Selectors are intentionally narrow and deterministic.
        - Live verification happens in the crawler verification step.
        - This source is Arabic-first and may present anti-bot challenges.
    """

    source_name: str = "Saudi Etimad"
    source_base_url: str = "https://tenders.etimad.sa"
    listing_url: str = "https://tenders.etimad.sa/Tender/"

    page_load_timeout_ms: int = 120_000
    default_wait_after_navigation_ms: int = 6_000
    min_jitter_ms: int = 5_000
    max_jitter_ms: int = 9_000

    page_body: str = "body"
    page_title: str = "title"
    detail_links: str = 'a[href*="DetailsForVisitor"]'

    expected_page_text_markers: tuple[str, ...] = (
        "المنافسات",
        "الرقم المرجعي للمنافسة",
        "حالة المنافسة",
        "الجهة الحكوميه",
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
        "التفاصيل",
        "عرض",
        "details",
        "view",
    )


SAUDI_ETIMAD_CONFIG = SaudiEtimadConfig()
