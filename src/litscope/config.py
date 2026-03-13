"""Configuration management with pydantic-settings."""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings


class LitScopeSettings(BaseSettings):
    """Application settings loaded from environment variables with LITSCOPE_ prefix."""

    model_config = {"env_prefix": "LITSCOPE_"}

    db_path: Path = Path("litscope.duckdb")
    epub_dir: Path = Path("data/epubs")
    log_level: str = "INFO"
    spacy_model: str = "en_core_web_sm"
    sentiment_model: str = "nlptown/bert-base-multilingual-uncased-sentiment"
    embedding_model: str = "all-MiniLM-L6-v2"
    sentiment_segments: int = 100
    dialogue_segments: int = 100
    time_slice_years: int = 25


@lru_cache(maxsize=1)
def get_settings() -> LitScopeSettings:
    """Return cached singleton settings instance."""
    return LitScopeSettings()
