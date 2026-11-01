"""
Services package for the Official Quran Plugin.
"""
from .normalizer import (
    normalize_quran_text,
    strip_quranic_diacritics,
)
from .search_service import (
    search_quran,
    search_quran_ayahs,
    highlight_authentic_text,
    highlight_search_matches,
    build_highlight_regex_for_token,
    QuranSearchService,
)
from .formatter import (
    to_persian_digits,
    format_quran_markdown_reference,
    format_ayah_model_reference,
    QuranMarkdownFormatter,
)

__all__ = [
    'normalize_quran_text',
    'strip_quranic_diacritics',
    'search_quran',
    'search_quran_ayahs',
    'highlight_authentic_text',
    'highlight_search_matches',
    'build_highlight_regex_for_token',
    'QuranSearchService',
    'to_persian_digits',
    'format_quran_markdown_reference',
    'format_ayah_model_reference',
    'QuranMarkdownFormatter',
]
