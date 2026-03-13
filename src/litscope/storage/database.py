"""DuckDB database connection and migration management."""

from pathlib import Path
from types import TracebackType
from typing import Self

import duckdb
import structlog

from litscope.exceptions import DatabaseError

logger = structlog.get_logger()


class Database:
    """DuckDB database wrapper with migration support."""

    def __init__(self, db_path: Path | str = ":memory:") -> None:
        self._db_path = str(db_path)
        self._conn: duckdb.DuckDBPyConnection | None = None

    @property
    def conn(self) -> duckdb.DuckDBPyConnection:
        """Return active connection, raising if not connected."""
        if self._conn is None:
            msg = "Database not connected. Call connect() first."
            raise RuntimeError(msg)
        return self._conn

    def connect(self) -> None:
        """Open a connection to the database."""
        try:
            self._conn = duckdb.connect(self._db_path)
        except Exception as e:
            raise DatabaseError(f"Failed to connect to {self._db_path}: {e}") from e

    def close(self) -> None:
        """Close the database connection."""
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    def __enter__(self) -> Self:
        self.connect()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        self.close()

    def migrate(self) -> None:
        """Run all pending SQL migrations in order."""
        conn = self.conn
        conn.execute(
            "CREATE TABLE IF NOT EXISTS _migrations ("
            "  name VARCHAR PRIMARY KEY,"
            "  applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
            ")"
        )
        migrations_dir = Path(__file__).parent / "migrations"
        applied: set[str] = {
            row[0] for row in conn.execute("SELECT name FROM _migrations").fetchall()
        }
        for sql_file in sorted(migrations_dir.glob("*.sql")):
            if sql_file.name not in applied:
                conn.execute(sql_file.read_text())
                conn.execute(
                    "INSERT INTO _migrations (name) VALUES (?)", [sql_file.name]
                )
