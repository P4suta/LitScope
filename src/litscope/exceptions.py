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


class WorkNotFoundError(LitScopeError):
    """Raised when a work is not found in the database."""


HTTP_STATUS_MAP: dict[type[LitScopeError], tuple[int, str]] = {
    EpubParseError: (422, "Unprocessable Entity"),
    IngestionError: (422, "Unprocessable Entity"),
    AnalyzerNotFoundError: (404, "Not Found"),
    WorkNotFoundError: (404, "Not Found"),
    CircularDependencyError: (400, "Bad Request"),
    DependencyNotSatisfiedError: (400, "Bad Request"),
    DatabaseError: (500, "Internal Server Error"),
}
