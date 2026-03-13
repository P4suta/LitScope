"""Integration test fixtures."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from litscope.api.app import create_app
from litscope.config import LitScopeSettings
from tests.conftest import create_sample_epub


@pytest.fixture
def integration_epub(tmp_path: Path) -> Path:
    """Create a sample EPUB for integration tests."""
    return create_sample_epub(tmp_path)


@pytest.fixture
def integration_client(tmp_path: Path) -> TestClient:
    """TestClient with a fresh database for integration tests."""
    db_path = tmp_path / "integration.duckdb"
    settings = LitScopeSettings(db_path=db_path)
    app = create_app(settings=settings)
    with TestClient(app) as client:
        yield client  # type: ignore[misc]
