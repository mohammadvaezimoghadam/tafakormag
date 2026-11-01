import sys
import unicodedata
import re

sys.stdout.reconfigure(encoding='utf-8')

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

# Invisible / directional formatting
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

# Letter normalization mappings
LETTER_MAPPINGS = {
    # Alef variations -> standard bare Alef (ا)
    'أ': 'ا',
    'إ': 'ا',
    'آ': 'ا',
    'ٱ': 'ا',  # Alef Wasla
    'ٲ': 'ا',
    'ٳ': 'ا',
    'ٵ': 'ا',

    # Yeh / Yaa variations -> unified Persian/Arabic Yeh (ی)
    'ي': 'ی',  # Arabic Yeh with two dots
    'ى': 'ی',  # Alef Maksura
    'ئ': 'ی',  # Yeh with Hamza above
    'ؽ': 'ی',
    'ؾ': 'ی',
    'ؿ': 'ی',
    'ے': 'ی',  # Urdu Yeh Barree
    'ۓ': 'ی',
    'ۑ': 'ی',
    'ې': 'ی',

    # Kaf variations -> standard Persian/Arabic Keheh (ک)
    'ك': 'ک',  # Arabic Kaf
    'ګ': 'ک',
    'ڬ': 'ک',
    'ڭ': 'ک',
    'ڮ': 'ک',
    'ڱ': 'ک',
    'ڲ': 'ک',
    'ڳ': 'ک',
    'ڴ': 'ک',

    # Waw variations -> standard Waw (و)
    'ؤ': 'و',  # Waw with Hamza
    'ۄ': 'و',
    'ۅ': 'و',
    'ۆ': 'و',
    'ۇ': 'و',
    'ۈ': 'و',
    'ۉ': 'و',
    'ۊ': 'و',
    'ۋ': 'و',
    'ۏ': 'و',

    # Teh Marbuta & Heh variations -> standard Heh (ه)
    'ة': 'ه',
    'ۀ': 'ه',
    'ۃ': 'ه',
    'ھ': 'ه',
    'ە': 'ه',

    # Tatweel / Kashida -> remove
    'ـ': '',

    # Quranic symbols & ornaments
    '﴿': ' ',
    '﴾': ' ',
    '«': ' ',
    '»': ' ',
    '“': ' ',
    '”': ' ',
    '‘': ' ',
    '’': ' ',
    '۝': ' ',
    '۞': ' ',
    '۩': ' ',
}

# Pre-compile mapping translation table for fast execution
MAPPING_TRANSLATION_TABLE = str.maketrans({
    **INVISIBLE_CHARS_MAP,
    **LETTER_MAPPINGS
})

def strip_quranic_diacritics(text: str) -> str:
    """Removes all Harakat, Tashkeel, Sukun, Tanwin, Shaddah, Maddah, Dagger Alef, and Quranic stop marks."""
    if not text:
        return ""
    # Strip regex marks
    text = QURANIC_DIACRITICS_REGEX.sub('', text)
    # NFKD decomposition & strip any leftover nonspacing/enclosing marks
    text = unicodedata.normalize('NFKD', text)
    text = ''.join(c for c in text if unicodedata.category(c) not in ('Mn', 'Me'))
    return text

def normalize_quran_text(text: str) -> str:
    """
    Standardizes Quranic Arabic & Persian text for indexing and searching:
    - Removes all diacritics and pause symbols.
    - Standardizes Alef, Yeh, Kaf, Waw, Teh Marbuta.
    - Removes Tatweel and invisible chars.
    - Strips punctuation and collapses whitespace.
    """
    if not text:
        return ""

    # Step 1: Strip diacritics
    text = strip_quranic_diacritics(text)

    # Step 2: Translate character variations and invisible chars
    text = text.translate(MAPPING_TRANSLATION_TABLE)

    # Step 3: Remove punctuation / special non-word symbols
    text = re.sub(r'[^\w\s\u0600-\u06FF]', ' ', text)

    # Step 4: Normalize whitespace & lower-case
    text = re.sub(r'\s+', ' ', text).strip().lower()
    return text

if __name__ == '__main__':
    test_cases = [
        ("بِسْمِ ٱللَّهِ ٱلرَّحْمَٰنِ ٱلرَّحِيمِ", "بسم الله الرحمن الرحیم"),
        ("إِيَّاكَ نَعْبُدُ وَإِيَّاكَ نَسْتَعِينُ", "ایاک نعبد وایاک نستعین"),
        ("قُلْ هُوَ اللَّهُ أَحَدٌ", "قل هو الله احد"),
        ("كُتِبَ عَلَيْكُمُ الصِّيَامُ", "کتب علیکم الصیام"),
        ("تَبَّتْ يَدَا أَبِي لَهَبٍ وَتَبَّ", "تبت یدا ابی لهب وتب"),
        ("الم ۝۱ ذَٰلِكَ الْكِتَابُ لَا رَيْبَ ۛ فِيهِ ۛ هُدًى لِّلْمُتَّقِينَ", "الم ۱ ذلک الکتاب لا ریب فیه هدی للمتقین"),
        ("﴿ قُلْ أَعُوذُ بِرَبِّ النَّاسِ ﴾", "قل اعوذ برب الناس"),
        ("وَٱلضُّحَىٰ ۝۱ وَٱلَّيْلِ إِذَا سَجَىٰ", "والضحی ۱ واللیل اذا سجی"),
        ("فَوَيْلٌۭ لِّلْمُصَلِّينَ", "فویل للمصلین"),
        ("يُؤْمِنُونَ بِٱلْغَيْبِ", "یومنون بالغیب"),
        ("رَحْمَةً", " رحمه"),
        ("تطهیر\u200cکننده", "تطهیر کننده"),
    ]

    all_passed = True
    for original, expected in test_cases:
        res = normalize_quran_text(original)
        norm_expected = re.sub(r'\s+', ' ', expected).strip()
        passed = (res == norm_expected)
        if not passed:
            all_passed = False
        print(f"[{'PASS' if passed else 'FAIL'}] '{original}' -> '{res}' (expected: '{norm_expected}')")

    print("\nAll passed:", all_passed)
