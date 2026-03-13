"""Tests for configuration management."""

from pathlib import Path

import pytest

from litscope.config import LitScopeSettings, get_settings


class TestLitScopeSettings:
    def test_defaults(self) -> None:
        settings = LitScopeSettings()
        assert settings.db_path == Path("litscope.duckdb")
        assert settings.epub_dir == Path("data/epubs")
        assert settings.log_level == "INFO"
        assert settings.spacy_model == "en_core_web_sm"
        assert (
            settings.sentiment_model
            == "nlptown/bert-base-multilingual-uncased-sentiment"
        )
        assert settings.embedding_model == "all-MiniLM-L6-v2"
        assert settings.sentiment_segments == 100
        assert settings.dialogue_segments == 100
        assert settings.time_slice_years == 25

    def test_path_types(self) -> None:
        settings = LitScopeSettings()
        assert isinstance(settings.db_path, Path)
        assert isinstance(settings.epub_dir, Path)

    def test_env_override(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("LITSCOPE_DB_PATH", "/tmp/test.duckdb")
        monkeypatch.setenv("LITSCOPE_LOG_LEVEL", "DEBUG")
        settings = LitScopeSettings()
        assert settings.db_path == Path("/tmp/test.duckdb")
        assert settings.log_level == "DEBUG"

    def test_analysis_env_override(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("LITSCOPE_SENTIMENT_SEGMENTS", "50")
        monkeypatch.setenv("LITSCOPE_TIME_SLICE_YEARS", "10")
        settings = LitScopeSettings()
        assert settings.sentiment_segments == 50
        assert settings.time_slice_years == 10

    def test_env_prefix(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("LITSCOPE_EPUB_DIR", "/data/books")
        settings = LitScopeSettings()
        assert settings.epub_dir == Path("/data/books")


class TestGetSettings:
    def test_returns_settings_instance(self) -> None:
        get_settings.cache_clear()
        settings = get_settings()
        assert isinstance(settings, LitScopeSettings)

    def test_caching(self) -> None:
        get_settings.cache_clear()
        s1 = get_settings()
        s2 = get_settings()
        assert s1 is s2
