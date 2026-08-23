"""
Unit tests for Quran Unicode Normalizer Engine.
"""
from django.test import SimpleTestCase
from plugins.quran.services.normalizer import (
    normalize_quran_text,
    strip_quranic_diacritics,
)


class QuranNormalizerTests(SimpleTestCase):
    def test_strip_diacritics(self):
        text = "بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ"
        stripped = strip_quranic_diacritics(text)
        self.assertNotIn("ِ", stripped)
        self.assertNotIn("َ", stripped)
        self.assertNotIn("ّ", stripped)
        self.assertNotIn("ٰ", stripped)
        self.assertEqual(stripped, "بسم الله الرحمن الرحيم")

    def test_dagger_alef_stripping(self):
        text = "هَٰذَا الْكِتَابُ"
        normalized = normalize_quran_text(text)
        self.assertEqual(normalized, "هذا الکتاب")

    def test_normalize_persian_and_arabic_letters(self):
        # Arabic Yeh and Kaf -> standard
        text = "يَعْلَمُونَ كِتَابٌ"
        normalized = normalize_quran_text(text)
        self.assertEqual(normalized, "یعلمون کتاب")

        # Kaf variants
        text_kaf = "ك ګ ڬ ڭ"
        self.assertEqual(normalize_quran_text(text_kaf), "ک ک ک ک")

        # Yeh variants
        text_yeh = "ي ى ئ ے"
        self.assertEqual(normalize_quran_text(text_yeh), "ی ی ی ی")

        # Waw variants
        text_waw = "ؤ ۄ ۅ ۆ"
        self.assertEqual(normalize_quran_text(text_waw), "و و و و")

        # Teh Marbuta & Heh
        text_heh = "ة ۀ ۃ"
        self.assertEqual(normalize_quran_text(text_heh), "ه ه ه")

    def test_normalize_alef_variations(self):
        text = "إِيَّاكَ أَنْعَمْتَ آمنوا ٱللَّه"
        normalized = normalize_quran_text(text)
        self.assertEqual(normalized, "ایاک انعمت امنوا الله")

        text_alefs = "أ إ آ ٱ ٲ ٳ ٵ"
        self.assertEqual(normalize_quran_text(text_alefs), "ا ا ا ا ا ا ا")

    def test_quranic_pause_marks_and_brackets(self):
        text = "﴿ الم ۝۱ ذَٰلِكَ الْكِتَابُ لَا رَيْبَ ۛ فِيهِ ۛ ﴾"
        normalized = normalize_quran_text(text)
        self.assertEqual(normalized, "الم ۱ ذلک الکتاب لا ریب فیه")

    def test_invisible_characters_cleaned(self):
        text = "کتاب\u200cخوان\ufeff\u200e"
        normalized = normalize_quran_text(text)
        self.assertEqual(normalized, "کتاب خوان")

    def test_idempotence(self):
        text = "قُلْ هُوَ اللَّهُ أَحَدٌ"
        first = normalize_quran_text(text)
        second = normalize_quran_text(first)
        self.assertEqual(first, second)

    def test_empty_and_none(self):
        self.assertEqual(normalize_quran_text(""), "")
        self.assertEqual(normalize_quran_text(None), "")
        self.assertEqual(strip_quranic_diacritics(""), "")
        self.assertEqual(strip_quranic_diacritics(None), "")
