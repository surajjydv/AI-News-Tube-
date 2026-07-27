"""
Custom Exceptions for AI-NewsTube.
"""


class AINewsTubeException(Exception):
    """Base exception for all AI-NewsTube errors."""
    pass


class APIKeyError(AINewsTubeException):
    """Raised when an API key is missing or invalid."""
    pass


class NewsFetchError(AINewsTubeException):
    """Raised when fetching news RSS feeds fails."""
    pass


class ScraperError(AINewsTubeException):
    """Raised when scraping article context fails."""
    pass


class ScriptGenerationError(AINewsTubeException):
    """Raised when LLM fails to generate a news script."""
    pass


class VoiceGenerationError(AINewsTubeException):
    """Raised when TTS fails to generate audio."""
    pass


class VideoGenerationError(AINewsTubeException):
    """Raised when video rendering fails."""
    pass
