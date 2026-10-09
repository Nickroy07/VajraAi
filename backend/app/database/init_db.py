import sqlite3
from pathlib import Path



def initialize_sqlite(sqlite_path: str) -> None:
    """Initialize local SQLite metadata tables only."""
    db_path = Path(sqlite_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
                id INTEGER PRIMARY KEY,
                applied_at TEXT NOT NULL
            )
            """
        )
        connection.commit()
