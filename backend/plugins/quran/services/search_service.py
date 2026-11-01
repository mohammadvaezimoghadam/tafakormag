"""
Search Engine Service for Official Quran Plugin.
Cross-database compatible search with diacritic-preserving authentic text highlighting.
"""
import re
from typing import List, Optional, Dict, Any, Union
from django.db.models import Q
from django.core.paginator import Paginator

from plugins.quran.services.normalizer import normalize_quran_text

# Regex fragment matching any Quranic diacritic or annotation character
DIACRITICS_AND_ANNOTATIONS = (
    r'[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06DC\u06DF-\u06E8\u06EA-\u06ED\u08D4-\u08E1\u08E3-\u08FF\u0640]*'
)

# Character variant mapping for authentic text regex building
CHAR_VARIANTS_REGEX = {
    'ا': r'[اأإآٱٲٳٵ]',
    'ی': r'[یيىئؽؾؿےۓۑې]',
    'ک': r'[کكګڬڭڮڱڲڳڴ]',
    'و': r'[وؤۄۅۆۇۈۉۊۋۏ]',
    'ه': r'[ههةۀۃھە]',
}


def build_highlight_regex_for_token(token: str) -> str:
    """
    Constructs a regular expression for a normalized token that matches
    any diacritical or orthographic variant in authentic Quranic text.
    """
    parts = []
    for char in token:
        variant = CHAR_VARIANTS_REGEX.get(char, re.escape(char))
        parts.append(f"{variant}{DIACRITICS_AND_ANNOTATIONS}")
    return "".join(parts)


def highlight_authentic_text(authentic_text: str, tokens: List[str]) -> str:
    """
    Highlights matching search tokens in authentic text with <mark> tags
    without stripping or corrupting original diacritics.
    """
    if not authentic_text or not tokens:
        return authentic_text

    # Clean tokens list and sort by length descending to match longer phrases first
    clean_tokens = [t.strip() for t in tokens if t and t.strip()]
    if not clean_tokens:
        return authentic_text

    sorted_tokens = sorted(set(clean_tokens), key=len, reverse=True)
    token_patterns = [build_highlight_regex_for_token(t) for t in sorted_tokens if t]
    if not token_patterns:
        return authentic_text

    try:
        combined_pattern = re.compile(f"({'|'.join(token_patterns)})", re.IGNORECASE)
        return combined_pattern.sub(r'<mark>\1</mark>', authentic_text)
    except re.error:
        # Fallback to simple escape matching if complex regex compilation fails
        escaped_tokens = [re.escape(t) for t in sorted_tokens]
        simple_pattern = re.compile(f"({'|'.join(escaped_tokens)})", re.IGNORECASE)
        return simple_pattern.sub(r'<mark>\1</mark>', authentic_text)


# Backward-compatibility alias
highlight_search_matches = highlight_authentic_text


