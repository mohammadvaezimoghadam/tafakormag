"""
Integration test for normalizer, search service logic, and formatter service.
"""
import sys
import unicodedata
import re
from typing import List, Optional, Dict, Any, Union

sys.stdout.reconfigure(encoding='utf-8')

# ---------------------------------------------------------------------------
# 1. Normalizer Logic
# ---------------------------------------------------------------------------
QURANIC_DIACRITICS_REGEX = re.compile(
    r'[\u0610-\u061A'  # Quranic annotations
    r'\u064B-\u065F'  # Harakat & Tashkeel & Maddah
    r'\u0670'          # Superscript/Dagger Alef
    r'\u06D6-\u06DC'  # Quranic Stop Marks
    r'\u06DF-\u06E8'  # Quranic special pause/sajda symbols
    r'\u06EA-\u06ED'  # Extra Quranic signs
    r'\u08D4-\u08E1'  # Extended Quranic Arabic-A
    r'\u08E3-\u08FF'  # Extended Quranic Arabic-A
    r']'
)

INVISIBLE_CHARS_MAP = {
    '\u200c': ' ',  # ZWNJ -> space
    '\u200d': '',   # ZWJ -> remove
    '\u200e': '',   # LRM -> remove
    '\u200f': '',   # RLM -> remove
    '\ufeff': '',   # BOM -> remove
    '\u00a0': ' ',  # Non-breaking space -> space
    '\u202a': '',   # LRE -> remove
    '\u202b': '',   # RLE -> remove
    '\u202c': '',   # PDF -> remove
    '\u202d': '',   # LRO -> remove
    '\u202e': '',   # RLO -> remove
    '\u2066': '',   # LRI -> remove
    '\u2067': '',   # RLI -> remove
    '\u2068': '',   # FSI -> remove
    '\u2069': '',   # PDI -> remove
    '\u2028': ' ',  # Line separator -> space
    '\u2029': ' ',  # Paragraph separator -> space
}

LETTER_MAPPINGS = {
    # Alef variations -> standard bare Alef (ا)
    'أ': 'ا', 'إ': 'ا', 'آ': 'ا', 'ٱ': 'ا', 'ٲ': 'ا', 'ٳ': 'ا', 'ٵ': 'ا',
    # Yeh / Yaa variations -> unified Persian/Arabic Yeh (ی)
    'ي': 'ی', 'ى': 'ی', 'ئ': 'ی', 'ؽ': 'ی', 'ؾ': 'ی', 'ؿ': 'ی', 'ے': 'ی', 'ۓ': 'ی', 'ۑ': 'ی', 'ې': 'ی',
    # Kaf variations -> standard Persian/Arabic Keheh (ک)
    'ك': 'ک', 'ګ': 'ک', 'ڬ': 'ک', 'ڭ': 'ک', 'ڮ': 'ک', 'ڱ': 'ک', 'ڲ': 'ک', 'ڳ': 'ک', 'ڴ': 'ک',
    # Waw variations -> standard Waw (و)
    'ؤ': 'و', 'ۄ': 'و', 'ۅ': 'و', 'ۆ': 'و', 'ۇ': 'و', 'ۈ': 'و', 'ۉ': 'و', 'ۊ': 'و', 'ۋ': 'و', 'ۏ': 'و',
    # Teh Marbuta & Heh variations -> standard Heh (ه)
    'ة': 'ه', 'ۀ': 'ه', 'ۃ': 'ه', 'ھ': 'ه', 'ە': 'ه',
    # Tatweel / Kashida -> remove
    'ـ': '',
    # Quranic symbols & ornaments
    '﴿': ' ', '﴾': ' ', '«': ' ', '»': ' ', '“': ' ', '”': ' ', '‘': ' ', '’': ' ',
    '۝': ' ', '۞': ' ', '۩': ' ',
}

