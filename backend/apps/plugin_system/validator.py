import re
from typing import Dict, Any, List, Set
from .exceptions import ManifestValidationError

try:
    import jsonschema
    JSONSCHEMA_AVAILABLE = True
except ImportError:
    JSONSCHEMA_AVAILABLE = False


class ManifestValidator:
    """
    Strict validator for Tafakor plugin manifests (manifest_version == 1).
    """
    ALLOWED_CAPABILITIES: Set[str] = {
        'composer_action',
        'mini_app',
        'search_provider',
        'topic_integration',
        'bot_action',
        'feed_card',
    }

    ALLOWED_SCOPES: Set[str] = {
        'read:content',
        'write:composer',
        'manage:topic',
        'read:quran',
        'write:bot',
    }

    IDENTIFIER_REGEX = re.compile(r'^[a-z0-9_-]+$')
    SEMVER_REGEX = re.compile(r'^\d+\.\d+\.\d+(-[a-zA-Z0-9_.]+)?$')

    @classmethod
    def validate(cls, manifest_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validates manifest data dictionary against Tafakor Plugin Specification.
        Returns validated dict or raises ManifestValidationError.
        """
        errors: List[str] = []

        if not isinstance(manifest_data, dict):
            raise ManifestValidationError("Manifest must be a JSON object / dictionary.")

        # 1. Manifest Version (strict requirement: integer == 1)
        if 'manifest_version' not in manifest_data:
            errors.append("Field 'manifest_version' is required.")
        else:
            manifest_version = manifest_data['manifest_version']
            # Must strictly be integer 1 (reject booleans like True since isinstance(True, int) is True in Python)
            if isinstance(manifest_version, bool) or not isinstance(manifest_version, int) or manifest_version != 1:
                errors.append(f"Invalid manifest_version: {manifest_version}. Expected 1.")

        # 2. Identifier
        if 'identifier' not in manifest_data:
            errors.append("Field 'identifier' is required.")
        else:
            identifier = manifest_data['identifier']
            if not isinstance(identifier, str) or not identifier.strip():
                errors.append("Field 'identifier' must be a non-empty string.")
            elif not cls.IDENTIFIER_REGEX.match(identifier):
                errors.append(f"Invalid identifier '{identifier}'. Must match lowercase pattern '^[a-z0-9_-]+$'.")

        # 3. Name
        if 'name' not in manifest_data:
            errors.append("Field 'name' is required.")
        else:
            name = manifest_data['name']
            if not isinstance(name, str) or not name.strip():
                errors.append("Field 'name' must be a non-empty string.")

        # 4. Version
        if 'version' not in manifest_data:
            errors.append("Field 'version' is required.")
        else:
            version = manifest_data['version']
            if not isinstance(version, str):
                errors.append("Field 'version' must be a semver string (e.g. '1.0.0').")
            elif not cls.SEMVER_REGEX.match(version):
                errors.append(f"Invalid version format '{version}'. Must follow semantic versioning (e.g. '1.0.0').")

        # 5. Capabilities
        capabilities = manifest_data.get('capabilities', [])
        if not isinstance(capabilities, list):
            errors.append("Field 'capabilities' must be a list.")
        else:
            for cap in capabilities:
                if cap not in cls.ALLOWED_CAPABILITIES:
                    errors.append(f"Unknown capability '{cap}'. Allowed: {sorted(cls.ALLOWED_CAPABILITIES)}")

        # 6. Scopes
        scopes = manifest_data.get('scopes', [])
        if not isinstance(scopes, list):
            errors.append("Field 'scopes' must be a list.")
        else:
            for scope in scopes:
                if scope not in cls.ALLOWED_SCOPES:
                    errors.append(f"Unknown scope '{scope}'. Allowed: {sorted(cls.ALLOWED_SCOPES)}")

        # 7. Settings Schema & Default Config
        settings_schema = manifest_data.get('settings_schema', {})
        default_config = manifest_data.get('default_config', {})

        if not isinstance(settings_schema, dict):
            errors.append("Field 'settings_schema' must be a dict / JSON object.")
        if not isinstance(default_config, dict):
            errors.append("Field 'default_config' must be a dict / JSON object.")

        if JSONSCHEMA_AVAILABLE and isinstance(settings_schema, dict) and settings_schema:
            try:
                jsonschema.Draft7Validator.check_schema(settings_schema)
            except jsonschema.exceptions.SchemaError as se:
                errors.append(f"Invalid 'settings_schema' JSON Schema: {se.message}")

            if isinstance(default_config, dict) and default_config:
                try:
                    jsonschema.validate(instance=default_config, schema=settings_schema)
                except jsonschema.exceptions.ValidationError as ve:
                    errors.append(f"'default_config' does not conform to 'settings_schema': {ve.message}")

        if errors:
            raise ManifestValidationError(f"Manifest validation failed with {len(errors)} error(s).", errors=errors)

        # Return standardized copy with defaults filled
        result = dict(manifest_data)
        result.setdefault('capabilities', [])
        result.setdefault('scopes', [])
        result.setdefault('settings_schema', {})
        result.setdefault('default_config', {})
        result.setdefault('description', '')
        result.setdefault('author', '')
        result.setdefault('icon', 'BookOpen')
        result.setdefault('is_core', False)
        return result
