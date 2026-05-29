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
notes = []


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


def unique_ids(records, key):
    values = set()
    for row in records:
        value = row.get(key)
        if value is not None:
            values.add(str(value))
    return values


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


def subtree_has_files(root, relative_dir_name):
    target = root / relative_dir_name
    return target.is_dir() and has_files(target)


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
            if done_obj.get("status") != "done":
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
    "WORKSPACE_ROOT/stage3/18-real-image-semi-supervised-gt/semi_gt_manifest.sqlite_export.jsonl",
    "WORKSPACE_ROOT/stage3/19-benchmark-image-semi-supervised-gt/semi_gt_manifest.sqlite_export.jsonl",
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

stage2_real_manifest = workspace_path(
    "WORKSPACE_ROOT/stage2/15-real-image-acquisition/real_image_manifest.sqlite_export.jsonl"
)
stage2_benchmark_manifest = workspace_path(
    "WORKSPACE_ROOT/stage2/16-existing-benchmark-acquisition/benchmark_manifest.sqlite_export.jsonl"
)
stage2_sim_manifest = workspace_path(
    "WORKSPACE_ROOT/stage2/17-simulator-multimodal-gt-acquisition/sim_trace_manifest.sqlite_export.jsonl"
)
stage3_real_unified = workspace_path(
    "WORKSPACE_ROOT/stage3/21-real-image-unified-format/unified_records.sqlite_export.jsonl"
)
stage3_benchmark_unified = workspace_path(
    "WORKSPACE_ROOT/stage3/22-benchmark-unified-format/unified_records.sqlite_export.jsonl"
)
stage3_sim_unified = workspace_path(
    "WORKSPACE_ROOT/stage3/23-simulator-unified-format/unified_records.sqlite_export.jsonl"
)
stage3_real_cleaned = workspace_path(
    "WORKSPACE_ROOT/stage3/24-real-image-data-juicer-cleaning/cleaned_records.sqlite_export.jsonl"
)
stage3_benchmark_cleaned = workspace_path(
    "WORKSPACE_ROOT/stage3/25-benchmark-data-juicer-cleaning/cleaned_records.sqlite_export.jsonl"
)
stage3_sim_cleaned = workspace_path(
    "WORKSPACE_ROOT/stage3/26-simulator-data-juicer-cleaning/cleaned_records.sqlite_export.jsonl"
)

stage2_real_ids = (
    unique_ids(read_jsonl(stage2_real_manifest), "sample_id")
    if stage2_real_manifest.exists()
    else set()
)
stage2_benchmark_ids = (
    unique_ids(read_jsonl(stage2_benchmark_manifest), "sample_id")
    if stage2_benchmark_manifest.exists()
    else set()
)
stage2_sim_ids = (
    unique_ids(read_jsonl(stage2_sim_manifest), "sample_id")
    if stage2_sim_manifest.exists()
    else set()
)
stage3_real_unified_ids = (
    unique_ids(read_jsonl(stage3_real_unified), "record_id")
    if stage3_real_unified.exists()
    else set()
)
stage3_benchmark_unified_ids = (
    unique_ids(read_jsonl(stage3_benchmark_unified), "record_id")
    if stage3_benchmark_unified.exists()
    else set()
)
stage3_sim_unified_ids = (
    unique_ids(read_jsonl(stage3_sim_unified), "record_id")
    if stage3_sim_unified.exists()
    else set()
)
stage3_real_cleaned_ids = (
    unique_ids(read_jsonl(stage3_real_cleaned), "record_id")
    if stage3_real_cleaned.exists()
    else set()
)
stage3_benchmark_cleaned_ids = (
    unique_ids(read_jsonl(stage3_benchmark_cleaned), "record_id")
    if stage3_benchmark_cleaned.exists()
    else set()
)
stage3_sim_cleaned_ids = (
    unique_ids(read_jsonl(stage3_sim_cleaned), "record_id")
    if stage3_sim_cleaned.exists()
    else set()
)

if stage2_real_ids and stage3_real_unified_ids != stage2_real_ids:
    errors.append(
        f"node 21 unified coverage mismatch: expected {len(stage2_real_ids)} real-image records from Stage2, got {len(stage3_real_unified_ids)}"
    )
if stage2_benchmark_ids and stage3_benchmark_unified_ids != stage2_benchmark_ids:
    errors.append(
        f"node 22 unified coverage mismatch: expected {len(stage2_benchmark_ids)} benchmark records from Stage2, got {len(stage3_benchmark_unified_ids)}"
    )
if stage2_sim_ids and stage3_sim_unified_ids != stage2_sim_ids:
    errors.append(
        f"node 23 unified coverage mismatch: expected {len(stage2_sim_ids)} simulator records from Stage2, got {len(stage3_sim_unified_ids)}"
    )

