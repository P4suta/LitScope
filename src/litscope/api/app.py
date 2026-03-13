"""FastAPI application factory."""

from __future__ import annotations

import uuid
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

import structlog
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from litscope import __version__
from litscope.config import LitScopeSettings
from litscope.config import get_settings as default_get_settings
from litscope.exceptions import HTTP_STATUS_MAP, LitScopeError
from litscope.storage.database import Database

from .routers import authors, compare, genres, health, ingest, timeline, topics, works

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator, Awaitable, Callable

logger = structlog.get_logger()


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Add X-Request-ID header and bind request_id to structlog context."""

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        request_id = str(uuid.uuid4())
        structlog.contextvars.bind_contextvars(request_id=request_id)
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        structlog.contextvars.unbind_contextvars("request_id")
        return response


def create_app(
    db: Database | None = None,
    settings: LitScopeSettings | None = None,
) -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = settings or default_get_settings()
    owns_db = db is None

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
        if owns_db:
            app_db = Database(settings.db_path)
            app_db.connect()
            app_db.migrate()
            app.state.db = app_db
        else:
            app.state.db = db
        app.state.settings = settings
        yield
        if owns_db:
            app.state.db.close()

    app = FastAPI(
        title="LitScope",
        version=__version__,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            o.strip() for o in settings.cors_origins.split(",")
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_middleware(RequestIDMiddleware)

    @app.exception_handler(LitScopeError)
    async def litscope_error_handler(
        request: Request, exc: LitScopeError
    ) -> JSONResponse:
        status_code, title = HTTP_STATUS_MAP.get(
            type(exc), (500, "Internal Server Error")
        )
        return JSONResponse(
            status_code=status_code,
            content={
                "type": "about:blank",
                "title": title,
                "status": status_code,
                "detail": str(exc),
            },
        )

    @app.exception_handler(Exception)
    async def generic_error_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        logger.error(
            "unhandled_exception",
            exc_type=type(exc).__name__,
            detail=str(exc),
            path=str(request.url),
        )
        return JSONResponse(
            status_code=500,
            content={
                "type": "about:blank",
                "title": "Internal Server Error",
                "status": 500,
                "detail": "An unexpected error occurred",
            },
        )

    app.include_router(health.router, prefix="/api/v1")
    app.include_router(works.router, prefix="/api/v1")
    app.include_router(compare.router, prefix="/api/v1")
    app.include_router(authors.router, prefix="/api/v1")
    app.include_router(topics.router, prefix="/api/v1")
    app.include_router(timeline.router, prefix="/api/v1")
    app.include_router(genres.router, prefix="/api/v1")
    app.include_router(ingest.router, prefix="/api/v1")

    return app
