"""
Tests for Atomic Source-Driven Quran Importer Command.
"""
import tempfile
import json
from pathlib import Path
from django.test import TestCase
from django.core.management import call_command, CommandError
from plugins.quran.models import QuranEdition, QuranSurah, QuranJuz, QuranAyah


class QuranImporterCommandTests(TestCase):
    def test_import_seed_and_sample(self):
        call_command('import_quran', sample=True, force=True)
        self.assertEqual(QuranSurah.objects.count(), 114)
        self.assertEqual(QuranJuz.objects.count(), 30)
        self.assertTrue(QuranEdition.objects.filter(identifier='quran-simple').exists())
        self.assertGreaterEqual(QuranAyah.objects.filter(edition_id='quran-simple', surah__number=1).count(), 7)

    def test_dry_run_mode(self):
        call_command('import_quran', sample=True, dry_run=True)
        # In dry-run mode, models are not committed if DB was empty initially
        # Dry run must succeed without error

    def test_atomic_rollback_on_invalid_data(self):
        # Create corrupted JSON fixture referencing invalid surah 999
        corrupted_data = {
            "edition": {
                "identifier": "invalid-edition",
                "name": "Invalid Edition",
                "language": "ar"
            },
            "ayahs": [
                {"surah": 1, "number_in_surah": 1, "text": "Valid text"},
                {"surah": 999, "number_in_surah": 2, "text": "Invalid surah number"},
            ]
        }
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as tmp:
            json.dump(corrupted_data, tmp)
            tmp_path = tmp.name

        try:
            with self.assertRaises(CommandError):
                call_command('import_quran', file=tmp_path)

            # Ensure complete rollback: edition and ayahs not created
            self.assertFalse(QuranEdition.objects.filter(identifier='invalid-edition').exists())
            self.assertEqual(QuranAyah.objects.filter(edition_id='invalid-edition').count(), 0)
        finally:
            Path(tmp_path).unlink(missing_ok=True)

    def test_bismillah_prefix_stripping(self):
        # Ensure surahs exist
        call_command('import_quran', sample=True, force=True)

        bismillah_data = {
            "edition": {
                "identifier": "bismillah-test",
                "name": "Bismillah Test",
                "language": "ar",
                "type": "quran"
            },
            "ayahs": [
                # Surah 1:1 - Should preserve Bismillah
                {"surah": 1, "number_in_surah": 1, "text": "بِسْمِ ٱللَّهِ ٱلرَّحْمَٰنِ ٱلرَّحِيمِ"},
                # Surah 2:1 - Erroneous Bismillah prefix should be stripped
                {"surah": 2, "number_in_surah": 1, "text": "بِسْمِ ٱللَّهِ ٱلرَّحْمَٰنِ ٱلرَّحِيمِ الٓمٓ"},
            ]
        }
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as tmp:
            json.dump(bismillah_data, tmp)
            tmp_path = tmp.name

        try:
            call_command('import_quran', file=tmp_path)
            a1 = QuranAyah.objects.get(edition_id='bismillah-test', surah__number=1, number_in_surah=1)
            a2 = QuranAyah.objects.get(edition_id='bismillah-test', surah__number=2, number_in_surah=1)

            self.assertEqual(a1.text, "بِسْمِ ٱللَّهِ ٱلرَّحْمَٰنِ ٱلرَّحِيمِ")
            self.assertEqual(a2.text, "الٓمٓ")
        finally:
            Path(tmp_path).unlink(missing_ok=True)
