"""
Adversarial and Stress Tests for Quran Importer Command (`import_quran`).
Tests edge cases, corrupted fixtures, transactional rollback, dry-run, force,
extreme batch sizes, and data integrity.
"""
import os
import tempfile
import json
from pathlib import Path
from django.test import TransactionTestCase
from django.core.management import call_command, CommandError
from plugins.quran.models import QuranEdition, QuranSurah, QuranJuz, QuranAyah


class QuranImporterAdversarialTests(TransactionTestCase):
    """
    TransactionTestCase ensures transactions commit and rollback realistically
    during management command execution.
    """

    def setUp(self):
        # Ensure base canonical Surahs and Juzs are present
        call_command('import_quran', sample=True, force=True)

    def test_importer_corrupted_json_syntax(self):
        """Passing a file with malformed JSON syntax must raise CommandError or json decode error."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as tmp:
            tmp.write("{ invalid json content: [")
            tmp_path = tmp.name

        try:
            with self.assertRaises(Exception):
                call_command('import_quran', file=tmp_path)
        finally:
            Path(tmp_path).unlink(missing_ok=True)

    def test_importer_empty_json_file(self):
        """Passing an empty JSON object must raise CommandError."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as tmp:
            tmp.write("{}")
            tmp_path = tmp.name

        try:
            with self.assertRaises(CommandError):
                call_command('import_quran', file=tmp_path)
        finally:
            Path(tmp_path).unlink(missing_ok=True)

    def test_importer_invalid_root_types(self):
        """Passing non-dict/non-list root (e.g. int, bool, string) must raise CommandError."""
        for invalid_root in [12345, True, "just a string"]:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as tmp:
                json.dump(invalid_root, tmp)
                tmp_path = tmp.name

            try:
                with self.assertRaises(CommandError):
                    call_command('import_quran', file=tmp_path)
            finally:
                Path(tmp_path).unlink(missing_ok=True)

    def test_importer_missing_identifier(self):
        """Dataset without edition identifier must raise CommandError."""
        payload = {
            "edition": {
                "name": "No Identifier Edition",
                "language": "ar"
            },
            "ayahs": [
                {"surah": 1, "number_in_surah": 1, "text": "بِسْمِ اللَّهِ"}
            ]
        }
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as tmp:
            json.dump(payload, tmp)
            tmp_path = tmp.name

        try:
            with self.assertRaises(CommandError):
                call_command('import_quran', file=tmp_path)
        finally:
            Path(tmp_path).unlink(missing_ok=True)

    def test_importer_missing_ayahs(self):
        """Dataset with empty ayahs list must raise CommandError."""
        payload = {
            "edition": {
                "identifier": "empty-ayahs-edition",
                "name": "Empty Edition",
                "language": "ar"
            },
            "ayahs": []
        }
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as tmp:
            json.dump(payload, tmp)
            tmp_path = tmp.name

        try:
            with self.assertRaises(CommandError):
                call_command('import_quran', file=tmp_path)
            self.assertFalse(QuranEdition.objects.filter(identifier='empty-ayahs-edition').exists())
        finally:
            Path(tmp_path).unlink(missing_ok=True)

    def test_importer_empty_text_rejection(self):
        """Ayah with empty text or whitespace-only text must be rejected."""
        payload = {
            "edition": {
                "identifier": "empty-text-edition",
                "name": "Empty Text Edition",
                "language": "ar"
            },
            "ayahs": [
                {"surah": 1, "number_in_surah": 1, "text": "   "}
            ]
        }
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as tmp:
            json.dump(payload, tmp)
            tmp_path = tmp.name

        try:
            with self.assertRaises(CommandError):
                call_command('import_quran', file=tmp_path)
            self.assertFalse(QuranEdition.objects.filter(identifier='empty-text-edition').exists())
        finally:
            Path(tmp_path).unlink(missing_ok=True)

    def test_importer_invalid_surah_numbers(self):
        """Surah numbers < 1 or > 114 must be rejected."""
        for invalid_s in [0, 115, -1, 999]:
            payload = {
                "edition": {
                    "identifier": f"invalid-surah-{invalid_s}",
                    "name": f"Invalid Surah {invalid_s}",
                    "language": "ar"
                },
                "ayahs": [
                    {"surah": invalid_s, "number_in_surah": 1, "text": "Test"}
                ]
            }
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as tmp:
                json.dump(payload, tmp)
                tmp_path = tmp.name

            try:
                with self.assertRaises(CommandError):
                    call_command('import_quran', file=tmp_path)
                self.assertFalse(QuranEdition.objects.filter(identifier=f"invalid-surah-{invalid_s}").exists())
            finally:
                Path(tmp_path).unlink(missing_ok=True)

    def test_importer_transactional_rollback_on_mid_dataset_failure(self):
        """
        Verify that if 49 verses are valid and the 50th verse is invalid,
        the entire transaction is rolled back: 0 verses exist in the DB for that edition.
        """
        valid_ayahs = [
            {"surah": 1, "number_in_surah": i, "text": f"Ayah content {i}"}
            for i in range(1, 8)
        ]
        # Append an invalid ayah at the end
        valid_ayahs.append({"surah": 999, "number_in_surah": 8, "text": "Invalid Surah 999"})

        payload = {
            "edition": {
                "identifier": "rollback-test-edition",
                "name": "Rollback Test Edition",
                "language": "ar"
            },
            "ayahs": valid_ayahs
        }
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as tmp:
            json.dump(payload, tmp)
            tmp_path = tmp.name

        try:
            with self.assertRaises(CommandError):
                call_command('import_quran', file=tmp_path)

            # Strict verification: no edition and zero ayahs created
            self.assertFalse(QuranEdition.objects.filter(identifier='rollback-test-edition').exists())
            self.assertEqual(QuranAyah.objects.filter(edition_id='rollback-test-edition').count(), 0)
        finally:
            Path(tmp_path).unlink(missing_ok=True)

    def test_importer_force_and_no_force_behavior(self):
        """
        Without --force, importing an existing edition must skip with a warning and not crash.
        With --force, importing an existing edition must overwrite successfully.
        """
        payload1 = {
            "edition": {
                "identifier": "force-test-edition",
                "name": "Initial Name",
                "language": "ar"
            },
            "ayahs": [
                {"surah": 1, "number_in_surah": 1, "text": "Original text"}
            ]
        }
        payload2 = {
            "edition": {
                "identifier": "force-test-edition",
                "name": "Updated Name",
                "language": "ar"
            },
            "ayahs": [
                {"surah": 1, "number_in_surah": 1, "text": "Updated text"}
            ]
        }
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as tmp1:
            json.dump(payload1, tmp1)
            tmp1_path = tmp1.name
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as tmp2:
            json.dump(payload2, tmp2)
            tmp2_path = tmp2.name

        try:
            # 1. Initial import
            call_command('import_quran', file=tmp1_path)
            ed = QuranEdition.objects.get(identifier='force-test-edition')
            self.assertEqual(ed.name, "Initial Name")
            a = QuranAyah.objects.get(edition_id='force-test-edition', surah__number=1, number_in_surah=1)
            self.assertEqual(a.text, "Original text")

            # 2. Re-import without force (should skip)
            call_command('import_quran', file=tmp2_path)
            ed.refresh_from_db()
            self.assertEqual(ed.name, "Initial Name")
            a_unmodified = QuranAyah.objects.get(edition_id='force-test-edition', surah__number=1, number_in_surah=1)
            self.assertEqual(a_unmodified.text, "Original text")

            # 3. Re-import with force (should update)
            call_command('import_quran', file=tmp2_path, force=True)
            ed.refresh_from_db()
            self.assertEqual(ed.name, "Updated Name")
            a_updated = QuranAyah.objects.get(edition_id='force-test-edition', surah__number=1, number_in_surah=1)
            self.assertEqual(a_updated.text, "Updated text")
        finally:
            Path(tmp1_path).unlink(missing_ok=True)
            Path(tmp2_path).unlink(missing_ok=True)

    def test_importer_dry_run_guarantee(self):
        """
        --dry-run validates data structure but writes NOTHING to database.
        """
        payload = {
            "edition": {
                "identifier": "dry-run-guarantee-edition",
                "name": "Dry Run Guarantee",
                "language": "ar"
            },
            "ayahs": [
                {"surah": 1, "number_in_surah": 1, "text": "Dry run text"}
            ]
        }
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as tmp:
            json.dump(payload, tmp)
            tmp_path = tmp.name

        try:
            call_command('import_quran', file=tmp_path, dry_run=True)
            self.assertFalse(QuranEdition.objects.filter(identifier='dry-run-guarantee-edition').exists())
            self.assertEqual(QuranAyah.objects.filter(edition_id='dry-run-guarantee-edition').count(), 0)
        finally:
            Path(tmp_path).unlink(missing_ok=True)

    def test_importer_extreme_batch_sizes(self):
        """
        Verify importer operates identically with --batch-size 1 and --batch-size 10000.
        """
        payload = {
            "edition": {
                "identifier": "batch-size-test",
                "name": "Batch Size Test",
                "language": "ar"
            },
            "ayahs": [
                {"surah": 1, "number_in_surah": 1, "text": "Verse 1"},
                {"surah": 1, "number_in_surah": 2, "text": "Verse 2"},
                {"surah": 1, "number_in_surah": 3, "text": "Verse 3"},
            ]
        }
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as tmp:
            json.dump(payload, tmp)
            tmp_path = tmp.name

        try:
            # Batch size = 1
            call_command('import_quran', file=tmp_path, force=True, batch_size=1)
            self.assertEqual(QuranAyah.objects.filter(edition_id='batch-size-test').count(), 3)

            # Batch size = 10000
            call_command('import_quran', file=tmp_path, force=True, batch_size=10000)
            self.assertEqual(QuranAyah.objects.filter(edition_id='batch-size-test').count(), 3)
        finally:
            Path(tmp_path).unlink(missing_ok=True)

    def test_importer_non_existent_file_and_dir(self):
        """Non-existent file and directory paths must raise CommandError."""
        with self.assertRaises(CommandError):
            call_command('import_quran', file='non_existent_file_path_xyz.json')

        with self.assertRaises(CommandError):
            call_command('import_quran', dir='non_existent_dir_path_xyz')

    def test_importer_directory_with_no_json_files(self):
        """Directory with no JSON files must handle gracefully without raising unhandled exception."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Create a non-json file
            Path(tmp_dir, 'readme.txt').write_text('Not a json file')
            call_command('import_quran', dir=tmp_dir)

    def test_importer_translation_edition_does_not_strip_bismillah(self):
        """
        When importing a translation edition (type='translation'), Bismillah on Surah 2:1
        must NOT be stripped.
        """
        payload = {
            "edition": {
                "identifier": "trans-bismillah-test",
                "name": "Translation Bismillah Test",
                "language": "fa",
                "type": "translation"
            },
            "ayahs": [
                {"surah": 2, "number_in_surah": 1, "text": "به نام خدا. الف لام میم"}
            ]
        }
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as tmp:
            json.dump(payload, tmp)
            tmp_path = tmp.name

        try:
            call_command('import_quran', file=tmp_path)
            a = QuranAyah.objects.get(edition_id='trans-bismillah-test', surah__number=2, number_in_surah=1)
            self.assertEqual(a.text, "به نام خدا. الف لام میم")
        finally:
            Path(tmp_path).unlink(missing_ok=True)
