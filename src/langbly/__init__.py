"""Langbly — Official Python SDK for the Langbly translation API."""

from .client import (
    AuthenticationError,
    Detection,
    Langbly,
    LangblyError,
    Language,
    RateLimitError,
    Translation,
)

__all__ = [
    "AuthenticationError",
    "Detection",
    "Langbly",
    "LangblyError",
    "Language",
    "RateLimitError",
    "Translation",
]
__version__ = "0.1.0"
