"""Tests for API app factory and middleware."""

import uuid
from pathlib import Path
from unittest.mock import patch

from fastapi import Depends
from fastapi.testclient import TestClient

from litscope.api.app import create_app
from litscope.config import LitScopeSettings
from litscope.exceptions import (
    AnalyzerNotFoundError,
    CircularDependencyError,
    DatabaseError,
    DependencyNotSatisfiedError,
    EpubParseError,
    IngestionError,
    LitScopeError,
    WorkNotFoundError,
)
from litscope.storage.database import Database


class TestDependencies:
    def test_get_settings_from_app_state(self, seeded_db: Database) -> None:
        settings = LitScopeSettings()
        app = create_app(db=seeded_db, settings=settings)
        with TestClient(app) as client:
            resp = client.get("/api/v1/health")
            assert resp.status_code == 200
            assert app.state.settings is settings

    def test_get_settings_returns_settings(self, seeded_db: Database) -> None:
        from litscope.api.dependencies import (
            get_settings as dep_get_settings,
        )

        settings = LitScopeSettings(api_port=9999)
        app = create_app(db=seeded_db, settings=settings)

        @app.get("/test-settings-dep")
        def test_dep(
            s: LitScopeSettings = Depends(dep_get_settings),
        ) -> dict[str, int]:
            return {"port": s.api_port}

        with TestClient(app) as client:
            resp = client.get("/test-settings-dep")
            assert resp.status_code == 200
            assert resp.json()["port"] == 9999


