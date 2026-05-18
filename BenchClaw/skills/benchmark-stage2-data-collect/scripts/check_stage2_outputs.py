#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

REQUIRED = {
    "13-execution-plan-ingest": [
        "execution_plan.md",
        "stage2_collection_targets.json",
        "input_manifest.json",
        "USED_INPUTS.json",
        "DONE.json",
    ],
    "14-simulator-skill-registry": [
        "simulator_skill_registry.json",
        "simulator_io_contracts.json",
        "adapter_plan.md",
        "USED_INPUTS.json",
        "DONE.json",
    ],
    "15-real-image-acquisition": [
        "images",
        "real_image_manifest.jsonl",
        "expected_annotation_spec.json",
        "acquisition_report.md",
        "USED_INPUTS.json",
        "DONE.json",
    ],
    "16-existing-benchmark-acquisition": [
        "benchmark_manifest.jsonl",
        "existing_labels_manifest.jsonl",
        "expected_extra_annotation_spec.json",
        "license_and_split_report.md",
        "USED_INPUTS.json",
        "DONE.json",
    ],
    "17-simulator-multimodal-gt-acquisition": [
        "observations",
        "provenance",
        "sim_trace_manifest.jsonl",
        "gt_manifest.jsonl",
        "collection_report.md",
        "USED_INPUTS.json",
        "DONE.json",
    ],
}

TERMINALS = [
    "15-real-image-acquisition",
    "16-existing-benchmark-acquisition",
    "17-simulator-multimodal-gt-acquisition",
]

def read_json(p):
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workspace", default="WORKSPACE_ROOT")
    ap.add_argument("--strict", action="store_true", help="Also require all non-terminal bridge outputs.")
    args = ap.parse_args()

    base = Path(args.workspace) / "stage2"
    required_nodes = list(REQUIRED.keys()) if args.strict else TERMINALS
    errors = []

    for node in required_nodes:
        node_dir = base / node
        for item in REQUIRED[node]:
            path = node_dir / item
            if not path.exists():
                errors.append(f"missing: {path}")
        done = node_dir / "DONE.json"
        if done.exists():
            try:
                obj = read_json(done)
                if obj.get("status") not in ("done", "skipped_with_reason"):
                    errors.append(f"bad DONE status: {done}")
            except Exception as e:
                errors.append(f"invalid DONE json: {done}: {e}")

    if errors:
        print("ERROR: Stage2 output check failed.")
        for e in errors:
            print(" - " + e)
        raise SystemExit(1)

    print("OK: Stage2 terminal outputs are complete.")
    if not args.strict:
        print("Note: bridge nodes 13/14 were not checked. Use --strict to include them.")

if __name__ == "__main__":
    main()
