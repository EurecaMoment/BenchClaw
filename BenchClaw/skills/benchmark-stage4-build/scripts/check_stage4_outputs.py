#!/usr/bin/env python3
import argparse, json
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("--workspace", default="WORKSPACE_ROOT")
ap.add_argument("--dag", default="dag.json")
args = ap.parse_args()
with open(args.dag, "r", encoding="utf-8") as f:
    dag = json.load(f)
nodes = dag["nodes"]
errors = []


def has_files(path):
    return path.exists() and any(child.is_file() for child in path.rglob("*"))


def workspace_path(path_value):
    text = str(path_value).replace("\\", "/")
    if text == "WORKSPACE_ROOT":
        return Path(args.workspace)
    if text.startswith("WORKSPACE_ROOT/"):
        return Path(args.workspace) / text[len("WORKSPACE_ROOT/") :]
    return Path(path_value)


for nid, node in nodes.items():
    out = workspace_path(node["output_dir"])
    if not (out / "DONE.json").exists():
        errors.append(f"missing DONE for node {nid}: {out}/DONE.json")
        continue
    try:
        done_obj = json.loads((out / "DONE.json").read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        errors.append(f"invalid DONE json for node {nid}: {exc}")
        continue
    if str(done_obj.get("node_id")) != str(nid):
        errors.append(f"node_id mismatch in DONE for node {nid}")
    expected_status = "waived" if nid in ["33", "34"] else "done"
    if done_obj.get("status") != expected_status:
        errors.append(
            f"bad DONE status for node {nid}: expected {expected_status!r}, got {done_obj.get('status')!r}"
        )
for nid in ["33", "34"]:
    out = workspace_path(nodes[nid]["output_dir"])
    if not (out / "WAIVED.json").exists():
        errors.append(f"node {nid} must be waived but WAIVED.json missing")
term = workspace_path(nodes["37"]["output_dir"])
required = [
    term / "EVALSET_DATASET" / "README.md",
    term / "EVALSET_DATASET" / "data" / "test.jsonl",
    term / "EVALSET_DATASET" / "images",
    term / "EVALSET_DATASET" / "metrics" / "evaluate.py",
    term / "FINAL_BENCHMARK_CARD.md",
    term / "STAGE4_REPORT.md",
    term / "DONE.json",
]
for p in required:
    if not p.exists():
        errors.append(f"missing final artifact: {p}")

images_dir = term / "EVALSET_DATASET" / "images"
if images_dir.exists() and not has_files(images_dir):
    errors.append(
        f"artifact pack images directory has no materialized image files: {images_dir}"
    )

hf_metric_entry = term / "EVALSET_DATASET" / "metrics" / "evaluate.py"
if hf_metric_entry.exists():
    metric_text = hf_metric_entry.read_text(encoding="utf-8").strip()
    if not metric_text:
        errors.append(f"EVALSET_DATASET metric entry is empty: {hf_metric_entry}")

hf_dataset = term / "EVALSET_DATASET" / "data" / "test.jsonl"
if hf_dataset.exists():
    unresolved_hf_refs = []
    for idx, line in enumerate(hf_dataset.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append(
                f"invalid JSONL in EVALSET_DATASET/data/test.jsonl at line {idx}: {exc}"
            )
            continue
        refs = row.get("image_refs") or row.get("media_refs") or []
        if not isinstance(refs, list):
            errors.append(
                f"EVALSET_DATASET/data/test.jsonl line {idx} has non-list image/media refs"
            )
            continue
        for ref in refs:
            if not isinstance(ref, str):
                errors.append(
                    f"EVALSET_DATASET/data/test.jsonl line {idx} has non-string media ref {ref!r}"
                )
                continue
            if ref.startswith("/"):
                unresolved_hf_refs.append((idx, ref, "absolute path"))
                continue
            candidate = images_dir / ref
            if not candidate.exists():
                unresolved_hf_refs.append(
                    (idx, ref, "missing under EVALSET_DATASET/images/")
                )
    if unresolved_hf_refs:
        preview = ", ".join(
            f"line {idx}: {ref} ({reason})"
            for idx, ref, reason in unresolved_hf_refs[:10]
        )
        errors.append(
            f"EVALSET_DATASET/data/test.jsonl contains unresolved media refs: {preview}"
        )
if errors:
    print("ERROR: Stage4 output check failed:")
    for e in errors:
        print(" - " + e)
    raise SystemExit(1)
print("OK: Stage4 outputs complete.")
