---
name: benchmark-stage2-data-collect
description: "Stage 2 pipeline orchestrator. 从 Stage 1 产物出发，完成数据能力调研、采集计划、raw schema、逐源脚本生成、subagent 并行采集、单元测试；只产出原始数据与问题标记，不做清洗/过滤/拒收。"
argument-hint: [workspace-root-or-stage1-dir]
allowed-tools: Bash(*), Read, Write, Edit, Grep, Glob, Skill
---

# Stage 2 Pipeline: raw data collection with parallel subagents

## 0. Non-negotiable contract

This skill is an orchestrator. It must run the Stage 2 phases in order and must not replace subskills with free-form reasoning.

Hard constraints:

- `BENCHCLAW_ROOT` is read-only. It may be read for cards/templates only. Never write logs, cache, data, reports, scripts, patches, or temp files under it.
- `WORKSPACE_ROOT` is the active benchmark workspace. If the argument points to `stage1/`, use its parent. If it points to a workspace root, use it directly. Do not create a new `workspace{i}` and do not reuse another workspace.
- All Stage 2 outputs go under `WORKSPACE_ROOT/stage2/`.
- Stage 2 is raw-only: no cleaning, dedup deletion, quality filtering, confidence threshold rejection, Stage 4 readiness filtering, or synthetic placeholder samples.
- Enabled source types are exactly: `simulator`, `existing_dataset`, `real_data`.
- Every enabled source must be traceable to Stage 1 requirements and to a read-only source card, or be explicitly marked `NEEDS_CARD`, `NEEDS_CARD_DETAIL`, or `NEEDS_USER_INPUT`.
- Simulator sources must create a new runtime/session/run before samples can count as successfully collected. Old images, old JSON, cache, or other workspace data must not be counted.
- After writing `stage2/STAGE2_SUMMARY.md`, stop. Do not enter Stage 3.

## 1. Required Stage 1 inputs

Before any phase call, verify that these files exist:

```text
stage1/CAPABILITY_SCOPE.md
stage1/DATA_SOURCE_MAPPING.md
stage1/BENCHMARK_DRAFT.md
stage1/EVALSET_PROTOTYPE.md
stage1/EXECUTION_PLAN.md
```

If any required file is missing, stop and write `stage2/PIPELINE_BLOCKED.md` listing missing paths. Do not invent Stage 1 content.

## 2. Canonical Stage 2 outputs

The pipeline is successful only if these artifacts are produced or a blocking report explains why they cannot be produced:

```text
stage2/SOURCE_CAPABILITY_SURVEY.md
stage2/source_inventory.jsonl
stage2/COLLECTION_GUIDANCE_PLAN.md
stage2/source_plan.jsonl
stage2/TEMPLATE_REFINEMENT_REPORT.md
stage2/templates/*.yaml
stage2/DATA_SCHEMA.md
stage2/source_runs/{source_type}/{source_name}/...
stage2/source_jobs/*.json
stage2/source_results/*.json
stage2/collected_data/{source_type}/{source_name}/images/
stage2/collected_data/{source_type}/{source_name}/records/
stage2/collected_data/{source_type}/{source_name}/manifest.jsonl
stage2/RAW_DATA_COLLECTION_REPORT.md
stage2/unit_tests/test_stage2_contract.py
stage2/unit_tests/results.json
stage2/STAGE2_UNIT_TEST_REPORT.md
stage2/STAGE2_SUMMARY.md
stage2/status/*.json
```

If a source is blocked, its result file is still required and must contain the blocking status and reason.

## 3. Pipeline execution order

Create `stage2/status/` first. After each phase, write a small JSON status file:

```json
{"phase":"phase_name","status":"PASS|PARTIAL|BLOCKED|FAIL","inputs":[],"outputs":[],"notes":[]}
```

Run exactly these phase skills in order:

### Phase 1 — source capability survey

Call skill `benchmark-data-capability-survey` with argument `WORKSPACE_ROOT`.

Expected outputs:

```text
stage2/SOURCE_CAPABILITY_SURVEY.md
stage2/source_inventory.jsonl
stage2/status/phase1_survey.json
```

### Phase 2 — collection guidance

Call skill `benchmark-collection-guidance` with argument `WORKSPACE_ROOT`.

Expected outputs:

```text
stage2/COLLECTION_GUIDANCE_PLAN.md
stage2/source_plan.jsonl
stage2/status/phase2_guidance.json
```

### Phase 3 — raw template refinement

Call skill `benchmark-template-refinement` with argument `WORKSPACE_ROOT`.

Expected outputs:

```text
stage2/TEMPLATE_REFINEMENT_REPORT.md
stage2/templates/*.yaml
stage2/template_index.jsonl
stage2/status/phase3_templates.json
```

### Phase 4 — source script generation

Call skill `benchmark-collect-codegen` with argument `WORKSPACE_ROOT`.

Expected outputs:

```text
stage2/DATA_SCHEMA.md
stage2/source_runs/{source_type}/{source_name}/README.md
stage2/source_runs/{source_type}/{source_name}/config.yaml
stage2/source_runs/{source_type}/{source_name}/{collect.py|ingest.py|register.py}
stage2/status/phase4_codegen.json
```

### Phase 5 — batch collect through subagents

Call skill `benchmark-batch-collect` with argument `WORKSPACE_ROOT`.

This phase must dispatch one `benchmark-source-collect-worker` subagent per enabled source job. The current agent must act as dispatcher/aggregator, not as the worker for all sources.

Expected outputs:

```text
stage2/source_jobs/*.json
stage2/source_results/*.json
stage2/collected_data/...
stage2/RAW_DATA_COLLECTION_REPORT.md
stage2/status/phase5_batch_collect.json
```

### Phase 6 — Stage 2 unit test

Call skill `benchmark-unit-test-stage2` with argument `WORKSPACE_ROOT`.

Expected outputs:

```text
stage2/unit_tests/test_stage2_contract.py
stage2/unit_tests/results.json
stage2/STAGE2_UNIT_TEST_REPORT.md
stage2/status/phase6_unit_test.json
```

## 4. Final summary

After Phase 6, write `stage2/STAGE2_SUMMARY.md` with:

- workspace root
- total enabled sources by type
- source statuses: `PASS`, `PARTIAL`, `NEEDS_RUNTIME`, `NEEDS_CARD`, `NEEDS_USER_INPUT`, `FAIL`
- number of collected raw samples by source
- collected data root
- whether subagent dispatch was used
- unit test verdict
- exact next-step instruction: Stage 2 stops here; Stage 3 must be invoked separately.

Do not continue beyond this summary.
