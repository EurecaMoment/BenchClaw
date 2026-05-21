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
    CREATE TABLE IF NOT EXISTS real_image_records (
      sample_id TEXT PRIMARY KEY,
      image_path TEXT NOT NULL,
      source TEXT,
      license TEXT,
      capture_metadata_json TEXT,
      target_dimensions_json TEXT,
      expected_annotation_fields_json TEXT,
      gt_status TEXT,
      provenance_json TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS benchmark_records (
      sample_id TEXT PRIMARY KEY,
      benchmark_name TEXT,
      raw_data_path TEXT NOT NULL,
      modalities_json TEXT,
      question TEXT,
      answer TEXT,
      split TEXT,
      target_dimensions_json TEXT,
      official_label_available INTEGER,
      license TEXT,
      provenance_json TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS benchmark_label_records (
      sample_id TEXT NOT NULL,
      label_type TEXT NOT NULL,
      label_value_path_or_inline TEXT,
      label_source TEXT,
      confidence REAL,
      PRIMARY KEY (sample_id, label_type)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS simulator_trace_records (
      sample_id TEXT PRIMARY KEY,
      simulator_id TEXT NOT NULL,
      episode_id TEXT,
      scene_id TEXT,
      seed INTEGER,
      modalities_json TEXT,
      observation_paths_json TEXT,
      target_dimensions_json TEXT,
      task_context_json TEXT,
      provenance_path TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS simulator_gt_records (
      sample_id TEXT NOT NULL,
      gt_field TEXT NOT NULL,
      gt_value_path_or_inline TEXT,
      gt_source TEXT,
      simulator_query TEXT,
      confidence REAL,
      timestamp_or_frame_id TEXT,
      PRIMARY KEY (sample_id, gt_field, timestamp_or_frame_id)
    )
    """,
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workspace", default="WORKSPACE_ROOT")
    args = ap.parse_args()
    db_path = Path(args.workspace) / "stage2" / "stage2.db"
    conn = connect_db(db_path)
    try:
        for stmt in SCHEMA:
            conn.execute(stmt)
        conn.commit()
    finally:
        conn.close()


if __name__ == "__main__":
    main()
