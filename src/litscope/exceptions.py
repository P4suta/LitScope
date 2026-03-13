"""Custom exception hierarchy for LitScope."""


class LitScopeError(Exception):
    """Base exception for all LitScope errors."""


class EpubParseError(LitScopeError):
    """Raised when EPUB parsing fails."""


class IngestionError(LitScopeError):
    """Raised when the ingestion pipeline encounters an error."""


class DatabaseError(LitScopeError):
    """Raised when a database operation fails."""


class AnalysisError(LitScopeError):
    """Raised when an analysis operation fails."""


class AnalyzerNotFoundError(AnalysisError):
    """Raised when a requested analyzer is not registered."""


class CircularDependencyError(AnalysisError):
    """Raised when analyzer dependencies form a cycle."""


class DependencyNotSatisfiedError(AnalysisError):
    """Raised when a required dependency has not been satisfied."""
