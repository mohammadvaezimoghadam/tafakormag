"""
Adversarial and Resilience Tests for Quran Plugin REST API endpoints (`/api/plugins/quran/`).
Tests parameter fuzzing, SQL injection, XSS payloads, out-of-bounds inputs,
comparative view edge cases, and pagination boundaries.
"""
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.core.management import call_command
from plugins.quran.models import QuranEdition, QuranSurah, QuranAyah, QuranJuz


class QuranAPIAdversarialTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('import_quran', sample=True, force=True)

    def setUp(self):
        self.client = APIClient()

    # -------------------------------------------------------------------------
    # 1. Surahs Endpoints Bounds & Filtering
    # -------------------------------------------------------------------------
    def test_surah_detail_out_of_bounds(self):
        """Out-of-bounds surah numbers must return 404 Not Found."""
        for invalid_num in [0, 115, 9999]:
            res = self.client.get(f'/api/plugins/quran/surahs/{invalid_num}/')
            self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_surah_list_invalid_filter_values(self):
        """Invalid query parameters on surahs list should return empty results without 500 error."""
        res = self.client.get('/api/plugins/quran/surahs/?revelation_type=InvalidType')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 0)

        res_juz = self.client.get('/api/plugins/quran/surahs/?juz=999')
        self.assertEqual(res_juz.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res_juz.data), 0)

    def test_surah_ayahs_inverted_range(self):
        """When from_ayah > to_ayah, API returns count=0 without crashing."""
        res = self.client.get('/api/plugins/quran/surahs/1/ayahs/?from_ayah=7&to_ayah=2')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['count'], 0)
        self.assertEqual(len(res.data['ayahs']), 0)

    def test_surah_ayahs_non_existent_edition(self):
        """Requesting ayahs for non-existent edition returns empty ayahs list without error."""
        res = self.client.get('/api/plugins/quran/surahs/1/ayahs/?edition=non-existent-edition-xyz')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['count'], 0)
        self.assertEqual(len(res.data['ayahs']), 0)

    def test_surah_ayahs_non_existent_translation(self):
        """Requesting with non-existent translation returns primary ayahs with null/empty translation."""
        res = self.client.get('/api/plugins/quran/surahs/1/ayahs/?edition=quran-simple&with_translation=non-existent-trans')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['count'], 7)
        first_ayah = res.data['ayahs'][0]
        # Primary text present, translation text empty
        self.assertIn('بِسْمِ', first_ayah['text'])
        self.assertEqual(first_ayah['translation']['text'], '')

    def test_surah_ayahs_pagination_boundary(self):
        """Paginating beyond total pages returns 404 or empty page."""
        res = self.client.get('/api/plugins/quran/surahs/1/ayahs/?page=999&page_size=5')
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    # -------------------------------------------------------------------------
    # 2. Ayah Detail Endpoints Coordinates & Global Numbers
    # -------------------------------------------------------------------------
    def test_ayah_detail_by_coordinates_invalid(self):
        """Invalid surah/ayah coordinate combinations return 404."""
        invalid_coords = [
            (1, 8),    # Al-Fatihah has only 7 ayahs
            (0, 1),    # Invalid surah 0
            (115, 1),  # Invalid surah 115
            (1, 999),  # Out-of-bounds ayah
        ]
        for s_num, a_num in invalid_coords:
            res = self.client.get(f'/api/plugins/quran/ayahs/{s_num}/{a_num}/')
            self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_ayah_detail_by_global_number_out_of_bounds(self):
        """Global ayah number <= 0 or > 6236 returns 404."""
        for invalid_g in [0, 6237, 99999]:
            res = self.client.get(f'/api/plugins/quran/ayahs/{invalid_g}/')
            self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    # -------------------------------------------------------------------------
    # 3. Juz Endpoints Bounds
    # -------------------------------------------------------------------------
    def test_juz_detail_bounds(self):
        """Juz number < 1 or > 30 returns 404."""
        for invalid_j in [0, 31, 100]:
            res = self.client.get(f'/api/plugins/quran/juz/{invalid_j}/')
            self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_juz_ayahs_non_existent_edition(self):
        """Juz ayahs with non-existent edition returns empty results."""
        res = self.client.get('/api/plugins/quran/juz/1/ayahs/?edition=non-existent-edition')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['count'], 0)
        self.assertEqual(len(res.data['results']), 0)

    # -------------------------------------------------------------------------
    # 4. Editions Endpoints & Filtering
    # -------------------------------------------------------------------------
    def test_edition_detail_non_existent(self):
        """Non-existent edition identifier returns 404."""
        res = self.client.get('/api/plugins/quran/editions/non-existent-edition-slug/')
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_edition_list_query_filters(self):
        """Filtering editions by language/type/q returns expected filtered subset."""
        res_fa = self.client.get('/api/plugins/quran/editions/?language=fa')
        self.assertEqual(res_fa.status_code, status.HTTP_200_OK)
        for ed in res_fa.data:
            self.assertEqual(ed['language'], 'fa')

        res_none = self.client.get('/api/plugins/quran/editions/?language=non_existent_lang')
        self.assertEqual(res_none.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res_none.data), 0)

    # -------------------------------------------------------------------------
    # 5. Search API Fuzzing, SQLi, XSS, and Edge Cases
    # -------------------------------------------------------------------------
    def test_search_empty_and_short_query(self):
        """Search query with < 2 characters or whitespace returns 400 Bad Request."""
        res_empty = self.client.get('/api/plugins/quran/search/?q=')
        self.assertEqual(res_empty.status_code, status.HTTP_400_BAD_REQUEST)

        res_ws = self.client.get('/api/plugins/quran/search/?q=   ')
        self.assertEqual(res_ws.status_code, status.HTTP_400_BAD_REQUEST)

        res_single = self.client.get('/api/plugins/quran/search/?q=a')
        self.assertEqual(res_single.status_code, status.HTTP_400_BAD_REQUEST)

    def test_search_sql_injection_payloads(self):
        """SQL injection payloads must be treated as literal strings and not crash or corrupt database."""
        sqli_payloads = [
            "' OR '1'='1",
            "'; DROP TABLE plugins_quran_quranayah; --",
            "1' UNION SELECT 1, 2, 3, 4, 5, 6, 7, 8, 9, 10 --",
            "admin'--",
            "' OR 1=1 #",
        ]
        for payload in sqli_payloads:
            res = self.client.get('/api/plugins/quran/search/', {'q': payload, 'edition': 'quran-simple'})
            self.assertEqual(res.status_code, status.HTTP_200_OK)
            self.assertIn('results', res.data)
            self.assertIn('total_matches', res.data)

    def test_search_xss_and_html_payloads(self):
        """XSS and HTML tags in search query must not cause 500 error or uncaught regex error."""
        xss_payloads = [
            '<script>alert("xss")</script>',
            '<img src=x onerror=alert(1)>',
            '<mark>nested mark</mark>',
            '<b>bold term</b>',
        ]
        for payload in xss_payloads:
            res = self.client.get('/api/plugins/quran/search/', {'q': payload, 'edition': 'quran-simple'})
            self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_search_regex_special_characters(self):
        """Regex meta-characters in search query must not break regex compiler during highlighting."""
        regex_chars = [
            ".*",
            "+++",
            "???",
            "[a-z]+",
            "(((",
            "\\\\\\",
            "^$$$*",
        ]
        for payload in regex_chars:
            res = self.client.get('/api/plugins/quran/search/', {'q': payload, 'edition': 'quran-simple'})
            self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_search_unicode_and_emojis(self):
        """Search query with high Unicode symbols and emojis handles gracefully."""
        res = self.client.get('/api/plugins/quran/search/', {'q': '﷽😀🔥', 'edition': 'quran-simple'})
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_search_with_non_existent_surah_or_juz(self):
        """Search scoped to non-existent surah or juz returns 0 matches."""
        res_surah = self.client.get('/api/plugins/quran/search/?q=الله&surah=999')
        self.assertEqual(res_surah.status_code, status.HTTP_200_OK)
        self.assertEqual(res_surah.data['total_matches'], 0)

        res_juz = self.client.get('/api/plugins/quran/search/?q=الله&juz=999')
        self.assertEqual(res_juz.status_code, status.HTTP_200_OK)
        self.assertEqual(res_juz.data['total_matches'], 0)

    # -------------------------------------------------------------------------
    # 6. Compare API Adversarial Tests
    # -------------------------------------------------------------------------
    def test_compare_api_missing_parameters(self):
        """Missing 'surah' or 'ayah' parameter returns 400 Bad Request."""
        res1 = self.client.get('/api/plugins/quran/compare/?surah=1')
        self.assertEqual(res1.status_code, status.HTTP_400_BAD_REQUEST)

        res2 = self.client.get('/api/plugins/quran/compare/?ayah=1')
        self.assertEqual(res2.status_code, status.HTTP_400_BAD_REQUEST)

    def test_compare_api_non_existent_surah_and_ayah(self):
        """Non-existent Surah or Ayah in compare endpoint returns 404."""
        res_surah = self.client.get('/api/plugins/quran/compare/?surah=999&ayah=1')
        self.assertEqual(res_surah.status_code, status.HTTP_404_NOT_FOUND)

        res_ayah = self.client.get('/api/plugins/quran/compare/?surah=1&ayah=999')
        self.assertEqual(res_ayah.status_code, status.HTTP_404_NOT_FOUND)

    def test_compare_api_non_existent_editions(self):
        """Specifying all non-existent edition identifiers returns 404."""
        res = self.client.get('/api/plugins/quran/compare/?surah=1&ayah=1&editions=fake1,fake2')
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_compare_api_partial_editions(self):
        """Specifying mixed valid and invalid edition identifiers returns only the valid ones."""
        res = self.client.get('/api/plugins/quran/compare/?surah=1&ayah=1&editions=quran-simple,fake-edition-xyz')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data['editions']), 1)
        self.assertEqual(res.data['editions'][0]['edition']['identifier'], 'quran-simple')

    # -------------------------------------------------------------------------
    # 7. Format Reference API Adversarial Tests
    # -------------------------------------------------------------------------
    def test_format_reference_missing_surah(self):
        """Missing surah field returns 400 Validation Error."""
        res = self.client.post('/api/plugins/quran/format-reference/', {'ayah_from': 1, 'ayah_to': 3}, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_format_reference_inverted_ayah_range(self):
        """ayah_to < ayah_from returns 400 Validation Error."""
        payload = {
            'surah_number': 1,
            'ayah_from': 5,
            'ayah_to': 2,
        }
        res = self.client.post('/api/plugins/quran/format-reference/', payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_format_reference_out_of_bounds_surah_validation(self):
        """Surah number > 114 returns 400 validation error from serializer constraint."""
        payload = {
            'surah_number': 999,
            'ayah_from': 1,
            'ayah_to': 1,
        }
        res = self.client.post('/api/plugins/quran/format-reference/', payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_format_reference_non_existent_ayah_range(self):
        """Out of bounds ayah range returns 404 Not Found."""
        payload = {
            'surah_number': 1,
            'ayah_from': 50,
            'ayah_to': 60,
        }
        res = self.client.post('/api/plugins/quran/format-reference/', payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_format_reference_invalid_language(self):
        """Unsupported language choice returns 400 Validation Error."""
        payload = {
            'surah_number': 1,
            'ayah_number': 1,
            'lang': 'unsupported_lang_xx',
        }
        res = self.client.post('/api/plugins/quran/format-reference/', payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
