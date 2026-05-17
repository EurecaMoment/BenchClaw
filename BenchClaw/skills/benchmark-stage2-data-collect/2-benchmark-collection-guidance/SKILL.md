---
name: benchmark-collection-guidance
description: "Stage 2 Phase 2. 将 Stage 1 能力维度路由到 source，生成可执行采集计划和 source_plan.jsonl；不写清洗/过滤规则。"
argument-hint: [workspace-root]
allowed-tools: Bash(*), Read, Write, Grep, Glob
---

# Phase 2 — Collection guidance

## Purpose

Convert the Phase 1 inventory into an execution plan. Every future raw sample must be traceable to a capability dimension, a Stage 1 requirement, and a source card or explicit missing-card status.

## Inputs

```text
WORKSPACE_ROOT/stage1/CAPABILITY_SCOPE.md
WORKSPACE_ROOT/stage1/DATA_SOURCE_MAPPING.md
WORKSPACE_ROOT/stage1/BENCHMARK_DRAFT.md
WORKSPACE_ROOT/stage1/EVALSET_PROTOTYPE.md
WORKSPACE_ROOT/stage1/EXECUTION_PLAN.md
WORKSPACE_ROOT/stage2/SOURCE_CAPABILITY_SURVEY.md
WORKSPACE_ROOT/stage2/source_inventory.jsonl
```

## Procedure

For each enabled source:

1. Assign one `source_role`:
   - `primary_gt`: authoritative GT source for one or more capability dimensions
   - `coverage_expansion`: expands visual/scene/task diversity
   - `negative_or_edge_case`: supplies hard cases or boundary cases
   - `realism_anchor`: real-world grounding source
   - `auxiliary_raw`: raw-only supplemental source
2. Map the source to capability dimensions and expected raw evidence.
3. Define only raw acquisition/ingestion/registration instructions.
4. Carry forward card status. If card information is insufficient, mark the source blocked or needs input; do not hallucinate paths, startup commands, schemas, or license status.

## Outputs

Write `WORKSPACE_ROOT/stage2/source_plan.jsonl`, one JSON object per enabled source:

```json
{
  "job_id": "source_type__source_name",
  "source_type": "simulator|existing_dataset|real_data",
  "source_name": "stable_dir_name",
  "enabled": true,
  "status_before_codegen": "READY|NEEDS_CARD|NEEDS_CARD_DETAIL|NEEDS_USER_INPUT|BLOCKED",
  "source_role": "primary_gt|coverage_expansion|negative_or_edge_case|realism_anchor|auxiliary_raw",
  "capability_dimensions": [],
  "stage1_requirement_refs": [],
  "card_path": "...",
  "raw_modalities_to_save": [],
  "gt_or_label_refs_to_save": [],
  "script_kind": "collect|ingest|register",
  "expected_output_root": "stage2/collected_data/source_type/source_name",
  "runtime_or_access_requirements": [],
  "raw_flags_to_record": ["access_error", "annotation_gap", "integrity_notes", "needs_human_review"],
  "old_data_reuse_allowed": false,
  "notes": []
}
```

Write `WORKSPACE_ROOT/stage2/COLLECTION_GUIDANCE_PLAN.md` with:

```text
# Collection Guidance Plan
## Capability-To-Source Routing
## Per-Source Execution Plan
## Simulator Collection Plan
## Existing Dataset Ingestion Plan
## Real Data Registration Plan
## Coverage Gaps And Compensation
## Blocked Sources And Required Inputs
## Raw-Only Prohibitions
```

Write `WORKSPACE_ROOT/stage2/status/phase2_guidance.json`.

## Required semantics

- `simulator`: must require new runtime/session/run creation in Phase 5.
- `existing_dataset`: may copy, hardlink, or register external paths, but must preserve original ID/path/hash when available.
- `real_data`: may register incomplete metadata, but must never convert model guesses into GT.

## Forbidden

Do not include cleaning framework commands, quality thresholds, dedup deletion, sample rejection rules, or Stage 4 item-building logic.
