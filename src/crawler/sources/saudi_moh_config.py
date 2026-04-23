from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SaudiMohConfig:
    """
    Configuration inventory for the official Saudi MOH tenders public page.

    Notes:
        - The strongest official public surface currently verified is the MOH
          "Tenders and Procurement" page under the Ministry section.
        - This source-discovery slice is limited to public-page navigation and
          deterministic raw extraction only.
        - The page exposes visible structured tender rows in text-heavy tables,
          so extraction is intentionally driven from the rendered body text
          instead of brittle table selectors.
    """

    source_name: str = 'Saudi MOH Tenders'
    source_base_url: str = 'https://www.moh.gov.sa'
    listing_url: str = (
        'https://www.moh.gov.sa/en/Ministry/About/Pages/Tenders-and-Procurement.aspx'
    )

    page_load_timeout_ms: int = 90_000
    min_jitter_ms: int = 2_000
    max_jitter_ms: int = 4_000

    page_body: str = 'body'

    expected_page_text_markers: tuple[str, ...] = (
        'Tenders and Procurement',
        'Planned Tenders and procurement',
        'Archived Tenders and Procurement',
        'Submission deadline',
        'Expected launch Date',
    )

    anti_bot_text_markers: tuple[str, ...] = (
        'access denied',
        'reference id',
        'support id',
        'verify you are human',
        'captcha',
        'request rejected',
        'temporarily unavailable',
    )


SAUDI_MOH_CONFIG = SaudiMohConfig()
