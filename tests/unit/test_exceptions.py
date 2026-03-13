"""Tests for custom exception hierarchy."""

import pytest

from litscope.exceptions import (
    DatabaseError,
    EpubParseError,
    IngestionError,
    LitScopeError,
)


class TestExceptionHierarchy:
    def test_base_exception(self) -> None:
        with pytest.raises(LitScopeError):
            raise LitScopeError("base error")

    def test_epub_parse_error_is_litscope_error(self) -> None:
        with pytest.raises(LitScopeError):
            raise EpubParseError("parse failed")

    def test_ingestion_error_is_litscope_error(self) -> None:
        with pytest.raises(LitScopeError):
            raise IngestionError("ingestion failed")

    def test_database_error_is_litscope_error(self) -> None:
        with pytest.raises(LitScopeError):
            raise DatabaseError("db failed")

    def test_error_message(self) -> None:
        err = EpubParseError("corrupt file")
        assert str(err) == "corrupt file"

    def test_all_are_exceptions(self) -> None:
        for exc_class in (LitScopeError, EpubParseError, IngestionError, DatabaseError):
            assert issubclass(exc_class, Exception)
