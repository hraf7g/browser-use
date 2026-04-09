from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FederalMOFConfig:
    """
    Centralized configuration and selector inventory for the UAE Federal
    Ministry of Finance procurement source.

    Notes:
        - This file is configuration-only.
        - Selectors here are intentionally explicit and deterministic.
        - Live selector validation will happen in the crawler verification step.
        - No AI or heuristic extraction belongs in this file.
        - This source is Arabic/English aware from the start.
    """

    source_name: str = "Federal MOF"
    source_base_url: str = "https://mof.gov.ae"
    listing_url: str = (
        "https://mof.gov.ae/en/public-finance/government-procurement/"
        "current-business-opportunities/"
    )

    page_load_timeout_ms: int = 120_000
    default_wait_after_navigation_ms: int = 5_000
    min_jitter_ms: int = 5_000
    max_jitter_ms: int = 10_000

    # Content selectors
    page_body: str = "body"
    page_title: str = "title"

    # Generic public-content selectors for first-pass verification
    main_content: str = "main"
    article_links: str = "main a"
    tables: str = "table"
    table_rows: str = "table tbody tr"
    table_cells: str = "td"

    # Known text anchors to help deterministic verification
    expected_page_text_markers: tuple[str, ...] = (
        "Current Business Opportunities",
        "Digital Procurement Platform",
        "government procurement",
        "الفرص التجارية الحالية",
        "منصة المشتريات الرقمية",
    )


FEDERAL_MOF_CONFIG = FederalMOFConfig()