if stage3_real_cleaned_ids and not stage3_real_cleaned_ids.issubset(
    stage3_real_unified_ids
):
    errors.append(
        "node 24 cleaned_records.sqlite_export.jsonl contains record_ids not present in node 21 unified_records.sqlite_export.jsonl"
    )
if stage3_benchmark_cleaned_ids and not stage3_benchmark_cleaned_ids.issubset(
    stage3_benchmark_unified_ids
):
    errors.append(
        "node 25 cleaned_records.sqlite_export.jsonl contains record_ids not present in node 22 unified_records.sqlite_export.jsonl"
    )
if stage3_sim_cleaned_ids and not stage3_sim_cleaned_ids.issubset(
    stage3_sim_unified_ids
):
    errors.append(
        "node 26 cleaned_records.sqlite_export.jsonl contains record_ids not present in node 23 unified_records.sqlite_export.jsonl"
    )

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
        "WORKSPACE_ROOT/stage3/18-real-image-semi-supervised-gt/semi_gt_manifest.sqlite_export.jsonl",
        "WORKSPACE_ROOT/stage3/realdata/",
    ),
    (
        "WORKSPACE_ROOT/stage3/19-benchmark-image-semi-supervised-gt/semi_gt_manifest.sqlite_export.jsonl",
        "WORKSPACE_ROOT/stage3/benchmarkdataset/",
    ),
]:
    manifest_path = workspace_path(rel)
    if not manifest_path.exists():
        continue
    try:
        stage3_record_ids = set()
        for idx, record in enumerate(read_jsonl(manifest_path), start=1):
            if record.get("record_id") is not None:
                stage3_record_ids.add(str(record.get("record_id")))
            if not record.get("gt_candidates"):
                errors.append(f"{manifest_path} line {idx} has no gt_candidates")
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
                    if not resolved.exists() or not resolved.is_file():
                        errors.append(
                            f"{manifest_path} line {idx} artifact_paths[{key!r}] points to missing file: {resolved}"
                        )
                gt_value = artifact_paths.get("gt")
                if not gt_value:
                    errors.append(
                        f"{manifest_path} line {idx} candidate missing artifact_paths['gt']"
                    )
                else:
                    resolved = workspace_path(gt_value)
                    if not resolved.exists() or not resolved.is_file():
                        errors.append(
                            f"{manifest_path} line {idx} artifact_paths['gt'] points to missing file: {resolved}"
                        )
        if (
            "18-real-image-semi-supervised-gt" in str(manifest_path)
            and stage2_real_manifest.exists()
        ):
            expected = (
                stage3_real_cleaned_ids or stage3_real_unified_ids or stage2_real_ids
            )
            if stage3_record_ids != expected:
                errors.append(
                    f"stage3 realdata manifest record coverage mismatch: expected {len(expected)} record_ids from upstream Stage3/Stage2, got {len(stage3_record_ids)}"
                )
        if (
            "19-benchmark-image-semi-supervised-gt" in str(manifest_path)
            and stage2_benchmark_manifest.exists()
        ):
            expected = (
                stage3_benchmark_cleaned_ids
                or stage3_benchmark_unified_ids
                or stage2_benchmark_ids
            )
            if stage3_record_ids != expected:
                errors.append(
                    f"stage3 benchmarkdataset manifest record coverage mismatch: expected {len(expected)} record_ids from upstream Stage3/Stage2, got {len(stage3_record_ids)}"
                )
    except Exception as e:
        errors.append(f"invalid semi gt manifest jsonl: {manifest_path}: {e}")

