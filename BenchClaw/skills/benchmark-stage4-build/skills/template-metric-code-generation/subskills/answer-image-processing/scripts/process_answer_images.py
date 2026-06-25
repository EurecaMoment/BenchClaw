#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Process and validate model-facing answer images for BenchClaw Stage4.

This script does not decide answers and does not generate benchmark items. It
normalizes readable Stage3 images into bundle-local, leak-safe image assets and
writes a manifest that downstream template/runtime code can consume.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import shutil
from collections import Counter
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

try:
    from PIL import Image, ImageDraw, ImageFont, ImageOps
except Exception:  # pragma: no cover - the report will expose limited mode.
    Image = None  # type: ignore
    ImageDraw = None  # type: ignore
    ImageFont = None  # type: ignore
    ImageOps = None  # type: ignore


IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
FORBIDDEN_FINAL_TERMS = {
    "answer",
    "correct",
    "gt",
    "groundtruth",
    "ground_truth",
    "label",
    "target",
    "positive",
    "negative",
    "true",
    "false",
    "gold",
    "left",
    "right",
    "near",
    "far",
    "success",
    "failure",
}
FORBIDDEN_OVERLAY_TERMS = {
    "correct",
    "answer",
    "target",
    "ground truth",
    "success",
    "failure",
}
SUPPORTED_COMPOSERS = {
    "safe_copy",
    "bbox_label_overlay",
    "point_label_overlay",
    "multi_view_grid",
    "candidate_panel",
}
LABELS = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    if not path.is_file():
        return rows
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                payload = json.loads(line)
                if isinstance(payload, dict):
                    rows.append(payload)
    return rows


read_jsonl = load_jsonl


def write_jsonl(path: Path, rows: Iterable[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=False) + "\n")


def write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def stable_id(text: str, length: int = 10) -> str:
    return hashlib.sha1(text.encode("utf-8", errors="ignore")).hexdigest()[:length]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def is_url(value: str) -> bool:
    lowered = value.lower()
    return lowered.startswith(("http://", "https://", "file://", "data:"))


def safe_text(value: Any) -> str:
    return str(value or "").strip()


