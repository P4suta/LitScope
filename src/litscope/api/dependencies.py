"""FastAPI dependency injection."""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import Request  # noqa: TC002

if TYPE_CHECKING:
    from litscope.config import LitScopeSettings
    from litscope.storage.database import Database


def get_db(request: Request) -> Database:
    """Return the database instance from app state."""
    db: Database = request.app.state.db
    return db


def get_settings(request: Request) -> LitScopeSettings:
    """Return the settings instance from app state."""
    settings: LitScopeSettings = request.app.state.settings
    return settings
