"""Database engine and table initialisation.

Lives in its own module so both `main.py` (creates tables at startup) and
`routes/*.py` (read/write records) can import the same engine without
importing each other.
"""
import os
from pathlib import Path

from sqlmodel import SQLModel, create_engine

BACKEND_DIR = Path(__file__).resolve().parent

# Resolve relative paths from the repository root, regardless of the launch directory.
_db_path = Path(os.getenv("DATABASE_PATH", "backend/data/vigil.db"))
if not _db_path.is_absolute():
    _db_path = BACKEND_DIR.parent / _db_path
_db_path.parent.mkdir(parents=True, exist_ok=True)

engine = create_engine(f"sqlite:///{_db_path}")


def init_db() -> None:
    """Create every table that doesn't exist yet (safe to call repeatedly)."""
    import models.record  # noqa: F401

    SQLModel.metadata.create_all(engine)

    # create_all does not add columns to tables that already exist.
    with engine.begin() as conn:
        columns = {row[1] for row in conn.exec_driver_sql("PRAGMA table_info(detectionrecord)")}
        if "inference_time_ms" not in columns:
            conn.exec_driver_sql(
                "ALTER TABLE detectionrecord ADD COLUMN inference_time_ms FLOAT NOT NULL DEFAULT 0.0"
            )
