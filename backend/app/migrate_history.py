"""Copy a validated SQLite history without overwriting either installation."""

from __future__ import annotations

import argparse
import os
import sqlite3
import tempfile
from contextlib import closing
from pathlib import Path


def migrate_history(source: Path, destination: Path) -> int:
    """Snapshot live/WAL SQLite into a new file, publishing only a valid copy.

    Both the source and any existing destination are preserved on failure.
    The hard link publishes atomically and refuses an existing destination,
    including one created by another process after the initial check.
    """
    source = source.resolve(strict=True)
    destination = destination.absolute()
    if destination.exists() or destination.is_symlink():
        raise FileExistsError(f"Destination already exists: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    descriptor, name = tempfile.mkstemp(prefix=".history-migration-", dir=destination.parent)
    temporary = Path(name)
    os.close(descriptor)
    try:
        with (
            closing(sqlite3.connect(source.as_uri() + "?mode=ro", uri=True)) as original,
            closing(sqlite3.connect(temporary)) as copy,
        ):
            original.backup(copy)
            if copy.execute("PRAGMA integrity_check").fetchall() != [("ok",)]:
                raise ValueError("Source database failed its integrity check")
            columns = {row[1] for row in copy.execute("PRAGMA table_info(history)")}
            if not {"id", "created_at", "action_type", "file_name", "details"} <= columns:
                raise ValueError("Source database does not contain a supported history table")
            count = copy.execute("SELECT COUNT(*) FROM history").fetchone()[0]
        with temporary.open("rb") as handle:
            os.fsync(handle.fileno())
        os.link(temporary, destination)
        if os.name == "posix":
            directory = os.open(destination.parent, os.O_RDONLY)
            try:
                os.fsync(directory)
            finally:
                os.close(directory)
        return count
    finally:
        temporary.unlink(missing_ok=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    count = migrate_history(args.source, args.destination)
    print(f"Copied {count} history rows to {args.destination}; source preserved.")


if __name__ == "__main__":
    main()
