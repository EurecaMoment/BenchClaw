#!/usr/bin/env python3
import argparse
import json
import sys
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("--workspace", default="WORKSPACE_ROOT")
ap.add_argument("--dag", default="dag.json")
ap.add_argument("--contracts", default="contracts/node_io_contracts.json")
args = ap.parse_args()

dag = json.loads(Path(args.dag).read_text(encoding="utf-8"))
contracts = json.loads(Path(args.contracts).read_text(encoding="utf-8"))[
    "node_contracts"
]
missing = []
errors = []


def has_files(path):
    return path.exists() and any(child.is_file() for child in path.rglob("*"))


def read_jsonl(path):
    records = []
    for line in path.read_text(encoding="utf-8").splitlines():
        text = line.strip()
        if not text:
            continue
        records.append(json.loads(text))
    return records


def has_scene_asset_tree(root):
    if not root.exists() or not root.is_dir():
        return False
    for scene_dir in root.iterdir():
        if not scene_dir.is_dir():
            continue
        if all(
            (scene_dir / name).is_dir()
            for name in ["original", "semantic_entity_segmentation", "depth", "gt"]
        ):
            return True
    return False


def has_dataset_asset_tree(root):
    if not root.exists() or not root.is_dir():
        return False
    for dataset_dir in root.iterdir():
        if not dataset_dir.is_dir():
            continue
        for split_dir in dataset_dir.iterdir():
            if not split_dir.is_dir():
                continue
            if all(
                (split_dir / name).is_dir()
                for name in ["original", "semantic_entity_segmentation", "depth", "gt"]
            ):
                return True
    return False


def has_simulator_asset_tree(root):
    if not root.exists() or not root.is_dir():
        return False
    for simulator_dir in root.iterdir():
        if not simulator_dir.is_dir():
            continue
        for scene_dir in simulator_dir.iterdir():
            if not scene_dir.is_dir():
                continue
            if all(
                (scene_dir / name).is_dir()
                for name in ["original", "semantic_entity_segmentation", "depth", "gt"]
            ):
                return True
    return False


def workspace_path(path_value):
    text = str(path_value).replace("\\", "/")
    if text == "WORKSPACE_ROOT":
        return Path(args.workspace)
    if text.startswith("WORKSPACE_ROOT/"):
        return Path(args.workspace) / text[len("WORKSPACE_ROOT/") :]
    return Path(path_value)