def as_list(value: Any) -> List[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def safe_label_list(raw: Any, count: int) -> List[str]:
    labels = [safe_text(x) for x in as_list(raw) if safe_text(x)]
    defaults = LABELS + [f"P{idx}" for idx in range(27, max(27, count + 1))]
    if not labels:
        labels = defaults[:count]
    if len(labels) < count:
        labels.extend(defaults[len(labels):count])
    return labels[:count]


def path_has_forbidden_final_term(path: Path) -> bool:
    lowered = path.name.lower()
    tokens = re.split(r"[^a-z0-9]+", lowered)
    return any(term in tokens or term in lowered for term in FORBIDDEN_FINAL_TERMS)


def overlay_text_safe(texts: Sequence[str]) -> bool:
    joined = " ".join(texts).lower()
    return not any(term in joined for term in FORBIDDEN_OVERLAY_TERMS)


def resolve_path(raw: Any, *, evidence_path: Path, bundle: Path, row: Optional[Dict[str, Any]] = None) -> Optional[Path]:
    text = safe_text(raw)
    if not text or is_url(text):
        return None
    path = Path(text).expanduser()
    roots: List[Path] = []
    if row:
        for key in ("root_dir", "artifact_root", "source_root", "workspace_root"):
            value = row.get(key)
            if value:
                roots.append(Path(str(value)).expanduser())
    roots.extend([bundle, bundle.parent, evidence_path.parent, Path.cwd()])

    candidates = [path] if path.is_absolute() else [root / path for root in roots]
    for candidate in candidates:
        try:
            resolved = candidate.resolve()
        except Exception:
            continue
        if resolved.is_file():
            return resolved
    return None


def image_info(path: Path) -> Dict[str, Any]:
    info: Dict[str, Any] = {
        "readable": False,
        "width": None,
        "height": None,
        "format": path.suffix.lower().lstrip("."),
        "mode": None,
    }
    if not path.is_file():
        info["reason"] = "PATH_NOT_FOUND"
        return info
    if path.is_symlink():
        info["reason"] = "SYMLINK_NOT_ALLOWED"
        return info
    if path.suffix.lower() not in IMAGE_EXTS:
        info["reason"] = "UNSUPPORTED_FORMAT"
        return info
    if path.stat().st_size <= 1024:
        info["reason"] = "TOO_SMALL_FILE"
        return info
    if Image is None:
        info["readable"] = True
        return info
    try:
        with Image.open(path) as img:
            img = ImageOps.exif_transpose(img)
            info.update(
                {
                    "readable": True,
                    "width": int(img.width),
                    "height": int(img.height),
                    "format": (img.format or path.suffix.lstrip(".") or "jpg").lower(),
                    "mode": img.mode,
                }
            )
    except Exception as exc:
        info["reason"] = "UNREADABLE_IMAGE"
        info["detail"] = repr(exc)
        return info
    if not info["width"] or not info["height"]:
        info["readable"] = False
        info["reason"] = "ZERO_SIZE_IMAGE"
    return info


validate_image = image_info


def ensure_rgb_image(path: Path) -> "Image.Image":
    if Image is None or ImageOps is None:
        raise RuntimeError("Pillow is required for image composition")
    with Image.open(path) as img:
        img = ImageOps.exif_transpose(img)
        if img.mode in {"RGBA", "LA"}:
            background = Image.new("RGB", img.size, "white")
            background.paste(img, mask=img.split()[-1])
            return background
        return img.convert("RGB")


def save_jpeg(image: "Image.Image", path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path, "JPEG", quality=92)


def rel_model_path(path: Path, bundle: Path) -> str:
    try:
        return str(path.resolve().relative_to(bundle.parent.resolve()))
    except ValueError:
        try:
            return str(path.resolve().relative_to(Path.cwd().resolve()))
        except ValueError:
            return str(path.resolve())


def leakage_check(output_path: Path, overlay_texts: Sequence[str]) -> Dict[str, bool]:
    filename_safe = not path_has_forbidden_final_term(output_path)
    overlay_safe = overlay_text_safe(overlay_texts)
    return {
        "path_safe": True,
        "filename_safe": filename_safe,
        "overlay_text_safe": overlay_safe,
        "contains_answer_hint": not (filename_safe and overlay_safe),
    }


check_answer_leakage = leakage_check


def extract_image_candidates(row: Dict[str, Any]) -> List[Dict[str, Any]]:
    candidates: List[Dict[str, Any]] = []

    def add(image_id: str, raw_path: Any, modality: str = "image") -> None:
        text = safe_text(raw_path)
        if text:
            candidates.append({"image_id": image_id or Path(text).stem, "path": text, "modality": modality})

    for key in ("image_path", "rgb_path", "image", "workspace_image", "file_path"):
        if key in row:
            add(safe_text(row.get("image_id") or row.get("media_id") or key), row.get(key))

    media = row.get("media")
    if isinstance(media, str):
        add(safe_text(row.get("image_id") or "media"), media)
    elif isinstance(media, dict):
        for key in ("path", "image_path", "rgb_path"):
            if key in media:
                add(safe_text(media.get("image_id") or media.get("id") or key), media.get(key), safe_text(media.get("modality") or "image"))
        for key in ("paths", "images"):
            for idx, entry in enumerate(as_list(media.get(key))):
                if isinstance(entry, dict):
                    add(safe_text(entry.get("image_id") or entry.get("id") or f"{key}_{idx}"), entry.get("path") or entry.get("image_path"))
                else:
                    add(f"{key}_{idx}", entry)
    elif isinstance(media, list):
        for idx, entry in enumerate(media):
            if isinstance(entry, dict):
                add(safe_text(entry.get("image_id") or entry.get("id") or f"media_{idx}"), entry.get("path") or entry.get("image_path"))
            else:
                add(f"media_{idx}", entry)

    for key in ("images", "image_paths", "visible_images", "source_media", "workspace_observations"):
        value = row.get(key)
        if isinstance(value, dict):
            for image_id, path_value in value.items():
                if isinstance(path_value, dict):
                    add(safe_text(path_value.get("image_id") or image_id), path_value.get("path") or path_value.get("image_path"))
                else:
                    add(str(image_id), path_value)
        elif isinstance(value, list):
            for idx, entry in enumerate(value):
                if isinstance(entry, dict):
                    add(safe_text(entry.get("image_id") or entry.get("id") or f"{key}_{idx}"), entry.get("path") or entry.get("image_path"))
                else:
                    add(f"{key}_{idx}", entry)

    seen = set()
    deduped: List[Dict[str, Any]] = []
    for item in candidates:
        key = (item["image_id"], item["path"])
        if key not in seen:
            deduped.append(item)
            seen.add(key)
    return deduped


def extract_objects(row: Dict[str, Any]) -> List[Dict[str, Any]]:
    for key in ("objects", "visible_objects", "candidate_objects", "annotations"):
        value = row.get(key)
        if isinstance(value, list):
            return [obj for obj in value if isinstance(obj, dict)]
    gt_summary = row.get("gt_summary")
    if isinstance(gt_summary, dict):
        value = gt_summary.get("objects") or gt_summary.get("visible_actors")
        if isinstance(value, list):
            return [obj for obj in value if isinstance(obj, dict)]
    return []


def object_id(obj: Dict[str, Any]) -> str:
    for key in ("object_id", "actor_id", "instance_id", "entity_id", "id"):
        value = obj.get(key)
        if value not in (None, ""):
            return str(value)
    return ""


def parse_bbox(value: Any) -> Optional[Tuple[int, int, int, int]]:
    if isinstance(value, (list, tuple)) and len(value) == 4:
        try:
            x1, y1, x2, y2 = [int(round(float(v))) for v in value]
            return (x1, y1, x2, y2) if x2 > x1 and y2 > y1 else None
        except Exception:
            return None
    if not isinstance(value, dict):
        return None
    if "xyxy" in value:
        return parse_bbox(value.get("xyxy"))
    if {"xmin", "ymin", "xmax", "ymax"} <= set(value):
        return parse_bbox([value["xmin"], value["ymin"], value["xmax"], value["ymax"]])
    if {"x1", "y1", "x2", "y2"} <= set(value):
        return parse_bbox([value["x1"], value["y1"], value["x2"], value["y2"]])
    if {"x", "y", "w", "h"} <= set(value):
        try:
            x, y, w, h = [float(value[k]) for k in ("x", "y", "w", "h")]
            return parse_bbox([x, y, x + w, y + h])
        except Exception:
            return None
    return None


def bbox_for_object(row: Dict[str, Any], image_id: str, wanted_object_id: str) -> Optional[Tuple[int, int, int, int]]:
    for obj in extract_objects(row):
        if object_id(obj) != wanted_object_id:
            continue
        for key in ("bbox_xyxy", "bbox", "bbox2d", "bbox_2d", "box"):
            bbox = parse_bbox(obj.get(key))
            if bbox:
                return bbox

    bbox_by_image = row.get("bbox_by_image")
    if isinstance(bbox_by_image, dict):
        image_payload = bbox_by_image.get(image_id) or bbox_by_image.get(str(image_id))
        if isinstance(image_payload, dict):
            candidate = image_payload.get(wanted_object_id)
            bbox = parse_bbox(candidate)
            if bbox:
                return bbox
            if isinstance(candidate, dict):
                for key in ("bbox_xyxy", "bbox", "bbox_2d"):
                    bbox = parse_bbox(candidate.get(key))
                    if bbox:
                        return bbox
    return None


def parse_point(value: Any) -> Optional[Tuple[int, int]]:
    if isinstance(value, (list, tuple)) and len(value) >= 2:
        try:
            return (int(round(float(value[0]))), int(round(float(value[1]))))
        except Exception:
            return None
    if isinstance(value, dict):
        for x_key, y_key in (("x", "y"), ("cx", "cy"), ("u", "v")):
            if {x_key, y_key} <= set(value):
                try:
                    return (int(round(float(value[x_key]))), int(round(float(value[y_key]))))
                except Exception:
                    return None
    return None


def point_for_object(row: Dict[str, Any], image_id: str, wanted_object_id: str) -> Optional[Tuple[int, int]]:
    for obj in extract_objects(row):
        if object_id(obj) != wanted_object_id:
            continue
        for key in ("point", "point2d", "centroid", "centroid_xy", "center", "center_xy"):
            point = parse_point(obj.get(key))
            if point:
                return point
        bbox = bbox_for_object(row, image_id, wanted_object_id)
        if bbox:
            x1, y1, x2, y2 = bbox
            return (int(round((x1 + x2) / 2)), int(round((y1 + y2) / 2)))
    bbox = bbox_for_object(row, image_id, wanted_object_id)
    if bbox:
        x1, y1, x2, y2 = bbox
        return (int(round((x1 + x2) / 2)), int(round((y1 + y2) / 2)))
    return None


def marker_candidate_object_ids(row: Dict[str, Any], image_id: str, limit: int = 4) -> List[str]:
    candidates: List[Tuple[int, str]] = []
    for obj in extract_objects(row):
        obj_id = object_id(obj)
        if not obj_id:
            continue
        bbox = bbox_for_object(row, image_id, obj_id)
        if not bbox:
            continue
        x1, y1, x2, y2 = bbox
        area = max(1, (x2 - x1) * (y2 - y1))
        candidates.append((area, obj_id))
    candidates.sort(reverse=True)
    return [obj_id for _area, obj_id in candidates[:limit]]


class ImageProcessor:
    def __init__(self, *, bundle: Path, evidence_path: Path, out_dir: Path, requests_path: Optional[Path]) -> None:
        self.bundle = bundle.resolve()
        self.evidence_path = evidence_path.resolve()
        self.out_dir = out_dir.resolve()
        self.requests_path = requests_path.resolve() if requests_path else None
        self.image_dir = self.out_dir / "images"
        self.preview_dir = self.out_dir / "previews"
        self.log_dir = self.out_dir / "logs"
        self.manifest: List[Dict[str, Any]] = []
        self.rejected: List[Dict[str, Any]] = []
        self.composer_counts: Counter[str] = Counter()
        self.rejection_counts: Counter[str] = Counter()
        self.evidence_rows = load_jsonl(self.evidence_path)
        self.requests = load_jsonl(self.requests_path) if self.requests_path else []
        self.by_sample: Dict[str, List[Dict[str, Any]]] = {}
        self.by_image: Dict[str, Tuple[Dict[str, Any], Dict[str, Any]]] = {}
        self._index_evidence()

    def _index_evidence(self) -> None:
        for row in self.evidence_rows:
            sample_id = safe_text(row.get("sample_id") or row.get("record_id") or row.get("item_id") or row.get("id"))
            if sample_id:
                self.by_sample.setdefault(sample_id, []).append(row)
            for image_entry in extract_image_candidates(row):
                image_id = safe_text(image_entry.get("image_id"))
                if image_id:
                    self.by_image[image_id] = (row, image_entry)

    def output_path(self) -> Path:
        return self.image_dir / f"imgproc_{len(self.manifest) + 1:06d}.jpg"

    def reject(self, reason_code: str, reason: str, *, row: Optional[Dict[str, Any]] = None, request: Optional[Dict[str, Any]] = None, image_id: str = "", path: Any = "") -> None:
        payload = {
            "sample_id": safe_text((request or {}).get("sample_id") or (row or {}).get("sample_id")),
            "request_id": safe_text((request or {}).get("request_id")),
            "image_id": image_id,
            "path": safe_text(path),
            "composer": safe_text((request or {}).get("composer") or "safe_copy"),
            "reason_code": reason_code,
            "reason": reason,
            "recoverable": False,
        }
        self.rejected.append(payload)
        self.rejection_counts[reason_code] += 1

    def accepted_record(
        self,
        *,
        output_path: Path,
        source_paths: Sequence[Path],
        source_image_ids: Sequence[str],
        composer: str,
        row: Optional[Dict[str, Any]] = None,
        request: Optional[Dict[str, Any]] = None,
        visual_labels: Optional[List[Dict[str, Any]]] = None,
        layout: Optional[Dict[str, Any]] = None,
        overlay_texts: Optional[Sequence[str]] = None,
    ) -> Dict[str, Any]:
        info = image_info(output_path)
        labels = visual_labels or []
        record = {
            "manifest_id": output_path.stem,
            "sample_id": safe_text((request or {}).get("sample_id") or (row or {}).get("sample_id") or (row or {}).get("record_id")),
            "scene_id": safe_text((row or {}).get("scene_id") or (row or {}).get("scene")),
            "request_id": safe_text((request or {}).get("request_id")),
            "composer": composer,
            "model_input_path": rel_model_path(output_path, self.bundle),
            "source_image_ids": list(source_image_ids),
            "source_paths": [str(path) for path in source_paths],
            "width": info.get("width"),
            "height": info.get("height"),
            "format": "jpg",
            "sha256": sha256(output_path),
            "visual_labels": labels,
            "layout": layout or {"type": composer},
            "available_evidence_flags": {
                "has_rgb": True,
                "has_depth": bool((row or {}).get("depth_path") or (row or {}).get("depth")),
                "has_bbox": bool(labels) or any(bbox_for_object(row or {}, source_image_ids[0] if source_image_ids else "", object_id(obj)) for obj in extract_objects(row or {})),
                "has_mask": bool((row or {}).get("mask") or (row or {}).get("mask_by_image")),
                "has_camera_pose": bool((row or {}).get("camera_pose")),
                "has_trajectory": bool((row or {}).get("trajectory")),
            },
            "leakage_check": leakage_check(output_path, overlay_texts or []),
            "status": "accepted",
        }
        return record

    def source_for_image_id(self, image_ref: Any, request: Optional[Dict[str, Any]] = None) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]], Optional[Path]]:
        text = safe_text(image_ref)
        if text in self.by_image:
            row, image_entry = self.by_image[text]
            return row, image_entry, resolve_path(image_entry.get("path"), evidence_path=self.evidence_path, bundle=self.bundle, row=row)
        request_sample = safe_text((request or {}).get("sample_id"))
        rows = self.by_sample.get(request_sample, []) if request_sample else self.evidence_rows
        for row in rows:
            for image_entry in extract_image_candidates(row):
                if text in {safe_text(image_entry.get("image_id")), Path(safe_text(image_entry.get("path"))).stem, safe_text(image_entry.get("path"))}:
                    return row, image_entry, resolve_path(image_entry.get("path"), evidence_path=self.evidence_path, bundle=self.bundle, row=row)
        path = resolve_path(text, evidence_path=self.evidence_path, bundle=self.bundle, row=None)
        return None, {"image_id": Path(text).stem, "path": text}, path

    def compose_safe_copy(self, row: Dict[str, Any], image_entry: Dict[str, Any], request: Optional[Dict[str, Any]] = None) -> None:
        composer = "safe_copy"
        image_id = safe_text(image_entry.get("image_id"))
        src = resolve_path(image_entry.get("path"), evidence_path=self.evidence_path, bundle=self.bundle, row=row)
        if not src:
            self.reject("PATH_NOT_FOUND", "image path cannot be resolved", row=row, request=request, image_id=image_id, path=image_entry.get("path"))
            return
        info = image_info(src)
        if not info.get("readable"):
            self.reject(safe_text(info.get("reason") or "UNREADABLE_IMAGE"), "source image is not readable", row=row, request=request, image_id=image_id, path=src)
            return
        dst = self.output_path()
        if Image is None:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
        else:
            save_jpeg(ensure_rgb_image(src), dst)
        record = self.accepted_record(
            output_path=dst,
            source_paths=[src],
            source_image_ids=[image_id],
            composer=composer,
            row=row,
            request=request,
        )
        self.manifest.append(record)
        self.composer_counts[composer] += 1

    def compose_bbox_label_overlay(self, request: Dict[str, Any]) -> None:
        composer = "bbox_label_overlay"
        source_images = as_list(request.get("source_images"))
        candidate_objects = [safe_text(x) for x in as_list(request.get("candidate_objects")) if safe_text(x)]
        if not source_images:
            self.reject("MISSING_RGB", "bbox_label_overlay requires at least one source image", request=request)
            return
        if not candidate_objects:
            self.reject("MISSING_CANDIDATE_OBJECTS", "bbox_label_overlay requires candidate_objects", request=request)
            return
        row, image_entry, src = self.source_for_image_id(source_images[0], request)
        image_id = safe_text((image_entry or {}).get("image_id") or source_images[0])
        if not row or not src:
            self.reject("PATH_NOT_FOUND", "source image cannot be resolved", request=request, image_id=image_id, path=source_images[0])
            return
        if Image is None or ImageDraw is None or ImageFont is None:
            self.reject("INVALID_RECIPE", "Pillow is required for bbox_label_overlay", row=row, request=request, image_id=image_id, path=src)
            return
        info = image_info(src)
        if not info.get("readable"):
            self.reject(safe_text(info.get("reason") or "UNREADABLE_IMAGE"), "source image is not readable", row=row, request=request, image_id=image_id, path=src)
            return
        labels = safe_label_list((request.get("layout") or {}).get("labels") if isinstance(request.get("layout"), dict) else None, len(candidate_objects))
        if not overlay_text_safe(labels):
            self.reject("ANSWER_LEAKAGE_RISK", "overlay labels contain forbidden answer hints", row=row, request=request, image_id=image_id, path=src)
            return

        canvas = ensure_rgb_image(src)
        draw = ImageDraw.Draw(canvas)
        try:
            font = ImageFont.truetype("DejaVuSans-Bold.ttf", 26)
        except Exception:
            font = ImageFont.load_default()
        palette = ["#D62828", "#1D4ED8", "#2A9D8F", "#F4A261", "#6D28D9", "#111827"]
        visual_labels: List[Dict[str, Any]] = []
        for idx, obj_id in enumerate(candidate_objects):
            bbox = bbox_for_object(row, image_id, obj_id)
            if not bbox:
                self.reject("MISSING_BBOX", f"missing bbox for candidate object {obj_id}", row=row, request=request, image_id=image_id, path=src)
                return
            x1, y1, x2, y2 = bbox
            x1 = max(0, min(canvas.width - 1, x1))
            y1 = max(0, min(canvas.height - 1, y1))
            x2 = max(0, min(canvas.width - 1, x2))
            y2 = max(0, min(canvas.height - 1, y2))
            if x2 <= x1 or y2 <= y1:
                self.reject("INVALID_DIMENSION", f"bbox out of bounds for candidate object {obj_id}", row=row, request=request, image_id=image_id, path=src)
                return
            label = labels[idx]
            color = palette[idx % len(palette)]
            draw.rectangle([x1, y1, x2, y2], outline=color, width=4)
            text_box = draw.textbbox((x1, y1), label, font=font)
            tw = text_box[2] - text_box[0]
            th = text_box[3] - text_box[1]
            top = max(0, y1 - th - 8)
            draw.rectangle([x1, top, x1 + tw + 10, top + th + 8], fill=color)
            draw.text((x1 + 5, top + 3), label, fill="white", font=font)
            visual_labels.append(
                {
                    "label": label,
                    "object_id": obj_id,
                    "bbox_xyxy": [x1, y1, x2, y2],
                    "label_type": "neutral_letter",
                }
            )
        dst = self.output_path()
        save_jpeg(canvas, dst)
        self.manifest.append(
            self.accepted_record(
                output_path=dst,
                source_paths=[src],
                source_image_ids=[image_id],
                composer=composer,
                row=row,
                request=request,
                visual_labels=visual_labels,
                layout={"type": "single_overlay", "panels": [{"panel_id": "main", "source_image_id": image_id}]},
                overlay_texts=labels,
            )
        )
        self.composer_counts[composer] += 1

    def compose_point_label_overlay(self, request: Dict[str, Any]) -> None:
        composer = "point_label_overlay"
        source_images = as_list(request.get("source_images"))
        candidate_objects = [safe_text(x) for x in as_list(request.get("candidate_objects")) if safe_text(x)]
        if not source_images:
            self.reject("MISSING_RGB", "point_label_overlay requires at least one source image", request=request)
            return
        if not candidate_objects:
            self.reject("MISSING_CANDIDATE_OBJECTS", "point_label_overlay requires candidate_objects", request=request)
            return
        row, image_entry, src = self.source_for_image_id(source_images[0], request)
        image_id = safe_text((image_entry or {}).get("image_id") or source_images[0])
        if not row or not src:
            self.reject("PATH_NOT_FOUND", "source image cannot be resolved", request=request, image_id=image_id, path=source_images[0])
            return
        if Image is None or ImageDraw is None or ImageFont is None:
            self.reject("INVALID_RECIPE", "Pillow is required for point_label_overlay", row=row, request=request, image_id=image_id, path=src)
            return
        info = image_info(src)
        if not info.get("readable"):
            self.reject(safe_text(info.get("reason") or "UNREADABLE_IMAGE"), "source image is not readable", row=row, request=request, image_id=image_id, path=src)
            return
        labels = safe_label_list((request.get("layout") or {}).get("labels") if isinstance(request.get("layout"), dict) else None, len(candidate_objects))
        if not overlay_text_safe(labels):
            self.reject("ANSWER_LEAKAGE_RISK", "point labels contain forbidden answer hints", row=row, request=request, image_id=image_id, path=src)
            return

        canvas = ensure_rgb_image(src)
        draw = ImageDraw.Draw(canvas)
        try:
            font = ImageFont.truetype("DejaVuSans-Bold.ttf", 26)
        except Exception:
            font = ImageFont.load_default()
        palette = ["#D62828", "#1D4ED8", "#2A9D8F", "#F4A261", "#6D28D9", "#111827"]
        visual_labels: List[Dict[str, Any]] = []
        radius = max(8, min(canvas.width, canvas.height) // 120)
        for idx, obj_id in enumerate(candidate_objects):
            point = point_for_object(row, image_id, obj_id)
            if not point:
                self.reject("MISSING_POINT", f"missing point or bbox-derived center for candidate object {obj_id}", row=row, request=request, image_id=image_id, path=src)
                return
            x, y = point
            if not (0 <= x < canvas.width and 0 <= y < canvas.height):
                self.reject("INVALID_DIMENSION", f"point out of bounds for candidate object {obj_id}", row=row, request=request, image_id=image_id, path=src)
                return
            label = labels[idx]
            color = palette[idx % len(palette)]
            draw.ellipse([x - radius, y - radius, x + radius, y + radius], outline=color, width=4)
            draw.line([x - radius * 2, y, x + radius * 2, y], fill=color, width=2)
            draw.line([x, y - radius * 2, x, y + radius * 2], fill=color, width=2)
            text_box = draw.textbbox((x, y), label, font=font)
            tw = text_box[2] - text_box[0]
            th = text_box[3] - text_box[1]
            left = min(max(0, x + radius + 6), max(0, canvas.width - tw - 10))
            top = min(max(0, y - th - 10), max(0, canvas.height - th - 8))
            draw.rectangle([left, top, left + tw + 10, top + th + 8], fill=color)
            draw.text((left + 5, top + 3), label, fill="white", font=font)
            bbox = bbox_for_object(row, image_id, obj_id)
            visual_labels.append(
                {
                    "label": label,
                    "object_id": obj_id,
                    "point_xy": [x, y],
                    "bbox_xyxy": list(bbox) if bbox else None,
                    "label_type": "neutral_point",
                }
            )
        dst = self.output_path()
        save_jpeg(canvas, dst)
        self.manifest.append(
            self.accepted_record(
                output_path=dst,
                source_paths=[src],
                source_image_ids=[image_id],
                composer=composer,
                row=row,
                request=request,
                visual_labels=visual_labels,
                layout={"type": "single_point_overlay", "panels": [{"panel_id": "main", "source_image_id": image_id}]},
                overlay_texts=labels,
            )
        )
        self.composer_counts[composer] += 1

    def compose_auto_marker_overlay(self, row: Dict[str, Any], image_entry: Dict[str, Any]) -> None:
        image_id = safe_text(image_entry.get("image_id"))
        candidate_objects = marker_candidate_object_ids(row, image_id, limit=4)
        if len(candidate_objects) < 2:
            return
        self.compose_bbox_label_overlay(
            {
                "request_id": f"auto_bbox_markers_{image_id or safe_text(row.get('sample_id') or row.get('record_id'))}",
                "sample_id": safe_text(row.get("sample_id") or row.get("record_id") or row.get("item_id") or row.get("id")),
                "composer": "bbox_label_overlay",
                "source_images": [image_id or image_entry.get("path")],
                "candidate_objects": candidate_objects,
                "layout": {"labels": LABELS[: len(candidate_objects)]},
                "purpose": "auto_gt_object_question_anchors",
            }
        )

    def compose_grid(self, request: Dict[str, Any], composer: str) -> None:
        source_images = as_list(request.get("source_images") or request.get("candidate_images"))
        if len(source_images) < 2:
            self.reject("INVALID_RECIPE", f"{composer} requires at least two source images", request=request)
            return
        if Image is None or ImageDraw is None or ImageFont is None:
            self.reject("INVALID_RECIPE", f"Pillow is required for {composer}", request=request)
            return
        labels = safe_label_list((request.get("layout") or {}).get("labels") if isinstance(request.get("layout"), dict) else None, len(source_images))
        if not overlay_text_safe(labels):
            self.reject("ANSWER_LEAKAGE_RISK", "panel labels contain forbidden answer hints", request=request)
            return
        panels: List[Tuple[str, Dict[str, Any], Path, "Image.Image"]] = []
        first_row: Optional[Dict[str, Any]] = None
        for idx, ref in enumerate(source_images):
            row, image_entry, src = self.source_for_image_id(ref, request)
            image_id = safe_text((image_entry or {}).get("image_id") or f"panel_{idx}")
            if not src:
                self.reject("PATH_NOT_FOUND", "panel source image cannot be resolved", row=row, request=request, image_id=image_id, path=ref)
                return
            info = image_info(src)
            if not info.get("readable"):
                self.reject(safe_text(info.get("reason") or "UNREADABLE_IMAGE"), "panel source image is not readable", row=row, request=request, image_id=image_id, path=src)
                return
            first_row = first_row or row
            panels.append((image_id, image_entry or {"image_id": image_id}, src, ensure_rgb_image(src)))

        thumb_w, thumb_h = 480, 360
        cols = min(3, max(1, math.ceil(math.sqrt(len(panels)))))
        rows = math.ceil(len(panels) / cols)
        header_h = 38
        canvas = Image.new("RGB", (cols * thumb_w, rows * (thumb_h + header_h)), "white")
        draw = ImageDraw.Draw(canvas)
        try:
            font = ImageFont.truetype("DejaVuSans-Bold.ttf", 24)
        except Exception:
            font = ImageFont.load_default()
        layout_panels: List[Dict[str, Any]] = []
        for idx, (image_id, _entry, src, img) in enumerate(panels):
            col = idx % cols
            row_idx = idx // cols
            x = col * thumb_w
            y = row_idx * (thumb_h + header_h)
            img.thumbnail((thumb_w, thumb_h), Image.Resampling.LANCZOS if hasattr(Image, "Resampling") else Image.LANCZOS)
            paste_x = x + (thumb_w - img.width) // 2
            paste_y = y + header_h + (thumb_h - img.height) // 2
            draw.rectangle([x, y, x + thumb_w, y + header_h], fill="#111827")
            draw.text((x + 12, y + 7), labels[idx], fill="white", font=font)
            canvas.paste(img, (paste_x, paste_y))
            layout_panels.append({"panel_id": labels[idx], "source_image_id": image_id, "source_path": str(src)})
        dst = self.output_path()
        save_jpeg(canvas, dst)
        self.manifest.append(
            self.accepted_record(
                output_path=dst,
                source_paths=[panel[2] for panel in panels],
                source_image_ids=[panel[0] for panel in panels],
                composer=composer,
                row=first_row,
                request=request,
                visual_labels=[{"label": label, "label_type": "neutral_panel"} for label in labels],
                layout={"type": composer, "panels": layout_panels},
                overlay_texts=labels,
            )
        )
        self.composer_counts[composer] += 1

    def process_default(self) -> None:
        for row in self.evidence_rows:
            for image_entry in extract_image_candidates(row):
                self.compose_safe_copy(row, image_entry)
                self.compose_auto_marker_overlay(row, image_entry)

    def process_requests(self) -> None:
        for request in self.requests:
            composer = safe_text(request.get("composer") or "safe_copy")
            if composer not in SUPPORTED_COMPOSERS:
                self.reject("INVALID_RECIPE", f"unsupported composer: {composer}", request=request)
                continue
            if composer == "safe_copy":
                for ref in as_list(request.get("source_images")):
                    row, image_entry, src = self.source_for_image_id(ref, request)
                    if not row or not image_entry:
                        self.reject("PATH_NOT_FOUND", "safe_copy source image cannot be resolved", request=request, path=ref)
                        continue
                    self.compose_safe_copy(row, image_entry, request=request)
            elif composer == "bbox_label_overlay":
                self.compose_bbox_label_overlay(request)
            elif composer == "point_label_overlay":
                self.compose_point_label_overlay(request)
            elif composer in {"multi_view_grid", "candidate_panel"}:
                self.compose_grid(request, composer)

    def write_outputs(self) -> Dict[str, Any]:
        self.out_dir.mkdir(parents=True, exist_ok=True)
        self.image_dir.mkdir(parents=True, exist_ok=True)
        self.preview_dir.mkdir(parents=True, exist_ok=True)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        write_jsonl(self.out_dir / "image_manifest.jsonl", self.manifest)
        write_jsonl(self.out_dir / "rejected_images.jsonl", self.rejected)
        report = {
            "total_samples": len({safe_text(row.get("sample_id") or row.get("record_id") or idx) for idx, row in enumerate(self.evidence_rows)}),
            "total_requests": len(self.requests),
            "accepted_images": len(self.manifest),
            "rejected_images": len(self.rejected),
            "composer_counts": dict(sorted(self.composer_counts.items())),
            "rejection_counts": dict(sorted(self.rejection_counts.items())),
            "blocking": not self.manifest,
            "blocking_reasons": [] if self.manifest else ["NO_ACCEPTED_IMAGES"],
            "warnings": [] if Image is not None else ["Pillow unavailable; composition support is limited."],
            "outputs": {
                "image_manifest": str(self.out_dir / "image_manifest.jsonl"),
                "rejected_images": str(self.out_dir / "rejected_images.jsonl"),
                "images": str(self.image_dir),
            },
        }
        write_json(self.out_dir / "image_processing_report.json", report)
        (self.log_dir / "process_answer_images.log").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return report

    def run(self) -> Dict[str, Any]:
        if self.requests:
            self.process_requests()
        else:
            self.process_default()
        return self.write_outputs()


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Normalize Stage4 answer images into a bundle-local manifest.")
    parser.add_argument("--bundle", default="", help="data_20_template_metric_code_bundle directory.")
    parser.add_argument("--evidence-index", required=True)
    parser.add_argument("--image-requests", default="")
    parser.add_argument("--out", default="", help="Output image_processing directory.")
    parser.add_argument("--out-dir", default="", help="Backward-compatible alias for --out.")
    parser.add_argument("--no-copy-images", action="store_true", help="Deprecated compatibility flag; output still remains bundle-local.")
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    evidence_path = Path(args.evidence_index).expanduser().resolve()
    if not evidence_path.is_file():
        raise SystemExit(f"Missing evidence index: {evidence_path}")
    bundle = Path(args.bundle).expanduser().resolve() if args.bundle else evidence_path.parent.resolve()
    out_dir = Path(args.out or args.out_dir or (bundle / "image_processing")).expanduser().resolve()
    requests_path = Path(args.image_requests).expanduser().resolve() if args.image_requests else None
    if requests_path and not requests_path.is_file():
        raise SystemExit(f"Missing image requests: {requests_path}")
    processor = ImageProcessor(bundle=bundle, evidence_path=evidence_path, out_dir=out_dir, requests_path=requests_path)
    report = processor.run()
    print(json.dumps(report, ensure_ascii=False))
    return 0 if not report.get("blocking") else 1


if __name__ == "__main__":
    raise SystemExit(main())
