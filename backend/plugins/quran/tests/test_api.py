"""
Integration tests for Quran Plugin REST APIs.
"""
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.core.management import call_command
from plugins.quran.models import QuranEdition, QuranSurah, QuranAyah, QuranJuz


class QuranAPITests(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Run import_quran command with sample data
        call_command('import_quran', sample=True, force=True)

    def setUp(self):
        self.client = APIClient()

    def test_list_editions(self):
        res = self.client.get('/api/plugins/quran/editions/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(res.data), 1)

    def test_get_edition_detail(self):
        res = self.client.get('/api/plugins/quran/editions/quran-simple/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['identifier'], 'quran-simple')

    def test_list_surahs(self):
        res = self.client.get('/api/plugins/quran/surahs/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 114)
        first_surah = res.data[0]
        self.assertEqual(first_surah['number'], 1)
        self.assertEqual(first_surah['name'], 'الفاتحة')

    def test_get_surah_detail(self):
        res = self.client.get('/api/plugins/quran/surahs/1/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['name'], 'الفاتحة')
        self.assertEqual(res.data['ayah_count'], 7)
        self.assertIsNone(res.data['prev_surah'])
        self.assertEqual(res.data['next_surah']['number'], 2)

    def test_get_surah_ayahs(self):
        res = self.client.get('/api/plugins/quran/surahs/1/ayahs/?edition=quran-simple&with_translation=fa.ansarian')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['count'], 7)
        self.assertEqual(len(res.data['ayahs']), 7)
        first_ayah = res.data['ayahs'][0]
        self.assertIn('بِسْمِ', first_ayah['text'])
        self.assertIsNotNone(first_ayah['translation'])

    def test_get_single_ayah_by_coordinates(self):
        res = self.client.get('/api/plugins/quran/ayahs/1/1/?edition=quran-simple&with_translation=fa.ansarian')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['number_in_surah'], 1)
        self.assertIn('بِسْمِ', res.data['text'])
        self.assertIsNotNone(res.data['translation'])

    def test_get_single_ayah_by_global_number(self):
        res = self.client.get('/api/plugins/quran/ayahs/1/?edition=quran-simple&with_translation=fa.ansarian')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['number'], 1)
        self.assertIn('بِسْمِ', res.data['text'])

    def test_list_juzs(self):
        res = self.client.get('/api/plugins/quran/juzs/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 30)

        # Also test singular juz/ route
        res_singular = self.client.get('/api/plugins/quran/juz/')
        self.assertEqual(res_singular.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res_singular.data), 30)

    def test_get_juz_detail(self):
        res = self.client.get('/api/plugins/quran/juz/1/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['number'], 1)
        self.assertEqual(res.data['start_surah'], 1)

    def test_get_juz_ayahs(self):
        res = self.client.get('/api/plugins/quran/juz/1/ayahs/?edition=quran-simple')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('results', res.data)
        self.assertGreaterEqual(len(res.data['results']), 1)

    def test_search_quran(self):
        res = self.client.get('/api/plugins/quran/search/?q=الرحمن&edition=quran-simple')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertGreater(res.data['total_matches'], 0)
        self.assertIn('highlighted_text', res.data['results'][0])

    def test_compare_api(self):
        res = self.client.get('/api/plugins/quran/compare/?surah=1&ayah=1&editions=quran-simple,fa.ansarian')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data['editions']), 2)

    def test_format_reference(self):
        payload = {
            'surah_number': 1,
            'ayah_number': 1,
            'edition_id': 'quran-simple',
            'translation_id': 'fa.ansarian',
            'include_citation': True,
            'lang': 'fa',
        }
        res = self.client.post('/api/plugins/quran/format-reference/', payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('markdown', res.data)
        self.assertIn('الفاتحة', res.data['markdown'])
        self.assertEqual(res.data['external_id'], 'surah:1,ayah:1')
