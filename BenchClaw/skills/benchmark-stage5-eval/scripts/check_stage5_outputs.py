#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("--workspace", default="WORKSPACE_ROOT")
args = parser.parse_args()
ws = Path(args.workspace)

required = [
    ws / "stage5" / "38-evaluation-run" / "eval_results.json",
    ws / "stage5" / "38-evaluation-run" / "prediction_logs.jsonl",
    ws / "stage5" / "38-evaluation-run" / "failure_cases.jsonl",
    ws / "stage5" / "38-evaluation-run" / "report_payload.json",
    ws / "stage5" / "38-evaluation-run" / "run_config.yaml",
    ws / "stage5" / "38-evaluation-run" / "DONE.json",
    ws / "stage5" / "39-evaluation-report" / "report.md",
    ws / "stage5" / "39-evaluation-report" / "leaderboard.csv",
    ws / "stage5" / "39-evaluation-report" / "per_dimension.csv",
    ws / "stage5" / "39-evaluation-report" / "error_analysis.md",
    ws / "stage5" / "39-evaluation-report" / "DONE.json",
]
missing = [str(p) for p in required if not p.exists()]
if missing:
    print(json.dumps({"ok": False, "missing": missing}, ensure_ascii=False, indent=2))
    raise SystemExit(1)
print(json.dumps({"ok": True, "checked": len(required)}, ensure_ascii=False, indent=2))
