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
    CREATE TABLE IF NOT EXISTS stage1_template_metric_inputs (
      source_id TEXT PRIMARY KEY,
      source_json TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS stage3_real_inputs (
      source_id TEXT PRIMARY KEY,
      source_json TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS stage3_benchmark_inputs (
      source_id TEXT PRIMARY KEY,
      source_json TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS stage3_simulator_inputs (
      source_id TEXT PRIMARY KEY,
      source_json TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS evidence_pool (
      evidence_id TEXT PRIMARY KEY,
      evidence_json TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS template_evidence_bindings (
      binding_id TEXT PRIMARY KEY,
      binding_json TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS binding_rejections (
      rejection_id TEXT PRIMARY KEY,
      rejection_json TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS question_blueprints (
      blueprint_id TEXT PRIMARY KEY,
      blueprint_json TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS eval_items (
      item_id TEXT PRIMARY KEY,
      item_json TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS quality_rejections (
      rejection_id TEXT PRIMARY KEY,
      rejection_json TEXT NOT NULL
    )
    """,
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workspace", default="WORKSPACE_ROOT")
    args = ap.parse_args()
    db_path = Path(args.workspace) / "stage4" / "stage4.db"
    conn = connect_db(db_path)
    try:
        for stmt in SCHEMA:
            conn.execute(stmt)
        conn.commit()
    finally:
        conn.close()


if __name__ == "__main__":
    main()
