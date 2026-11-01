import sys
import unicodedata
import re

sys.stdout.reconfigure(encoding='utf-8')

DIACRITICS_AND_ANNOTATIONS = (
    r'[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06DC\u06DF-\u06E8\u06EA-\u06ED\u08D4-\u08E1\u08E3-\u08FF\u0640]*'
)

# Reverse mapping for building regex from normalized characters
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
    any morphological/diacritical variant in the authentic Quranic text.
    """
    parts = []
    for char in token:
        variant = CHAR_VARIANTS_REGEX.get(char, re.escape(char))
        parts.append(f"{variant}{DIACRITICS_AND_ANNOTATIONS}")
    return "".join(parts)

def highlight_authentic_text_regex(authentic_text: str, tokens: list[str]) -> str:
    """
    Highlights matching tokens in authentic text with <mark> tags using regex matching.
    """
    if not authentic_text or not tokens:
        return authentic_text

    # Compile regex pattern combining all tokens
    token_patterns = [build_highlight_regex_for_token(t) for t in tokens if t.strip()]
    if not token_patterns:
        return authentic_text

    combined_pattern = re.compile(f"({'|'.join(token_patterns)})", re.IGNORECASE)
    
    # Replace matches with <mark>...</mark>
    return combined_pattern.sub(r'<mark>\1</mark>', authentic_text)

# Test with various verses and queries
test_cases = [
    (
        "بِسْمِ ٱللَّهِ ٱلرَّحْمَٰنِ ٱلرَّحِيمِ",
        ["رحمن"],
    ),
    (
        "بِسْمِ ٱللَّهِ ٱلرَّحْمَٰنِ ٱلرَّحِيمِ",
        ["الله", "رحیم"],
    ),
    (
        "إِيَّاكَ نَعْبُدُ وَإِيَّاكَ نَسْتَعِينُ",
        ["ایاک", "نستعین"],
    ),
    (
        "كُتِبَ عَلَيْكُمُ الصِّيَامُ",
        ["کتب", "صیام"],
    ),
    (
        "قُلْ هُوَ اللَّهُ أَحَدٌ",
        ["احد"],
    ),
    (
        "مَٰلِكِ يَوْمِ ٱلدِّينِ",
        ["ملک"],
    ),
    (
        "وَٱلضُّحَىٰ",
        ["ضحی"],
    ),
    (
        "الْحَمْدُ لِلَّهِ رَبِّ الْعَالَمِينَ",
        ["الحمد", "عالمین"],
    ),
    (
        "به نام خداوند بخشنده و مهربان",
        ["بخشنده", "مهربان"],
    ),
]

for orig, q_tokens in test_cases:
    highlighted = highlight_authentic_text_regex(orig, q_tokens)
    print(f"Original:    {orig}")
    print(f"Tokens:      {q_tokens}")
    print(f"Highlighted: {highlighted}")
    print("-" * 50)
