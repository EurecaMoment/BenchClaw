#!/usr/bin/env python3
"""Minimal deterministic full-synthesis skeleton.

Input: question_blueprints.jsonl (optionally exported as question_blueprints.jsonl) + metric_registry.json.
Output: eval_dataset.jsonl with traceability fields.
This skeleton is intentionally conservative: it only serializes blueprints that already
contain a ground-truth answer or an answer_program_id. It does not invent GT.
"""

import argparse, json, hashlib, random
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("--blueprints", required=True)
ap.add_argument("--metric-registry", required=True)
ap.add_argument("--out", required=True)
ap.add_argument("--seed", type=int, default=20260518)
args = ap.parse_args()
random.seed(args.seed)
Path(args.out).parent.mkdir(parents=True, exist_ok=True)
with open(args.metric_registry, encoding="utf-8") as f:
    metrics = json.load(f)
written = 0
with (
    open(args.blueprints, encoding="utf-8") as src,
    open(args.out, "w", encoding="utf-8") as dst,
):
    for line in src:
        if not line.strip():
            continue
        bp = json.loads(line)
        if not bp.get("gt_answer") and not bp.get("answer_program_id"):
            continue
        item_id = (
            bp.get("item_id")
            or "item_"
            + hashlib.sha1(
                json.dumps(bp, sort_keys=True, ensure_ascii=False).encode("utf-8")
            ).hexdigest()[:16]
        )
        item = {
            "item_id": item_id,
            "question": bp.get("question"),
            "options": bp.get("options", []),
            "answer": bp.get("gt_answer"),
            "answer_program_id": bp.get("answer_program_id"),
            "metric_id": bp.get(
                "metric_id", metrics.get("default_metric_id", "exact_match")
            ),
            "capability_tags": bp.get("capability_tags", []),
            "source_trace": bp.get("source_trace", {}),
            "seed": args.seed,
        }
        dst.write(json.dumps(item, ensure_ascii=False) + "\n")
        written += 1
print(f"WROTE {written} items to {args.out}")
