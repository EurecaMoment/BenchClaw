#!/usr/bin/env python3
import argparse, json
from collections import Counter
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


PLACEHOLDER_GT_TOKENS = [
    "computed from",
    "privileged_gt",
    "official label answer",
    "placeholder",
    "to_be_generated",
    "pending",
]

GENERIC_QUESTION_PATTERNS = [
    "what is the optimal path from start to goal",
    "success metrics computed from",
]

TASK_SPECIFIC_INPUT_HINTS = [
    "start",
    "goal",
    "target",
    "instruction",
    "choice",
    "option",
    "subject",
    "reference",
    "object",
    "relation",
    "trajectory",
    "waypoint",
    "map",
]


def lower_text(value):
    return str(value or "").strip().lower()


def nested_keys(obj):
    keys = set()
    if isinstance(obj, dict):
        for k, v in obj.items():
            keys.add(str(k))
            keys.update(nested_keys(v))
    elif isinstance(obj, list):
        for item in obj:
            keys.update(nested_keys(item))
    return keys


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
    rows = []
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
        rows.append(row)
        question = str(row.get("question") or "").strip()
        question_lower = lower_text(question)
        if len(question) < 16:
            errors.append(
                f"line {idx} question too short to be a concrete benchmark item"
            )
        if (
            "..." in question
            or "<" in question
            or ">" in question
            or "tbd" in question_lower
        ):
            errors.append(
                f"line {idx} question contains unresolved placeholder markers"
            )
        if any(token in question_lower for token in GENERIC_QUESTION_PATTERNS):
            keys = {k.lower() for k in nested_keys(row.get("input_fields") or {})}
            if not any(
                any(hint in k for hint in TASK_SPECIFIC_INPUT_HINTS) for k in keys
            ):
                errors.append(
                    f"line {idx} question looks like a generic template shell without concrete task variables"
                )

        gt_answer = row.get("ground_truth_answer")
        if gt_answer in (None, ""):
            errors.append(f"line {idx} missing ground_truth_answer")
        elif any(token in lower_text(gt_answer) for token in PLACEHOLDER_GT_TOKENS):
            errors.append(f"line {idx} has placeholder-like ground_truth_answer")

        input_fields = row.get("input_fields")
        if not isinstance(input_fields, dict) or not input_fields:
            errors.append(f"line {idx} missing concrete input_fields")
        else:
            if set(input_fields.keys()) <= {"scene_id", "modality_condition"}:
                errors.append(
                    f"line {idx} input_fields only contain generic scene/modality fields without task-specific variables"
                )

        if row.get("evaluation_ready") is not True:
            errors.append(
                f"line {idx} evaluation_ready must be true only for final accepted items"
            )

        modality = row.get("modality_condition")
        if not isinstance(modality, dict) and isinstance(input_fields, dict):
            modality = input_fields.get("modality_condition")
        if isinstance(modality, dict):
            meta_text = " ".join(
                [
                    lower_text(row.get("question_type")),
                    lower_text(row.get("template_id")),
                    " ".join(lower_text(x) for x in (row.get("capability_tags") or [])),
                ]
            )
            if "depth" in meta_text and modality.get("depth") is not True:
                errors.append(
                    f"line {idx} requires depth semantics but modality_condition.depth is not true"
                )
            if (
                any(token in meta_text for token in ["instruction", "language", "lang"])
                and modality.get("language") is not True
            ):
                errors.append(
                    f"line {idx} requires language input but modality_condition.language is not true"
                )

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

    total = len(rows)
    if total == 0:
        errors.append("EVALSET_DATASET/data/test.jsonl contains no items")
    else:
        questions = [str(row.get("question") or "").strip() for row in rows]
        unique_questions = set(questions)
        unique_ratio = len(unique_questions) / total
        if total >= 50 and unique_ratio < 0.5:
            errors.append(
                f"question uniqueness is too low for a formal benchmark: {len(unique_questions)}/{total} unique questions"
            )

        top_question_count = Counter(questions).most_common(1)[0][1]
        if total >= 50 and top_question_count > max(20, int(total * 0.1)):
            errors.append(
                f"one question text is reused too heavily: max duplicate count {top_question_count} across {total} items"
            )

        dimensions = [
            str(row.get("dimension") or "") for row in rows if row.get("dimension")
        ]
        if dimensions:
            top_dimension_count = Counter(dimensions).most_common(1)[0][1]
            if total >= 50 and top_dimension_count / total > 0.4:
                errors.append(
                    f"dimension distribution is too concentrated: top dimension share {top_dimension_count}/{total}"
                )

        templates = [
            str(row.get("template_id") or "") for row in rows if row.get("template_id")
        ]
        if templates:
            top_template_count = Counter(templates).most_common(1)[0][1]
            if total >= 50 and top_template_count / total > 0.25:
                errors.append(
                    f"template distribution is too concentrated: top template share {top_template_count}/{total}"
                )

        scene_ids = []
        for row in rows:
            source_trace = row.get("source_trace") or {}
            if isinstance(source_trace, dict):
                scene_id = source_trace.get("scene_id") or source_trace.get(
                    "source_record_id"
                )
                if scene_id:
                    scene_ids.append(str(scene_id))
        if scene_ids:
            top_scene_count = Counter(scene_ids).most_common(1)[0][1]
            if total >= 50 and top_scene_count > 10:
                errors.append(
                    f"scene reuse is too concentrated: one scene/source appears {top_scene_count} times"
                )

        seeds = [row.get("seed") for row in rows if row.get("seed") is not None]
        if total >= 50 and seeds and len(set(seeds)) == 1 and unique_ratio < 0.8:
            errors.append(
                f"all items share the same seed {seeds[0]!r} while question diversity is too low"
            )
if errors:
    print("ERROR: Stage4 output check failed:")
    for e in errors:
        print(" - " + e)
    raise SystemExit(1)
print("OK: Stage4 outputs complete.")