sim_manifest = workspace_path(
    "WORKSPACE_ROOT/stage3/20-simulator-clean-gt-pack/simulator_gt_manifest.sqlite_export.jsonl"
)
if sim_manifest.exists():
    text = sim_manifest.read_text(encoding="utf-8")
    for token in ["sample only", "to_be_generated", "pending"]:
        if token in text:
            errors.append(
                f"forbidden placeholder token {token!r} found in {sim_manifest}"
            )
    try:
        stage3_sim_record_ids = set()
        for idx, record in enumerate(read_jsonl(sim_manifest), start=1):
            if record.get("record_id") is not None:
                stage3_sim_record_ids.add(str(record.get("record_id")))
            artifact_paths = record.get("artifact_paths", {})
            for key in ["original", "semantic_entity_segmentation", "depth", "gt"]:
                value = artifact_paths.get(key)
                if not value:
                    errors.append(
                        f"{sim_manifest} line {idx} missing artifact_paths[{key!r}]"
                    )
                    continue
                if not str(value).startswith("WORKSPACE_ROOT/stage3/simulator/"):
                    errors.append(
                        f"{sim_manifest} line {idx} artifact_paths[{key!r}] must start with 'WORKSPACE_ROOT/stage3/simulator/': {value!r}"
                    )
                    continue
                resolved = workspace_path(value)
                if not resolved.exists() or not resolved.is_file():
                    errors.append(
                        f"{sim_manifest} line {idx} artifact_paths[{key!r}] points to missing file: {resolved}"
                    )
        if stage2_sim_manifest.exists():
            expected = (
                stage3_sim_cleaned_ids or stage3_sim_unified_ids or stage2_sim_ids
            )
            if stage3_sim_record_ids != expected:
                errors.append(
                    f"stage3 simulator manifest record coverage mismatch: expected {len(expected)} record_ids from upstream Stage3/Stage2, got {len(stage3_sim_record_ids)}"
                )
    except Exception as e:
        errors.append(f"invalid simulator gt manifest jsonl: {sim_manifest}: {e}")

for scene_dir in (
    [p for p in realdata_root.iterdir() if p.is_dir()] if realdata_root.exists() else []
):
    for name in ["original", "semantic_entity_segmentation", "depth", "gt"]:
        if not subtree_has_files(scene_dir, name):
            errors.append(
                f"realdata scene/source missing materialized files in {scene_dir / name}"
            )

for dataset_dir in (
    [p for p in benchmark_root.iterdir() if p.is_dir()]
    if benchmark_root.exists()
    else []
):
    for split_dir in [p for p in dataset_dir.iterdir() if p.is_dir()]:
        for name in ["original", "semantic_entity_segmentation", "depth", "gt"]:
            if not subtree_has_files(split_dir, name):
                errors.append(
                    f"benchmarkdataset split/category missing materialized files in {split_dir / name}"
                )

for simulator_dir in (
    [p for p in simulator_root.iterdir() if p.is_dir()]
    if simulator_root.exists()
    else []
):
    for scene_dir in [p for p in simulator_dir.iterdir() if p.is_dir()]:
        for name in ["original", "semantic_entity_segmentation", "depth", "gt"]:
            if not subtree_has_files(scene_dir, name):
                errors.append(
                    f"simulator scene missing materialized files in {scene_dir / name}"
                )
if missing or errors:
    report = {
        "status": "FAIL",
        "missing": missing,
        "errors": errors,
        "notes": notes,
    }
    report_json = workspace_path("WORKSPACE_ROOT/stage3/STAGE3_VALIDATION_REPORT.json")
    report_md = workspace_path("WORKSPACE_ROOT/stage3/STAGE3_VALIDATION_REPORT.md")
    report_json.parent.mkdir(parents=True, exist_ok=True)
    report_json.write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    md_lines = ["# Stage3 Validation Report", "", "Status: FAIL", ""]
    if missing:
        md_lines.append("## Missing")
        md_lines.extend([f"- {item}" for item in missing])
        md_lines.append("")
    if errors:
        md_lines.append("## Errors")
        md_lines.extend([f"- {item}" for item in errors])
        md_lines.append("")
    if notes:
        md_lines.append("## Notes")
        md_lines.extend([f"- {item}" for item in notes])
        md_lines.append("")
    report_md.write_text("\n".join(md_lines), encoding="utf-8")
    print("ERROR: missing Stage3 terminal outputs:")
    for m in missing:
        print("  -", m)
    for e in errors:
        print("  -", e)
    sys.exit(1)
report = {
    "status": "PASS",
    "missing": [],
    "errors": [],
    "notes": [
        "All Stage3 terminal outputs exist.",
        "All Stage2->L1->L2->L3 record coverage checks passed.",
        "All required original/semantic_entity_segmentation/depth/gt files are materialized.",
    ],
}
report_json = workspace_path("WORKSPACE_ROOT/stage3/STAGE3_VALIDATION_REPORT.json")
report_md = workspace_path("WORKSPACE_ROOT/stage3/STAGE3_VALIDATION_REPORT.md")
report_json.parent.mkdir(parents=True, exist_ok=True)
report_json.write_text(
    json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
)
report_md.write_text(
    "\n".join(
        [
            "# Stage3 Validation Report",
            "",
            "Status: PASS",
            "",
            "## Notes",
            "- All Stage3 terminal outputs exist.",
            "- All Stage2->L1->L2->L3 record coverage checks passed.",
            "- All required original/semantic_entity_segmentation/depth/gt files are materialized.",
            "",
        ]
    ),
    encoding="utf-8",
)
print("OK: Stage3 terminal outputs are complete: 18, 19, 20.")
