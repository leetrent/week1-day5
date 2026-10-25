import sqlite3

from app.board import Board
from app.db import get_board_for_user, get_db_path, initialize_database, update_board_for_user


def test_initialize_database_creates_file_and_tables(monkeypatch, tmp_path):
    db_path = tmp_path / "pm.db"
    monkeypatch.setenv("PM_DB_PATH", str(db_path))

    initialize_database()

    assert get_db_path() == db_path
    assert db_path.exists()

    with sqlite3.connect(db_path) as connection:
        tables = connection.execute(
            """
            SELECT name FROM sqlite_master
            WHERE type = 'table' AND name IN ('users', 'boards')
            ORDER BY name
            """
        ).fetchall()
        assert [name for (name,) in tables] == ["boards", "users"]


def test_get_board_for_user_creates_default_board(monkeypatch, tmp_path):
    monkeypatch.setenv("PM_DB_PATH", str(tmp_path / "pm.db"))
    initialize_database()

    result = get_board_for_user("user")

    assert result["username"] == "user"
    board = result["board"]
    assert isinstance(board, Board)
    assert len(board.columns) == 5
    assert "card-1" in board.cards
    assert result["version"] == 1


def test_update_board_for_user_persists_changes_and_increments_version(monkeypatch, tmp_path):
    monkeypatch.setenv("PM_DB_PATH", str(tmp_path / "pm.db"))
    initialize_database()

    initial = get_board_for_user("user")
    board = initial["board"].model_copy(deep=True)
    board.columns[0].title = "Renamed Backlog"

    updated = update_board_for_user("user", board)
    reloaded = get_board_for_user("user")

    assert updated["version"] == initial["version"] + 1
    assert reloaded["board"].columns[0].title == "Renamed Backlog"
