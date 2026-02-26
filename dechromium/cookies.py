from __future__ import annotations

import json
import sqlite3
from pathlib import Path


_COLUMNS = [
    "creation_utc", "host_key", "top_frame_site_key", "name", "value",
    "encrypted_value", "path", "expires_utc", "is_secure", "is_httponly",
    "last_access_utc", "has_expires", "is_persistent", "priority",
    "samesite", "source_scheme", "source_port", "last_update_utc",
    "source_type", "has_cross_site_ancestor",
]

_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS cookies (
    creation_utc INTEGER NOT NULL,
    host_key TEXT NOT NULL DEFAULT '',
    top_frame_site_key TEXT NOT NULL DEFAULT '',
    name TEXT NOT NULL DEFAULT '',
    value TEXT NOT NULL DEFAULT '',
    encrypted_value BLOB NOT NULL DEFAULT X'',
    path TEXT NOT NULL DEFAULT '/',
    expires_utc INTEGER NOT NULL DEFAULT 0,
    is_secure INTEGER NOT NULL DEFAULT 1,
    is_httponly INTEGER NOT NULL DEFAULT 0,
    last_access_utc INTEGER NOT NULL DEFAULT 0,
    has_expires INTEGER NOT NULL DEFAULT 1,
    is_persistent INTEGER NOT NULL DEFAULT 1,
    priority INTEGER NOT NULL DEFAULT 1,
    samesite INTEGER NOT NULL DEFAULT -1,
    source_scheme INTEGER NOT NULL DEFAULT 2,
    source_port INTEGER NOT NULL DEFAULT 443,
    last_update_utc INTEGER NOT NULL DEFAULT 0,
    source_type INTEGER NOT NULL DEFAULT 0,
    has_cross_site_ancestor INTEGER NOT NULL DEFAULT 0
);
"""


def _db_path(data_dir: Path) -> Path:
    return data_dir / "Default" / "Network" / "Cookies"


def export_cookies(data_dir: Path, output: Path | None = None) -> list[dict]:
    db = _db_path(data_dir)
    if not db.exists():
        return []

    conn = sqlite3.connect(str(db))
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM cookies").fetchall()
    conn.close()

    result = []
    for row in rows:
        entry = {}
        for col in _COLUMNS:
            val = row[col]
            if col == "encrypted_value":
                val = ""
            entry[col] = val
        result.append(entry)

    if output:
        output.write_text(json.dumps(result, indent=2))

    return result


def import_cookies(data_dir: Path, source: Path | list[dict]) -> int:
    if isinstance(source, list):
        data = source
    else:
        data = json.loads(source.read_text())

    if not data:
        return 0

    db = _db_path(data_dir)
    db.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(db))
    conn.execute(_CREATE_TABLE)
    conn.execute("DELETE FROM cookies")

    col_names = ", ".join(_COLUMNS)
    placeholders = ", ".join(["?"] * len(_COLUMNS))
    sql = f"INSERT INTO cookies ({col_names}) VALUES ({placeholders})"

    for entry in data:
        values = []
        for col in _COLUMNS:
            if col == "encrypted_value":
                values.append(b"")
            else:
                values.append(entry.get(col, ""))
        conn.execute(sql, values)

    conn.commit()
    conn.close()
    return len(data)
