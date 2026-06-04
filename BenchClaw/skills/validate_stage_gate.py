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
    "template_manifest.jsonl",
    "metric_manifest.jsonl",
    "code_manifest.json",
    "synthesis_plan.yaml",
    "traceability.csv",
    "scripts/generate_items.py",
    "scripts/score_predictions.py",
    "scripts/validate_bundle.py",
    "contracts/benchmark_item.schema.json",
    "tests/smoke_test.py",
    "self_test/dry_run_items.jsonl",
    "self_test/perfect_score_report.json",
    "self_test/negative_score_report.json",
    "self_test/py_compile.log",
    "self_test/self_test_report.md",
]

STAGE4_DATA21_REQUIRED = [
    "report.md",
    "template_status.csv",
    "item_level_findings.jsonl",
]

STAGE4_DATA22_REQUIRED = [
    "dataset.jsonl",
    "manifest.json",
    "cards/benchmark_card.md",
    "checksums.json",
]

STAGE5_DATA23_REQUIRED = [
    "evaluation_report.md",
    "metrics.json",
    "prediction_audit.jsonl",
    "error_taxonomy.jsonl",
]

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
            status = str(done.get("status", ""))
            gate.add(status == "PASS", f"{stage}.{node_id}.DONE.status", f"DONE status is {status!r}", node_dir / "DONE.json")
        gate.file_nonempty(node_dir / "NODE_REPORT.md", f"{stage}.{node_id}.NODE_REPORT")


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
            "template_manifest.jsonl",
            "metric_manifest.jsonl",
            "self_test/dry_run_items.jsonl",
        ]:
            gate.jsonl_nonempty(data20 / rel_path, f"stage4.data20.jsonl.{rel_path}")
        gate.json_file(data20 / "code_manifest.json", "stage4.data20.code_manifest")
        gate.json_file(data20 / "self_test/perfect_score_report.json", "stage4.data20.perfect_score_report")
        gate.json_file(data20 / "self_test/negative_score_report.json", "stage4.data20.negative_score_report")
        gate.csv_nonempty(data20 / "traceability.csv", "stage4.data20.traceability")

    if data21.exists():
        check_required_files(gate, data21, STAGE4_DATA21_REQUIRED, "stage4.data21.required")
        gate.jsonl_nonempty(data21 / "item_level_findings.jsonl", "stage4.data21.item_level_findings")

    if data22.exists():
        check_required_files(gate, data22, STAGE4_DATA22_REQUIRED, "stage4.data22.required")
        gate.jsonl_nonempty(data22 / "dataset.jsonl", "stage4.data22.dataset")
        gate.json_file(data22 / "manifest.json", "stage4.data22.manifest")
        gate.json_file(data22 / "checksums.json", "stage4.data22.checksums")
        for dirname in ("media", "ground_truth", "metrics"):
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

    for stage in ("stage3", "stage4", "stage5"):
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


VALIDATORS = {
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
