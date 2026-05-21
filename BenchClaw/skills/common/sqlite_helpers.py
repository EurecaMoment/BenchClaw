#!/usr/bin/env python3
import json
import sqlite3
from pathlib import Path


def ensure_parent(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)


def connect_db(path: Path):
    ensure_parent(path)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def table_exists(conn: sqlite3.Connection, table_name: str) -> bool:
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,)
    ).fetchone()
    return row is not None


def count_rows(conn: sqlite3.Connection, table_name: str) -> int:
    return int(conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0])


def unique_values(conn: sqlite3.Connection, table_name: str, column_name: str):
    rows = conn.execute(
        f"SELECT DISTINCT {column_name} FROM {table_name} WHERE {column_name} IS NOT NULL"
    ).fetchall()
    return {str(row[0]) for row in rows}


def export_table_jsonl(conn: sqlite3.Connection, table_name: str, out_path: Path):
    ensure_parent(out_path)
    rows = conn.execute(f"SELECT * FROM {table_name}").fetchall()
    with out_path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(dict(row), ensure_ascii=False) + "\n")


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))
