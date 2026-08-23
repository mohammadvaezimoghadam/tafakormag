"""
Tests for Quran Search Engine Service across SQLite and PostgreSQL.
"""
from django.test import TestCase
from plugins.quran.models import QuranEdition, QuranSurah, QuranAyah
from plugins.quran.services.search_service import (
    search_quran,
    search_quran_ayahs,
    highlight_authentic_text,
    highlight_search_matches,
)


class QuranSearchServiceTests(TestCase):
    def setUp(self):
        self.ar_edition = QuranEdition.objects.create(
            identifier='quran-simple',
            name='Simple Quran',
            language='ar',
            type='quran',
            is_default=True,
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
            revelation_type='Meccan',
            ayah_count=7,
        )
        self.surah112 = QuranSurah.objects.create(
            number=112,
            name='الإخلاص',
            english_name='Al-Ikhlaas',
            revelation_type='Meccan',
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
            text="بِسْمِ ٱللَّهِ ٱلرَّحْمَٰنِ ٱلرَّحِيمِ",
            normalized_text="بسم الله الرحمن الرحیم",
        )
        QuranAyah.objects.create(
            edition=self.fa_edition,
            surah=self.surah1,
            number=1,
            number_in_surah=1,
            juz=1,
            page=1,
            text="به نام خداوند بخشنده مهربان",
            normalized_text="به نام خداوند بخشنده مهربان",
        )
        # Surah 112:1
        QuranAyah.objects.create(
            edition=self.ar_edition,
            surah=self.surah112,
            number=6222,
            number_in_surah=1,
            juz=30,
            page=604,
            text="قُلْ هُوَ اللَّهُ أَحَدٌ",
            normalized_text="قل هو الله احد",
        )

    def test_highlight_authentic_text(self):
        orig = "بِسْمِ ٱللَّهِ ٱلرَّحْمَٰنِ ٱلرَّحِيمِ"
        hl = highlight_authentic_text(orig, ["الرحمن"])
        self.assertIn("<mark>ٱلرَّحْمَٰنِ</mark>", hl)

    def test_search_arabic_unaccented_query(self):
        res = search_quran(query="الرحمن", edition_id='quran-simple')
        self.assertEqual(res['count'], 1)
        self.assertEqual(res['results'][0]['number_in_surah'], 1)
        self.assertIn("<mark>", res['results'][0]['highlighted_text'])

    def test_search_multi_word_query(self):
        res = search_quran(query="الله احد", edition_id='quran-simple')
        self.assertEqual(res['count'], 1)
        self.assertEqual(res['results'][0]['surah']['number'], 112)

    def test_search_filter_by_surah(self):
        res = search_quran(query="الله", surah_number=112)
        self.assertEqual(res['count'], 1)
        self.assertEqual(res['results'][0]['surah']['number'], 112)

    def test_search_with_paired_translation(self):
        res = search_quran(query="الرحمن", edition_id='quran-simple', with_translation='fa.ansarian')
        self.assertEqual(res['count'], 1)
        self.assertIsNotNone(res['results'][0]['translation'])
        self.assertEqual(res['results'][0]['translation']['text'], "به نام خداوند بخشنده مهربان")

    def test_search_exact_phrase(self):
        res = search_quran(query="بسم الله الرحمن", exact=True, edition_id='quran-simple')
        self.assertEqual(res['count'], 1)
        self.assertEqual(res['results'][0]['surah']['number'], 1)

    def test_search_empty_query(self):
        res = search_quran(query="")
        self.assertEqual(res['count'], 0)
        self.assertEqual(len(res['results']), 0)
