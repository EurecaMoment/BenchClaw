---
name: benchmark-data-capability-survey
description: "Stage 2 Phase 1. 读取 Stage 1 数据源映射和只读 source cards，生成数据源能力清单；不采集、不清洗、不筛选。"
argument-hint: [workspace-root]
allowed-tools: Bash(*), Read, Write, Grep, Glob
---

# Phase 1 — Source capability survey

## Purpose

Produce a machine-readable inventory of every Stage 1 source and a short human-readable survey. This phase only observes capabilities; it does not run any collector.

## Inputs

Required:

```text
WORKSPACE_ROOT/stage1/DATA_SOURCE_MAPPING.md
WORKSPACE_ROOT/stage1/CAPABILITY_SCOPE.md
WORKSPACE_ROOT/stage1/BENCHMARK_DRAFT.md
WORKSPACE_ROOT/stage1/EVALSET_PROTOTYPE.md
```

Read-only card roots:

```text
BENCHCLAW_ROOT/simulatorCards/
BENCHCLAW_ROOT/benchmarkDatasetCards/
BENCHCLAW_ROOT/realDataCards/
```

Resolve `BENCHCLAW_ROOT` from the current skill bundle/repository location. Do not assume a fixed `/home/...` path.

## Procedure

1. Parse `DATA_SOURCE_MAPPING.md` and extract every enabled source with:
   - `source_type`: `simulator`, `existing_dataset`, or `real_data`
   - `source_name`
   - related capability dimensions
   - explicit Stage 1 requirement references if present
2. For every source, find and read the corresponding source card:
   - `simulator` -> `simulatorCards/`
   - `existing_dataset` -> `benchmarkDatasetCards/`
   - `real_data` -> `realDataCards/`
3. Record only evidence found in Stage 1 files or source cards. If a card or field is missing, mark it missing; do not guess.
4. Do not write anywhere under `BENCHCLAW_ROOT`.

## Outputs

Write `WORKSPACE_ROOT/stage2/source_inventory.jsonl`, one JSON object per source:

```json
{
  "source_type": "simulator|existing_dataset|real_data",
  "source_name": "stable_dir_name",
  "enabled": true,
  "capability_dimensions": [],
  "stage1_requirement_refs": [],
  "card_path": "...",
  "card_status": "FOUND|NEEDS_CARD|NEEDS_CARD_DETAIL|NEEDS_USER_INPUT",
  "card_evidence": {
    "startup_or_access": null,
    "data_root_or_endpoint": null,
    "schema_fields": [],
    "modalities": [],
    "gt_fields": [],
    "license_or_privacy": null,
    "runtime_constraints": []
  },
  "known_risks": [],
  "raw_only_notes": []
}
```

Write `WORKSPACE_ROOT/stage2/SOURCE_CAPABILITY_SURVEY.md` with these sections:

```text
# Source Capability Survey
## Source Inventory
## Source Card Evidence
## Simulator Sources
## Existing Dataset Sources
## Real Data Sources
## Missing Cards Or Fields
## Raw-Only Notes
```

Write `WORKSPACE_ROOT/stage2/status/phase1_survey.json` with status:

- `PASS`: all enabled sources have sufficient cards.
- `PARTIAL`: some sources are missing optional details.
- `BLOCKED`: no valid enabled source or required Stage 1 input is missing.

## Forbidden

- Do not run collection scripts.
- Do not create placeholder samples.
- Do not propose cleaning/filtering/deletion.
- Do not edit source cards.