class TestCreateApp:
    def test_creates_app_with_injected_db(self, seeded_db: Database) -> None:
        app = create_app(db=seeded_db)
        assert app.title == "LitScope"

    def test_cors_middleware_applied(self, seeded_db: Database) -> None:
        settings = LitScopeSettings(cors_origins="http://localhost:3000")
        app = create_app(db=seeded_db, settings=settings)
        with TestClient(app) as client:
            resp = client.options(
                "/api/v1/health",
                headers={
                    "Origin": "http://localhost:3000",
                    "Access-Control-Request-Method": "GET",
                },
            )
            origin = resp.headers.get("access-control-allow-origin")
            assert origin == "http://localhost:3000"

    def test_cors_multiple_origins(self, seeded_db: Database) -> None:
        settings = LitScopeSettings(
            cors_origins="http://localhost:3000,http://localhost:5173"
        )
        app = create_app(db=seeded_db, settings=settings)
        with TestClient(app) as client:
            resp = client.options(
                "/api/v1/health",
                headers={
                    "Origin": "http://localhost:5173",
                    "Access-Control-Request-Method": "GET",
                },
            )
            origin = resp.headers.get("access-control-allow-origin")
            assert origin == "http://localhost:5173"

    def test_litscope_error_handler(self, seeded_db: Database) -> None:
        app = create_app(db=seeded_db)

        @app.get("/test-error")
        def raise_error() -> None:
            raise LitScopeError("test error")

        with TestClient(app, raise_server_exceptions=False) as client:
            resp = client.get("/test-error")
            assert resp.status_code == 500
            body = resp.json()
            assert body["title"] == "Internal Server Error"
            assert body["detail"] == "test error"
            assert body["type"] == "about:blank"

    def test_epub_parse_error_returns_422(self, seeded_db: Database) -> None:
        app = create_app(db=seeded_db)

        @app.get("/test-epub-error")
        def raise_epub_error() -> None:
            raise EpubParseError("bad epub")

        with TestClient(app, raise_server_exceptions=False) as client:
            resp = client.get("/test-epub-error")
            assert resp.status_code == 422
            body = resp.json()
            assert body["title"] == "Unprocessable Entity"
            assert body["detail"] == "bad epub"

    def test_ingestion_error_returns_422(self, seeded_db: Database) -> None:
        app = create_app(db=seeded_db)

        @app.get("/test-ingestion-error")
        def raise_ingestion_error() -> None:
            raise IngestionError("ingestion failed")

        with TestClient(app, raise_server_exceptions=False) as client:
            resp = client.get("/test-ingestion-error")
            assert resp.status_code == 422
            body = resp.json()
            assert body["title"] == "Unprocessable Entity"
            assert body["detail"] == "ingestion failed"

    def test_analyzer_not_found_returns_404(self, seeded_db: Database) -> None:
        app = create_app(db=seeded_db)

        @app.get("/test-analyzer-error")
        def raise_analyzer_error() -> None:
            raise AnalyzerNotFoundError("no_such_analyzer")

        with TestClient(app, raise_server_exceptions=False) as client:
            resp = client.get("/test-analyzer-error")
            assert resp.status_code == 404
            body = resp.json()
            assert body["title"] == "Not Found"

    def test_database_error_returns_500(self, seeded_db: Database) -> None:
        app = create_app(db=seeded_db)

        @app.get("/test-db-error")
        def raise_db_error() -> None:
            raise DatabaseError("db broken")

        with TestClient(app, raise_server_exceptions=False) as client:
            resp = client.get("/test-db-error")
            assert resp.status_code == 500
            body = resp.json()
            assert body["title"] == "Internal Server Error"

    def test_work_not_found_error_returns_404(self, seeded_db: Database) -> None:
        app = create_app(db=seeded_db)

        @app.get("/test-work-not-found")
        def raise_work_not_found() -> None:
            raise WorkNotFoundError("missing-id")

        with TestClient(app, raise_server_exceptions=False) as client:
            resp = client.get("/test-work-not-found")
            assert resp.status_code == 404
            body = resp.json()
            assert body["title"] == "Not Found"
            assert body["detail"] == "missing-id"

    def test_circular_dependency_error_returns_400(self, seeded_db: Database) -> None:
        app = create_app(db=seeded_db)

        @app.get("/test-circular")
        def raise_circular() -> None:
            raise CircularDependencyError("a -> b -> a")

        with TestClient(app, raise_server_exceptions=False) as client:
            resp = client.get("/test-circular")
            assert resp.status_code == 400
            body = resp.json()
            assert body["title"] == "Bad Request"

    def test_dependency_not_satisfied_returns_400(self, seeded_db: Database) -> None:
        app = create_app(db=seeded_db)

        @app.get("/test-dep-not-satisfied")
        def raise_dep_not_satisfied() -> None:
            raise DependencyNotSatisfiedError("need X first")

        with TestClient(app, raise_server_exceptions=False) as client:
            resp = client.get("/test-dep-not-satisfied")
            assert resp.status_code == 400
            body = resp.json()
            assert body["title"] == "Bad Request"

    def test_unhandled_exception_returns_500_and_logs(
        self, seeded_db: Database
    ) -> None:
        app = create_app(db=seeded_db)

        @app.get("/test-unhandled")
        def raise_unhandled() -> None:
            raise RuntimeError("unexpected boom")

        with (
            TestClient(app, raise_server_exceptions=False) as client,
            patch("litscope.api.app.logger") as mock_logger,
        ):
            resp = client.get("/test-unhandled")
            assert resp.status_code == 500
            body = resp.json()
            assert body["title"] == "Internal Server Error"
            assert body["detail"] == "An unexpected error occurred"
            mock_logger.error.assert_called_once()

    def test_response_contains_x_request_id_header(self, seeded_db: Database) -> None:
        app = create_app(db=seeded_db)
        with TestClient(app) as client:
            resp = client.get("/api/v1/health")
            assert "x-request-id" in resp.headers

    def test_request_id_is_uuid(self, seeded_db: Database) -> None:
        app = create_app(db=seeded_db)
        with TestClient(app) as client:
            resp = client.get("/api/v1/health")
            request_id = resp.headers["x-request-id"]
            parsed = uuid.UUID(request_id)
            assert str(parsed) == request_id

    def test_lifespan_owns_db(self, tmp_path: Path) -> None:
        db_path = tmp_path / "test.duckdb"
        settings = LitScopeSettings(db_path=db_path)
        app = create_app(settings=settings)
        with TestClient(app) as client:
            resp = client.get("/api/v1/health")
            assert resp.status_code == 200

    def test_app_state_has_db_and_settings(self, seeded_db: Database) -> None:
        app = create_app(db=seeded_db)
        with TestClient(app) as client:
            assert app.state.db is seeded_db
            assert app.state.settings is not None
            resp = client.get("/api/v1/health")
            assert resp.status_code == 200