def search_quran(
    query: str,
    edition_id: Optional[str] = None,
    language: Optional[str] = None,
    surah_number: Optional[int] = None,
    juz_number: Optional[int] = None,
    page: int = 1,
    page_size: int = 20,
    exact: bool = False,
    with_translation: Optional[str] = None,
    with_translation_edition_id: Optional[str] = None,
    with_translation_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Executes cross-database search over QuranAyah normalized_text.
    """
    from plugins.quran.models import QuranAyah, QuranEdition

    # Unify translation edition parameter
    trans_id = with_translation or with_translation_edition_id or with_translation_id

    if not query or not query.strip():
        return {
            "query": "",
            "normalized_query": "",
            "edition": edition_id or "",
            "count": 0,
            "total_matches": 0,
            "page": page,
            "page_size": page_size,
            "total_pages": 0,
            "results": [],
        }

    # Normalize query
    normalized_query = normalize_quran_text(query)
    tokens = [t for t in normalized_query.split() if t]

    if not tokens:
        return {
            "query": query,
            "normalized_query": normalized_query,
            "edition": edition_id or "",
            "count": 0,
            "total_matches": 0,
            "page": page,
            "page_size": page_size,
            "total_pages": 0,
            "results": [],
        }

    # Base QuerySet with optimizations
    qs = QuranAyah.objects.select_related('surah', 'edition')

    # Edition / Language scoping
    if edition_id:
        qs = qs.filter(edition_id=edition_id)
    elif language:
        qs = qs.filter(edition__language=language)
    else:
        # Default to default edition or 'quran-simple'
        default_edition = QuranEdition.objects.filter(is_default=True, type='quran').first()
        if default_edition:
            qs = qs.filter(edition=default_edition)
        else:
            first_quran = QuranEdition.objects.filter(type='quran').first()
            if first_quran:
                qs = qs.filter(edition=first_quran)
            else:
                qs = qs.filter(edition_id='quran-simple')

    # Structural filters
    if surah_number is not None:
        qs = qs.filter(surah_id=surah_number)
    if juz_number is not None:
        qs = qs.filter(juz=juz_number)

    # Search Query Construction
    is_exact_phrase = exact or (query.startswith('"') and query.endswith('"'))
    if is_exact_phrase:
        qs = qs.filter(normalized_text__contains=normalized_query)
    else:
        # Multi-word Token AND query
        q_filter = Q()
        for token in tokens:
            q_filter &= Q(normalized_text__contains=token)
        qs = qs.filter(q_filter)

    qs = qs.order_by('surah_id', 'number_in_surah')

    # Pagination
    page_size = max(1, min(page_size, 100))
    paginator = Paginator(qs, page_size)
    page_obj = paginator.get_page(page)

    # Fetch paired translations in a single bulk query if requested
    translations_map = {}
    if trans_id and page_obj.object_list:
        surah_ayah_pairs = [(a.surah_id, a.number_in_surah) for a in page_obj.object_list]
        q_trans = Q()
        for s_num, a_num in surah_ayah_pairs:
            q_trans |= Q(surah_id=s_num, number_in_surah=a_num)

        trans_qs = QuranAyah.objects.filter(
            edition_id=trans_id
        ).filter(q_trans).select_related('edition')

        for t in trans_qs:
            translations_map[(t.surah_id, t.number_in_surah)] = {
                "edition": t.edition_id,
                "edition_id": t.edition_id,
                "edition_name": t.edition.name,
                "name": t.edition.name,
                "author": t.edition.author,
                "text": t.text,
            }

    # Format Results
    results = []
    for ayah in page_obj.object_list:
        hl_text = highlight_authentic_text(
            ayah.text,
            [normalized_query] if is_exact_phrase else tokens
        )
        trans_data = translations_map.get((ayah.surah_id, ayah.number_in_surah))

        results.append({
            "id": ayah.id,
            "number": ayah.number,
            "global_number": ayah.number,
            "number_in_surah": ayah.number_in_surah,
            "surah": {
                "number": ayah.surah.number,
                "name": ayah.surah.name,
                "english_name": ayah.surah.english_name,
                "english_name_translation": ayah.surah.english_name_translation,
            },
            "surah_number": ayah.surah.number,
            "surah_name": ayah.surah.name,
            "surah_english_name": ayah.surah.english_name,
            "juz": ayah.juz,
            "page": ayah.page,
            "text": ayah.text,
            "normalized_text": ayah.normalized_text,
            "highlighted_text": hl_text,
            "audio_url": ayah.audio_url,
            "edition": {
                "identifier": ayah.edition.identifier,
                "name": ayah.edition.name,
                "language": ayah.edition.language,
                "type": ayah.edition.type,
            },
            "translation": trans_data,
        })

    active_edition_id = edition_id or (page_obj.object_list[0].edition_id if page_obj.object_list else "")

    return {
        "query": query,
        "normalized_query": normalized_query,
        "edition": active_edition_id,
        "edition_id": active_edition_id,
        "count": paginator.count,
        "total_matches": paginator.count,
        "page": page_obj.number,
        "page_size": page_size,
        "total_pages": paginator.num_pages,
        "results": results,
    }


# Convenience / compatibility aliases
search_quran_ayahs = search_quran


class QuranSearchService:
    """
    Compatibility wrapper class for Quran search service.
    """
    @classmethod
    def search(
        cls,
        query: str,
        edition_id: Optional[str] = None,
        language: Optional[str] = None,
        surah_number: Optional[int] = None,
        juz_number: Optional[int] = None,
        page: int = 1,
        page_size: int = 20,
        exact: bool = False,
        with_translation_id: Optional[str] = None,
        with_translation_edition_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        return search_quran(
            query=query,
            edition_id=edition_id,
            language=language,
            surah_number=surah_number,
            juz_number=juz_number,
            page=page,
            page_size=page_size,
            exact=exact,
            with_translation=with_translation_id or with_translation_edition_id,
        )
