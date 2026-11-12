"""One-time migration of Jeenius users and sessions from SQLite to PostgreSQL.

Set DATABASE_URL to the target PostgreSQL connection string first.
Run this from the project directory after copying this script beside
jeenius_auth.sqlite3. The script is safe to rerun for non-conflicting rows.
"""
from __future__ import annotations

import os
import sqlite3
import sys
from pathlib import Path

import psycopg

ROOT = Path(__file__).resolve().parent
SOURCE_DB = Path(os.environ.get("SQLITE_SOURCE_PATH", str(ROOT / "jeenius_auth.sqlite3"))).expanduser()
DATABASE_URL = os.environ.get("DATABASE_URL", "").strip()

DDL = """
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    email TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    password_hash TEXT,
    google_sub TEXT UNIQUE,
    picture TEXT,
    created_at BIGINT NOT NULL,
    updated_at BIGINT NOT NULL
);
CREATE TABLE IF NOT EXISTS auth_sessions (
    token_hash TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    expires_at BIGINT NOT NULL,
    created_at BIGINT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_auth_sessions_expiry ON auth_sessions(expires_at);
"""


def main() -> int:
    if not DATABASE_URL:
        print("ERROR: Set DATABASE_URL to the target PostgreSQL connection string.", file=sys.stderr)
        return 2
    if not SOURCE_DB.is_file():
        print(f"ERROR: SQLite source database not found: {SOURCE_DB}", file=sys.stderr)
        return 2

    with sqlite3.connect(str(SOURCE_DB)) as source:
        source.row_factory = sqlite3.Row
        users = source.execute("SELECT id, email, name, password_hash, google_sub, picture, created_at, updated_at FROM users").fetchall()
        sessions = source.execute("SELECT token_hash, user_id, expires_at, created_at FROM auth_sessions").fetchall()

    copied_users = 0
    copied_sessions = 0
    with psycopg.connect(DATABASE_URL) as target:
        with target.cursor() as cursor:
            for statement in DDL.split(";"):
                if statement.strip():
                    cursor.execute(statement)
        with target.transaction():
            for row in users:
                cursor = target.execute(
                    """INSERT INTO users(id, email, name, password_hash, google_sub, picture, created_at, updated_at)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT DO NOTHING""",
                    tuple(row[key] for key in ("id", "email", "name", "password_hash", "google_sub", "picture", "created_at", "updated_at")),
                )
                copied_users += cursor.rowcount
            for row in sessions:
                exists = target.execute("SELECT 1 FROM users WHERE id = %s", (row["user_id"],)).fetchone()
                if not exists:
                    continue
                cursor = target.execute(
                    """INSERT INTO auth_sessions(token_hash, user_id, expires_at, created_at)
                       VALUES (%s, %s, %s, %s) ON CONFLICT DO NOTHING""",
                    tuple(row[key] for key in ("token_hash", "user_id", "expires_at", "created_at")),
                )
                copied_sessions += cursor.rowcount

    print(f"Migration finished. Inserted {copied_users} user(s) and {copied_sessions} session(s).")
    print("Rows skipped because of existing unique values were left unchanged.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
