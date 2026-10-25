import json
import os
import sqlite3
from pathlib import Path

from app.board import DEFAULT_BOARD, Board


BASE_DIR = Path(__file__).resolve().parent.parent


def get_db_path() -> Path:
    configured = os.getenv("PM_DB_PATH")
    if configured:
        return Path(configured)
    return BASE_DIR / "data" / "pm.db"


def get_connection() -> sqlite3.Connection:
    db_path = get_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_database() -> None:
    with get_connection() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              username TEXT NOT NULL UNIQUE,
              created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS boards (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              user_id INTEGER NOT NULL UNIQUE,
              board_json TEXT NOT NULL CHECK (json_valid(board_json)),
              version INTEGER NOT NULL DEFAULT 1,
              created_at TEXT NOT NULL DEFAULT (datetime('now')),
              updated_at TEXT NOT NULL DEFAULT (datetime('now')),
              FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_boards_user_id ON boards(user_id);
            """
        )
        _ensure_user_and_board(connection, "user")


def _ensure_user_and_board(connection: sqlite3.Connection, username: str) -> int:
    user_id = _get_or_create_user(connection, username)
    existing_board = connection.execute(
        "SELECT id FROM boards WHERE user_id = ?",
        (user_id,),
    ).fetchone()

    if existing_board is None:
        connection.execute(
            """
            INSERT INTO boards (user_id, board_json, version)
            VALUES (?, ?, 1)
            """,
            (user_id, json.dumps(DEFAULT_BOARD)),
        )

    return user_id


def _get_or_create_user(connection: sqlite3.Connection, username: str) -> int:
    existing = connection.execute(
        "SELECT id FROM users WHERE username = ?",
        (username,),
    ).fetchone()
    if existing is not None:
        return int(existing["id"])

    cursor = connection.execute(
        "INSERT INTO users (username) VALUES (?)",
        (username,),
    )
    return int(cursor.lastrowid)


def get_board_for_user(username: str) -> dict[str, object]:
    with get_connection() as connection:
        _ensure_user_and_board(connection, username)
        row = connection.execute(
            """
            SELECT b.board_json, b.version, b.updated_at
            FROM boards b
            INNER JOIN users u ON b.user_id = u.id
            WHERE u.username = ?
            """,
            (username,),
        ).fetchone()
        if row is None:
            raise RuntimeError("Board lookup failed after ensure.")

        board_payload = Board.model_validate(json.loads(row["board_json"]))
        return {
            "username": username,
            "board": board_payload,
            "version": int(row["version"]),
            "updated_at": str(row["updated_at"]),
        }


def update_board_for_user(username: str, board: Board) -> dict[str, object]:
    with get_connection() as connection:
        user_id = _ensure_user_and_board(connection, username)
        connection.execute(
            """
            UPDATE boards
            SET board_json = ?, version = version + 1, updated_at = datetime('now')
            WHERE user_id = ?
            """,
            (board.model_dump_json(), user_id),
        )

        row = connection.execute(
            "SELECT board_json, version, updated_at FROM boards WHERE user_id = ?",
            (user_id,),
        ).fetchone()
        if row is None:
            raise RuntimeError("Board retrieval failed after update.")

        board_payload = Board.model_validate(json.loads(row["board_json"]))
        return {
            "username": username,
            "board": board_payload,
            "version": int(row["version"]),
            "updated_at": str(row["updated_at"]),
        }
