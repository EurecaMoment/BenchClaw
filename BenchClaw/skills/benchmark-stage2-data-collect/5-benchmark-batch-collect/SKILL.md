---
name: benchmark-batch-collect
description: "Stage 2 Phase 5 dispatcher. 生成 source_jobs，并为每个 source 启动 benchmark-source-collect-worker subagent 并行采集/接入/登记；聚合 source_results。"
argument-hint: [workspace-root]
allowed-tools: Bash(*), Read, Write, Edit, Grep, Glob, Skill
---

# Phase 5 — Batch collect dispatcher with per-source subagents

## Purpose

This skill is a dispatcher and aggregator. It must not personally execute all source collection work. It creates one job per enabled source and dispatches one `benchmark-source-collect-worker` subagent per job.

## Inputs

```text
WORKSPACE_ROOT/stage2/source_plan.jsonl
WORKSPACE_ROOT/stage2/DATA_SCHEMA.md
WORKSPACE_ROOT/stage2/source_runs/{source_type}/{source_name}/config.yaml
WORKSPACE_ROOT/stage2/source_runs/{source_type}/{source_name}/run_source.sh
WORKSPACE_ROOT/stage2/source_runs/{source_type}/{source_name}/{collect.py|ingest.py|register.py}
WORKSPACE_ROOT/stage2/templates/{source_type}__{source_name}.yaml
```

## Required directories

Create if missing:

```text
stage2/source_jobs/
stage2/source_results/
stage2/logs/
stage2/collected_data/
stage2/status/
```

## Job creation

For every row in `source_plan.jsonl`, write:

```text
stage2/source_jobs/{job_id}.json
```

Job JSON schema:

```json
{
  "job_id": "source_type__source_name",
  "workspace_root": "...",
  "source_type": "simulator|existing_dataset|real_data",
  "source_name": "...",
  "enabled": true,
  "status_before_collect": "READY|NEEDS_CARD|NEEDS_CARD_DETAIL|NEEDS_USER_INPUT|BLOCKED",
  "source_role": "...",
  "capability_dimensions": [],
  "stage1_requirement_refs": [],
  "card_path": "...",
  "config_path": "stage2/source_runs/source_type/source_name/config.yaml",
  "script_path": "stage2/source_runs/source_type/source_name/collect.py|ingest.py|register.py",
  "template_path": "stage2/templates/source_type__source_name.yaml",
  "output_root": "stage2/collected_data/source_type/source_name",
  "result_path": "stage2/source_results/job_id.json",
  "log_root": "stage2/logs/job_id",
  "no_placeholder": true,
  "no_cleaning": true,
  "no_filtering": true,
  "old_data_reuse_allowed": false,
  "requires_subagent": true
}
```

If a source is blocked before execution, still create a job and dispatch a worker; the worker should write a blocked result without fabricating data.

## Mandatory subagent dispatch

Dispatch all source jobs as independent worker tasks:

```text
Skill: benchmark-source-collect-worker
Argument: WORKSPACE_ROOT/stage2/source_jobs/{job_id}.json
```

Rules:

- Start one worker subagent per source job.
- Dispatch all independent jobs before aggregating results.
- If the runtime supports true parallel subagents, use it. Do not serialize by choice.
- If the runtime only supports sequential Skill calls, still call the worker skill once per source job and mark `parallel_mode=sequential_fallback` in the report.
- The dispatcher must not bypass the worker by directly running all scripts itself.

## Aggregation

After workers finish, read every `stage2/source_results/{job_id}.json` and aggregate into `RAW_DATA_COLLECTION_REPORT.md`.

Result status values:

```text
PASS
PARTIAL
NEEDS_RUNTIME
NEEDS_CARD
NEEDS_CARD_DETAIL
NEEDS_USER_INPUT
BLOCKED
FAIL
NEEDS_REVIEW
```

`RAW_DATA_COLLECTION_REPORT.md` must contain:

```text
# Raw Data Collection Report
## Dispatch Summary
- parallel_mode: true_parallel | sequential_fallback | unavailable
- total_jobs
- worker_skill: benchmark-source-collect-worker

## Source Results Table
| Job ID | Type | Source | Status | Samples | Result Path | Log Root |

## Simulator Runtime Evidence
## Existing Dataset Ingestion Evidence
## Real Data Registration Evidence
## Failed Or Blocked Sources
## Placeholder / Old-Data Reuse Checks
## Collected Data Layout
## Next Action
```

Write `stage2/status/phase5_batch_collect.json`.

## Success criteria

Phase 5 is:

- `PASS`: every ready source produced valid raw data or a legitimate empty/access-limited result, and no placeholder/old-data reuse was detected.
- `PARTIAL`: at least one source succeeded and at least one source needs runtime/card/user input.
- `FAIL`: scripts fabricated data, used old data as current, wrote to `BENCHCLAW_ROOT`, or produced untraceable samples.

## Forbidden

- No dummy/mock/example images.
- No copying samples from other workspaces or old `collected_data`.
- No deleting raw samples due to low quality or missing GT.
- No cleaning or filtering.
- No writing under `BENCHCLAW_ROOT`.
