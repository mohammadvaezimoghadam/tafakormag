"""
Unicode Normalization Service for the Official Quran Plugin.
Provides deterministic, high-performance Arabic & Persian text standardization.
"""
import re
import unicodedata

# Unicode character classes for Quranic diacritics, signs, and annotations
# Includes: Tashkeel (Fathah, Dammah, Kasrah, Sukun, Shaddah, Tanwin),
# Small High Signs (Sajda, Rub el Hizb, Waqf stops), Dagger Alef, Madda,
# and Extended Arabic-A Quranic annotation marks.
QURANIC_DIACRITICS_REGEX = re.compile(
    r'[\u0610-\u061A'  # Arabic Quranic annotations (Sallallahou, Alayhe, etc.)
    r'\u064B-\u065F'  # Harakat, Tanwin, Shaddah, Sukun, Maddah, Hamza above/below
    r'\u0670'          # Superscript/Dagger Alef (ٰ)
    r'\u0674'          # High Hamza
    r'\u06D6-\u06DC'  # Quranic Stop Marks (صلے، قلے، ج، لا، etc.)
    r'\u06DF-\u06E8'  # Quranic special pause/sajda symbols
    r'\u06EA-\u06ED'  # Extra Quranic signs
    r'\u08D4-\u08E1'  # Extended Quranic Arabic-A signs
    r'\u08E3-\u08FF'  # Extended Quranic Arabic-A vowels & tone marks
    r']'
)

# Invisible / Zero-width / Directional formatting characters
INVISIBLE_CHARS_MAP = {
    '\u0674': '',   # High Hamza -> remove
    '\u200c': ' ',  # Zero-Width Non-Joiner (ZWNJ) -> space
    '\u200d': '',   # Zero-Width Joiner (ZWJ) -> remove
    '\u200e': '',   # Left-to-Right Mark (LRM) -> remove
    '\u200f': '',   # Right-to-Left Mark (RLM) -> remove
    '\ufeff': '',   # Byte Order Mark (BOM) -> remove
    '\u00a0': ' ',  # Non-Breaking Space (NBSP) -> space
    '\u202a': '',   # Left-to-Right Embedding (LRE) -> remove
    '\u202b': '',   # Right-to-Left Embedding (RLE) -> remove
    '\u202c': '',   # Pop Directional Formatting (PDF) -> remove
    '\u202d': '',   # Left-to-Right Override (LRO) -> remove
    '\u202e': '',   # Right-to-Left Override (RLO) -> remove
    '\u2066': '',   # Left-to-Right Isolate (LRI) -> remove
    '\u2067': '',   # Right-to-Left Isolate (RLI) -> remove
    '\u2068': '',   # First Strong Isolate (FSI) -> remove
    '\u2069': '',   # Pop Directional Isolate (PDI) -> remove
    '\u2028': ' ',  # Line Separator -> space
    '\u2029': ' ',  # Paragraph Separator -> space
}

# Letter normalization mappings across Arabic & Persian alphabets
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

    # Quranic symbols, quotes & brackets
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

# Pre-compiled high-performance translation table
MAPPING_TRANSLATION_TABLE = str.maketrans({
    **INVISIBLE_CHARS_MAP,
    **LETTER_MAPPINGS
})


def strip_quranic_diacritics(text: str) -> str:
    """
    Removes all Harakat, Tashkeel, Sukun, Tanwin, Shaddah, Maddah,
    Dagger Alef, and Quranic pause/stop marks.
    """
    if not text:
        return ""
    # NFKD decomposition
    text = unicodedata.normalize('NFKD', str(text))
    # Strip explicit regex marks and high hamza
    text = QURANIC_DIACRITICS_REGEX.sub('', text)
    # Strip remaining combining marks
    text = ''.join(c for c in text if unicodedata.category(c) not in ('Mn', 'Me', 'Sk'))
    return text


def normalize_quran_text(text: str) -> str:
    """
    Transforms Arabic or Persian Quranic text into canonical searchable form:
    1. Strips all diacritics and combining characters.
    2. Maps letter variants (Alef, Yeh, Kaf, Waw, Teh Marbuta).
    3. Cleans invisible, zero-width, and directional characters.
    4. Strips non-word punctuation while preserving letters/digits.
    5. Normalizes whitespace and returns lowercased string.
    """
    if not text:
        return ""

    # Step 1: Strip diacritics & NFKD decomposition
    text = strip_quranic_diacritics(text)

    # Step 2: Translate character variations and invisible chars
    text = text.translate(MAPPING_TRANSLATION_TABLE)

    # Step 3: Remove punctuation / special symbols, keeping Arabic, Persian, Latin, Digits
    text = re.sub(r'[^\w\s\u0600-\u06FF]', ' ', text)

    # Step 4: Collapse whitespace and lowercase
    text = re.sub(r'\s+', ' ', text).strip()
    return text.lower()
