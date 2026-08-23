"""
Markdown Reference Formatter Service for Official Quran Plugin.
Generates beautiful, standard Markdown blockquotes for the Frontend Composer Action.
"""
from typing import List, Optional, Union, Any

PERSIAN_DIGITS_TABLE = str.maketrans('0123456789', '۰۱۲۳۴۵۶۷۸۹')


def to_persian_digits(val: Union[int, str]) -> str:
    """Converts ASCII digits in string or int to Persian digits."""
    return str(val).translate(PERSIAN_DIGITS_TABLE)


def format_quran_markdown_reference(
    surah: Any = None,
    ayah_from: int = 1,
    ayah_to: Optional[int] = None,
    arabic_ayahs: Optional[List[Any]] = None,
    translation_ayahs: Optional[List[Any]] = None,
    translation_edition_name: str = "",
    lang: str = "fa",
    # Alternative/legacy keyword arguments
    surah_name: Optional[str] = None,
    surah_english_name: Optional[str] = None,
    surah_number: Optional[int] = None,
    arabic_texts: Optional[List[str]] = None,
    translation_texts: Optional[List[str]] = None,
    translation_name: Optional[str] = None,
) -> str:
    """
    Constructs a standard Markdown blockquote citation for Quranic verses.
    
    Compatible with both Model instances (arabic_ayahs) and raw strings (arabic_texts),
    and accepts either a QuranSurah instance (surah) or explicit surah parameters.
    """
    # Resolve Surah metadata
    s_number = surah_number
    s_name = surah_name
    s_english_name = surah_english_name

    if surah is not None:
        if hasattr(surah, 'number'):
            s_number = surah.number
        elif isinstance(surah, dict):
            s_number = s_number or surah.get('number')
            s_name = s_name or surah.get('name')
            s_english_name = s_english_name or surah.get('english_name')

        if hasattr(surah, 'name') and not s_name:
            s_name = surah.name
        if hasattr(surah, 'english_name') and not s_english_name:
            s_english_name = surah.english_name

    s_number = s_number or 1
    s_name = s_name or f"سوره {s_number}"
    s_english_name = s_english_name or f"Surah {s_number}"

    # Resolve ayah range
    ayah_to = ayah_to or ayah_from

    # Resolve Arabic text strings
    ar_texts = []
    if arabic_ayahs:
        for a in arabic_ayahs:
            if hasattr(a, 'text'):
                ar_texts.append(a.text)
            elif isinstance(a, dict):
                ar_texts.append(a.get('text', ''))
            elif isinstance(a, str):
                ar_texts.append(a)
    elif arabic_texts:
        ar_texts = list(arabic_texts)

    if not ar_texts:
        return ""

    # Resolve Translation text strings
    tr_texts = []
    if translation_ayahs:
        for t in translation_ayahs:
            if hasattr(t, 'text'):
                tr_texts.append(t.text)
            elif isinstance(t, dict):
                tr_texts.append(t.get('text', ''))
            elif isinstance(t, str):
                tr_texts.append(t)
    elif translation_texts:
        tr_texts = list(translation_texts)

    trans_name = translation_edition_name or translation_name or ""

    is_range = (ayah_to > ayah_from) or (len(ar_texts) > 1)

    # 1. Format Arabic text
    if is_range:
        arabic_segments = []
        for i, text in enumerate(ar_texts):
            current_ayah_num = ayah_from + i
            num_str = to_persian_digits(current_ayah_num) if lang == "fa" else str(current_ayah_num)
            clean_t = text.strip()
            if not clean_t.endswith('۝') and not any(c in clean_t[-3:] for c in '۝۞۩'):
                arabic_segments.append(f"{clean_t} ۝{num_str}")
            else:
                arabic_segments.append(clean_t)
        arabic_content = " ".join(arabic_segments)
    else:
        arabic_content = ar_texts[0].strip()

    lines = [f"> ﴿{arabic_content}﴾"]

    # 2. Format Translation text
    if tr_texts:
        if is_range:
            trans_segments = []
            for i, text in enumerate(tr_texts):
                current_ayah_num = ayah_from + i
                num_str = to_persian_digits(current_ayah_num) if lang == "fa" else str(current_ayah_num)
                trans_segments.append(f"{text.strip()} ({num_str})")
            translation_content = " ".join(trans_segments)
        else:
            translation_content = tr_texts[0].strip()

        lines.append(f"> *{translation_content}*")

    # 3. Format Citation line
    if is_range:
        ref_coord = f"{s_number}:{ayah_from}-{ayah_to}"
    else:
        ref_coord = f"{s_number}:{ayah_from}"

    if lang == "fa":
        coord_fa = to_persian_digits(ref_coord)
        citation = f"— **سوره {s_name} ({coord_fa})**"
        if trans_name:
            citation += f" — *{trans_name}*"
    else:
        citation = f"— **Surah {s_english_name} ({ref_coord})**"
        if trans_name:
            citation += f" — *{trans_name}*"

    lines.append(f"> {citation}")

    return "\n".join(lines)


def format_ayah_model_reference(
    ayah_instances: List[Any],
    translation_instances: Optional[List[Any]] = None,
    translation_name: str = "",
    lang: str = "fa",
) -> str:
    """
    Convenience helper that extracts attributes from QuranAyah model instances
    and formats the Markdown reference blockquote.
    """
    if not ayah_instances:
        return ""

    first_ayah = ayah_instances[0]
    surah = first_ayah.surah
    ayah_from = first_ayah.number_in_surah
    ayah_to = ayah_instances[-1].number_in_surah

    trans_name = translation_name
    if translation_instances and not trans_name:
        first_trans = translation_instances[0]
        if hasattr(first_trans, 'edition') and hasattr(first_trans.edition, 'name'):
            trans_name = first_trans.edition.name

    return format_quran_markdown_reference(
        surah=surah,
        ayah_from=ayah_from,
        ayah_to=ayah_to,
        arabic_ayahs=ayah_instances,
        translation_ayahs=translation_instances,
        translation_edition_name=trans_name,
        lang=lang,
    )


class QuranMarkdownFormatter:
    """
    Class-based interface for Markdown formatting compatibility.
    """
    @classmethod
    def format_verse(
        cls,
        surah_name: str,
        surah_number: int,
        ayah_number: int,
        arabic_text: str,
        translation_text: Optional[str] = None,
        translation_author: Optional[str] = None,
        include_citation: bool = True,
        lang: str = "fa",
    ) -> str:
        arabic_texts = [arabic_text] if arabic_text else []
        translation_texts = [translation_text] if translation_text else None
        return format_quran_markdown_reference(
            surah_name=surah_name,
            surah_english_name=surah_name,
            surah_number=surah_number,
            ayah_from=ayah_number,
            ayah_to=ayah_number,
            arabic_texts=arabic_texts,
            translation_texts=translation_texts,
            translation_name=translation_author or "",
            lang=lang,
        )
