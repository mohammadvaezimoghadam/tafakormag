"""
Unit tests for ManifestValidator enforcing schema v1, capabilities, scopes, and regex constraints.
"""
from django.test import TestCase
from apps.plugin_system.validator import ManifestValidator
from apps.plugin_system.exceptions import ManifestValidationError


class ManifestValidatorTestCase(TestCase):
    def setUp(self):
        self.valid_manifest = {
            "manifest_version": 1,
            "identifier": "quran",
            "name": "قرآن کریم",
            "version": "1.0.0",
            "description": "پلاگین رسمی قرآن کریم",
            "author": "Tafakor Team",
            "icon": "BookOpen",
            "entry_point": "plugins.quran.plugin.QuranPlugin",
            "capabilities": ["composer_action", "mini_app", "search_provider", "topic_integration"],
            "scopes": ["read:quran", "write:composer"],
            "settings_schema": {
                "type": "object",
                "properties": {
                    "default_edition": {"type": "string"}
                }
            },
            "default_config": {
                "default_edition": "quran-simple"
            }
        }

    def test_valid_manifest_passes(self):
        """A complete valid manifest dictionary must validate without exceptions."""
        validated = ManifestValidator.validate(self.valid_manifest)
        self.assertEqual(validated["identifier"], "quran")
        self.assertEqual(validated["manifest_version"], 1)

    def test_minimal_valid_manifest_passes(self):
        """Manifest with only mandatory fields must validate with safe defaults."""
        minimal = {
            "manifest_version": 1,
            "identifier": "minimal-plugin",
            "name": "Minimal",
            "version": "0.1.0"
        }
        validated = ManifestValidator.validate(minimal)
        self.assertEqual(validated["capabilities"], [])
        self.assertEqual(validated["scopes"], [])
        self.assertEqual(validated["settings_schema"], {})
        self.assertEqual(validated["default_config"], {})
        self.assertEqual(validated["description"], "")

    def test_non_dict_manifest_fails(self):
        """Non-dictionary manifest must raise ManifestValidationError."""
        with self.assertRaises(ManifestValidationError):
            ManifestValidator.validate("not a dict")
        with self.assertRaises(ManifestValidationError):
            ManifestValidator.validate(None)
        with self.assertRaises(ManifestValidationError):
            ManifestValidator.validate([1, 2, 3])

    def test_missing_required_fields(self):
        """Missing any required field raises ManifestValidationError."""
        required_fields = ["manifest_version", "identifier", "name", "version"]
        for field in required_fields:
            data = dict(self.valid_manifest)
            del data[field]
            with self.assertRaises(ManifestValidationError, msg=f"Should fail when missing '{field}'"):
                ManifestValidator.validate(data)

    def test_invalid_manifest_version(self):
        """Manifest version other than integer 1 must raise ManifestValidationError."""
        invalid_versions = [0, 2, "1", 1.0, None, -1, True]
        for ver in invalid_versions:
            data = dict(self.valid_manifest, manifest_version=ver)
            with self.assertRaises(ManifestValidationError, msg=f"Should fail for manifest_version={ver}"):
                ManifestValidator.validate(data)

    def test_identifier_regex_validation(self):
        """Identifier must strictly match ^[a-z0-9_-]+$."""
        invalid_identifiers = [
            "Quran",            # Uppercase
            "quran plugin",     # Space
            "quran@123",        # Special character
            "quran.core",       # Dot
            "قرآن",             # Non-ascii
            "",                 # Empty
            "   ",              # Whitespace
            "quran/reader"      # Slash
        ]
        for ident in invalid_identifiers:
            data = dict(self.valid_manifest, identifier=ident)
            with self.assertRaises(ManifestValidationError, msg=f"Should fail for identifier='{ident}'"):
                ManifestValidator.validate(data)

        valid_identifiers = ["quran", "quran_v1", "my-plugin-2", "a", "123_abc-xyz"]
        for ident in valid_identifiers:
            data = dict(self.valid_manifest, identifier=ident)
            validated = ManifestValidator.validate(data)
            self.assertEqual(validated["identifier"], ident)

    def test_invalid_capabilities(self):
        """Capabilities must be a list containing only allowed capability keywords."""
        with self.assertRaises(ManifestValidationError):
            ManifestValidator.validate(dict(self.valid_manifest, capabilities="composer_action"))

        with self.assertRaises(ManifestValidationError):
            ManifestValidator.validate(dict(self.valid_manifest, capabilities=["composer_action", "arbitrary_exec"]))

    def test_invalid_scopes(self):
        """Scopes must be a list containing only recognized scope permissions."""
        with self.assertRaises(ManifestValidationError):
            ManifestValidator.validate(dict(self.valid_manifest, scopes="read:quran"))

        with self.assertRaises(ManifestValidationError):
            ManifestValidator.validate(dict(self.valid_manifest, scopes=["read:quran", "root:admin"]))

    def test_malformed_settings_schema(self):
        """settings_schema and default_config must be dictionaries."""
        with self.assertRaises(ManifestValidationError):
            ManifestValidator.validate(dict(self.valid_manifest, settings_schema="not a dict"))

        with self.assertRaises(ManifestValidationError):
            ManifestValidator.validate(dict(self.valid_manifest, default_config=["not a dict"]))

    def test_schema_mismatch_in_default_config(self):
        """When default_config violates settings_schema, validation fails."""
        data = dict(
            self.valid_manifest,
            settings_schema={
                "type": "object",
                "properties": {
                    "port": {"type": "integer"}
                },
                "required": ["port"]
            },
            default_config={
                "port": "not-an-integer"
            }
        )
        with self.assertRaises(ManifestValidationError):
            ManifestValidator.validate(data)
