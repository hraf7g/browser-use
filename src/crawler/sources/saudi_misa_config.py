from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SaudiMisaConfig:
    """
    Configuration inventory for the Saudi MISA procurements public page.

    Notes:
        - This source is the official MISA procurements page.
        - The strongest public structured surface is the official `المنافسات`
          wpDataTables table embedded on the page.
        - This slice is discovery-only: no normalization, quality, or DB writes.
    """

    source_name: str = "Saudi MISA Procurements"
    source_base_url: str = "https://misa.gov.sa"
    listing_url: str = "https://misa.gov.sa/ar/resources/procurements/"

    page_load_timeout_ms: int = 120_000
    default_wait_after_navigation_ms: int = 4_000
    min_jitter_ms: int = 3_000
    max_jitter_ms: int = 6_000

    page_body: str = "body"
    table_title: str = "#wdt-table-title-6"
    structured_table: str = "#wpdtSimpleTable-6"
    structured_rows: str = "#wpdtSimpleTable-6 tbody tr.wpdt-cell-row"

    expected_page_text_markers: tuple[str, ...] = (
        "المشتريات",
        "المنافسات",
        "اسم المنافسة",
        "الرقم المرجعي",
        "تاريخ الطرح",
        "آخر موعد لتقديم العروض",
        "حالة المنافسة عبر منصة اعتماد",
    )

    anti_bot_text_markers: tuple[str, ...] = (
        "access denied",
        "reference id",
        "support id",
        "verify you are human",
        "captcha",
        "request rejected",
    )


SAUDI_MISA_CONFIG = SaudiMisaConfig()
