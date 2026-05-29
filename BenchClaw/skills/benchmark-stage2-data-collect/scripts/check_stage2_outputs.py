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
        "realdata",
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
        "benchmarkdataset",
        "USED_INPUTS.json",
        "DONE.json",
    ],
    "17-simulator-multimodal-gt-acquisition": [
        "observations",
        "simulator",
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


def require_prefix(errors, value, prefix, label):
    if not str(value).startswith(prefix):
        errors.append(f"{label} must start with {prefix!r}: {value!r}")


def has_scene_subtree(root):
    if not root.exists() or not root.is_dir():
        return False
    for scene_dir in root.iterdir():
        if scene_dir.is_dir() and has_files(scene_dir):
            return True
    return False


def has_dataset_subtree(root):
    if not root.exists() or not root.is_dir():
        return False
    for dataset_dir in root.iterdir():
        if not dataset_dir.is_dir():
            continue
        for split_dir in dataset_dir.iterdir():
            if split_dir.is_dir() and has_files(split_dir):
                return True
    return False


def has_simulator_scene_subtree(root):
    if not root.exists() or not root.is_dir():
        return False
    for simulator_dir in root.iterdir():
        if not simulator_dir.is_dir():
            continue
        for scene_dir in simulator_dir.iterdir():
            if scene_dir.is_dir() and has_files(scene_dir):
                return True
    return False


def count_timepoints_for_obs_paths(obs_paths):
    frame_stems = set()
    for rel_path in obs_paths.values():
        p = Path(str(rel_path))
        frame_stems.add(p.stem)
    return len(frame_stems)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workspace", default="WORKSPACE_ROOT")
    ap.add_argument(
        "--strict",
        action="store_true",
        help="Also require all non-terminal bridge outputs.",
    )
    args = ap.parse_args()

    base = Path(args.workspace) / "stage2"
    required_nodes = list(REQUIRED.keys()) if args.strict else TERMINALS
    errors = []
    min_sim_timepoints = 50

    stage2_targets = (
        base / "13-execution-plan-ingest" / "stage2_collection_targets.json"
    )
    if stage2_targets.exists():
        try:
            targets_obj = read_json(stage2_targets)
            value = targets_obj.get("simulator_scene_min_timepoints", 50)
            if isinstance(value, int):
                min_sim_timepoints = value
            else:
                errors.append(
                    f"stage2_collection_targets.json has non-integer simulator_scene_min_timepoints: {value!r}"
                )
            if targets_obj.get("real_image_flow_policy") not in (
                None,
                "full_selected_dataset",
            ):
                errors.append(
                    "stage2_collection_targets.json real_image_flow_policy must be 'full_selected_dataset'"
                )
            if targets_obj.get("existing_benchmark_flow_policy") not in (
                None,
                "full_selected_dataset",
            ):
                errors.append(
                    "stage2_collection_targets.json existing_benchmark_flow_policy must be 'full_selected_dataset'"
                )
            if min_sim_timepoints < 50:
                errors.append(
                    f"stage2_collection_targets.json simulator_scene_min_timepoints must be >= 50, got {min_sim_timepoints}"
                )
        except Exception as e:
            errors.append(
                f"invalid stage2_collection_targets.json: {stage2_targets}: {e}"
            )

    for node in required_nodes:
        node_dir = base / node
        for item in REQUIRED[node]:
            path = (
                node_dir / item
                if not item.startswith("../")
                else (node_dir / item).resolve()
            )
            if not path.exists():
                errors.append(f"missing: {path}")
        done = node_dir / "DONE.json"
        if done.exists():
            try:
                obj = read_json(done)
                if obj.get("status") != "done":
                    errors.append(f"bad DONE status: {done}")
            except Exception as e:
                errors.append(f"invalid DONE json: {done}: {e}")

    real_images_dir = base / "15-real-image-acquisition" / "images"
    realdata_dir = base / "15-real-image-acquisition" / "realdata"
    if "15-real-image-acquisition" in required_nodes and not has_files(real_images_dir):
        errors.append(
            f"real image acquisition has no materialized image files: {real_images_dir}"
        )
    if "15-real-image-acquisition" in required_nodes and not has_scene_subtree(
        realdata_dir
    ):
        errors.append(
            f"real image acquisition has no materialized realdata scene/source subtree: {realdata_dir}"
        )

    real_manifest = (
        base / "15-real-image-acquisition" / "real_image_manifest.jsonl"
    )
    if "15-real-image-acquisition" in required_nodes and real_manifest.exists():
        try:
            for idx, record in enumerate(read_jsonl(real_manifest), start=1):
                image_path = record.get("image_path", "")
                require_prefix(
                    errors,
                    image_path,
                    "realdata/",
                    f"real_image_manifest.jsonl line {idx} image_path",
                )
                resolved = base / "15-real-image-acquisition" / image_path
                if not resolved.exists() or not resolved.is_file():
                    errors.append(
                        f"real_image_manifest.jsonl line {idx} points to missing file: {resolved}"
                    )
        except Exception as e:
            errors.append(f"invalid real image manifest jsonl: {real_manifest}: {e}")

    benchmark_raw_dir = base / "16-existing-benchmark-acquisition" / "raw"
    benchmarkdataset_dir = (
        base / "16-existing-benchmark-acquisition" / "benchmarkdataset"
    )
    if "16-existing-benchmark-acquisition" in required_nodes and not has_files(
        benchmark_raw_dir
    ):
        errors.append(
            f"existing benchmark acquisition has no materialized raw sample files: {benchmark_raw_dir}"
        )
    if (
        "16-existing-benchmark-acquisition" in required_nodes
        and not has_dataset_subtree(benchmarkdataset_dir)
    ):
        errors.append(
            f"existing benchmark acquisition has no materialized benchmarkdataset subtree: {benchmarkdataset_dir}"
        )

    benchmark_manifest = (
        base
        / "16-existing-benchmark-acquisition"
        / "benchmark_manifest.jsonl"
    )
    if (
        "16-existing-benchmark-acquisition" in required_nodes
        and benchmark_manifest.exists()
    ):
        try:
            for idx, record in enumerate(read_jsonl(benchmark_manifest), start=1):
                raw_path = record.get("raw_data_path", "")
                require_prefix(
                    errors,
                    raw_path,
                    "benchmarkdataset/",
                    f"benchmark_manifest.jsonl line {idx} raw_data_path",
                )
                resolved = base / "16-existing-benchmark-acquisition" / raw_path
                if not resolved.exists():
                    errors.append(
                        f"benchmark_manifest.jsonl line {idx} points to missing path: {resolved}"
                    )
        except Exception as e:
            errors.append(
                f"invalid benchmark manifest jsonl: {benchmark_manifest}: {e}"
            )

    simulator_obs_dir = base / "17-simulator-multimodal-gt-acquisition" / "observations"
    simulator_tree_dir = base / "17-simulator-multimodal-gt-acquisition" / "simulator"
    simulator_prov_dir = base / "17-simulator-multimodal-gt-acquisition" / "provenance"
    if "17-simulator-multimodal-gt-acquisition" in required_nodes:
        if not has_files(simulator_obs_dir):
            errors.append(
                f"simulator acquisition has no materialized observation files: {simulator_obs_dir}"
            )
        if not has_simulator_scene_subtree(simulator_tree_dir):
            errors.append(
                f"simulator acquisition has no materialized simulator/<simulator>/<scene> subtree: {simulator_tree_dir}"
            )
        if not has_files(simulator_prov_dir):
            errors.append(
                f"simulator acquisition has no materialized provenance files: {simulator_prov_dir}"
            )

    sim_trace_manifest = (
        base
        / "17-simulator-multimodal-gt-acquisition"
        / "sim_trace_manifest.jsonl"
    )
    if (
        "17-simulator-multimodal-gt-acquisition" in required_nodes
        and sim_trace_manifest.exists()
    ):
        try:
            per_scene_counts = {}
            for idx, record in enumerate(read_jsonl(sim_trace_manifest), start=1):
                obs_paths = record.get("observation_paths", {})
                if not isinstance(obs_paths, dict) or not obs_paths:
                    errors.append(
                        f"sim_trace_manifest.jsonl line {idx} has empty observation_paths"
                    )
                    continue
                for modality, rel_path in obs_paths.items():
                    require_prefix(
                        errors,
                        rel_path,
                        "simulator/",
                        f"sim_trace_manifest.jsonl line {idx} observation_paths[{modality!r}]",
                    )
                    resolved = (
                        base / "17-simulator-multimodal-gt-acquisition" / rel_path
                    )
                    if not resolved.exists():
                        errors.append(
                            f"sim_trace_manifest.jsonl line {idx} points to missing observation path: {resolved}"
                        )
                simulator_id = str(record.get("simulator_id") or "")
                scene_id = str(record.get("scene_id") or "")
                if simulator_id and scene_id:
                    key = (simulator_id, scene_id)
                    per_scene_counts[key] = per_scene_counts.get(
                        key, 0
                    ) + count_timepoints_for_obs_paths(obs_paths)
                for required_modality in ["rgb"]:
                    if (
                        required_modality in record.get("modalities", [])
                        and required_modality not in obs_paths
                    ):
                        errors.append(
                            f"sim_trace_manifest.jsonl line {idx} declares modality {required_modality!r} but provides no path"
                        )
            for (simulator_id, scene_id), frame_count in sorted(
                per_scene_counts.items()
            ):
                if frame_count < min_sim_timepoints:
                    errors.append(
                        f"simulator scene {simulator_id}/{scene_id} has only {frame_count} timepoints, below required minimum {min_sim_timepoints}"
                    )
        except Exception as e:
            errors.append(
                f"invalid simulator trace manifest jsonl: {sim_trace_manifest}: {e}"
            )

    if errors:
        print("ERROR: Stage2 output check failed.")
        for e in errors:
            print(" - " + e)
        raise SystemExit(1)

    print("OK: Stage2 terminal outputs are complete.")
    if not args.strict:
        print(
            "Note: bridge nodes 13/14 were not checked. Use --strict to include them."
        )


if __name__ == "__main__":
    main()
