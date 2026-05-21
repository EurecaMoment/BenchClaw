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
    CREATE TABLE IF NOT EXISTS stage2_real_sources (
      sample_id TEXT PRIMARY KEY,
      source_manifest_path TEXT,
      source_json TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS stage2_benchmark_sources (
      sample_id TEXT PRIMARY KEY,
      source_manifest_path TEXT,
      source_json TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS stage2_simulator_sources (
      sample_id TEXT PRIMARY KEY,
      source_manifest_path TEXT,
      source_json TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS stage2_simulator_gt_sources (
      sample_id TEXT NOT NULL,
      gt_field TEXT NOT NULL,
      source_json TEXT,
      PRIMARY KEY (sample_id, gt_field)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS unified_real_records (
      record_id TEXT PRIMARY KEY,
      record_json TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS unified_benchmark_records (
      record_id TEXT PRIMARY KEY,
      record_json TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS unified_simulator_records (
      record_id TEXT PRIMARY KEY,
      record_json TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS cleaned_real_records (
      record_id TEXT PRIMARY KEY,
      record_json TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS cleaned_benchmark_records (
      record_id TEXT PRIMARY KEY,
      record_json TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS cleaned_simulator_records (
      record_id TEXT PRIMARY KEY,
      record_json TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS semi_gt_candidates (
      record_id TEXT NOT NULL,
      candidate_id TEXT NOT NULL,
      branch TEXT NOT NULL,
      source_type TEXT,
      artifact_paths_json TEXT,
      candidate_json TEXT NOT NULL,
      PRIMARY KEY (record_id, candidate_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS benchmark_label_records (
      record_id TEXT NOT NULL,
      label_type TEXT NOT NULL,
      label_json TEXT NOT NULL,
      PRIMARY KEY (record_id, label_type)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS simulator_gt_records (
      record_id TEXT PRIMARY KEY,
      artifact_paths_json TEXT,
      record_json TEXT NOT NULL
    )
    """,
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workspace", default="WORKSPACE_ROOT")
    args = ap.parse_args()
    db_path = Path(args.workspace) / "stage3" / "stage3.db"
    conn = connect_db(db_path)
    try:
        for stmt in SCHEMA:
            conn.execute(stmt)
        conn.commit()
    finally:
        conn.close()


if __name__ == "__main__":
    main()
