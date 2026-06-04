#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Validate the strict fixed BenchClaw template library."""
from __future__ import annotations
import csv, json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REG = ROOT / "template_library" / "benchclaw_fixed_template_registry.csv"
BAD_WORDS = ["不可回答", "无法判断", "信息不足", "是否可回答", "是否足以判断", "仅凭图像判断"]
GT_LEAK_WORDS = ["depth_median", "GT", "gt", "object_id", "可见物体列表", "已有 GT 字段"]
DEPRECATED_OK = "DEPRECATED_LOCKED"

def fail(msg: str) -> None:
    print("[FAIL]", msg)
    sys.exit(1)

def main() -> None:
    rows = list(csv.DictReader(REG.open(encoding="utf-8")))
    if len(rows) != 100:
        fail(f"expected 100 templates, got {len(rows)}")
    ids = [r["template_id"] for r in rows]
    if len(ids) != len(set(ids)):
        fail("duplicate template_id")
    selectable = [r for r in rows if r["agent_selectable"].lower() == "true"]
    for r in selectable:
        q = r["fixed_question_template"]
        if r["canonical_question_type"] == "DEPRECATED_LOCKED":
            fail(f"selectable deprecated template: {r['template_id']}")
        if any(w in q for w in BAD_WORDS):
            fail(f"unanswerable wording in selectable {r['template_id']}: {q}")
        if any(w in q for w in GT_LEAK_WORDS):
            fail(f"GT leakage in selectable {r['template_id']}: {q}")
        if "数值题" in r["original_format"] and r["canonical_question_type"] != "QT4_INTERVAL_CHOICE":
            fail(f"raw numeric not converted: {r['template_id']}")
    deprecated = [r for r in rows if r["status"] == DEPRECATED_OK]
    for r in deprecated:
        if r["agent_selectable"].lower() != "false":
            fail(f"deprecated not locked: {r['template_id']}")
    print(json.dumps({"status":"PASS","templates":len(rows),"agent_selectable":len(selectable),"deprecated_locked":len(deprecated)}, ensure_ascii=False))

if __name__ == "__main__":
    main()
