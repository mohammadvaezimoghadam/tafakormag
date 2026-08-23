"""
Adversarial Stress Test Suite for Official Quran Plugin.
Empirical verification of Unicode Normalizer, Search Engine, and Markdown Formatter.
"""
import time
import re
from django.test import TestCase, SimpleTestCase
from plugins.quran.models import QuranEdition, QuranSurah, QuranAyah
from plugins.quran.services.normalizer import (
    normalize_quran_text,
    strip_quranic_diacritics,
    QURANIC_DIACRITICS_REGEX,
    MAPPING_TRANSLATION_TABLE,
)
from plugins.quran.services.search_service import (
    search_quran,
    search_quran_ayahs,
    highlight_authentic_text,
    build_highlight_regex_for_token,
    QuranSearchService,
)
from plugins.quran.services.formatter import (
    to_persian_digits,
    format_quran_markdown_reference,
    format_ayah_model_reference,
    QuranMarkdownFormatter,
)


class QuranNormalizerAdversarialTests(SimpleTestCase):
    """
    Adversarial tests for normalizer.py across extreme Unicode edge cases.
    """

    def test_dense_overlapping_diacritics(self):
        """Test stacking of 10+ diacritics on single letters."""
        # Fatha + Damma + Kasra + Shaddah + Tanwin + Sukun + Maddah + Dagger Alef + Stop signs
        stacked = "ب" + "\u064E\u064F\u0650\u0651\u064B\u064C\u064D\u0652\u0653\u0670\u06D6\u06E1"
        normalized = normalize_quran_text(stacked)
        self.assertEqual(normalized, "ب")
        self.assertEqual(strip_quranic_diacritics(stacked), "ب")

    def test_quranic_dagger_alefs_and_high_hamzas(self):
        """Test dagger alef (ٰ) and high hamza (ٴ) in various positions."""
        # هَٰذَا -> هذا
        self.assertEqual(normalize_quran_text("هَٰذَا"), "هذا")
        # سَمَٰوَٰتِ -> سموت
        self.assertEqual(normalize_quran_text("سَمَٰوَٰتِ"), "سموت")
        # رَحْمَٰنِ -> رحمن
        self.assertEqual(normalize_quran_text("رَحْمَٰنِ"), "رحمن")
        # High hamza: يَتَسَآءَلُونَ (with high hamza \u0674 or \u0621)
        text_with_high_hamza = "يَتَسَا\u0674لُونَ"
        normalized = normalize_quran_text(text_with_high_hamza)
        self.assertNotIn("\u0674", normalized)
        self.assertEqual(normalized, "یتسالون")

    def test_all_hamza_and_alef_variants(self):
        """Test all Unicode Hamza and Alef variants standardizing to bare Alef or canonical forms."""
        alef_variants = [
            ("أَحْمَدُ", "احمد"),
            ("إِبْرَاهِيمَ", "ابراهیم"),
            ("آدَمَ", "ادم"),
            ("ٱلَّذِينَ", "الذین"),      # Alef Wasla
            ("ٲ", "ا"),                 # Alef with wavy hamza above
            ("ٳ", "ا"),                 # Alef with wavy hamza below
            ("ٵ", "ا"),                 # High hamza alef
        ]
        for raw, expected in alef_variants:
            self.assertEqual(normalize_quran_text(raw), expected, f"Failed for {raw}")

    def test_arabic_presentation_forms_a_and_b(self):
        """Test Unicode Presentation Forms A and B (isolated, initial, medial, final glyphs)."""
        # Presentation Forms-B: ﺏ (FE8F), ﻙ (FED9), ﻱ (FEF1) -> ب ك ي -> ب ک ی
        forms_b_spaced = "\uFE8F \uFED9 \uFEF1"
        self.assertEqual(normalize_quran_text(forms_b_spaced), "ب ک ی")

        forms_b_unspaced = "\uFE8F\uFED9\uFEF1"
        self.assertEqual(normalize_quran_text(forms_b_unspaced), "بکی")

        # Presentation Forms-B Ligature: ﻻ (U+FEFB - Lam-Alef)
        lam_alef_ligature = "\uFEFB \uFE8D"
        self.assertEqual(normalize_quran_text(lam_alef_ligature), "لا ا")

        # Persian Presentation Forms-A: ﮎ ﮏ ﮐ ﮑ
        persian_kaf_forms = "\uFB8E \uFB8F \uFB90 \uFB91"
        self.assertEqual(normalize_quran_text(persian_kaf_forms), "ک ک ک ک")

        # Persian Presentation Forms-A: ﭖ (Peh), ﭺ (Tcheh)
        persian_pe_tche = "\uFB56 \uFB7A"
        self.assertEqual(normalize_quran_text(persian_pe_tche), "پ چ")

    def test_zero_width_and_directional_characters(self):
        """Test all zero-width, formatting, and directional override characters."""
        # ZWNJ (\u200c), ZWJ (\u200d), LRM (\u200e), RLM (\u200f), BOM (\ufeff)
        # LRE (\u202a), RLE (\u202b), PDF (\u202c), LRO (\u202d), RLO (\u202e)
        # LRI (\u2066), RLI (\u2067), FSI (\u2068), PDI (\u2069)
        bad_string = (
            "الْحَمْدُ\u200cلِلَّهِ\u200d\u200e\u200f\ufeff "
            "\u202a\u202b\u202c\u202d\u202e\u2066\u2067\u2068\u2069"
            "رَبِّ\u00a0الْعَالَمِينَ\u2028\u2029"
        )
        normalized = normalize_quran_text(bad_string)
        self.assertEqual(normalized, "الحمد لله رب العالمین")

    def test_quranic_stop_signs_and_annotations(self):
        """Test all Quranic stop marks, pause signs, sajda, rub-el-hizb."""
        text = (
            "ذَٰلِكَ الْكِتَابُ لَا رَيْبَ ۛ فِيهِ ۛ هُدًى لِّلْمُتَّقِينَ ۙ "
            "الَّذِينَ يُؤْمِنُونَ بِالْغَيْبِ ۚ وَيُقِيمُونَ الصَّلَاةَ ۖ "
            "وَمِمَّا رَزَقْنَاهُمْ يُنفِقُونَ ۗ ۩ ۞ ۝ ﴿ ﴾"
        )
        normalized = normalize_quran_text(text)
        expected = "ذلک الکتاب لا ریب فیه هدی للمتقین الذین یومنون بالغیب ویقیمون الصلاه ومما رزقناهم ینفقون"
        self.assertEqual(normalized, expected)

    def test_kashida_tatweel_removal(self):
        """Test Arabic tatweel/kashida (ـ) is cleanly stripped."""
        text = "بـــــــــســـــــم اللّــــــــــــه"
        self.assertEqual(normalize_quran_text(text), "بسم الله")

    def test_emojis_and_special_symbols_stripped(self):
        """Test emojis, math symbols, and Latin punctuation are removed cleanly."""
        text = "🕌 بِسْمِ اللَّهِ! ✨ 100% ⭐️ (الرَّحْمَٰنِ) + [الرَّحِيمِ] 📖"
        normalized = normalize_quran_text(text)
        self.assertEqual(normalized, "بسم الله 100 الرحمن الرحیم")

    def test_normalizer_idempotence_and_stability(self):
        """Test idempotence: normalize(normalize(text)) == normalize(text)."""
        samples = [
            "بِسْمِ ٱللَّهِ ٱلرَّحْمَٰنِ ٱلرَّحِيمِ",
            "قُلْ أَعُوذُ بِرَبِّ ٱلنَّاسِ ۝۱ مَلِكِ ٱلنَّاسِ ۝۲",
            "كَهَيَعَصٓ ۝۱ ذِكْرُ رَحْمَتِ رَبِّكَ عَبْدَهُۥ زَكَرِيَّآ ۝۲",
            "اللَّهُ لَا إِلَٰهَ إِلَّا هُوَ الْحَيُّ الْقَيُّومُ ۚ لَا تَأْخُذُهُ سِنَةٌ وَلَا نَوْمٌ",
        ]
        for s in samples:
            norm1 = normalize_quran_text(s)
            norm2 = normalize_quran_text(norm1)
            self.assertEqual(norm1, norm2, f"Idempotence failed for {s}")

    def test_performance_under_large_text(self):
        """Test performance: normalizing a 100KB repetitive Quranic text executes rapidly."""
        verse = "بِسْمِ ٱللَّهِ ٱلرَّحْمَٰنِ ٱلرَّحِيمِ الْحَمْدُ لِلَّهِ رَبِّ الْعَالَمِينَ ۝۱ "
        large_text = verse * 1000  # ~80KB
        start_time = time.perf_counter()
        normalized = normalize_quran_text(large_text)
        elapsed = time.perf_counter() - start_time
        self.assertLess(elapsed, 0.5, f"Normalizer too slow: {elapsed:.3f}s for 80KB")
        self.assertTrue(len(normalized) > 0)


