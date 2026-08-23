import sys
from typing import List, Optional, Union

sys.stdout.reconfigure(encoding='utf-8')

PERSIAN_DIGITS_TABLE = str.maketrans('0123456789', '۰۱۲۳۴۵۶۷۸۹')

def to_persian_digits(val: Union[int, str]) -> str:
    """Converts English digits in string or int to Persian digits."""
    return str(val).translate(PERSIAN_DIGITS_TABLE)

def format_quran_markdown_reference(
    surah_name: str,
    surah_english_name: str,
    surah_number: int,
    ayah_from: int,
    ayah_to: int,
    arabic_texts: List[str],
    translation_texts: Optional[List[str]] = None,
    translation_name: str = "",
    lang: str = "fa",
) -> str:
    """
    Constructs a standard Markdown blockquote citation for Quranic verses.
    
    Args:
        surah_name: Arabic name of the Surah (e.g. 'الفاتحة')
        surah_english_name: English name of the Surah (e.g. 'Al-Faatiha')
        surah_number: Surah index (1..114)
        ayah_from: Starting Ayah number in surah
        ayah_to: Ending Ayah number in surah
        arabic_texts: List of authentic Arabic ayah text strings
        translation_texts: Optional list of translated ayah text strings
        translation_name: Name of translation edition (e.g. 'ترجمه انصاریان')
        lang: Language for citation label ('fa' or 'en')
        
    Returns:
        Formatted Markdown blockquote string.
    """
    if not arabic_texts:
        return ""

    is_range = (ayah_to > ayah_from) or (len(arabic_texts) > 1)
    
    # 1. Format Arabic verse(s)
    if is_range:
        arabic_segments = []
        for i, text in enumerate(arabic_texts):
            current_ayah_num = ayah_from + i
            num_str = to_persian_digits(current_ayah_num) if lang == "fa" else str(current_ayah_num)
            clean_t = text.strip()
            # If text already ends with verse ornament, don't duplicate
            if not clean_t.endswith('۝') and not any(c in clean_t[-3:] for c in '۝۞۩'):
                arabic_segments.append(f"{clean_t} ۝{num_str}")
            else:
                arabic_segments.append(clean_t)
        arabic_content = " ".join(arabic_segments)
    else:
        arabic_content = arabic_texts[0].strip()

    # Wrap Arabic text in Quranic bracket ornaments
    arabic_line = f"> ﴿{arabic_content}﴾"

    lines = [arabic_line]

    # 2. Format Translation verse(s) if provided
    if translation_texts:
        if is_range:
            trans_segments = []
            for i, text in enumerate(translation_texts):
                current_ayah_num = ayah_from + i
                num_str = to_persian_digits(current_ayah_num) if lang == "fa" else str(current_ayah_num)
                trans_segments.append(f"{text.strip()} ({num_str})")
            translation_content = " ".join(trans_segments)
        else:
            translation_content = translation_texts[0].strip()

        lines.append(f"> *{translation_content}*")

    # 3. Format Citation line
    if is_range:
        ref_coord = f"{surah_number}:{ayah_from}-{ayah_to}"
    else:
        ref_coord = f"{surah_number}:{ayah_from}"

    if lang == "fa":
        coord_fa = to_persian_digits(ref_coord)
        citation = f"— **سوره {surah_name} ({coord_fa})**"
        if translation_name:
            citation += f" — *{translation_name}*"
    else:
        citation = f"— **Surah {surah_english_name} ({ref_coord})**"
        if translation_name:
            citation += f" — *{translation_name}*"

    lines.append(f"> {citation}")

    return "\n".join(lines)


if __name__ == '__main__':
    # Test 1: Single Ayah in Persian
    md1 = format_quran_markdown_reference(
        surah_name="الفاتحة",
        surah_english_name="Al-Faatiha",
        surah_number=1,
        ayah_from=1,
        ayah_to=1,
        arabic_texts=["بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ"],
        translation_texts=["به نام خداوند بخشنده مهربان"],
        translation_name="ترجمه انصاریان",
        lang="fa",
    )
    print("Test 1 (Single Ayah FA):")
    print(md1)
    print("=" * 50)

    # Test 2: Ayah Range in Persian
    md2 = format_quran_markdown_reference(
        surah_name="الفاتحة",
        surah_english_name="Al-Faatiha",
        surah_number=1,
        ayah_from=1,
        ayah_to=3,
        arabic_texts=[
            "بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ",
            "الْحَمْدُ لِلَّهِ رَبِّ الْعَالَمِينَ",
            "الرَّحْمَٰنِ الرَّحِيمِ",
        ],
        translation_texts=[
            "به نام خداوند بخشنده مهربان",
            "ستایش خدای را که پروردگار جهانیان است",
            "بخشنده مهربان",
        ],
        translation_name="ترجمه انصاریان",
        lang="fa",
    )
    print("Test 2 (Range FA):")
    print(md2)
    print("=" * 50)

    # Test 3: Single Ayah in English
    md3 = format_quran_markdown_reference(
        surah_name="الإخلاص",
        surah_english_name="Al-Ikhlaas",
        surah_number=112,
        ayah_from=1,
        ayah_to=1,
        arabic_texts=["قُلْ هُوَ اللَّهُ أَحَدٌ"],
        translation_texts=["Say, 'He is Allah, [who is] One'"],
        translation_name="Sahih International",
        lang="en",
    )
    print("Test 3 (Single Ayah EN):")
    print(md3)
    print("=" * 50)
