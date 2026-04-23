from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class OmanTenderBoardConfig:
    """
    Configuration inventory for the Oman Tender Board public tenders source.

    Notes:
        - This file is configuration-only.
        - Selectors are intentionally narrow and deterministic.
        - Live verification happens in the crawler verification step.
        - This source currently targets the official public "new tenders" view
          because it exposes real public tender rows with row-level detail handlers.
    """

    source_name: str = "Oman Tender Board"
    source_base_url: str = "https://etendering.tenderboard.gov.om"
    listing_url: str = "https://etendering.tenderboard.gov.om/product/publicDash?viewFlag=NewTenders"

    page_load_timeout_ms: int = 120_000
    default_wait_after_navigation_ms: int = 5_000
    min_jitter_ms: int = 4_000
    max_jitter_ms: int = 8_000

    page_body: str = "body"
    page_title: str = "title"
    listing_tables: str = "table"

    expected_page_text_markers: tuple[str, ...] = (
        "المناقصات المطروحة",
        "رقم المناقصة",
        "إسم المناقصة",
        "الجهة/الوحدة الحكومية",
        "نوع المناقصه",
        "Bid Closing Date",
    )

    anti_bot_text_markers: tuple[str, ...] = (
        "please enable javascript",
        "access denied",
        "reference id",
        "support id",
        "verify you are human",
        "captcha",
        "you are unable to access the requested page",
    )


OMAN_TENDER_BOARD_CONFIG = OmanTenderBoardConfig()
