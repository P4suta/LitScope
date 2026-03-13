"""Custom exception hierarchy for LitScope."""


class LitScopeError(Exception):
    """Base exception for all LitScope errors."""


class EpubParseError(LitScopeError):
    """Raised when EPUB parsing fails."""


class IngestionError(LitScopeError):
    """Raised when the ingestion pipeline encounters an error."""


class DatabaseError(LitScopeError):
    """Raised when a database operation fails."""
