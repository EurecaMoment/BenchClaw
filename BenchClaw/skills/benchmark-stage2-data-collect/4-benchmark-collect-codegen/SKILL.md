---
name: benchmark-collect-codegen
description: "Stage 2 Phase 4. 为每个 source 生成独立入口脚本、配置和 README；脚本只采集/接入/登记 raw data，不执行清洗过滤。"
argument-hint: [workspace-root]
allowed-tools: Bash(*), Read, Write, Edit, Grep, Glob
---

# Phase 4 — Collect/ingest/register code generation

## Purpose

Generate executable per-source code. Do not run it here. Phase 5 workers run it.

## Inputs

```text
WORKSPACE_ROOT/stage2/source_plan.jsonl
WORKSPACE_ROOT/stage2/template_index.jsonl
WORKSPACE_ROOT/stage2/templates/*.yaml
WORKSPACE_ROOT/stage2/COLLECTION_GUIDANCE_PLAN.md
WORKSPACE_ROOT/stage2/SOURCE_CAPABILITY_SURVEY.md
```

## Output layout

For each source:

```text
stage2/source_runs/{source_type}/{source_name}/README.md
stage2/source_runs/{source_type}/{source_name}/config.yaml
stage2/source_runs/{source_type}/{source_name}/run_source.sh
stage2/source_runs/{source_type}/{source_name}/{collect.py|ingest.py|register.py}
```

Choose script name by source type:

- `simulator` -> `collect.py`
- `existing_dataset` -> `ingest.py`
- `real_data` -> `register.py`

Also write:

```text
stage2/DATA_SCHEMA.md
stage2/status/phase4_codegen.json
```

## Per-source config contract

Each `config.yaml` must include:

```yaml
job_id:
source_type:
source_name:
source_role:
card_path:
card_status:
script_kind:
workspace_root:
output_root: stage2/collected_data/{source_type}/{source_name}
template_path:
capability_dimensions: []
stage1_requirement_refs: []
source_card_fields_used: []
runtime_or_access:
  startup_command:
  endpoint:
  data_root:
  manifest_or_sheet:
  split:
  scene_or_map:
  sensor_config:
safety:
  benchclaw_root_readonly: true
  no_placeholder: true
  no_cleaning: true
  no_filtering: true
  old_data_reuse_allowed: false
```

## Script requirements

All scripts must accept:

```bash
python {collect|ingest|register}.py --workspace-root <WORKSPACE_ROOT> --config config.yaml --job-json <stage2/source_jobs/job.json>
```

All scripts must write only under:

```text
WORKSPACE_ROOT/stage2/collected_data/{source_type}/{source_name}/
WORKSPACE_ROOT/stage2/logs/{source_type}__{source_name}/
```

For every successful sample, scripts must create:

```text
images/{sample_id}.{ext}
records/{sample_id}.json
manifest.jsonl
```

Every manifest row and record JSON must include:

```text
sample_id, source_type, source_name, capability_dimension, source_role,
stage1_requirement_ref, image_path, record_json_path, original_source_ref,
source_card_path, source_card_fields_used, raw_observation_flags,
access_error, annotation_gap, integrity_notes, license_and_privacy
```

Simulator records must additionally include:

```text
simulator_started_at, simulator_start_command, run_id or session_id,
frame_id, scene_or_map, sensor_config, current_run_only=true,
old_data_reuse=false
```

## Simulator script minimum behavior

A simulator `collect.py` must:

1. Read `startup_command` or equivalent runtime instructions from config/card evidence.
2. Start the simulator or create a new simulator session unless the source is marked `NEEDS_RUNTIME`.
3. Generate a new `run_id` or `session_id`.
4. Record pre-existing output files before collection.
5. Count only files produced by the current run/session.
6. Never copy data from another workspace, old `collected_data`, Downloads, cache, or undeclared external folder.
7. On runtime failure, write logs and exit non-zero; do not create fake images.

## Existing dataset script minimum behavior

An `ingest.py` must preserve at least one traceability proof per sample: original ID, original path, file size, file hash, or manifest row.

## Real data script minimum behavior

A `register.py` must preserve original image path or registration row and record license/privacy uncertainty as raw metadata, not as a deletion rule.

## DATA_SCHEMA.md

Write a concise schema document covering:

- fixed directory layout
- required JSON fields
- required manifest fields
- source-specific fields
- accepted source status values
- raw-only prohibitions

## Forbidden

- No one-script-only solution for all sources unless each source still has its own entrypoint directory and config.
- No placeholder/dummy/mock/example samples.
- No writing under `BENCHCLAW_ROOT`.
- No cleaning or filtering code.