for nid in dag["terminal_nodes"]:
    node = dag["nodes"][nid]
    done = workspace_path(node["output_dir"]) / "DONE.json"
    if not done.exists():
        missing.append(str(done))
    else:
        try:
            done_obj = json.loads(done.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors.append(f"invalid DONE json: {done}: {exc}")
            done_obj = None
        if done_obj is not None:
            if done_obj.get("node_id") != nid:
                errors.append(f"node_id mismatch in {done}")
            if done_obj.get("status") != "DONE":
                errors.append(
                    f"invalid DONE status in {done}: {done_obj.get('status')!r}"
                )
    for item in contracts[nid]["must_write"]:
        p = workspace_path(item)
        if str(item).endswith("/"):
            if not p.exists() or not p.is_dir():
                missing.append(str(p))
        elif "*" in str(item):
            continue
        else:
            if not p.exists():
                missing.append(str(p))

real_ann_root = workspace_path(
    "WORKSPACE_ROOT/stage3/18-real-image-semi-supervised-gt/annotations"
)
bench_ann_root = workspace_path(
    "WORKSPACE_ROOT/stage3/19-benchmark-image-semi-supervised-gt/annotations"
)
for label, root in (("18", real_ann_root), ("19", bench_ann_root)):
    for subdir in ["yoloe", "sam3", "depthanything3", "fused"]:
        path = root / subdir
        if not has_files(path):
            errors.append(
                f"node {label} missing materialized annotation files in {path}"
            )

for rel in [
    "WORKSPACE_ROOT/stage3/18-real-image-semi-supervised-gt/semi_gt_manifest.jsonl",
    "WORKSPACE_ROOT/stage3/19-benchmark-image-semi-supervised-gt/semi_gt_manifest.jsonl",
]:
    manifest_path = workspace_path(rel)
    if manifest_path.exists():
        text = manifest_path.read_text(encoding="utf-8")
        banned_tokens = [
            "pending tool output",
            '"status": "pending"',
            "expected pipeline",
            "sample only",
            "to_be_generated",
        ]
        for token in banned_tokens:
            if token in text:
                errors.append(
                    f"forbidden placeholder token {token!r} found in {manifest_path}"
                )

realdata_root = workspace_path("WORKSPACE_ROOT/stage3/realdata")
benchmark_root = workspace_path("WORKSPACE_ROOT/stage3/benchmarkdataset")
simulator_root = workspace_path("WORKSPACE_ROOT/stage3/simulator")

if not has_scene_asset_tree(realdata_root):
    errors.append(
        f"stage3 realdata tree is missing required original/semantic_entity_segmentation/depth/gt subdirectories: {realdata_root}"
    )

if not has_dataset_asset_tree(benchmark_root):
    errors.append(
        f"stage3 benchmarkdataset tree is missing required original/semantic_entity_segmentation/depth/gt subdirectories: {benchmark_root}"
    )

if not has_simulator_asset_tree(simulator_root):
    errors.append(
        f"stage3 simulator tree is missing required original/semantic_entity_segmentation/depth/gt subdirectories: {simulator_root}"
    )

for rel, root_prefix in [
    (
        "WORKSPACE_ROOT/stage3/18-real-image-semi-supervised-gt/semi_gt_manifest.jsonl",
        "WORKSPACE_ROOT/stage3/realdata/",
    ),
    (
        "WORKSPACE_ROOT/stage3/19-benchmark-image-semi-supervised-gt/semi_gt_manifest.jsonl",
        "WORKSPACE_ROOT/stage3/benchmarkdataset/",
    ),
]:
    manifest_path = workspace_path(rel)
    if not manifest_path.exists():
        continue
    try:
        for idx, record in enumerate(read_jsonl(manifest_path), start=1):
            for cand in record.get("gt_candidates", []):
                artifact_paths = cand.get("artifact_paths", {})
                for key in ["original", "semantic_entity_segmentation", "depth"]:
                    value = artifact_paths.get(key)
                    if not value:
                        errors.append(
                            f"{manifest_path} line {idx} candidate missing artifact_paths[{key!r}]"
                        )
                        continue
                    if not str(value).startswith(root_prefix):
                        errors.append(
                            f"{manifest_path} line {idx} artifact_paths[{key!r}] must start with {root_prefix!r}: {value!r}"
                        )
                        continue
                    resolved = workspace_path(value)
                    if not resolved.exists():
                        errors.append(
                            f"{manifest_path} line {idx} artifact_paths[{key!r}] points to missing file: {resolved}"
                        )
                gt_value = artifact_paths.get("gt")
                if gt_value:
                    resolved = workspace_path(gt_value)
                    if not resolved.exists():
                        errors.append(
                            f"{manifest_path} line {idx} artifact_paths['gt'] points to missing file: {resolved}"
                        )
    except Exception as e:
        errors.append(f"invalid semi gt manifest jsonl: {manifest_path}: {e}")

sim_manifest = workspace_path(
    "WORKSPACE_ROOT/stage3/20-simulator-clean-gt-pack/simulator_gt_manifest.jsonl"
)
if sim_manifest.exists():
    text = sim_manifest.read_text(encoding="utf-8")
    for token in ["sample only", "to_be_generated", "pending"]:
        if token in text:
            errors.append(
                f"forbidden placeholder token {token!r} found in {sim_manifest}"
            )
if missing or errors:
    print("ERROR: missing Stage3 terminal outputs:")
    for m in missing:
        print("  -", m)
    for e in errors:
        print("  -", e)
    sys.exit(1)
print("OK: Stage3 terminal outputs are complete: 18, 19, 20.")
