from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DubaiESupplyConfig:
    """
    Centralized configuration and selector inventory for the Dubai eSupply source.

    Notes:
        - This file is configuration-only.
        - Selectors here are intentionally explicit and deterministic.
        - Live selector validation will happen in the crawler verification step.
        - No AI or heuristic extraction belongs in this file.
    """

    source_name: str = "Dubai eSupply"
    source_base_url: str = "https://esupply.dubai.gov.ae"
    listing_url: str = "https://esupply.dubai.gov.ae/esop/guest/go/public/opportunity/current"
    page_load_timeout_ms: int = 120_000
    default_wait_after_navigation_ms: int = 5_000
    min_jitter_ms: int = 5_000
    max_jitter_ms: int = 10_000

    # Listing page selectors
    opportunities_table: str = "table"
    table_rows: str = "table tbody tr"
    table_cells: str = "td"

    # Generic fallback content selectors
    page_body: str = "body"
    page_title: str = "title"

    # Known text anchors to help deterministic verification
    expected_page_text_markers: tuple[str, ...] = (
        "Opportunity",
        "Closing",
        "Tender",
    )


DUBAI_ESUPPLY_CONFIG = DubaiESupplyConfig()
