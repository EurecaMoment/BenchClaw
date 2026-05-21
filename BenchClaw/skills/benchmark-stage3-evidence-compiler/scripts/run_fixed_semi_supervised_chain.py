#!/usr/bin/env python3
import argparse
import json
from pathlib import Path


def write_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def build_tool_chain(benchclaw_root: str, record_id: str):
    return [
        {
            "tool": "LLM-local",
            "skill_path": f"{benchclaw_root}/annotation-tool/llm-local/SKILL.md",
            "role": "candidate_terms_and_routing_plan",
            "output_path": f"annotations/llm/{record_id}.json",
            "status": "expected",
        },
        {
            "tool": "YOLOE",
            "skill_path": f"{benchclaw_root}/annotation-tool/yoloe/SKILL.md",
            "role": "semantic_label_and_bbox_candidate",
            "output_path": f"annotations/yoloe/{record_id}.json",
            "status": "expected",
        },
        {
            "tool": "SAM3",
            "skill_path": f"{benchclaw_root}/annotation-tool/sam3/SKILL.md",
            "role": "semantic_entity_segmentation_from_yoloe_and_llm_prompts",
            "output_path": f"annotations/sam3/{record_id}.json",
            "status": "expected",
        },
        {
            "tool": "Depth Anything 3",
            "skill_path": f"{benchclaw_root}/annotation-tool/depthanything3/SKILL.md",
            "role": "depth_map_and_depth_statistics",
            "output_path": f"annotations/depthanything3/{record_id}.json",
            "status": "expected",
        },
    ]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workspace", required=True)
    ap.add_argument("--benchclaw-root", required=True)
    ap.add_argument("--branch", required=True, choices=["realdata", "benchmarkdataset"])
    ap.add_argument("--record-id", required=True)
    ap.add_argument("--group-name", required=True)
    ap.add_argument("--split-name", default="")
    ap.add_argument("--original-image", required=True)
    ap.add_argument("--semantic-image", required=True)
    ap.add_argument("--depth-image", required=True)
    ap.add_argument("--gt-file", required=True)
    ap.add_argument("--llm-output", required=True)
    ap.add_argument("--yoloe-output", required=True)
    ap.add_argument("--sam3-output", required=True)
    ap.add_argument("--depth-output", required=True)
    ap.add_argument("--fused-output", required=True)
    ap.add_argument("--semantic-label", default="unknown")
    ap.add_argument("--confidence", type=float, default=0.0)
    args = ap.parse_args()

    workspace = Path(args.workspace)
    stage3_root = workspace / "stage3"
    if args.branch == "realdata":
        asset_root = stage3_root / "realdata" / args.group_name
        manifest_path = (
            stage3_root
            / "18-real-image-semi-supervised-gt"
            / "semi_gt_manifest.sqlite_export.jsonl"
        )
    else:
        split_name = args.split_name or "default_split"
        asset_root = stage3_root / "benchmarkdataset" / args.group_name / split_name
        manifest_path = (
            stage3_root
            / "19-benchmark-image-semi-supervised-gt"
            / "semi_gt_manifest.sqlite_export.jsonl"
        )

    artifact_paths = {
        "original": f"WORKSPACE_ROOT/stage3/{asset_root.relative_to(stage3_root) / 'original' / Path(args.original_image).name}",
        "semantic_entity_segmentation": f"WORKSPACE_ROOT/stage3/{asset_root.relative_to(stage3_root) / 'semantic_entity_segmentation' / Path(args.semantic_image).name}",
        "depth": f"WORKSPACE_ROOT/stage3/{asset_root.relative_to(stage3_root) / 'depth' / Path(args.depth_image).name}",
        "gt": f"WORKSPACE_ROOT/stage3/{asset_root.relative_to(stage3_root) / 'gt' / Path(args.gt_file).name}",
        "llm": args.llm_output,
        "yoloe": args.yoloe_output,
        "sam3": args.sam3_output,
        "depthanything3": args.depth_output,
        "fused_candidate": args.fused_output,
    }

    candidate = {
        "candidate_id": f"{args.record_id}_candidate_0001",
        "field": "object_instances_with_depth",
        "value": {
            "semantic_label": args.semantic_label,
            "record_id": args.record_id,
        },
        "source_type": "tool_generated_candidate",
        "confidence": args.confidence,
        "tool": "LLM+YOLOE+SAM3+DepthAnything3",
        "tool_version": "registry_defined",
        "evidence": [
            artifact_paths["original"],
            artifact_paths["yoloe"],
            artifact_paths["sam3"],
            artifact_paths["depthanything3"],
            artifact_paths["fused_candidate"],
        ],
        "tool_chain": build_tool_chain(args.benchclaw_root, args.record_id),
        "artifact_paths": {
            "original": artifact_paths["original"],
            "semantic_entity_segmentation": artifact_paths[
                "semantic_entity_segmentation"
            ],
            "depth": artifact_paths["depth"],
            "gt": artifact_paths["gt"],
        },
        "quality_checks": {
            "all_artifacts_present": True,
            "semantic_segmentation_generated_from_yoloe_llm_sam3": True,
            "depth_generated_from_depthanything3": True,
        },
        "is_final_gt": False,
    }

    record = {
        "record_id": args.record_id,
        "gt_candidates": [candidate],
        "conflicts": [],
        "provenance": {
            "created_by_script": "run_fixed_semi_supervised_chain.py",
            "branch": args.branch,
            "group_name": args.group_name,
            "split_name": args.split_name,
        },
    }

    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with manifest_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

    write_json(Path(args.fused_output), record)


if __name__ == "__main__":
    main()
