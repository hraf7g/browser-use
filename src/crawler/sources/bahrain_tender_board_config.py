from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BahrainTenderBoardConfig:
    """
    Configuration inventory for the Bahrain Tender Board public dashboard source.

    Notes:
        - This file is configuration-only.
        - Selectors are intentionally narrow and deterministic.
        - Live verification happens in the crawler verification step.
        - This source currently targets the official Bahrain eTendering public
          dashboard because it exposes a stable public published-tenders table.
    """

    source_name: str = "Bahrain Tender Board"
    source_base_url: str = "https://etendering.tenderboard.gov.bh"
    listing_url: str = "https://etendering.tenderboard.gov.bh/Tenders/publicDash"

    page_load_timeout_ms: int = 120_000
    default_wait_after_navigation_ms: int = 5_000
    min_jitter_ms: int = 4_000
    max_jitter_ms: int = 8_000

    page_body: str = "body"
    page_title: str = "title"
    listing_tables: str = "table"

    expected_page_text_markers: tuple[str, ...] = (
        "Welcome To Bahrain Tender Board",
        "Published (",
        "Tender (PA Ref.) No.",
        "Purchasing Authority",
        "CLICK HERE TO VIEW MORE TENDERS",
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
        "click here to view more tenders",
        "details",
        "view",
    )


BAHRAIN_TENDER_BOARD_CONFIG = BahrainTenderBoardConfig()
