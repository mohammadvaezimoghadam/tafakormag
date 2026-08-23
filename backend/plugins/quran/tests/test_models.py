"""
Unit tests for Quran Plugin Models: QuranEdition, QuranSurah, QuranJuz, QuranAyah.
"""
from django.test import TestCase
from django.db import IntegrityError
from plugins.quran.models import QuranEdition, QuranSurah, QuranJuz, QuranAyah


class QuranModelTests(TestCase):
    def setUp(self):
        self.edition = QuranEdition.objects.create(
            identifier='quran-simple',
            name='متن ساده قرآن کریم',
            english_name='Simple Arabic Quran',
            language='ar',
            type='quran',
            format='text',
            direction='rtl',
            author='Tanzil Project',
            is_default=True,
            total_ayahs=7,
        )
        self.surah = QuranSurah.objects.create(
            number=1,
            name='الفاتحة',
            english_name='Al-Faatiha',
            english_name_translation='The Opening',
            revelation_type='Meccan',
            ayah_count=7,
            order_of_revelation=5,
            page_start=1,
            page_end=1,
            juz_start=1,
            bismillah_pre=True,
        )
        self.juz = QuranJuz.objects.create(
            number=1,
            name='جزء ۱',
            start_surah=self.surah,
            start_ayah=1,
            end_surah=self.surah,
            end_ayah=7,
            surah_mapping=[{'surah': 1, 'ayah_from': 1, 'ayah_to': 7}],
        )

    def test_edition_creation_and_str(self):
        self.assertEqual(str(self.edition), "متن ساده قرآن کریم (quran-simple)")
        self.assertTrue(self.edition.is_default)
        self.assertEqual(self.edition.language, 'ar')
        self.assertEqual(self.edition.type, 'quran')

    def test_surah_creation_and_str(self):
        self.assertEqual(str(self.surah), "1. الفاتحة (Al-Faatiha)")
        self.assertEqual(self.surah.ayah_count, 7)
        self.assertEqual(self.surah.revelation_type, 'Meccan')

    def test_juz_creation_and_str(self):
        self.assertIn("Juz 1", str(self.juz))
        self.assertEqual(self.juz.start_surah, self.surah)
        self.assertEqual(self.juz.end_surah, self.surah)
        self.assertEqual(len(self.juz.surah_mapping), 1)

    def test_ayah_creation_and_str(self):
        ayah = QuranAyah.objects.create(
            edition=self.edition,
            surah=self.surah,
            number=1,
            number_in_surah=1,
            juz=1,
            page=1,
            text="بِسْمِ ٱللَّهِ ٱلرَّحْمَٰنِ ٱلرَّحِيمِ",
            normalized_text="بسم الله الرحمن الرحیم",
        )
        self.assertEqual(ayah.surah.name, 'الفاتحة')
        self.assertEqual(ayah.edition_id, 'quran-simple')
        self.assertIn("quran-simple", str(ayah))

    def test_unique_edition_global_number_constraint(self):
        QuranAyah.objects.create(
            edition=self.edition,
            surah=self.surah,
            number=1,
            number_in_surah=1,
            juz=1,
            text="text 1",
            normalized_text="text 1",
        )
        with self.assertRaises(IntegrityError):
            QuranAyah.objects.create(
                edition=self.edition,
                surah=self.surah,
                number=1,  # duplicate global number in same edition
                number_in_surah=2,
                juz=1,
                text="text 2",
                normalized_text="text 2",
            )

    def test_unique_edition_surah_ayah_constraint(self):
        QuranAyah.objects.create(
            edition=self.edition,
            surah=self.surah,
            number=1,
            number_in_surah=1,
            juz=1,
            text="text 1",
            normalized_text="text 1",
        )
        with self.assertRaises(IntegrityError):
            QuranAyah.objects.create(
                edition=self.edition,
                surah=self.surah,
                number=2,
                number_in_surah=1,  # duplicate number_in_surah for same (edition, surah)
                juz=1,
                text="duplicate ayah 1",
                normalized_text="duplicate",
            )

    def test_cascading_deletion(self):
        QuranAyah.objects.create(
            edition=self.edition,
            surah=self.surah,
            number=1,
            number_in_surah=1,
            juz=1,
            text="test",
            normalized_text="test",
        )
        self.assertEqual(QuranAyah.objects.count(), 1)
        self.edition.delete()
        self.assertEqual(QuranAyah.objects.count(), 0)
