from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Literal

ARABIC_DIACRITICS_PATTERN = re.compile(
    "["
    # Arabic combining marks / tashkil
    "\u0610-\u061A"
    "\u064B-\u065F"
    "\u0670"
    "\u06D6-\u06ED"
    "]"
)

MULTISPACE_PATTERN = re.compile(r"\s+")
TOKEN_PATTERN = re.compile(r"[A-Za-z0-9]+|[\u0600-\u06FF0-9]+", re.UNICODE)
ARABIC_LETTER_PATTERN = re.compile(r"[\u0600-\u06FF]")
LATIN_LETTER_PATTERN = re.compile(r"[A-Za-z]")

@dataclass(frozen=True)
class MultilingualTextSnapshot:
    """
    Deterministic normalized view of a multilingual text value.

    Notes:
        - raw text is preserved separately by callers
        - this object is for matching/search/quality logic only
        - no translation or AI enrichment occurs here
    """
    raw: str
    normalized: str
    collapsed: str
    script: Literal["arabic", "latin", "mixed", "unknown"]
    tokens: tuple[str, ...]

def build_multilingual_snapshot(value: str | None) -> MultilingualTextSnapshot:
    """
    Build a deterministic normalized snapshot for Arabic/English-aware backend use.

    Pipeline:
    1. coerce None to empty string
    2. Unicode normalize with NFKC
    3. normalize Arabic-specific presentation noise conservatively
    4. casefold for Latin matching
    5. collapse whitespace
    6. detect dominant script class
    7. tokenize deterministically

    This function is intentionally conservative:
        - preserves semantic text structure
        - does not translate
        - does not rewrite source meaning
        - does not guess language
    """
    raw = "" if value is None else value
    if not isinstance(raw, str):
        raise TypeError("value must be a string or None")

    unicode_normalized = unicodedata.normalize("NFKC", raw)
    arabic_normalized = _normalize_arabic_for_matching(unicode_normalized)
    casefolded = arabic_normalized.casefold()
    collapsed = collapse_whitespace(casefolded)
    script = detect_script(collapsed)
    tokens = tokenize_multilingual(collapsed)

    return MultilingualTextSnapshot(
        raw=raw,
        normalized=casefolded,
        collapsed=collapsed,
        script=script,
        tokens=tokens,
    )

def normalize_multilingual_text(value: str | None) -> str:
    """Return a collapsed deterministic Arabic/English matching string."""
    return build_multilingual_snapshot(value).collapsed

def collapse_whitespace(value: str) -> str:
    """Trim and collapse internal whitespace to a single ASCII space."""
    if not isinstance(value, str):
        raise TypeError("value must be a string")
    return MULTISPACE_PATTERN.sub(" ", value.strip())

def tokenize_multilingual(value: str) -> tuple[str, ...]:
    """
    Tokenize Arabic/English text deterministically.

    Notes:
        - preserves token order
        - removes empty tokens
        - intended for matching/search/quality logic, not linguistic parsing
    """
    if not isinstance(value, str):
        raise TypeError("value must be a string")

    tokens = [match.group(0) for match in TOKEN_PATTERN.finditer(value)]
    return tuple(token for token in tokens if token)

def detect_script(value: str | None) -> Literal["arabic", "latin", "mixed", "unknown"]:
    """
    Classify script presence in a conservative way.

    Returns:
        - arabic: Arabic letters only
        - latin: Latin letters only
        - mixed: both Arabic and Latin letters appear
        - unknown: neither Arabic nor Latin letters appear
    """
    if value is None:
        return "unknown"
    if not isinstance(value, str):
        raise TypeError("value must be a string or None")

    has_arabic = ARABIC_LETTER_PATTERN.search(value) is not None
    has_latin = LATIN_LETTER_PATTERN.search(value) is not None

    if has_arabic and has_latin:
        return "mixed"
    if has_arabic:
        return "arabic"
    if has_latin:
        return "latin"

    return "unknown"

def contains_token(haystack: str | None, needle: str | None) -> bool:
    """
    Deterministic token-aware containment check after multilingual normalization.
    This avoids raw substring checks on unnormalized Arabic/English text.
    """
    haystack_tokens = set(tokenize_multilingual(normalize_multilingual_text(haystack)))
    needle_tokens = tokenize_multilingual(normalize_multilingual_text(needle))

    if not needle_tokens:
        return False

    return all(token in haystack_tokens for token in needle_tokens)

def _normalize_arabic_for_matching(value: str) -> str:
    """
    Apply conservative Arabic normalization for backend matching.

    Included:
        - remove Arabic diacritics / tashkeel
        - remove tatweel
        - normalize Arabic/Persian letter variants that are safe for matching:
          أ, إ, آ -> ا
          ى -> ي
          ي/ى Persian/Arabic Yeh variants -> ي
          ك/ک -> ك

        ؤ and ئ are preserved to avoid overly aggressive conflation
        ة is preserved to avoid semantic over-flattening

    Excluded on purpose:
        - no translation
        - no stemming
        - no lemmatization
        - no AI rewriting
    """
    without_diacritics = ARABIC_DIACRITICS_PATTERN.sub("", value)
    without_tatweel = without_diacritics.replace("ـ", "")

    translation_table = str.maketrans(
        {
            "أ": "ا",
            "إ": "ا",
            "آ": "ا",
            "ٱ": "ا",
            "ى": "ي",
            "ی": "ي",
            "ې": "ي",
            "ک": "ك",
        }
    )
    return without_tatweel.translate(translation_table)
