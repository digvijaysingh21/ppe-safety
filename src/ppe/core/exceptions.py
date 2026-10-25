"""Domain-specific exceptions.

Why: catching `ValueError` everywhere hides which part of the system failed.
A small hierarchy lets callers catch exactly what they can handle, and lets
services map errors to the right response (for example HTTP 422 vs 500).
"""

from __future__ import annotations


class PPEError(Exception):
    """Base class for every error raised on purpose by this project."""


class ConfigError(PPEError):
    """A config file or environment setting is missing or invalid."""


class InvalidBoxError(PPEError, ValueError):
    """A bounding box or score violates geometric or range rules."""


class DataValidationError(PPEError):
    """A dataset or label file breaks the data contract (used from Phase 1)."""
