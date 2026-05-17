---
name: benchmark-unit-test-stage2
description: "Stage 2 Phase 6. 生成并运行契约测试：phase 产物、subagent job/result、raw layout、manifest、card traceability、simulator 新 run 证据、raw-only 禁令。"
argument-hint: [workspace-root]
allowed-tools: Bash(*), Read, Write, Edit, Grep, Glob
---

# Phase 6 — Stage 2 contract unit test

## Purpose

Generate and execute `stage2/unit_tests/test_stage2_contract.py`. The test should validate the Stage 2 contract, not model quality.

## Inputs

```text
WORKSPACE_ROOT/stage2/source_inventory.jsonl
WORKSPACE_ROOT/stage2/source_plan.jsonl
WORKSPACE_ROOT/stage2/template_index.jsonl
WORKSPACE_ROOT/stage2/DATA_SCHEMA.md
WORKSPACE_ROOT/stage2/source_jobs/*.json
WORKSPACE_ROOT/stage2/source_results/*.json
WORKSPACE_ROOT/stage2/RAW_DATA_COLLECTION_REPORT.md
WORKSPACE_ROOT/stage2/collected_data/
```

## Test file

Write:

```text
stage2/unit_tests/test_stage2_contract.py
```

The test must check at least these assertions:

### 1. Required phase artifacts

Required files exist:

```text
SOURCE_CAPABILITY_SURVEY.md
source_inventory.jsonl
COLLECTION_GUIDANCE_PLAN.md
source_plan.jsonl
TEMPLATE_REFINEMENT_REPORT.md
template_index.jsonl
DATA_SCHEMA.md
RAW_DATA_COLLECTION_REPORT.md
```

### 2. Source plan to job/result completeness

For every enabled source in `source_plan.jsonl`:

- a job JSON exists in `source_jobs/`
- a result JSON exists in `source_results/`
- result contains `worker_skill=benchmark-source-collect-worker`
- result status is one of the allowed values

### 3. Subagent dispatch evidence

`RAW_DATA_COLLECTION_REPORT.md` must contain:

- `Dispatch Summary`
- `worker_skill: benchmark-source-collect-worker`
- `parallel_mode`

### 4. Fixed raw layout

For each result with counted samples:

```text
collected_data/{source_type}/{source_name}/images/
collected_data/{source_type}/{source_name}/records/
collected_data/{source_type}/{source_name}/manifest.jsonl
```

No town/scene/shard/split subdirectories may replace the fixed `images/` and `records/` directories.

### 5. Image/JSON/manifest consistency

For each counted sample:

- image exists and is non-empty
- same-ID record JSON exists
- manifest path fields point to real files
- required fields are non-empty

### 6. Source card traceability

For ready/successful sources:

- `source_card_path` exists
- path belongs to the correct read-only card root
- scripts/configs/results reference the same source card

For missing-card sources, status must be `NEEDS_CARD`, `NEEDS_CARD_DETAIL`, `NEEDS_USER_INPUT`, or `BLOCKED`; they must not be marked `PASS`.

### 7. Simulator current-run evidence

For successful simulator sources:

- `simulator_started_at` exists
- `simulator_start_command` exists
- `run_id` or `session_id` exists
- `frame_id` exists for counted samples
- `current_run_only` is true
- `old_data_reuse` is false

### 8. Placeholder and old-data ban

Scan scripts, configs, manifests, records, reports, and results for forbidden placeholder tokens when used as sample evidence:

```text
placeholder, dummy, mock, fake, todo, example_only, replace_me
```

Also fail if counted sample paths point to another workspace, old `collected_data`, Downloads, cache, or undeclared external directories.

### 9. Raw-only boundary

Fail if Stage 2 artifacts contain cleaning/filtering actions such as:

```text
delete low quality, quality threshold rejection, deduplicate and remove,
cleaned_data, filter_out, stage3 cleaning, readiness filtering
```

This is a semantic scan: do not fail mere mentions inside explicit prohibition sections.

### 10. BENCHCLAW_ROOT read-only

Fail if any script/config/report plans to write logs/cache/temp/output/data under `BENCHCLAW_ROOT`.

## Outputs

Run the test and write:

```text
stage2/unit_tests/results.json
stage2/STAGE2_UNIT_TEST_REPORT.md
stage2/status/phase6_unit_test.json
```

`results.json` schema:

```json
{
  "verdict": "PASS|PARTIAL|FAIL",
  "checks": [],
  "failures": [],
  "warnings": [],
  "tested_at": "..."
}
```

`STAGE2_UNIT_TEST_REPORT.md` must include:

```text
# Stage 2 Unit Test Report
## Verdict
## Checks Passed
## Failures
## Warnings
## Source-Level Summary
## Required Fixes Before Stage 3
```

## Verdict rules

- `PASS`: all required contract checks pass.
- `PARTIAL`: pipeline is structurally valid but some sources legitimately need runtime/card/user input.
- `FAIL`: missing core artifacts, invalid manifest, untraceable samples, placeholder/old-data reuse, simulator without new run evidence marked as success, or writes under `BENCHCLAW_ROOT`.