class QuranSearchEngineAdversarialTests(TestCase):
    """
    Adversarial tests for search_service.py: regex injections, highlighting edge cases,
    mixed scripts, and extreme filters.
    """

    def setUp(self):
        self.ar_edition = QuranEdition.objects.create(
            identifier='quran-simple',
            name='Simple Quran',
            language='ar',
            type='quran',
            is_default=True,
        )
        self.uthmani_edition = QuranEdition.objects.create(
            identifier='quran-uthmani',
            name='Uthmani Quran',
            language='ar',
            type='quran',
            is_default=False,
        )
        self.fa_edition = QuranEdition.objects.create(
            identifier='fa.ansarian',
            name='Ansarian Translation',
            language='fa',
            type='translation',
            is_default=True,
        )
        self.surah1 = QuranSurah.objects.create(
            number=1,
            name='الفاتحة',
            english_name='Al-Faatiha',
            ayah_count=7,
        )
        self.surah2 = QuranSurah.objects.create(
            number=2,
            name='البقرة',
            english_name='Al-Baqara',
            ayah_count=286,
        )
        self.surah112 = QuranSurah.objects.create(
            number=112,
            name='الإخلاص',
            english_name='Al-Ikhlaas',
            ayah_count=4,
        )

        # Surah 1:1
        QuranAyah.objects.create(
            edition=self.ar_edition,
            surah=self.surah1,
            number=1,
            number_in_surah=1,
            juz=1,
            page=1,
            text="بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ",
            normalized_text=normalize_quran_text("بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ"),
        )
        QuranAyah.objects.create(
            edition=self.uthmani_edition,
            surah=self.surah1,
            number=1,
            number_in_surah=1,
            juz=1,
            page=1,
            text="بِسْمِ ٱللَّهِ ٱلرَّحْمَٰنِ ٱلرَّحِيمِ",
            normalized_text=normalize_quran_text("بِسْمِ ٱللَّهِ ٱلرَّحْمَٰنِ ٱلرَّحِيمِ"),
        )
        QuranAyah.objects.create(
            edition=self.fa_edition,
            surah=self.surah1,
            number=1,
            number_in_surah=1,
            juz=1,
            page=1,
            text="به نام خداوند بخشنده مهربان",
            normalized_text=normalize_quran_text("به نام خداوند بخشنده مهربان"),
        )

        # Surah 2:255 (Ayat al-Kursi with repeated "الله")
        ayat_kursi_ar = (
            "اللَّهُ لَا إِلَٰهَ إِلَّا هُوَ الْحَيُّ الْقَيُّومُ ۚ "
            "لَا تَأْخُذُهُ سِنَةٌ وَلَا نَوْمٌ ۚ لَّهُ مَا فِي السَّمَاوَاتِ وَمَا فِي الْأَرْضِ ۗ "
            "مَن ذَا الَّذِي يَشْفَعُ عِندَهُ إِلَّا بِإِذْنِهِ ۚ "
            "يَعْلَمُ مَا بَيْنَ أَيْدِيهِمْ وَمَا خَلْفَهُمْ ۖ "
            "وَلَا يُحِيطُونَ بِشَيْءٍ مِّنْ عِلْمِهِ إِلَّا بِمَا شَاءَ ۚ "
            "وَسِعَ كُرْسِيُّهُ السَّمَاوَاتِ وَالْأَرْضَ ۖ "
            "وَلَا يَئُودُهُ حِفْظُهُمَا ۚ وَهُوَ الْعَلِيُّ الْعَظِيمُ"
        )
        QuranAyah.objects.create(
            edition=self.ar_edition,
            surah=self.surah2,
            number=262,
            number_in_surah=255,
            juz=3,
            page=42,
            text=ayat_kursi_ar,
            normalized_text=normalize_quran_text(ayat_kursi_ar),
        )

        # Surah 112:1-4
        QuranAyah.objects.create(
            edition=self.ar_edition,
            surah=self.surah112,
            number=6222,
            number_in_surah=1,
            juz=30,
            page=604,
            text="قُلْ هُوَ اللَّهُ أَحَدٌ",
            normalized_text=normalize_quran_text("قُلْ هُوَ اللَّهُ أَحَدٌ"),
        )
        QuranAyah.objects.create(
            edition=self.ar_edition,
            surah=self.surah112,
            number=6223,
            number_in_surah=2,
            juz=30,
            page=604,
            text="اللَّهُ الصَّمَدُ",
            normalized_text=normalize_quran_text("اللَّهُ الصَّمَدُ"),
        )

    def test_regex_injection_queries(self):
        """Verify queries containing raw regex metacharacters do not crash or cause ReDoS."""
        regex_injections = [
            "(", "[", "]", "*", "+", "?", "\\", "^", "$", ".",
            ".*", "([a-z]+)*", "(((.*)+)+)", "(?<=abc)", "a{1,1000}",
            "\\u064E+", "[\\u0600-\\u06FF]*", "(?i)", "(?x)",
        ]
        for evil_query in regex_injections:
            res = search_quran(query=evil_query, edition_id='quran-simple')
            self.assertIsInstance(res, dict)
            self.assertIn("results", res)
            self.assertIn("total_matches", res)

    def test_highlighting_regex_special_characters(self):
        """Verify highlighting does not crash on malformed token strings."""
        tokens = ["(", "[a-z]", "*+", ".*", "الله"]
        text = "قُلْ هُوَ اللَّهُ أَحَدٌ"
        hl = highlight_authentic_text(text, tokens)
        self.assertIn("<mark>اللَّهُ</mark>", hl)

    def test_highlighting_repeated_occurrences(self):
        """Verify multiple occurrences of search tokens in long verses are all highlighted."""
        text = "اللَّهُ لَا إِلَٰهَ إِلَّا هُوَ الْحَيُّ الْقَيُّومُ... لَّهُ مَا فِي... عِندَهُ إِلَّا... وَهُوَ الْعَلِيُّ"
        hl = highlight_authentic_text(text, ["هو"])
        # Should highlight both occurrences of هُوَ (standalone and after conjunction)
        self.assertEqual(hl.count("<mark>هُوَ</mark>"), 2)

    def test_highlighting_uthmani_script_with_dagger_alef(self):
        """Verify highlighting matches Uthmani script with dagger alef and wasla."""
        uthmani_text = "بِسْمِ ٱللَّهِ ٱلرَّحْمَٰنِ ٱلرَّحِيمِ"
        hl = highlight_authentic_text(uthmani_text, ["الرحمن"])
        self.assertIn("<mark>ٱلرَّحْمَٰنِ</mark>", hl)

    def test_highlighting_overlapping_tokens(self):
        """Verify highlighting handles substring tokens cleanly without producing nested tags."""
        text = "بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ"
        hl = highlight_authentic_text(text, ["الرحمن", "رحمن"])
        self.assertIn("<mark>الرَّحْمَٰنِ</mark>", hl)
        self.assertNotIn("<mark><mark>", hl)

    def test_highlighting_prefix_and_full_word(self):
        """Verify highlighting prefix terms alongside longer full terms."""
        text = "اللَّهُ الصَّمَدُ وَاللَّهُمَّ"
        hl = highlight_authentic_text(text, ["الله", "اللهم"])
        self.assertIn("<mark>اللَّهُ</mark>", hl)
        self.assertIn("<mark>اللَّهُمَّ</mark>", hl)

    def test_mixed_persian_arabic_query(self):
        """Verify search matches regardless of whether user types Persian or Arabic letters."""
        # User types Persian 'ک' and 'ی'
        res_fa = search_quran(query="رحیم", edition_id='quran-simple')
        self.assertEqual(res_fa['count'], 1)
        self.assertEqual(res_fa['results'][0]['surah']['number'], 1)

        # User types Arabic 'ي' with tanwin or fatha
        res_ar = search_quran(query="رَحِيْمٍ", edition_id='quran-simple')
        self.assertEqual(res_ar['count'], 1)

    def test_empty_and_whitespace_and_invisible_queries(self):
        """Verify queries with empty strings or only whitespace/invisible chars return empty results."""
        queries = ["", "   ", "\t\n", "\u200c\u200d\ufeff", "   \u00a0   "]
        for q in queries:
            res = search_quran(query=q)
            self.assertEqual(res['count'], 0)
            self.assertEqual(len(res['results']), 0)

    def test_exact_phrase_vs_token_order(self):
        """Verify exact phrase matching enforces token adjacency and sequence."""
        # Non-exact search for "احد الله" matches Surah 112:1 (has both words in any order)
        res_tokens = search_quran(query="احد الله", exact=False, edition_id='quran-simple')
        self.assertEqual(res_tokens['count'], 1)

        # Exact phrase search for "احد الله" does NOT match (verse is "الله احد")
        res_exact = search_quran(query="احد الله", exact=True, edition_id='quran-simple')
        self.assertEqual(res_exact['count'], 0)

        # Exact phrase search for "الله احد" matches
        res_exact_match = search_quran(query="الله احد", exact=True, edition_id='quran-simple')
        self.assertEqual(res_exact_match['count'], 1)

    def test_search_non_existent_translation_edition(self):
        """Verify querying with non-existent translation ID does not throw error."""
        res = search_quran(
            query="الرحمن",
            edition_id='quran-simple',
            with_translation='non-existent-edition'
        )
        self.assertEqual(res['count'], 1)
        self.assertIsNone(res['results'][0]['translation'])

    def test_search_pagination_boundary_cases(self):
        """Verify pagination handles out of range and huge page numbers gracefully."""
        res_first = search_quran(query="الله", page=1, page_size=1)
        self.assertEqual(res_first['page'], 1)
        self.assertEqual(len(res_first['results']), 1)

        res_huge = search_quran(query="الله", page=999999, page_size=20)
        self.assertTrue(res_huge['page'] <= res_huge['total_pages'])

        res_clamp_size = search_quran(query="الله", page_size=5000)
        self.assertEqual(res_clamp_size['page_size'], 100)


