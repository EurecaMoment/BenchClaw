#!/usr/bin/env python3
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from skills.common.sqlite_helpers import connect_db


SCHEMA = [
    """
    CREATE TABLE IF NOT EXISTS prediction_logs (
      sample_id TEXT NOT NULL,
      model TEXT NOT NULL,
      prediction TEXT,
      metadata_json TEXT,
      PRIMARY KEY (sample_id, model)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS failure_cases (
      sample_id TEXT NOT NULL,
      model TEXT NOT NULL,
      failure_json TEXT NOT NULL,
      PRIMARY KEY (sample_id, model)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS model_call_summary (
      model TEXT PRIMARY KEY,
      endpoint TEXT,
      prediction_file TEXT,
      summary_json TEXT
    )
    """,
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workspace", default="WORKSPACE_ROOT")
    args = ap.parse_args()
    db_path = Path(args.workspace) / "stage5" / "stage5.db"
    conn = connect_db(db_path)
    try:
        for stmt in SCHEMA:
            conn.execute(stmt)
        conn.commit()
    finally:
        conn.close()


if __name__ == "__main__":
    main()
