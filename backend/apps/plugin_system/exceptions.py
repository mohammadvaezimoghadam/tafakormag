"""
Custom exceptions for Tafakor Plugin System.
"""
from typing import List, Optional


class PluginSystemException(Exception):
    """Base exception for all plugin system errors."""
    pass


class ManifestValidationError(PluginSystemException, ValueError):
    """Raised when a plugin manifest fails schema or semantic validation."""
    def __init__(self, message: str, errors: Optional[List[str]] = None):
        super().__init__(message)
        self.message = message
        self.errors = errors or [message]

    def __str__(self):
        if self.errors and len(self.errors) > 1:
            return f"{self.message}: {'; '.join(self.errors)}"
        return self.message


class PluginRegistrationError(PluginSystemException):
    """Raised when registering a plugin fails."""
    pass


class PluginNotFoundError(PluginSystemException):
    """Raised when a requested plugin cannot be found in registry or DB."""
    pass
