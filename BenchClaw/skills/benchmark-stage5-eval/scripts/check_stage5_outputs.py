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
    ws / "stage5" / "stage5.db",
    ws / "stage5" / "38-evaluation-run" / "prediction_logs.sqlite_export.jsonl",
    ws / "stage5" / "38-evaluation-run" / "failure_cases.sqlite_export.jsonl",
    ws / "stage5" / "38-evaluation-run" / "report_payload.json",
    ws / "stage5" / "38-evaluation-run" / "run_config.yaml",
    ws / "stage5" / "38-evaluation-run" / "model_call_summary.json",
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

eval_results = json.loads(
    (ws / "stage5" / "38-evaluation-run" / "eval_results.json").read_text(
        encoding="utf-8"
    )
)
node38_done = json.loads(
    (ws / "stage5" / "38-evaluation-run" / "DONE.json").read_text(encoding="utf-8")
)
node39_done = json.loads(
    (ws / "stage5" / "39-evaluation-report" / "DONE.json").read_text(encoding="utf-8")
)

errors = []
if eval_results.get("status") != "scored":
    errors.append(
        f"eval_results.status must be 'scored', got {eval_results.get('status')!r}"
    )
if node38_done.get("status") != "done":
    errors.append(
        f"node 38 DONE status must be 'done', got {node38_done.get('status')!r}"
    )
if node39_done.get("status") != "done":
    errors.append(
        f"node 39 DONE status must be 'done', got {node39_done.get('status')!r}"
    )
if not eval_results.get("leaderboard"):
    errors.append("leaderboard is empty; Stage5 requires at least one scored model")

prediction_logs_path = (
    ws / "stage5" / "38-evaluation-run" / "prediction_logs.sqlite_export.jsonl"
)
model_summary_path = ws / "stage5" / "38-evaluation-run" / "model_call_summary.json"
prediction_lines = [
    line
    for line in prediction_logs_path.read_text(encoding="utf-8").splitlines()
    if line.strip()
]
if not prediction_lines:
    errors.append(
        "prediction_logs.sqlite_export.jsonl is empty; Stage5 requires real model predictions"
    )
for idx, line in enumerate(prediction_lines[:20], 1):
    try:
        row = json.loads(line)
    except json.JSONDecodeError as exc:
        errors.append(f"invalid prediction_logs.sqlite_export.jsonl line {idx}: {exc}")
        continue
    if row.get("metadata", {}).get("simulated") is True:
        errors.append(f"prediction log line {idx} is marked simulated")
    banned_keys = {"predicted_answer", "correct_answer", "is_correct"}
    if banned_keys.issubset(row.keys()) and "score" not in row:
        errors.append(
            f"prediction log line {idx} looks like pre-scored synthetic output instead of raw model prediction"
        )

required_models = {
    "qwen3-vl-235b-a22b-instruct",
    "kimi-k2.5",
    "llama-4-maverick-17b-128e-instruct",
    "grok-4-fast",
    "gpt-5.4-mini-2026-03-17",
    "glm-4.5v",
    "gemini-3-flash-preview",
    "claude-haiku-4-5-20251001-thinking",
    "claude-sonnet-4-5-20250929",
}
observed_models = set()
for line in prediction_lines:
    try:
        row = json.loads(line)
    except json.JSONDecodeError:
        continue
    model = row.get("model")
    if model:
        observed_models.add(str(model))

missing_models = sorted(required_models - observed_models)
if missing_models:
    errors.append(
        "Stage5 is missing required evaluated models: " + ", ".join(missing_models)
    )

try:
    model_summary = json.loads(model_summary_path.read_text(encoding="utf-8"))
    summary_models = {
        str(item.get("model"))
        for item in model_summary.get("models", [])
        if item.get("model")
    }
    missing_summary_models = sorted(required_models - summary_models)
    if missing_summary_models:
        errors.append(
            "model_call_summary.json is missing required models: "
            + ", ".join(missing_summary_models)
        )
except Exception as exc:
    errors.append(f"invalid model_call_summary.json: {exc}")

if errors:
    print(json.dumps({"ok": False, "errors": errors}, ensure_ascii=False, indent=2))
    raise SystemExit(1)

print(json.dumps({"ok": True, "checked": len(required)}, ensure_ascii=False, indent=2))
