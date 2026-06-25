#!/usr/bin/env python3
"""BenchClaw executable stage gate checks.

This validator is intentionally dependency-free so stage managers can run it
before writing stage completion markers. It checks for the failure modes that
natural-language skill text cannot reliably prevent: placeholder paths, empty
artifacts, missing node records, missing annotation evidence, missing synthesis
outputs, and missing evaluation provenance.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


STAGE_NODES = {
    "stage1": [
        "intent-understanding",
        "literature-search",
        "literature-review",
        "capability-dimension-planning",
        "template-metric-draft-generation",
        "benchmark-draft-generation",
        "execution-plan-generation",
    ],
    "stage2": [
        "stage2-plan-generation",
        "real-image-collection-analysis",
        "existing-benchmark-collection-analysis",
        "simulator-collection-analysis",
    ],
    "stage3": [
        "stage3-plan-generation",
        "real-image-evidence-compilation",
        "existing-benchmark-evidence-compilation",
        "simulator-evidence-compilation",
    ],
    "stage4": [
        "stage4-plan-generation",
        "template-metric-code-generation",
        "grey-batch-validation",
        "full-synthesis",
    ],
    "stage5": [
        "full-evaluation",
    ],
}

STAGE3_ARTIFACTS = [
    "data_17_annotated_real_image_bundle",
    "data_18_annotated_existing_benchmark_bundle",
    "data_19_annotated_simulator_bundle",
]

STAGE4_DATA20_REQUIRED = [
    "README.md",
    "source_inventory.jsonl",
    "field_catalog.yaml",
    "evidence_index.jsonl",
    "difficulty_mix_contract.json",
    "image_processing/image_manifest.jsonl",
    "contrib/gt_adapter/adapter_contract.json",
    "contrib/asset_builder/asset_builder_contract.json",
    "contrib/template_registry/template_registry.json",
    "contrib/metric_registry/metric_registry.json",
    "contrib/item_validator/item_validator_contract.json",
    "template_manifest.jsonl",
    "metric_manifest.jsonl",
    "code_manifest.json",
    "synthesis_plan.yaml",
    "traceability.csv",
    "scripts/benchclaw_stage4_synthesis_base.py",
    "scripts/generate_items.py",
    "scripts/score_predictions.py",
    "scripts/package_evalset.py",
    "scripts/check_difficulty_mix.py",
    "scripts/validate_bundle.py",
    "contracts/benchmark_item.schema.json",
    "tests/smoke_test.py",
    "self_test/dry_run_items.jsonl",
    "self_test/perfect_score_report.json",
    "self_test/negative_score_report.json",
    "self_test/difficulty_mix_report.json",
    "self_test/py_compile.log",
    "self_test/self_test_report.md",
]

STAGE4_DATA21_REQUIRED = [
    "report.md",
    "template_status.csv",
    "item_level_findings.jsonl",
    "per_template_batch/generated_items.jsonl",
    "invalid_item_screening/valid_items.jsonl",
    "invalid_item_screening/screening_report.json",
    "scorer_smoke/perfect_score_report.json",
    "scorer_smoke/negative_score_report.json",
    "small_model_eval/score_matrix.jsonl",
    "cdm_irt/cdm_irt_summary.json",
    "difficulty_mix_report.json",
]

STAGE4_DATA22_REQUIRED = [
    "audit_format/benchmark_items.jsonl",
    "audit_format/template_registry.json",
    "audit_format/generation_report.json",
    "dataset.jsonl",
    "data/test.jsonl",
    "ground_truth/answers.jsonl",
    "ground_truth/audit_items_with_answers.jsonl",
    "metrics/score_predictions.py",
    "manifest.json",
    "cards/benchmark_card.md",
    "checksums.json",
]

STAGE5_DATA23_REQUIRED = [
    "evaluation_report.md",
    "metrics.json",
    "prediction_audit.jsonl",
    "error_taxonomy.jsonl",
    "opencode_usage_report.json",
    "opencode_usage_report.txt",
]

MODEL_VISIBLE_FORBIDDEN_KEYS = {
    "answer",
    "answers",
    "gold_answer",
    "ground_truth",
    "gt",
    "metadata",
    "provenance",
    "object_provenance",
    "evidence_refs",
    "evidence_ref",
    "bbox",
    "bboxes",
    "bounding_box",
    "depth",
    "depth_map",
    "area",
    "areas",
    "label",
    "labels",
    "target",
    "targets",
}

MODEL_VISIBLE_FORBIDDEN_PREFIXES = ("gt_", "gold_")

FORBIDDEN_STAGE3_TEXT = [
    "ready_for_stage4",
    "deferred",
    "pending_stage4_verification",
    "pipeline ready",
    "ready_for_annotation",
]


def rel(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


class Gate:
    def __init__(self, workspace_root: Path, stage: str) -> None:
        self.workspace_root = workspace_root
        self.stage = stage
        self.checks: list[dict[str, Any]] = []

    def add(self, ok: bool, check: str, message: str, path: Path | None = None, **extra: Any) -> None:
        row: dict[str, Any] = {
            "status": "PASS" if ok else "FAIL",
            "check": check,
            "message": message,
        }
        if path is not None:
            row["path"] = rel(path, self.workspace_root)
        row.update(extra)
        self.checks.append(row)

    def fail(self, check: str, message: str, path: Path | None = None, **extra: Any) -> None:
        self.add(False, check, message, path, **extra)

    def pass_(self, check: str, message: str, path: Path | None = None, **extra: Any) -> None:
        self.add(True, check, message, path, **extra)

    def exists(self, path: Path, check: str, kind: str = "path") -> bool:
        ok = path.exists()
        self.add(ok, check, f"{kind} exists" if ok else f"missing {kind}", path)
        return ok

    def file_nonempty(self, path: Path, check: str) -> bool:
        ok = path.is_file() and path.stat().st_size > 0
        self.add(ok, check, "file is non-empty" if ok else "missing or empty file", path)
        return ok

    def dir_nonempty_files(self, path: Path, check: str) -> bool:
        ok = path.is_dir() and any(p.is_file() and p.stat().st_size > 0 for p in path.rglob("*"))
        self.add(ok, check, "directory has non-empty files" if ok else "missing or empty directory", path)
        return ok

    def json_file(self, path: Path, check: str) -> Any | None:
        if not self.file_nonempty(path, check):
            return None
        try:
            with path.open("r", encoding="utf-8") as fh:
                data = json.load(fh)
        except Exception as exc:  # noqa: BLE001 - report parser detail
            self.fail(check, f"invalid JSON: {exc}", path)
            return None
        self.pass_(check, "valid JSON", path)
        return data

    def jsonl_nonempty(self, path: Path, check: str) -> int:
        if not self.file_nonempty(path, check):
            return 0
        count = 0
        line_no = 0
        try:
            with path.open("r", encoding="utf-8") as fh:
                for line_no, line in enumerate(fh, start=1):
                    stripped = line.strip()
                    if not stripped:
                        continue
                    json.loads(stripped)
                    count += 1
        except Exception as exc:  # noqa: BLE001 - report parser detail
            self.fail(check, f"invalid JSONL at line {line_no}: {exc}", path)
            return count
        self.add(count > 0, check, f"valid JSONL records: {count}" if count else "empty JSONL", path, records=count)
        return count

    def csv_nonempty(self, path: Path, check: str) -> bool:
        if not self.file_nonempty(path, check):
            return False
        text = read_text_limited(path)
        rows = [line for line in text.splitlines() if line.strip()]
        ok = len(rows) >= 2
        self.add(ok, check, f"CSV-like file has {len(rows)} non-empty rows" if ok else "CSV-like file has no data rows", path)
        return ok

    @property
    def failed(self) -> bool:
        return any(row["status"] == "FAIL" for row in self.checks)

    def report(self) -> dict[str, Any]:
        return {
            "status": "FAIL" if self.failed else "PASS",
            "stage": self.stage,
            "workspace_root": str(self.workspace_root),
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "checks": self.checks,
            "summary": {
                "passed": sum(1 for row in self.checks if row["status"] == "PASS"),
                "failed": sum(1 for row in self.checks if row["status"] == "FAIL"),
            },
        }


def read_text_limited(path: Path, limit: int = 1_000_000) -> str:
    try:
        with path.open("r", encoding="utf-8", errors="replace") as fh:
            return fh.read(limit)
    except Exception:
        return ""


def check_workspace_root_contract(gate: Gate) -> None:
    workspace_root = gate.workspace_root
    workspace_suffix = workspace_root.name[len("workspace") :] if workspace_root.name.startswith("workspace") else ""
    workspace_name_ok = bool(workspace_suffix) and workspace_suffix.isdecimal()
    workspace_parent = workspace_root.parent
    project_root = workspace_parent.parent
    expected_workspace_parent = project_root / "workspaces"
    expected_workspace_root = expected_workspace_parent / workspace_root.name
    parent_ok = workspace_parent.name == "workspaces"
    project_root_ok = (project_root / "BenchClaw").is_dir()
    ok = workspace_name_ok and parent_ok and project_root_ok and workspace_root == expected_workspace_root

    reasons = []
    if not workspace_name_ok:
        reasons.append("workspace directory name must match workspace{I} with decimal digits")
    if not parent_ok:
        reasons.append("workspace parent directory must be named workspaces")
    if not project_root_ok:
        reasons.append("PROJECT_ROOT must contain BenchClaw/")

    gate.add(
        ok,
        "workspace.root_contract",
        "WORKSPACE_ROOT matches PROJECT_ROOT/workspaces/workspace{I}"
        if ok
        else "WORKSPACE_ROOT violates PROJECT_ROOT/workspaces/workspace{I}: " + "; ".join(reasons),
        workspace_root,
        actual=str(workspace_root),
        expected=str(expected_workspace_root),
        project_root=str(project_root),
        workspace_parent=str(expected_workspace_parent),
        workspace_index=workspace_suffix if workspace_name_ok else None,
    )

    path_resolution = workspace_root / "path_resolution.json"
    if not path_resolution.is_file():
        return
    path_data = gate.json_file(path_resolution, "workspace.path_resolution_json")
    if not isinstance(path_data, dict):
        return

    expected_paths = {
        "PROJECT_ROOT": project_root,
        "BENCHCLAW_ROOT": project_root / "BenchClaw",
        "WORKSPACE_PARENT": expected_workspace_parent,
        "WORKSPACE_ROOT": expected_workspace_root,
    }
    for key, expected_path in expected_paths.items():
        raw_value = path_data.get(key)
        resolved_value = Path(str(raw_value)).expanduser().resolve() if isinstance(raw_value, str) and raw_value else None
        matches = resolved_value == expected_path
        gate.add(
            matches,
            f"workspace.path_resolution_{key.lower()}",
            f"{key} matches frozen workspace contract" if matches else f"{key} must resolve to {expected_path}",
            path_resolution,
            actual=str(resolved_value) if resolved_value else raw_value,
            expected=str(expected_path),
        )


def has_nonempty_named_file(root: Path, names: Iterable[str]) -> bool:
    wanted = set(names)
    return any(p.is_file() and p.name in wanted and p.stat().st_size > 0 for p in root.rglob("*"))


def count_named_files(root: Path, names: Iterable[str]) -> int:
    wanted = set(names)
    return sum(1 for p in root.rglob("*") if p.is_file() and p.name in wanted and p.stat().st_size > 0)


def count_result_json(root: Path) -> int:
    return sum(
        1
        for p in root.rglob("result.json")
        if p.is_file() and p.stat().st_size > 0 and "default_annotation_output" in p.parts
    )


def stage2_min_total_images(workspace_root: Path) -> tuple[int, str]:
    """Return the Stage2 minimum image requirement, defaulting to 100."""
    default_minimum = 100
    plan_candidates = [
        workspace_root / "stage2" / "nodes" / "stage2-plan-generation" / "stage2_execution_plan.yaml",
        workspace_root
        / "stage2"
        / "nodes"
        / "stage2-plan-generation"
        / "artifacts"
        / "stage2_execution_plan"
        / "stage2_execution_plan.yaml",
        workspace_root / "stage2" / "artifacts" / "stage2_execution_plan" / "stage2_execution_plan.yaml",
    ]
    keys = (
        "default_min_total_images",
        "effective_min_total_images",
        "minimum_total_collected_images",
        "min_total_collected_images",
        "minimum_total_images",
        "min_total_images",
    )
    for path in plan_candidates:
        text = read_text_limited(path, limit=200_000)
        if not text:
            continue
        lowered_text = text.lower()
        has_explicit_exception = (
            "explicit_user_or_stage1_requirement: true" in lowered_text
            or "explicit_scale_exception:" in lowered_text
            and "explicit_scale_exception: null" not in lowered_text
            and "explicit_scale_exception: none" not in lowered_text
        )
        for raw_line in text.splitlines():
            line = raw_line.split("#", 1)[0].strip()
            if ":" not in line:
                continue
            key, value = line.split(":", 1)
            if key.strip() not in keys:
                continue
            value = value.strip().strip("'\"")
            if value.isdigit():
                planned_minimum = int(value)
                if planned_minimum >= default_minimum or has_explicit_exception:
                    return planned_minimum, f"explicit stage2 plan field {key.strip()}"
                return default_minimum, f"ignored lower stage2 plan field {key.strip()} without explicit scale exception"
    return default_minimum, "default stage2 minimum_total_collected_images"


def stage2_bundle_root_for_manifest(manifest_path: Path, artifacts: Path) -> Path:
    for bundle_name in (
        "data_14_real_image_collection_bundle",
        "data_15_existing_benchmark_collection_bundle",
        "data_16_simulator_collection_bundle",
        "data_16_simulated_scene_bundle",
    ):
        bundle_root = artifacts / bundle_name
        try:
            manifest_path.relative_to(bundle_root)
        except ValueError:
            continue
        return bundle_root
    return manifest_path.parent


def resolve_stage2_media_path(bundle_root: Path, manifest_path: Path, raw_path: Any) -> Path | None:
    if not isinstance(raw_path, str):
        return None
    text = raw_path.strip()
    if not text or text.startswith(("http://", "https://", "file://", "data:")):
        return None
    path = Path(text)
    candidates = [path] if path.is_absolute() else [bundle_root / path, manifest_path.parent / path]
    for candidate in candidates:
        resolved = candidate.resolve()
        if resolved.is_file() and not resolved.is_symlink() and resolved.stat().st_size > 0:
            return resolved
    return None


def count_stage2_valid_manifest_images(artifacts: Path) -> int:
    valid_paths: set[str] = set()
    for manifest_path in artifacts.rglob("media_manifest.jsonl"):
        bundle_root = stage2_bundle_root_for_manifest(manifest_path, artifacts)
        for _, record in iter_jsonl_records(manifest_path, limit=200000):
            modality = str(record.get("modality") or record.get("media_type") or "").strip().lower()
            role = str(record.get("role") or "").strip().lower()
            mime_type = str(record.get("mime_type") or "").strip().lower()
            decode_status = str(record.get("decode_status") or "").strip().lower()
            if not (modality == "image" or role.endswith("image") or mime_type.startswith("image/")):
                continue
            if decode_status and decode_status != "ok":
                continue
            raw_path = record.get("workspace_path") or record.get("path") or record.get("file_path")
            resolved = resolve_stage2_media_path(bundle_root, manifest_path, raw_path)
            if resolved is None or looks_like_placeholder_path(resolved.name):
                continue
            valid_paths.add(str(resolved))
    return len(valid_paths)


def first_jsonl_record(path: Path) -> dict[str, Any] | None:
    if not path.is_file() or path.stat().st_size == 0:
        return None
    try:
        with path.open("r", encoding="utf-8") as fh:
            for line in fh:
                stripped = line.strip()
                if not stripped:
                    continue
                data = json.loads(stripped)
                if isinstance(data, dict):
                    return data
                return None
    except Exception:
        return None
    return None


def nonempty_jsonl_records(paths: Iterable[Path]) -> int:
    total = 0
    for path in paths:
        if not path.is_file() or path.stat().st_size == 0:
            continue
        try:
            with path.open("r", encoding="utf-8") as fh:
                for line in fh:
                    if line.strip():
                        total += 1
        except Exception:
            continue
    return total


def iter_jsonl_records(path: Path, limit: int = 2000) -> Iterable[tuple[int, dict[str, Any]]]:
    if not path.is_file() or path.stat().st_size == 0:
        return
    count = 0
    with path.open("r", encoding="utf-8") as fh:
        for line_no, line in enumerate(fh, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            data = json.loads(stripped)
            if isinstance(data, dict):
                yield line_no, data
                count += 1
                if count >= limit:
                    return


def flatten_media_values(value: Any) -> list[str]:
    out: list[str] = []
    if value is None:
        return out
    if isinstance(value, str):
        text = value.strip()
        if text:
            out.append(text)
        return out
    if isinstance(value, dict):
        for key in ("path", "paths", "image", "images", "media", "url"):
            if key in value:
                out.extend(flatten_media_values(value[key]))
        return out
    if isinstance(value, (list, tuple, set)):
        for item in value:
            out.extend(flatten_media_values(item))
        return out
    return out


def record_media_paths(record: dict[str, Any]) -> list[str]:
    paths: list[str] = []
    for key in (
        "image",
        "images",
        "image_path",
        "image_paths",
        "media",
        "media_refs",
        "image_refs",
        "auxiliary_images",
        "source_media",
    ):
        if key in record:
            paths.extend(flatten_media_values(record.get(key)))
    seen = set()
    deduped: list[str] = []
    for item in paths:
        if item not in seen:
            deduped.append(item)
            seen.add(item)
    return deduped


def forbidden_model_visible_keys(record: dict[str, Any]) -> list[str]:
    hits: list[str] = []
    for key in record:
        lowered = str(key).strip().lower()
        if lowered in MODEL_VISIBLE_FORBIDDEN_KEYS or lowered.startswith(MODEL_VISIBLE_FORBIDDEN_PREFIXES):
            hits.append(str(key))
    return sorted(hits)


def check_model_visible_jsonl(gate: Gate, path: Path, check_prefix: str) -> int:
    count = gate.jsonl_nonempty(path, f"{check_prefix}.jsonl")
    if count == 0:
        return 0

    forbidden_hits: list[tuple[int, list[str]]] = []
    missing_question: list[int] = []
    missing_media: list[int] = []
    for line_no, record in iter_jsonl_records(path, limit=5000):
        hits = forbidden_model_visible_keys(record)
        if hits:
            forbidden_hits.append((line_no, hits))
        if not any(key in record for key in ("question", "question_text", "prompt")):
            missing_question.append(line_no)
        if not record_media_paths(record):
            missing_media.append(line_no)

    gate.add(
        not forbidden_hits,
        f"{check_prefix}.no_hidden_gt",
        "model-visible JSONL has no answer/GT/provenance leakage"
        if not forbidden_hits else
        f"model-visible JSONL leaks hidden fields on {len(forbidden_hits)} sampled records",
        path,
        line=forbidden_hits[0][0] if forbidden_hits else None,
        keys=forbidden_hits[0][1] if forbidden_hits else None,
    )
    gate.add(
        not missing_question,
        f"{check_prefix}.question_fields",
        "all sampled records include a question/prompt field"
        if not missing_question else
        f"records missing question/prompt field: {len(missing_question)}",
        path,
        line=missing_question[0] if missing_question else None,
    )
    gate.add(
        not missing_media,
        f"{check_prefix}.media_fields",
        "all sampled records include media references"
        if not missing_media else
        f"records missing media references: {len(missing_media)}",
        path,
        line=missing_media[0] if missing_media else None,
    )
    return count


def check_answers_jsonl(gate: Gate, path: Path, check_prefix: str) -> int:
    count = gate.jsonl_nonempty(path, f"{check_prefix}.jsonl")
    if count == 0:
        return 0

    missing_id: list[int] = []
    missing_answer: list[int] = []
    missing_audit: list[int] = []
    for line_no, record in iter_jsonl_records(path, limit=5000):
        if not any(key in record for key in ("id", "question_id", "item_id")):
            missing_id.append(line_no)
        if not any(key in record for key in ("answer", "answers", "gold_answer", "ground_truth", "gt")):
            missing_answer.append(line_no)
        if not any(key in record for key in ("evidence_refs", "evidence", "audit", "audit_trail", "source", "provenance", "metadata")):
            missing_audit.append(line_no)

    gate.add(
        not missing_id,
        f"{check_prefix}.id_fields",
        "all sampled answer records include an item id"
        if not missing_id else
        f"answer records missing item id: {len(missing_id)}",
        path,
        line=missing_id[0] if missing_id else None,
    )
    gate.add(
        not missing_answer,
        f"{check_prefix}.answer_fields",
        "all sampled answer records include gold answers"
        if not missing_answer else
        f"answer records missing gold answer: {len(missing_answer)}",
        path,
        line=missing_answer[0] if missing_answer else None,
    )
    gate.add(
        not missing_audit,
        f"{check_prefix}.audit_fields",
        "all sampled answer records include audit/evidence context"
        if not missing_audit else
        f"answer records missing audit/evidence context: {len(missing_audit)}",
        path,
        line=missing_audit[0] if missing_audit else None,
    )
    return count


def check_difficulty_mix(gate: Gate, path: Path, check_prefix: str) -> None:
    if gate.jsonl_nonempty(path, f"{check_prefix}.jsonl") == 0:
        return
    counts = {"easy": 0, "medium": 0, "hard": 0}
    total = 0
    missing = 0
    for _, record in iter_jsonl_records(path, limit=10000):
        total += 1
        difficulty = str(
            record.get("difficulty")
            or record.get("difficulty_level")
            or (record.get("metadata", {}) if isinstance(record.get("metadata"), dict) else {}).get("difficulty_level")
            or ""
        ).lower()
        if difficulty in counts:
            counts[difficulty] += 1
        else:
            missing += 1
    if total == 0:
        return
    ratios = {key: value / total for key, value in counts.items()}
    ok = ratios["easy"] >= 0.20 and ratios["medium"] >= 0.25 and ratios["hard"] >= 0.20 and missing == 0
    gate.add(
        ok,
        f"{check_prefix}.difficulty_mix",
        (
            "easy/medium/hard difficulty mix meets minimum ratios"
            if ok else
            "difficulty mix fails required easy>=0.20, medium>=0.25, hard>=0.20 or has unlabeled records"
        ),
        path,
        total=total,
        counts=counts,
        ratios=ratios,
        missing_or_unknown=missing,
    )


def looks_like_placeholder_path(path_text: str) -> bool:
    lowered = path_text.strip().lower()
    return any(token in lowered for token in ("placeholder", "dummy", "fake", "todo", "tbd"))


def is_evalset_relative_image_path(path_text: str) -> bool:
    text = path_text.strip()
    return text.startswith("./images/") and len(text) > len("./images/")


def resolve_evalset_media_path(evalset_root: Path, raw_path: str) -> Path | None:
    text = raw_path.strip()
    if not text or text.startswith(("http://", "https://", "file://", "data:")):
        return None
    if not is_evalset_relative_image_path(text):
        return None
    relative = text[2:]
    return (evalset_root / relative).resolve()


def check_workspace_evalset_dataset(gate: Gate, stage: str) -> None:
    evalset_root = gate.workspace_root / "EVALSET_DATASET"
    gate.dir_nonempty_files(evalset_root, f"{stage}.evalset_dataset.nonempty")
    if not evalset_root.exists():
        return

    gate.file_nonempty(evalset_root / "README.md", f"{stage}.evalset_dataset.readme")
    data_dir = evalset_root / "data"
    images_dir = evalset_root / "images"
    ground_truth_dir = evalset_root / "ground_truth"
    metrics_dir = evalset_root / "metrics"
    gate.dir_nonempty_files(data_dir, f"{stage}.evalset_dataset.data_dir")
    gate.dir_nonempty_files(images_dir, f"{stage}.evalset_dataset.images_dir")
    gate.dir_nonempty_files(ground_truth_dir, f"{stage}.evalset_dataset.ground_truth_dir")
    gate.dir_nonempty_files(metrics_dir, f"{stage}.evalset_dataset.metrics_dir")

    image_files = [p for p in images_dir.rglob("*") if p.is_file()]
    real_image_files = [p for p in image_files if not p.is_symlink()]
    placeholder_image_files = [p for p in image_files if looks_like_placeholder_path(p.name)]
    symlink_image_files = [p for p in image_files if p.is_symlink()]
    gate.add(
        len(real_image_files) > 0,
        f"{stage}.evalset_dataset.real_image_files",
        f"images/ contains {len(real_image_files)} non-symlink files"
        if real_image_files else
        "images/ has no real non-symlink files",
        images_dir,
        files=len(real_image_files),
    )
    gate.add(
        not placeholder_image_files,
        f"{stage}.evalset_dataset.no_placeholder_images",
        "no placeholder-named files under images/"
        if not placeholder_image_files else
        f"found placeholder-named files under images/: {len(placeholder_image_files)}",
        placeholder_image_files[0] if placeholder_image_files else images_dir,
    )
    gate.add(
        not symlink_image_files,
        f"{stage}.evalset_dataset.no_image_symlinks",
        "no symlink files under images/"
        if not symlink_image_files else
        f"found symlink files under images/: {len(symlink_image_files)}",
        symlink_image_files[0] if symlink_image_files else images_dir,
    )

    test_jsonl = data_dir / "test.jsonl"
    check_model_visible_jsonl(gate, test_jsonl, f"{stage}.evalset_dataset.test_jsonl")
    check_answers_jsonl(gate, ground_truth_dir / "answers.jsonl", f"{stage}.evalset_dataset.answers")

    data_jsonl_paths = sorted(p for p in data_dir.rglob("*.jsonl") if p.is_file())
    checked_records = 0
    records_with_media = 0
    total_media_refs = 0
    bad_url_refs: list[tuple[Path, int, str]] = []
    bad_relative_format_refs: list[tuple[Path, int, str]] = []
    bad_placeholder_refs: list[tuple[Path, int, str]] = []
    missing_local_refs: list[tuple[Path, int, str]] = []
    symlink_target_refs: list[tuple[Path, int, str]] = []
    outside_evalset_refs: list[tuple[Path, int, str]] = []
    unique_media_refs: set[str] = set()
    for jsonl_path in data_jsonl_paths:
        for line_no, rec in iter_jsonl_records(jsonl_path, limit=500):
            checked_records += 1
            media_paths = record_media_paths(rec)
            if media_paths:
                records_with_media += 1
            total_media_refs += len(media_paths)
            for raw_path in media_paths:
                text = raw_path.strip()
                if not text:
                    continue
                if text.startswith(("http://", "https://", "file://", "data:")):
                    bad_url_refs.append((jsonl_path, line_no, text))
                    continue
                if not is_evalset_relative_image_path(text):
                    bad_relative_format_refs.append((jsonl_path, line_no, text))
                    continue
                if looks_like_placeholder_path(text):
                    bad_placeholder_refs.append((jsonl_path, line_no, text))
                    continue
                resolved = resolve_evalset_media_path(evalset_root, text)
                if resolved is None or not resolved.exists() or not resolved.is_file():
                    missing_local_refs.append((jsonl_path, line_no, text))
                    continue
                try:
                    resolved.relative_to(evalset_root)
                except ValueError:
                    outside_evalset_refs.append((jsonl_path, line_no, text))
                    continue
                if resolved.is_symlink():
                    symlink_target_refs.append((jsonl_path, line_no, text))
                    continue
                unique_media_refs.add(str(resolved))
            if checked_records >= 1000:
                break
        if checked_records >= 1000:
            break

    gate.add(
        not bad_url_refs,
        f"{stage}.evalset_dataset.no_media_links",
        "no URL/data/file link media refs in data/*.jsonl"
        if not bad_url_refs else
        f"found forbidden linked media refs in data/*.jsonl: {len(bad_url_refs)}",
        bad_url_refs[0][0] if bad_url_refs else data_dir,
        line=bad_url_refs[0][1] if bad_url_refs else None,
        sample=bad_url_refs[0][2] if bad_url_refs else None,
    )
    gate.add(
        not bad_relative_format_refs,
        f"{stage}.evalset_dataset.media_refs_relative_format",
        "all sampled media refs use ./images/... relative-path format"
        if not bad_relative_format_refs else
        f"found non-./images/... media refs in data/*.jsonl: {len(bad_relative_format_refs)}",
        bad_relative_format_refs[0][0] if bad_relative_format_refs else data_dir,
        line=bad_relative_format_refs[0][1] if bad_relative_format_refs else None,
        sample=bad_relative_format_refs[0][2] if bad_relative_format_refs else None,
    )
    gate.add(
        not bad_placeholder_refs,
        f"{stage}.evalset_dataset.no_placeholder_media_refs",
        "no placeholder media refs in data/*.jsonl"
        if not bad_placeholder_refs else
        f"found placeholder media refs in data/*.jsonl: {len(bad_placeholder_refs)}",
        bad_placeholder_refs[0][0] if bad_placeholder_refs else data_dir,
        line=bad_placeholder_refs[0][1] if bad_placeholder_refs else None,
        sample=bad_placeholder_refs[0][2] if bad_placeholder_refs else None,
    )
    gate.add(
        not missing_local_refs,
        f"{stage}.evalset_dataset.media_refs_resolve",
        "all sampled media refs resolve to local files"
        if not missing_local_refs else
        f"found unresolved local media refs in data/*.jsonl: {len(missing_local_refs)}",
        missing_local_refs[0][0] if missing_local_refs else data_dir,
        line=missing_local_refs[0][1] if missing_local_refs else None,
        sample=missing_local_refs[0][2] if missing_local_refs else None,
    )
    gate.add(
        not outside_evalset_refs,
        f"{stage}.evalset_dataset.media_refs_inside_evalset",
        "sampled media refs point inside EVALSET_DATASET"
        if not outside_evalset_refs else
        f"found media refs outside EVALSET_DATASET: {len(outside_evalset_refs)}",
        outside_evalset_refs[0][0] if outside_evalset_refs else data_dir,
        line=outside_evalset_refs[0][1] if outside_evalset_refs else None,
        sample=outside_evalset_refs[0][2] if outside_evalset_refs else None,
    )
    gate.add(
        not symlink_target_refs,
        f"{stage}.evalset_dataset.no_symlink_media_targets",
        "sampled media refs point to real local files instead of symlinks"
        if not symlink_target_refs else
        f"found media refs pointing to symlink files: {len(symlink_target_refs)}",
        symlink_target_refs[0][0] if symlink_target_refs else data_dir,
        line=symlink_target_refs[0][1] if symlink_target_refs else None,
        sample=symlink_target_refs[0][2] if symlink_target_refs else None,
    )
    gate.add(
        records_with_media > 0,
        f"{stage}.evalset_dataset.records_with_media",
        f"sampled media-bearing records: {records_with_media}" if records_with_media else "no sampled records carry media refs",
        data_dir,
        records=records_with_media,
        checked_records=checked_records,
    )
    gate.add(
        total_media_refs >= records_with_media,
        f"{stage}.evalset_dataset.media_ref_volume",
        f"sampled media refs: {total_media_refs} across {records_with_media} records"
        if total_media_refs >= records_with_media else
        "sampled media refs are fewer than media-bearing records",
        data_dir,
        total_media_refs=total_media_refs,
        records_with_media=records_with_media,
    )
    gate.add(
        len(real_image_files) >= len(unique_media_refs),
        f"{stage}.evalset_dataset.unique_media_covered",
        f"real image files {len(real_image_files)} cover unique referenced images {len(unique_media_refs)}"
        if len(real_image_files) >= len(unique_media_refs) else
        f"real image files {len(real_image_files)} are fewer than unique referenced images {len(unique_media_refs)}",
        images_dir,
        real_image_files=len(real_image_files),
        unique_referenced_images=len(unique_media_refs),
    )
    if records_with_media >= 20 and unique_media_refs:
        max_records_per_unique_image = 20
        scale_ok = records_with_media <= len(unique_media_refs) * max_records_per_unique_image
        gate.add(
            scale_ok,
            f"{stage}.evalset_dataset.image_scale_consistency",
            (
                f"dataset/image scale looks plausible: {records_with_media} media-bearing records, "
                f"{len(unique_media_refs)} unique referenced images"
            )
            if scale_ok else
            (
                f"too few unique images for dataset scale: {records_with_media} media-bearing records but only "
                f"{len(unique_media_refs)} unique referenced images"
            ),
            images_dir,
            records_with_media=records_with_media,
            unique_referenced_images=len(unique_media_refs),
            max_records_per_unique_image=max_records_per_unique_image,
        )

    score_predictions = metrics_dir / "score_predictions.py"
    gate.file_nonempty(score_predictions, f"{stage}.evalset_dataset.score_predictions_py")


def check_common_stage(gate: Gate, stage: str) -> None:
    stage_dir = gate.workspace_root / stage
    gate.exists(stage_dir, f"{stage}.directory", "stage directory")
    if not stage_dir.exists():
        return

    placeholder_paths = [p for p in stage_dir.rglob("*") if "{" in str(p) or "}" in str(p)]
    if placeholder_paths:
        for path in placeholder_paths[:20]:
            gate.fail(f"{stage}.no_placeholder_paths", "literal brace placeholder path found", path)
        if len(placeholder_paths) > 20:
            gate.fail(f"{stage}.no_placeholder_paths", f"{len(placeholder_paths) - 20} more placeholder paths found")
    else:
        gate.pass_(f"{stage}.no_placeholder_paths", "no literal brace placeholder paths", stage_dir)

    blocked = [p for p in stage_dir.rglob("BLOCKED.*") if p.is_file()]
    if blocked:
        for path in blocked[:20]:
            gate.fail(f"{stage}.no_blocked_markers", "BLOCKED marker means stage is not complete", path)
    else:
        gate.pass_(f"{stage}.no_blocked_markers", "no BLOCKED markers", stage_dir)

    for node_id in STAGE_NODES[stage]:
        node_dir = stage_dir / "nodes" / node_id
        if not gate.exists(node_dir, f"{stage}.{node_id}.node_dir", "node directory"):
            continue
        gate.file_nonempty(node_dir / "USED_INPUTS.json", f"{stage}.{node_id}.USED_INPUTS")
        done = gate.json_file(node_dir / "DONE.json", f"{stage}.{node_id}.DONE")
        if isinstance(done, dict):
            status = str(done.get("status", "")).strip().upper()
            gate.add(
                status in {"PASS", "COMPLETED", "DONE", "SUCCESS"},
                f"{stage}.{node_id}.DONE.status",
                f"DONE status is {status!r}",
                node_dir / "DONE.json",
            )
        gate.file_nonempty(node_dir / "NODE_REPORT.md", f"{stage}.{node_id}.NODE_REPORT")


def check_stage1(gate: Gate) -> None:
    check_common_stage(gate, "stage1")
    stage_dir = gate.workspace_root / "stage1"
    artifacts = stage_dir / "artifacts"
    if not artifacts.exists():
        gate.fail("stage1.artifacts", "missing artifacts directory", artifacts)
        return

    for rel_path in [
        "data_01_user_idea/data_01.json",
        "data_05_source_capability_descriptions/data_05.json",
        "data_06_semisupervised_capability_signals/data_06.json",
        "data_08_preprocessed_capability_pool/data_08.json",
        "data_09_benchmark_data/data_09.json",
    ]:
        gate.file_nonempty(artifacts / rel_path, f"stage1.root_input.{rel_path}")

    data13 = stage_dir / "nodes" / "execution-plan-generation" / "artifacts" / "data_13_execution_plan"
    gate.file_nonempty(data13 / "execution_plan.yaml", "stage1.data13.execution_plan")
    gate.file_nonempty(data13 / "stage2_handoff.yaml", "stage1.data13.stage2_handoff")
    gate.file_nonempty(data13 / "stage3_handoff.yaml", "stage1.data13.stage3_handoff")
    gate.file_nonempty(data13 / "stage4_handoff.yaml", "stage1.data13.stage4_handoff")
    gate.file_nonempty(data13 / "stage5_handoff.yaml", "stage1.data13.stage5_handoff")


def check_stage2(gate: Gate) -> None:
    check_common_stage(gate, "stage2")
    artifacts = gate.workspace_root / "stage2" / "artifacts"
    if not artifacts.exists():
        gate.fail("stage2.artifacts", "missing artifacts directory", artifacts)
        return

    gate.dir_nonempty_files(artifacts / "data_14_real_image_collection_bundle", "stage2.data14.nonempty")
    gate.dir_nonempty_files(artifacts / "data_15_existing_benchmark_collection_bundle", "stage2.data15.nonempty")
    sim_bundle = artifacts / "data_16_simulator_collection_bundle"
    if not sim_bundle.exists():
        sim_bundle = artifacts / "data_16_simulated_scene_bundle"
    gate.dir_nonempty_files(sim_bundle, "stage2.data16.nonempty")

    image_file_count = sum(
        1
        for path in artifacts.rglob("*")
        if path.is_file() and path.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}
    )
    valid_manifest_images = count_stage2_valid_manifest_images(artifacts)
    min_total_images, min_source = stage2_min_total_images(gate.workspace_root)
    gate.add(
        image_file_count > 0,
        "stage2.real_media_files",
        f"stage2 media image files: {image_file_count}" if image_file_count else "no real media image files found",
        artifacts,
        count=image_file_count,
    )
    gate.add(
        valid_manifest_images >= min_total_images,
        "stage2.total_valid_images_minimum",
        f"stage2 valid manifest images: {valid_manifest_images}/{min_total_images} ({min_source})"
        if valid_manifest_images >= min_total_images
        else f"stage2 valid manifest images below required minimum: {valid_manifest_images}/{min_total_images} ({min_source})",
        artifacts,
        count=valid_manifest_images,
        minimum_total_images=min_total_images,
        minimum_source=min_source,
    )


def check_stage3(gate: Gate) -> None:
    check_common_stage(gate, "stage3")
    stage_dir = gate.workspace_root / "stage3"
    artifacts_dir = stage_dir / "artifacts"
    if not artifacts_dir.exists():
        return

    gate.file_nonempty(
        artifacts_dir / "stage3_execution_plan" / "stage3_execution_plan.yaml",
        "stage3.execution_plan",
    )

    for artifact_id in STAGE3_ARTIFACTS:
        gate.dir_nonempty_files(artifacts_dir / artifact_id, f"stage3.{artifact_id}.nonempty")

    data17 = artifacts_dir / "data_17_annotated_real_image_bundle"
    if data17.exists():
        gate.jsonl_nonempty(data17 / "real_image_manifest.jsonl", "stage3.data17.real_image_manifest")
        gate.dir_nonempty_files(data17 / "media", "stage3.data17.media")
        gate.file_nonempty(data17 / "evidence_manifest.json", "stage3.data17.evidence_manifest")
        gate.add(
            has_nonempty_named_file(data17, ["run_manifest.json"]),
            "stage3.data17.annotation_run_manifest",
            "default annotation run_manifest evidence exists"
            if has_nonempty_named_file(data17, ["run_manifest.json"])
            else "missing annotation_or_gt/run_manifest.json evidence",
            data17,
        )
        gate.add(
            has_nonempty_named_file(data17, ["annotation_records.jsonl"]),
            "stage3.data17.annotation_records",
            "annotation_records.jsonl exists"
            if has_nonempty_named_file(data17, ["annotation_records.jsonl"])
            else "missing annotation_records.jsonl",
            data17,
        )
        gate.add(
            has_nonempty_named_file(data17, ["default_annotation_manifest.jsonl"]),
            "stage3.data17.default_annotation_manifest",
            "default_annotation_manifest.jsonl exists"
            if has_nonempty_named_file(data17, ["default_annotation_manifest.jsonl"])
            else "missing default_annotation_manifest.jsonl",
            data17,
        )
        result_count = count_result_json(data17)
        gate.add(
            result_count > 0,
            "stage3.data17.default_annotation_results",
            f"default_annotation_output result.json count: {result_count}",
            data17,
            count=result_count,
        )

    data18 = artifacts_dir / "data_18_annotated_existing_benchmark_bundle"
    if data18.exists():
        gate.file_nonempty(data18 / "evidence_manifest.json", "stage3.data18.evidence_manifest")
        label_files = [
            "official_labels.jsonl",
            "added_annotation_records.jsonl",
            "annotation_records.jsonl",
        ]
        has_labels = has_nonempty_named_file(data18, label_files)
        gate.add(
            has_labels,
            "stage3.data18.gt_or_annotation_records",
            "official labels or added annotation records exist" if has_labels else "missing official label or added annotation records",
            data18,
        )
        target_records = nonempty_jsonl_records(data18.rglob("new_annotation_targets.jsonl"))
        if target_records > 0:
            review_records = nonempty_jsonl_records(data18.rglob("review_queue.jsonl"))
            result_count = count_result_json(data18)
            gate.add(
                result_count > 0 or review_records >= target_records,
                "stage3.data18.new_annotation_coverage",
                (
                    f"new targets covered by result.json ({result_count}) or review queue ({review_records}/{target_records})"
                    if result_count > 0 or review_records >= target_records
                    else f"new annotation targets are uncovered: result.json={result_count}, review_queue={review_records}, targets={target_records}"
                ),
                data18,
                targets=target_records,
                result_json=result_count,
                review_records=review_records,
            )

    data19 = artifacts_dir / "data_19_annotated_simulator_bundle"
    if data19.exists():
        gate.file_nonempty(data19 / "evidence_manifest.json", "stage3.data19.evidence_manifest")
        sim_files = [data19 / "privileged_gt.jsonl", data19 / "SIMULATOR_DATA.jsonl"]
        record_counts = [gate.jsonl_nonempty(path, f"stage3.data19.{path.name}") for path in sim_files if path.exists()]
        gate.add(
            any(count > 0 for count in record_counts),
            "stage3.data19.privileged_gt",
            "non-empty simulator privileged GT JSONL exists"
            if any(count > 0 for count in record_counts)
            else "missing non-empty privileged_gt.jsonl or SIMULATOR_DATA.jsonl",
            data19,
        )

    scan_stage3_for_forbidden_status(gate, stage_dir)


def scan_stage3_for_forbidden_status(gate: Gate, stage_dir: Path) -> None:
    targets = []
    for pattern in ("DONE.json", "NODE_REPORT.md", "_stage_report.md", "evidence_manifest.json"):
        targets.extend(stage_dir.rglob(pattern))
    hits: list[tuple[Path, str]] = []
    for path in targets:
        text = read_text_limited(path).lower()
        for phrase in FORBIDDEN_STAGE3_TEXT:
            if phrase in text:
                hits.append((path, phrase))
    if hits:
        for path, phrase in hits[:20]:
            gate.fail("stage3.no_deferred_or_ready_only_status", f"forbidden completion placeholder/status text found: {phrase}", path)
    else:
        gate.pass_("stage3.no_deferred_or_ready_only_status", "no forbidden deferred/ready-only status text", stage_dir)


def check_required_files(gate: Gate, root: Path, files: list[str], check_prefix: str) -> None:
    for rel_path in files:
        gate.file_nonempty(root / rel_path, f"{check_prefix}.{rel_path}")


def check_universal_audit_format(gate: Gate, audit_root: Path, check_prefix: str) -> None:
    items_path = audit_root / "benchmark_items.jsonl"
    registry_path = audit_root / "template_registry.json"
    report_path = audit_root / "generation_report.json"
    asset_dir = audit_root / "benchmark_assets"
    count = gate.jsonl_nonempty(items_path, f"{check_prefix}.benchmark_items")
    gate.json_file(registry_path, f"{check_prefix}.template_registry")
    gate.json_file(report_path, f"{check_prefix}.generation_report")
    gate.dir_nonempty_files(asset_dir, f"{check_prefix}.benchmark_assets")
    if count == 0:
        return

    missing_core: list[tuple[int, list[str]]] = []
    bad_asset_paths: list[tuple[int, list[str]]] = []
    for line_no, record in iter_jsonl_records(items_path, limit=5000):
        missing = [
            key for key in ("id", "template_id", "capability_id", "question_type", "answer", "provenance", "quality_flags")
            if record.get(key) in (None, "", [], {})
        ]
        if missing:
            missing_core.append((line_no, missing))
        media = record_media_paths(record)
        bad_paths = [path for path in media if not str(path).startswith("benchmark_assets/")]
        if not media or bad_paths:
            bad_asset_paths.append((line_no, bad_paths or media))

    gate.add(
        not missing_core,
        f"{check_prefix}.core_fields",
        "audit format rows contain answer, provenance and quality_flags"
        if not missing_core else
        f"audit format rows missing core fields: {len(missing_core)}",
        items_path,
        line=missing_core[0][0] if missing_core else None,
        keys=missing_core[0][1] if missing_core else None,
    )
    gate.add(
        not bad_asset_paths,
        f"{check_prefix}.asset_paths",
        "audit format media paths use benchmark_assets/"
        if not bad_asset_paths else
        f"audit format rows have missing or non-benchmark_assets media paths: {len(bad_asset_paths)}",
        items_path,
        line=bad_asset_paths[0][0] if bad_asset_paths else None,
        paths=bad_asset_paths[0][1] if bad_asset_paths else None,
    )


def check_stage4(gate: Gate) -> None:
    check_common_stage(gate, "stage4")
    artifacts = gate.workspace_root / "stage4" / "artifacts"
    if not artifacts.exists():
        return

    data20 = artifacts / "data_20_template_metric_code_bundle"
    data21 = artifacts / "data_21_grey_validation_report"
    data22 = artifacts / "data_22_full_benchmark_dataset"
    for artifact in (data20, data21, data22):
        gate.dir_nonempty_files(artifact, f"stage4.{artifact.name}.nonempty")

    if data20.exists():
        check_required_files(gate, data20, STAGE4_DATA20_REQUIRED, "stage4.data20.required")
        for rel_path in [
            "source_inventory.jsonl",
            "evidence_index.jsonl",
            "image_processing/image_manifest.jsonl",
            "template_manifest.jsonl",
            "metric_manifest.jsonl",
            "self_test/dry_run_items.jsonl",
        ]:
            gate.jsonl_nonempty(data20 / rel_path, f"stage4.data20.jsonl.{rel_path}")
        gate.json_file(data20 / "code_manifest.json", "stage4.data20.code_manifest")
        gate.json_file(data20 / "difficulty_mix_contract.json", "stage4.data20.difficulty_mix_contract")
        gate.json_file(data20 / "self_test/difficulty_mix_report.json", "stage4.data20.difficulty_mix_report")
        gate.json_file(data20 / "self_test/perfect_score_report.json", "stage4.data20.perfect_score_report")
        gate.json_file(data20 / "self_test/negative_score_report.json", "stage4.data20.negative_score_report")
        gate.csv_nonempty(data20 / "traceability.csv", "stage4.data20.traceability")
        check_difficulty_mix(gate, data20 / "self_test/dry_run_items.jsonl", "stage4.data20.dry_run_items")

    if data21.exists():
        check_required_files(gate, data21, STAGE4_DATA21_REQUIRED, "stage4.data21.required")
        gate.jsonl_nonempty(data21 / "item_level_findings.jsonl", "stage4.data21.item_level_findings")
        gate.jsonl_nonempty(data21 / "per_template_batch" / "generated_items.jsonl", "stage4.data21.per_template_batch.generated_items")
        gate.jsonl_nonempty(data21 / "invalid_item_screening" / "valid_items.jsonl", "stage4.data21.invalid_item_screening.valid_items")
        gate.json_file(data21 / "invalid_item_screening" / "screening_report.json", "stage4.data21.invalid_item_screening.screening_report")
        gate.json_file(data21 / "scorer_smoke" / "perfect_score_report.json", "stage4.data21.scorer_smoke.perfect_score_report")
        gate.json_file(data21 / "scorer_smoke" / "negative_score_report.json", "stage4.data21.scorer_smoke.negative_score_report")
        gate.jsonl_nonempty(data21 / "small_model_eval" / "score_matrix.jsonl", "stage4.data21.small_model_eval.score_matrix")
        cdm_summary = gate.json_file(data21 / "cdm_irt" / "cdm_irt_summary.json", "stage4.data21.cdm_irt.summary")
        if isinstance(cdm_summary, dict):
            status = str(cdm_summary.get("status", "")).upper()
            gate.add(
                status in {"PASS", "LIMITED_PASS"},
                "stage4.data21.cdm_irt.status",
                f"cdm/irt status is {status!r}",
                data21 / "cdm_irt" / "cdm_irt_summary.json",
            )
        gate.json_file(data21 / "difficulty_mix_report.json", "stage4.data21.difficulty_mix_report")
        check_difficulty_mix(gate, data21 / "invalid_item_screening" / "valid_items.jsonl", "stage4.data21.valid_items")

    if data22.exists():
        check_required_files(gate, data22, STAGE4_DATA22_REQUIRED, "stage4.data22.required")
        check_universal_audit_format(gate, data22 / "audit_format", "stage4.data22.audit_format")
        gate.jsonl_nonempty(data22 / "dataset.jsonl", "stage4.data22.dataset")
        check_difficulty_mix(gate, data22 / "dataset.jsonl", "stage4.data22.dataset")
        check_model_visible_jsonl(gate, data22 / "data" / "test.jsonl", "stage4.data22.test_jsonl")
        check_answers_jsonl(gate, data22 / "ground_truth" / "answers.jsonl", "stage4.data22.answers")
        gate.jsonl_nonempty(data22 / "ground_truth" / "audit_items_with_answers.jsonl", "stage4.data22.audit_items_with_answers")
        gate.json_file(data22 / "manifest.json", "stage4.data22.manifest")
        gate.json_file(data22 / "checksums.json", "stage4.data22.checksums")
        for dirname in ("audit_format/benchmark_assets", "media", "images", "ground_truth", "metrics"):
            gate.dir_nonempty_files(data22 / dirname, f"stage4.data22.{dirname}")
        old_names = [data22 / "sample_images", data22 / "gt_bundle"]
        if any(path.exists() for path in old_names) and not (data22 / "media").exists() and not (data22 / "ground_truth").exists():
            gate.fail(
                "stage4.data22.current_contract_names",
                "old output names sample_images/gt_bundle exist without current media/ground_truth contract directories",
                data22,
            )
        else:
            gate.pass_("stage4.data22.current_contract_names", "current full-synthesis directory names are used", data22)

    check_workspace_evalset_dataset(gate, "stage4")
    check_full_synthesis_logs(gate)


def check_full_synthesis_logs(gate: Gate) -> None:
    log_dir = gate.workspace_root / "stage4" / "nodes" / "full-synthesis" / "run_logs"
    if not log_dir.exists():
        gate.fail("stage4.full_synthesis.tmux_logs", "missing full-synthesis run_logs directory", log_dir)
        return
    monitoring = [p for p in log_dir.rglob("*.monitoring.jsonl") if p.is_file() and p.stat().st_size > 0]
    gate.add(
        bool(monitoring),
        "stage4.full_synthesis.monitoring_jsonl",
        f"monitoring jsonl files: {len(monitoring)}" if monitoring else "missing .monitoring.jsonl evidence",
        log_dir,
        count=len(monitoring),
    )
    logs = [p for p in log_dir.rglob("*.log") if p.is_file() and p.stat().st_size > 0]
    exit_ok = any("EXIT_CODE:0" in read_text_limited(path) for path in logs)
    gate.add(
        exit_ok,
        "stage4.full_synthesis.exit_code",
        "found EXIT_CODE:0 in full-synthesis logs" if exit_ok else "missing EXIT_CODE:0 in full-synthesis logs",
        log_dir,
        log_count=len(logs),
    )


def check_stage5(gate: Gate) -> None:
    check_common_stage(gate, "stage5")
    data23 = gate.workspace_root / "stage5" / "artifacts" / "data_23_evaluation_report"
    gate.dir_nonempty_files(data23, "stage5.data23.nonempty")
    if data23.exists():
        check_required_files(gate, data23, STAGE5_DATA23_REQUIRED, "stage5.data23.required")
        metrics = gate.json_file(data23 / "metrics.json", "stage5.data23.metrics")
        if isinstance(metrics, dict):
            gate.add(bool(metrics), "stage5.data23.metrics.nonempty_object", "metrics object is non-empty", data23 / "metrics.json")
        gate.jsonl_nonempty(data23 / "prediction_audit.jsonl", "stage5.data23.prediction_audit")
        gate.jsonl_nonempty(data23 / "error_taxonomy.jsonl", "stage5.data23.error_taxonomy")

    node_dir = gate.workspace_root / "stage5" / "nodes" / "full-evaluation"
    provenance_text = "\n".join(
        read_text_limited(path)
        for path in (node_dir / "USED_INPUTS.json", node_dir / "NODE_REPORT.md")
        if path.exists()
    ).lower()
    has_provenance = any(word in provenance_text for word in ["prediction", "model", "endpoint", "api", "预测", "模型"])
    gate.add(
        has_provenance,
        "stage5.full_evaluation.prediction_provenance",
        "model or prediction provenance is recorded"
        if has_provenance
        else "missing real model/prediction provenance in USED_INPUTS or NODE_REPORT",
        node_dir,
    )
    check_workspace_evalset_dataset(gate, "stage5")


def normalize_stage_name(value: str) -> str:
    value = value.strip().lower()
    if value in {"s1", "1", "stage1"}:
        return "stage1"
    if value in {"s2", "2", "stage2"}:
        return "stage2"
    if value in {"s3", "3", "stage3"}:
        return "stage3"
    if value in {"s4", "4", "stage4"}:
        return "stage4"
    if value in {"s5", "5", "stage5"}:
        return "stage5"
    return value


def check_pipeline(gate: Gate) -> None:
    placeholder_paths = [p for p in gate.workspace_root.rglob("*") if "{" in str(p) or "}" in str(p)]
    if placeholder_paths:
        for path in placeholder_paths[:20]:
            gate.fail("pipeline.no_placeholder_paths", "literal brace placeholder path found", path)
    else:
        gate.pass_("pipeline.no_placeholder_paths", "no literal brace placeholder paths", gate.workspace_root)

    state_path = gate.workspace_root / "pipeline_state.json"
    state = gate.json_file(state_path, "pipeline.pipeline_state")
    if isinstance(state, dict):
        completed = {
            normalize_stage_name(str(item))
            for item in state.get("stages_completed", [])
            if isinstance(item, str)
        }
        missing = [stage for stage in ["stage1", "stage2", "stage3", "stage4", "stage5"] if stage not in completed]
        gate.add(
            not missing,
            "pipeline.stages_completed",
            "pipeline_state records stage1-stage5 completion"
            if not missing
            else f"pipeline_state missing completed stages: {', '.join(missing)}",
            state_path,
            completed=sorted(completed),
        )

    for stage in ("stage1", "stage2", "stage3", "stage4", "stage5"):
        done_path = gate.workspace_root / stage / "_STAGE_DONE.json"
        gate.file_nonempty(done_path, f"pipeline.{stage}._STAGE_DONE")
        subgate = Gate(gate.workspace_root, stage)
        VALIDATORS[stage](subgate)
        report = subgate.report()
        gate.add(
            report["status"] == "PASS",
            f"pipeline.{stage}_gate",
            f"{stage} validator {report['status']} ({report['summary']['failed']} failures)",
            gate.workspace_root / stage,
            failures=report["summary"]["failed"],
        )
        for row in report["checks"]:
            if row["status"] == "FAIL":
                copied = dict(row)
                copied["check"] = f"pipeline.{copied['check']}"
                gate.checks.append(copied)

    pipeline_done_path = gate.workspace_root / "PIPELINE_DONE.json"
    pipeline_done = gate.json_file(pipeline_done_path, "pipeline.pipeline_done")
    if isinstance(pipeline_done, dict):
        completed = {
            normalize_stage_name(str(item))
            for item in pipeline_done.get("completed_stages", [])
            if isinstance(item, str)
        }
        missing = [stage for stage in ["stage1", "stage2", "stage3", "stage4", "stage5"] if stage not in completed]
        status = str(pipeline_done.get("pipeline_status", pipeline_done.get("status", ""))).strip().upper()
        gate.add(
            status in {"COMPLETE", "COMPLETED", "PASS", "DONE", "SUCCESS"} and not missing,
            "pipeline.pipeline_done_consistency",
            "PIPELINE_DONE records complete stage1-stage5 run"
            if status in {"COMPLETE", "COMPLETED", "PASS", "DONE", "SUCCESS"} and not missing
            else f"PIPELINE_DONE incomplete or inconsistent: status={status!r}, missing={', '.join(missing) if missing else 'none'}",
            pipeline_done_path,
            completed=sorted(completed),
        )


VALIDATORS = {
    "stage1": check_stage1,
    "stage2": check_stage2,
    "stage3": check_stage3,
    "stage4": check_stage4,
    "stage5": check_stage5,
    "pipeline": check_pipeline,
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate BenchClaw stage completion gates.")
    parser.add_argument("--workspace-root", required=True, help="Path to the BenchClaw workspace root.")
    parser.add_argument("--stage", required=True, choices=sorted(VALIDATORS), help="Stage gate to validate.")
    parser.add_argument("--report", help="Optional path to write the JSON validation report.")
    parser.add_argument("--json", action="store_true", help="Print full JSON report to stdout.")
    args = parser.parse_args(argv)

    workspace_root = Path(args.workspace_root).resolve()
    gate = Gate(workspace_root, args.stage)
    check_workspace_root_contract(gate)
    if not workspace_root.exists():
        gate.fail("workspace.exists", "workspace root does not exist", workspace_root)
    else:
        VALIDATORS[args.stage](gate)

    report = gate.report()
    if args.report:
        report_path = Path(args.report)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        with report_path.open("w", encoding="utf-8") as fh:
            json.dump(report, fh, indent=2, ensure_ascii=False)
            fh.write("\n")

    if args.json:
        json.dump(report, sys.stdout, indent=2, ensure_ascii=False)
        sys.stdout.write("\n")
    else:
        print(f"{report['stage']} gate: {report['status']} ({report['summary']['failed']} failures)")
        for row in report["checks"]:
            if row["status"] == "FAIL":
                path = f" [{row['path']}]" if "path" in row else ""
                print(f"- {row['check']}: {row['message']}{path}")

    return 1 if report["status"] == "FAIL" else 0


if __name__ == "__main__":
    raise SystemExit(main())