MAPPING_TRANSLATION_TABLE = str.maketrans({
    **INVISIBLE_CHARS_MAP,
    **LETTER_MAPPINGS
})

def strip_quranic_diacritics(text: str) -> str:
    if not text:
        return ""
    text = QURANIC_DIACRITICS_REGEX.sub('', text)
    text = unicodedata.normalize('NFKD', text)
    text = ''.join(c for c in text if unicodedata.category(c) not in ('Mn', 'Me'))
    return text

def normalize_quran_text(text: str) -> str:
    if not text:
        return ""
    text = strip_quranic_diacritics(text)
    text = text.translate(MAPPING_TRANSLATION_TABLE)
    text = re.sub(r'[^\w\s\u0600-\u06FF]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip().lower()
    return text

# ---------------------------------------------------------------------------
# 2. Search Highlighting Logic
# ---------------------------------------------------------------------------
DIACRITICS_AND_ANNOTATIONS = (
    r'[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06DC\u06DF-\u06E8\u06EA-\u06ED\u08D4-\u08E1\u08E3-\u08FF\u0640]*'
)

CHAR_VARIANTS_REGEX = {
    'ا': r'[اأإآٱٲٳٵ]',
    'ی': r'[یيىئؽؾؿےۓۑې]',
    'ک': r'[کكګڬڭڮڱڲڳڴ]',
    'و': r'[وؤۄۅۆۇۈۉۊۋۏ]',
    'ه': r'[ههةۀۃھە]',
}

def build_highlight_regex_for_token(token: str) -> str:
    parts = []
    for char in token:
        variant = CHAR_VARIANTS_REGEX.get(char, re.escape(char))
        parts.append(f"{variant}{DIACRITICS_AND_ANNOTATIONS}")
    return "".join(parts)

def highlight_authentic_text(authentic_text: str, tokens: List[str]) -> str:
    if not authentic_text or not tokens:
        return authentic_text
    sorted_tokens = sorted(set(tokens), key=len, reverse=True)
    token_patterns = [build_highlight_regex_for_token(t) for t in sorted_tokens if t.strip()]
    if not token_patterns:
        return authentic_text
    combined_pattern = re.compile(f"({'|'.join(token_patterns)})", re.IGNORECASE)
    return combined_pattern.sub(r'<mark>\1</mark>', authentic_text)

# ---------------------------------------------------------------------------
# 3. Formatter Logic
# ---------------------------------------------------------------------------
PERSIAN_DIGITS_TABLE = str.maketrans('0123456789', '۰۱۲۳۴۵۶۷۸۹')

def to_persian_digits(val: Union[int, str]) -> str:
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
    if not arabic_texts:
        return ""
    is_range = (ayah_to > ayah_from) or (len(arabic_texts) > 1)
    if is_range:
        arabic_segments = []
        for i, text in enumerate(arabic_texts):
            current_ayah_num = ayah_from + i
            num_str = to_persian_digits(current_ayah_num) if lang == "fa" else str(current_ayah_num)
            clean_t = text.strip()
            if not clean_t.endswith('۝') and not any(c in clean_t[-3:] for c in '۝۞۩'):
                arabic_segments.append(f"{clean_t} ۝{num_str}")
            else:
                arabic_segments.append(clean_t)
        arabic_content = " ".join(arabic_segments)
    else:
        arabic_content = arabic_texts[0].strip()

    lines = [f"> ﴿{arabic_content}﴾"]
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

# ---------------------------------------------------------------------------
# 4. Mock Search Execution Simulation
# ---------------------------------------------------------------------------
class MockSurah:
    def __init__(self, number, name, english_name, english_name_translation):
        self.number = number
        self.name = name
        self.english_name = english_name
        self.english_name_translation = english_name_translation

class MockAyah:
    def __init__(self, id, edition_id, surah, number, number_in_surah, text, juz=1, page=1):
        self.id = id
        self.edition_id = edition_id
        self.surah = surah
        self.number = number
        self.number_in_surah = number_in_surah
        self.text = text
        self.normalized_text = normalize_quran_text(text)
        self.juz = juz
        self.page = page

# Populate mock database
s1 = MockSurah(1, "الفاتحة", "Al-Faatiha", "The Opening")
s112 = MockSurah(112, "الإخلاص", "Al-Ikhlaas", "Sincerity")

mock_db = [
    MockAyah(1, "quran-simple", s1, 1, 1, "بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ"),
    MockAyah(2, "quran-simple", s1, 2, 2, "الْحَمْدُ لِلَّهِ رَبِّ الْعَالَمِينَ"),
    MockAyah(3, "quran-simple", s1, 3, 3, "الرَّحْمَٰنِ الرَّحِيمِ"),
    MockAyah(4, "quran-simple", s1, 4, 4, "مَالِكِ يَوْمِ الدِّينِ"),
    MockAyah(5, "quran-simple", s1, 5, 5, "إِيَّاكَ نَعْبُدُ وَإِيَّاكَ نَسْتَعِينُ"),
    MockAyah(6, "quran-simple", s1, 6, 6, "اهْدِنَا الصِّرَاطَ الْمُسْتَقِيمَ"),
    MockAyah(7, "quran-simple", s1, 7, 7, "صِرَاطَ الَّذِينَ أَنْعَمْتَ عَلَيْهِمْ غَيْرِ الْمَغْضُوبِ عَلَيْهِمْ وَلَا الضَّالِّينَ"),
    MockAyah(8, "quran-simple", s112, 6222, 1, "قُلْ هُوَ اللَّهُ أَحَدٌ"),
    MockAyah(9, "quran-simple", s112, 6223, 2, "اللَّهُ الصَّمَدُ"),
    MockAyah(10, "quran-simple", s112, 6224, 3, "لَمْ يَلِدْ وَلَمْ يُولَدْ"),
    MockAyah(11, "quran-simple", s112, 6225, 4, "وَلَمْ يَكُن لَّهُ كُفُوًا أَحَدٌ"),
]

mock_translations = {
    (1, 1): "به نام خداوند بخشنده مهربان",
    (1, 2): "ستایش خدای را که پروردگار جهانیان است",
    (1, 3): "بخشنده مهربان",
    (1, 4): "مالک روز جزا",
    (1, 5): "تنها تو را می‌پرستیم و تنها از تو یاری می‌جوییم",
    (112, 1): "بگو: او خدای یکتاست",
}

def simulate_search(q: str, edition_id="quran-simple", with_translation="fa.ansarian"):
    norm_q = normalize_quran_text(q)
    tokens = [t for t in norm_q.split() if t]
    
    # Filter matching ayahs
    matches = []
    for ayah in mock_db:
        if ayah.edition_id != edition_id:
            continue
        if all(tok in ayah.normalized_text for tok in tokens):
            matches.append(ayah)
            
    results = []
    for ayah in matches:
        hl_text = highlight_authentic_text(ayah.text, tokens)
        trans_text = mock_translations.get((ayah.surah.number, ayah.number_in_surah))
        results.append({
            "surah": f"{ayah.surah.number}. {ayah.surah.name}",
            "ayah": ayah.number_in_surah,
            "text": ayah.text,
            "highlighted_text": hl_text,
            "translation": trans_text,
        })
        
    return {
        "query": q,
        "normalized_query": norm_q,
        "count": len(results),
        "results": results
    }

if __name__ == '__main__':
    search_res = simulate_search("الله رحمن")
    print(f"Search Query: '{search_res['query']}' -> normalized: '{search_res['normalized_query']}' -> {search_res['count']} matches:")
    for r in search_res['results']:
        print(f" - [{r['surah']}:{r['ayah']}] {r['highlighted_text']}")
        if r['translation']:
            print(f"   Trans: {r['translation']}")
