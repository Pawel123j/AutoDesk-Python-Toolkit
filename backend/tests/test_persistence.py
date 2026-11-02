import sqlite3

from app import database


def test_history_survives_reinitialization_and_online_backup(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DATA_DIR", tmp_path)
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "toolkit.db")
    database.add_history("clean_csv", "sample.csv", {"rows": 2})
    database.init_db()
    assert database.fetch_history()[0]["details"] == {"rows": 2}
    backup = tmp_path / "backup.db"
    with sqlite3.connect(database.DB_PATH) as source, sqlite3.connect(backup) as target:
        source.backup(target)
    database.clear_history()
    assert database.fetch_history() == []
    with sqlite3.connect(backup) as source, sqlite3.connect(database.DB_PATH) as target:
        source.backup(target)
    assert database.fetch_history()[0]["file_name"] == "sample.csv"