class QuranFormatterAdversarialTests(TestCase):
    """
    Adversarial tests for formatter.py: single vs multi-verse ranges, missing translations,
    numeral standardizations, boundary conditions.
    """

    def setUp(self):
        self.edition_ar = QuranEdition.objects.create(
            identifier='quran-simple',
            name='متن ساده',
            english_name='Simple Quran',
            language='ar',
            type='quran',
        )
        self.edition_fa = QuranEdition.objects.create(
            identifier='fa.ansarian',
            name='ترجمه انصاریان',
            english_name='Ansarian',
            language='fa',
            type='translation',
        )
        self.surah = QuranSurah.objects.create(
            number=112,
            name='الإخلاص',
            english_name='Al-Ikhlaas',
            ayah_count=4,
        )
        self.ayah1 = QuranAyah.objects.create(
            edition=self.edition_ar,
            surah=self.surah,
            number=6222,
            number_in_surah=1,
            juz=30,
            text="قُلْ هُوَ اللَّهُ أَحَدٌ",
            normalized_text="قل هو الله احد",
        )
        self.ayah2 = QuranAyah.objects.create(
            edition=self.edition_ar,
            surah=self.surah,
            number=6223,
            number_in_surah=2,
            juz=30,
            text="اللَّهُ الصَّمَدُ",
            normalized_text="الله الصمد",
        )
        self.ayah3 = QuranAyah.objects.create(
            edition=self.edition_ar,
            surah=self.surah,
            number=6224,
            number_in_surah=3,
            juz=30,
            text="لَمْ يَلِدْ وَلَمْ يُولَدْ",
            normalized_text="لم یلد ولم یولد",
        )

    def test_single_verse_without_translation(self):
        """Verify single verse formatting without translation."""
        md = format_quran_markdown_reference(
            surah=self.surah,
            ayah_from=1,
            ayah_to=1,
            arabic_ayahs=[self.ayah1],
            translation_ayahs=None,
            lang="fa",
        )
        expected_lines = [
            "> ﴿قُلْ هُوَ اللَّهُ أَحَدٌ﴾",
            "> — **سوره الإخلاص (۱۱۲:۱)**",
        ]
        self.assertEqual(md, "\n".join(expected_lines))

    def test_multi_verse_range_with_ornaments(self):
        """Verify multi-verse range formatting inserts verse end ornaments and coordinate ranges."""
        md = format_quran_markdown_reference(
            surah=self.surah,
            ayah_from=1,
            ayah_to=3,
            arabic_ayahs=[self.ayah1, self.ayah2, self.ayah3],
            translation_texts=["بگو او خدای یکتاست", "خدای بی نیاز", "نه زاده و نه زاییده شده"],
            translation_edition_name="ترجمه انصاریان",
            lang="fa",
        )
        self.assertIn("قُلْ هُوَ اللَّهُ أَحَدٌ ۝۱", md)
        self.assertIn("اللَّهُ الصَّمَدُ ۝۲", md)
        self.assertIn("لَمْ يَلِدْ وَلَمْ يُولَدْ ۝۳", md)
        self.assertIn("بگو او خدای یکتاست (۱) خدای بی نیاز (۲) نه زاده و نه زاییده شده (۳)", md)
        self.assertIn("— **سوره الإخلاص (۱۱۲:۱-۳)** — *ترجمه انصاریان*", md)

    def test_english_formatting_and_numerals(self):
        """Verify English formatting preserves ASCII numerals and English labels."""
        md = format_quran_markdown_reference(
            surah_name="Al-Ikhlaas",
            surah_english_name="Al-Ikhlaas",
            surah_number=112,
            ayah_from=1,
            ayah_to=2,
            arabic_texts=["قُلْ هُوَ اللَّهُ أَحَدٌ", "اللَّهُ الصَّمَدُ"],
            translation_texts=["Say, He is Allah, [who is] One", "Allah, the Eternal Refuge"],
            translation_name="Sahih International",
            lang="en",
        )
        self.assertIn("۝1", md)
        self.assertIn("۝2", md)
        self.assertIn("Surah Al-Ikhlaas (112:1-2)", md)
        self.assertIn("Sahih International", md)

    def test_mismatched_translation_list_lengths(self):
        """Verify formatter does not crash when translation list is shorter or longer than verses."""
        # 3 Arabic verses, but only 1 translation text provided
        md = format_quran_markdown_reference(
            surah=self.surah,
            ayah_from=1,
            ayah_to=3,
            arabic_ayahs=[self.ayah1, self.ayah2, self.ayah3],
            translation_texts=["تنها یک ترجمه"],
            lang="fa",
        )
        self.assertIn("﴿قُلْ هُوَ اللَّهُ أَحَدٌ ۝۱ اللَّهُ الصَّمَدُ ۝۲ لَمْ يَلِدْ وَلَمْ يُولَدْ ۝۳﴾", md)
        self.assertIn("> *تنها یک ترجمه (۱)*", md)
        self.assertIn("سوره الإخلاص (۱۱۲:۱-۳)", md)

    def test_empty_arabic_texts_returns_empty_string(self):
        """Verify empty input returns empty string gracefully."""
        self.assertEqual(format_quran_markdown_reference(arabic_ayahs=[]), "")
        self.assertEqual(format_quran_markdown_reference(arabic_texts=[]), "")
        self.assertEqual(format_ayah_model_reference(ayah_instances=[]), "")

    def test_persian_digit_conversion(self):
        """Verify to_persian_digits handles various inputs."""
        self.assertEqual(to_persian_digits(0), "۰")
        self.assertEqual(to_persian_digits("Chapter 114: Ayah 6"), "Chapter ۱۱۴: Ayah ۶")
        self.assertEqual(to_persian_digits("No digits here!"), "No digits here!")

    def test_dict_and_model_surah_parameter(self):
        """Verify passing dict or model or individual kwargs for Surah metadata."""
        surah_dict = {'number': 112, 'name': 'الإخلاص', 'english_name': 'Al-Ikhlaas'}
        md_dict = format_quran_markdown_reference(
            surah=surah_dict,
            ayah_from=1,
            arabic_texts=["قُلْ هُوَ اللَّهُ أَحَدٌ"],
            lang="fa",
        )
        self.assertIn("سوره الإخلاص (۱۱۲:۱)", md_dict)
