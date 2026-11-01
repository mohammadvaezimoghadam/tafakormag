"""
Unit tests for Quran Markdown Reference Formatter Service.
"""
from django.test import TestCase
from plugins.quran.models import QuranEdition, QuranSurah, QuranAyah
from plugins.quran.services.formatter import (
    to_persian_digits,
    format_quran_markdown_reference,
    format_ayah_model_reference,
    QuranMarkdownFormatter,
)


class QuranFormatterTests(TestCase):
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
            number=1,
            name='الفاتحة',
            english_name='Al-Faatiha',
            ayah_count=7,
        )
        self.ayah1 = QuranAyah.objects.create(
            edition=self.edition_ar,
            surah=self.surah,
            number=1,
            number_in_surah=1,
            juz=1,
            text="بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ",
            normalized_text="بسم الله الرحمن الرحیم",
        )
        self.ayah2 = QuranAyah.objects.create(
            edition=self.edition_ar,
            surah=self.surah,
            number=2,
            number_in_surah=2,
            juz=1,
            text="الْحَمْدُ لِلَّهِ رَبِّ الْعَالَمِينَ",
            normalized_text="الحمد لله رب العالمین",
        )
        self.trans1 = QuranAyah.objects.create(
            edition=self.edition_fa,
            surah=self.surah,
            number=1,
            number_in_surah=1,
            juz=1,
            text="به نام خداوند بخشنده مهربان",
            normalized_text="به نام خداوند بخشنده مهربان",
        )
        self.trans2 = QuranAyah.objects.create(
            edition=self.edition_fa,
            surah=self.surah,
            number=2,
            number_in_surah=2,
            juz=1,
            text="ستایش مخصوص پروردگار جهانیان است",
            normalized_text="ستایش مخصوص پروردگار جهانیان است",
        )

    def test_to_persian_digits(self):
        self.assertEqual(to_persian_digits(1234567890), "۱۲۳۴۵۶۷۸۹۰")
        self.assertEqual(to_persian_digits("Surah 1:1-7"), "Surah ۱:۱-۷")

    def test_format_single_ayah(self):
        md = format_quran_markdown_reference(
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
        self.assertIn("> ﴿بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ﴾", md)
        self.assertIn("> *به نام خداوند بخشنده مهربان*", md)
        self.assertIn("سوره الفاتحة (۱:۱)", md)
        self.assertIn("ترجمه انصاریان", md)

    def test_format_ayah_range(self):
        md = format_quran_markdown_reference(
            surah_name="الفاتحة",
            surah_english_name="Al-Faatiha",
            surah_number=1,
            ayah_from=1,
            ayah_to=2,
            arabic_texts=["بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ", "الْحَمْدُ لِلَّهِ رَبِّ الْعَالَمِينَ"],
            translation_texts=["به نام خداوند", "ستایش خدای را"],
            lang="fa",
        )
        self.assertIn("۝۱", md)
        self.assertIn("۝۲", md)
        self.assertIn("سوره الفاتحة (۱:۱-۲)", md)

    def test_format_english_language(self):
        md = format_quran_markdown_reference(
            surah_name="الفاتحة",
            surah_english_name="Al-Faatiha",
            surah_number=1,
            ayah_from=1,
            ayah_to=1,
            arabic_texts=["بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ"],
            translation_texts=["In the name of Allah"],
            translation_name="Sahih International",
            lang="en",
        )
        self.assertIn("Surah Al-Faatiha (1:1)", md)
        self.assertIn("Sahih International", md)

    def test_format_ayah_model_reference(self):
        md = format_ayah_model_reference(
            ayah_instances=[self.ayah1, self.ayah2],
            translation_instances=[self.trans1, self.trans2],
            lang="fa",
        )
        self.assertIn("سوره الفاتحة", md)
        self.assertIn("ترجمه انصاریان", md)
        self.assertIn("۝۱", md)

    def test_quran_markdown_formatter_class(self):
        md = QuranMarkdownFormatter.format_verse(
            surah_name="الفاتحة",
            surah_number=1,
            ayah_number=1,
            arabic_text="بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ",
            translation_text="به نام خدا",
            translation_author="انصاریان",
        )
        self.assertIn("﴿بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ﴾", md)
        self.assertIn("به نام خدا", md)
