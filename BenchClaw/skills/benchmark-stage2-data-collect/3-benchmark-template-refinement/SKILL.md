---
name: benchmark-template-refinement
description: "Stage 2 Phase 3. 生成 raw schema 模板和 template_index；仅定义原始记录字段，不定义清洗/过滤。"
argument-hint: [workspace-root]
allowed-tools: Bash(*), Read, Write, Grep, Glob
---

# Phase 3 — Raw template refinement

## Purpose

Create source-specific raw record templates that Phase 4 scripts must follow.

## Inputs

```text
WORKSPACE_ROOT/stage2/source_plan.jsonl
WORKSPACE_ROOT/stage2/COLLECTION_GUIDANCE_PLAN.md
WORKSPACE_ROOT/stage2/source_inventory.jsonl
WORKSPACE_ROOT/stage1/EVALSET_PROTOTYPE.md
```

## Output directory

```text
WORKSPACE_ROOT/stage2/templates/
```

## Template rules

For every source in `source_plan.jsonl`, write:

```text
stage2/templates/{source_type}__{source_name}.yaml
```

Each YAML must contain these top-level keys:

```yaml
source:
  source_type:
  source_name:
  source_role:
  card_path:
  card_status:
stage1_trace:
  capability_dimensions: []
  stage1_requirement_refs: []
raw_record:
  sample_id:
  source_type:
  source_name:
  capability_dimension:
  source_role:
  stage1_requirement_ref:
  image_path:
  record_json_path:
  original_source_ref:
  raw_modalities: []
  gt_or_label_refs: {}
  raw_observation_flags: []
  access_error:
  annotation_gap:
  integrity_notes:
  license_and_privacy:
  source_card_path:
  source_card_fields_used: []
simulator_only:
  simulator_started_at:
  simulator_start_command:
  run_id:
  session_id:
  frame_id:
  scene_or_map:
  sensor_config:
  current_run_only: true
  old_data_reuse: false
existing_dataset_only:
  dataset_original_id:
  dataset_split:
  dataset_root_or_external_path:
  file_hash:
real_data_only:
  original_image_path:
  registration_row_id:
  consent_or_license_status:
```

Unused source-type-specific fields may remain null, but the key group must exist so tests can validate structure.

## Reports

Write `WORKSPACE_ROOT/stage2/template_index.jsonl`, one row per template:

```json
{"source_type":"...","source_name":"...","template_path":"stage2/templates/...yaml","required_fields":[],"source_specific_fields":[]}
```

Write `WORKSPACE_ROOT/stage2/TEMPLATE_REFINEMENT_REPORT.md` with:

```text
# Template Refinement Report
## Template Index
## Fields Inherited From Stage 1
## Fields Inherited From Source Cards
## Required Raw Record Fields
## Source-Specific Fields
## Missing Card Details
```

Write `WORKSPACE_ROOT/stage2/status/phase3_templates.json`.

## Forbidden

No cleaning schema, no filtering threshold, no duplicate removal rule, no scoring or evaluation-set construction field.
