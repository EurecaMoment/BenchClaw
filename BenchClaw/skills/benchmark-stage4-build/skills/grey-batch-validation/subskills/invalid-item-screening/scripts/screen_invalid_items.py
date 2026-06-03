#!/usr/bin/env python3
"""Screen invalid grey-batch items before model evaluation."""

from __future__ import annotations

import argparse
import csv
import json
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple


IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".gif", ".tif", ".tiff"}


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, 1):
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            if not isinstance(obj, dict):
                raise ValueError(f"{path}:{line_no}: expected JSON object")
            obj.setdefault("_line_no", line_no)
            rows.append(obj)
    return rows


def write_jsonl(path: Path, rows: Iterable[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            row = {k: v for k, v in row.items() if k != "_line_no"}
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=False) + "\n")


def write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: Sequence[Dict[str, Any]], fields: Sequence[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def item_id(item: Dict[str, Any]) -> str:
    return str(item.get("eval_id") or item.get("item_id") or item.get("id") or f"line_{item.get('_line_no', 'unknown')}")


def template_id(item: Dict[str, Any]) -> str:
    return str(item.get("template_id") or "UNKNOWN")


def answer_type(item: Dict[str, Any]) -> str:
    return str(item.get("answer_type") or item.get("answer_format") or item.get("question_format") or "").lower()


def gold_answer(item: Dict[str, Any]) -> Any:
    if "answer" in item:
        return item.get("answer")
    if "gold_answer" in item:
        return item.get("gold_answer")
    return None


def normalize_paths(value: Any) -> List[str]:
    if value is None or value == "":
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        out: List[str] = []
        for item in value:
            out.extend(normalize_paths(item))
        return out
    if isinstance(value, dict):
        out: List[str] = []
        for key in ("path", "workspace_path", "image", "uri"):
            if key in value:
                out.extend(normalize_paths(value[key]))
        return out
    return []


def media_paths(item: Dict[str, Any]) -> List[str]:
    paths: List[str] = []
    for key in ("image", "media", "images", "auxiliary_images", "image_refs", "evidence_ref"):
        paths.extend(normalize_paths(item.get(key)))
    meta = item.get("metadata")
    if isinstance(meta, dict):
        paths.extend(normalize_paths(meta.get("image")))
        paths.extend(normalize_paths(meta.get("auxiliary_images")))
    seen = set()
    out: List[str] = []
    for path in paths:
        path = str(path).strip()
        if path and path not in seen:
            out.append(path)
            seen.add(path)
    return out


def resolve_media(path_text: str, workspace_root: Optional[Path], item_file_dir: Path) -> Path:
    path = Path(path_text).expanduser()
    if path.is_absolute():
        return path
    if workspace_root:
        candidate = workspace_root / path
        if candidate.exists():
            return candidate
    return item_file_dir / path


def image_decode_ok(path: Path) -> Tuple[bool, str]:
    if path.suffix.lower() not in IMAGE_EXTS:
        return True, "not_image"
    try:
        head = path.read_bytes()[:16]
    except Exception as exc:
        return False, f"read_error:{exc!r}"
    kind = image_kind_from_header(head)
    if kind:
        return True, kind
    try:
        from PIL import Image  # type: ignore

        with Image.open(path) as image:
            image.verify()
        return True, "pil_ok"
    except Exception as exc:
        return False, f"decode_failed:{exc!r}"


def image_kind_from_header(head: bytes) -> str:
    if head.startswith(b"\xff\xd8\xff"):
        return "jpeg"
    if head.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if head.startswith((b"GIF87a", b"GIF89a")):
        return "gif"
    if head.startswith(b"BM"):
        return "bmp"
    if head.startswith(b"RIFF") and head[8:12] == b"WEBP":
        return "webp"
    if head.startswith((b"II*\x00", b"MM\x00*")):
        return "tiff"
    return ""


def option_values(options: Any) -> List[Any]:
    if isinstance(options, dict):
        return list(options.values())
    if isinstance(options, list):
        return list(options)
    return []


def option_keys(options: Any) -> List[str]:
    if isinstance(options, dict):
        return [str(k) for k in options]
    if isinstance(options, list):
        labels = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        return [labels[i] if i < len(labels) else str(i) for i in range(len(options))]
    return []


def has_duplicate_options(options: Any) -> bool:
    values = [json.dumps(v, ensure_ascii=False, sort_keys=True) for v in option_values(options)]
    return len(values) != len(set(values))


def answer_in_options(answer: Any, options: Any) -> bool:
    if not options:
        return True
    keys = set(k.upper() for k in option_keys(options))
    values = set(str(v).strip().casefold() for v in option_values(options))
    if isinstance(answer, list):
        return all(answer_in_options(x, options) for x in answer)
    text = str(answer).strip()
    return text.upper() in keys or text.casefold() in values


def check_item(item: Dict[str, Any], args: argparse.Namespace, item_file_dir: Path) -> List[Dict[str, Any]]:
    findings: List[Dict[str, Any]] = []
    iid = item_id(item)
    tid = template_id(item)

    def add(issue: str, severity: str, evidence: Any, recommendation: str) -> None:
        findings.append(
            {
                "finding_type": "invalid_item_screening",
                "severity": severity,
                "item_id": iid,
                "template_id": tid,
                "issue": issue,
                "evidence": evidence,
                "recommendation": recommendation,
            }
        )

    if not str(item.get("question") or item.get("question_text") or "").strip():
        add("missing_question", "error", {}, "Regenerate item with a non-empty question.")
    answer = gold_answer(item)
    if answer in (None, "", [], {}):
        add("missing_gold_answer", "error", {}, "Fix answer program or GT linkage before evaluation.")
    if not item.get("template_id"):
        add("missing_template_id", "error", {}, "Attach template_id for traceability and template-level gating.")

    paths = media_paths(item)
    if args.require_media and not paths:
        add("missing_media", "error", {}, "Visual grey-batch items must include workspace media paths.")
    for raw_path in paths:
        path = resolve_media(raw_path, Path(args.workspace_root).expanduser() if args.workspace_root else None, item_file_dir)
        if not path.exists():
            add("media_missing", "error", {"path": raw_path, "resolved": str(path)}, "Copy/link media into workspace before evaluation.")
            continue
        if path.is_file() and path.stat().st_size <= 0:
            add("media_empty", "error", {"path": raw_path, "resolved": str(path)}, "Replace empty media file.")
        if path.is_file():
            ok, note = image_decode_ok(path)
            if not ok:
                add("media_decode_failed", "error", {"path": raw_path, "resolved": str(path), "note": note}, "Regenerate item or replace corrupt image.")

    options = item.get("options")
    at = answer_type(item)
    if options:
        if has_duplicate_options(options):
            add("duplicate_options", "warning", {"options": options}, "Regenerate stronger distractors with unique option texts.")
        if answer not in (None, "", [], {}) and not answer_in_options(answer, options):
            add("answer_not_in_options", "error", {"answer": answer, "options": options}, "Fix option mapping so gold answer is valid.")
    if ("choice" in at or str(item.get("question_format", "")).startswith(("F1", "F2", "F3"))) and not options:
        add("choice_item_missing_options", "error", {"answer_type": at}, "Choice item must include options.")

    if not (item.get("evidence_refs") or item.get("evidence_ref") or item.get("provenance") or item.get("metadata")):
        add("missing_evidence_trace", "warning", {}, "Attach evidence refs and source provenance.")
    if not (item.get("scoring") or item.get("metric_id")):
        add("missing_scoring_contract", "error", {}, "Attach metric_id or scoring contract before model evaluation.")
    return findings


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Screen invalid grey-batch benchmark items.")
    p.add_argument("--items", required=True, help="Input generated item JSONL.")
    p.add_argument("--out-dir", required=True)
    p.add_argument("--workspace-root", default="", help="Workspace root for resolving relative media paths.")
    p.add_argument("--require-media", action=argparse.BooleanOptionalAction, default=True)
    return p.parse_args()


def main() -> int:
    args = parse_args()
    in_path = Path(args.items).expanduser().resolve()
    out_dir = Path(args.out_dir).expanduser().resolve()
    rows = load_jsonl(in_path)

    valid: List[Dict[str, Any]] = []
    invalid: List[Dict[str, Any]] = []
    findings: List[Dict[str, Any]] = []
    by_template = defaultdict(lambda: {"total": 0, "valid": 0, "invalid": 0, "errors": 0, "warnings": 0})

    for item in rows:
        item_findings = check_item(item, args, in_path.parent)
        findings.extend(item_findings)
        tid = template_id(item)
        by_template[tid]["total"] += 1
        by_template[tid]["errors"] += sum(1 for f in item_findings if f["severity"] == "error")
        by_template[tid]["warnings"] += sum(1 for f in item_findings if f["severity"] == "warning")
        if any(f["severity"] == "error" for f in item_findings):
            invalid.append(item)
            by_template[tid]["invalid"] += 1
        else:
            valid.append(item)
            by_template[tid]["valid"] += 1

    template_rows = []
    for tid, stats in sorted(by_template.items()):
        status = "pass" if stats["invalid"] == 0 else ("review" if stats["valid"] > 0 else "fail")
        template_rows.append({"template_id": tid, "status": status, **stats})

    write_jsonl(out_dir / "valid_items.jsonl", valid)
    write_jsonl(out_dir / "invalid_items.jsonl", invalid)
    write_jsonl(out_dir / "item_level_findings.jsonl", findings)
    write_csv(out_dir / "template_status.csv", template_rows, ["template_id", "status", "total", "valid", "invalid", "errors", "warnings"])
    write_json(
        out_dir / "screening_report.json",
        {
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "input": str(in_path),
            "total": len(rows),
            "valid": len(valid),
            "invalid": len(invalid),
            "findings": len(findings),
            "template_status": template_rows,
            "outputs": {
                "valid_items": str(out_dir / "valid_items.jsonl"),
                "invalid_items": str(out_dir / "invalid_items.jsonl"),
                "item_level_findings": str(out_dir / "item_level_findings.jsonl"),
                "template_status": str(out_dir / "template_status.csv"),
            },
        },
    )
    print(json.dumps({"total": len(rows), "valid": len(valid), "invalid": len(invalid), "findings": len(findings)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
