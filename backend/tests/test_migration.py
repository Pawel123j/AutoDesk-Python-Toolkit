import os
import sqlite3
import subprocess
import sys
from contextlib import closing
from pathlib import Path

import pytest
from app import database
from app.migrate_history import migrate_history


@pytest.fixture
def legacy(tmp_path, monkeypatch):
    folder = tmp_path / "legacy"
    monkeypatch.setattr(database, "DATA_DIR", folder)
    monkeypatch.setattr(database, "DB_PATH", folder / "toolkit.db")
    database.add_history("clean_csv", "important.csv", {"rows": 7})
    return database.DB_PATH


def test_migrated_history_survives_new_process(legacy, tmp_path):
    destination = tmp_path / "persistent/toolkit.db"
    assert migrate_history(legacy, destination) == 1
    assert legacy.exists()
    environment = dict(os.environ, AUTODESK_DATA_DIR=str(destination.parent))
    environment["PYTHONPATH"] = str(Path(__file__).resolve().parents[1])
    for _ in range(2):
        subprocess.run(
            [sys.executable, "-c", "from app.database import fetch_history; "
             "assert fetch_history()[0]['file_name'] == 'important.csv'"],
            env=environment, check=True,
        )


def test_migration_includes_committed_wal_rows(legacy, tmp_path):
    destination = tmp_path / "copy.db"
    with closing(sqlite3.connect(legacy)) as writer:
        writer.execute("PRAGMA journal_mode=WAL")
        writer.execute("UPDATE history SET file_name='wal.csv'")
        writer.commit()
        assert migrate_history(legacy, destination) == 1
    with closing(sqlite3.connect(destination)) as copied:
        assert copied.execute("SELECT file_name FROM history").fetchone() == ("wal.csv",)


@pytest.mark.parametrize("existing", [True, False])
def test_migration_preserves_existing_destination_and_symlink(legacy, tmp_path, existing):
    target = tmp_path / "existing.db"
    target.write_bytes(b"valuable destination")
    destination = target if existing else tmp_path / "link.db"
    if not existing:
        destination.symlink_to(target)
    with pytest.raises(FileExistsError):
        migrate_history(legacy, destination)
    assert target.read_bytes() == b"valuable destination"


@pytest.mark.parametrize("payload", [b"not sqlite", b""])
def test_invalid_source_does_not_create_destination(tmp_path, payload):
    source = tmp_path / "invalid.db"
    source.write_bytes(payload)
    destination = tmp_path / "copy.db"
    with pytest.raises((sqlite3.DatabaseError, ValueError)):
        migrate_history(source, destination)
    assert source.read_bytes() == payload
    assert not destination.exists()
    assert not list(tmp_path.glob(".history-migration-*"))


def test_failed_publish_preserves_source_and_existing_destination(legacy, tmp_path, monkeypatch):
    destination = tmp_path / "copy.db"
    original_link = os.link

    def competing_publish(source, target):
        target.write_bytes(b"concurrent data")
        original_link(source, target)

    monkeypatch.setattr(os, "link", competing_publish)
    with pytest.raises(FileExistsError):
        migrate_history(legacy, destination)
    assert destination.read_bytes() == b"concurrent data"
    assert database.fetch_history()[0]["file_name"] == "important.csv"
    assert not list(tmp_path.glob(".history-migration-*"))


def test_failed_snapshot_flush_keeps_source_and_does_not_publish(legacy, tmp_path, monkeypatch):
    destination = tmp_path / "copy.db"

    def failed_flush(_descriptor):
        raise OSError("disk flush failed")

    monkeypatch.setattr(os, "fsync", failed_flush)
    with pytest.raises(OSError, match="disk flush failed"):
        migrate_history(legacy, destination)
    assert not destination.exists()
    assert database.fetch_history()[0]["file_name"] == "important.csv"
    assert not list(tmp_path.glob(".history-migration-*"))
