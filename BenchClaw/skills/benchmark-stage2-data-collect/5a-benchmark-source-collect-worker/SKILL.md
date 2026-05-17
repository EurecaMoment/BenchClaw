---
name: benchmark-source-collect-worker
description: "Stage 2 Phase 5 worker. 单个 source 的 subagent：读取 source_job，执行对应 collect/ingest/register 脚本，校验 raw 产物，写 source_results。"
argument-hint: [source-job-json]
allowed-tools: Bash(*), Read, Write, Edit, Grep, Glob
---

# Source collect worker

## Role

You are a per-source worker subagent. Handle exactly one source job. Do not process other sources.

## Input

The argument is the absolute or workspace-relative path to one job JSON:

```text
stage2/source_jobs/{job_id}.json
```

Read the job JSON first. If it is missing or malformed, write a `FAIL` result if possible.

## Preflight

Before running any script, verify:

- `workspace_root` exists.
- `config_path`, `script_path`, and `template_path` exist for ready jobs.
- `card_path` exists for ready jobs and belongs to the correct card root.
- Output, log, temp, cache, and result paths are under `WORKSPACE_ROOT/stage2/`.
- The script/config does not plan to write under `BENCHCLAW_ROOT`.
- `no_placeholder=true`, `no_cleaning=true`, `no_filtering=true`, `old_data_reuse_allowed=false`.

If `status_before_collect` is not `READY`, do not run scripts. Write a blocked result with the same status and the reason.

## Execute

Run exactly the source script specified by `script_path`:

```bash
python <script_path> --workspace-root <WORKSPACE_ROOT> --config <config_path> --job-json <job_json>
```

Source-type semantics:

- `simulator`: the script must start a simulator or create a new run/session and record runtime evidence. If it cannot, return `NEEDS_RUNTIME` or `FAIL`; never create fake images.
- `existing_dataset`: ingest/copy/hardlink/register real existing data and preserve original ID/path/hash/manifest row.
- `real_data`: register real images/records and preserve original path/registration row/license/privacy fields.

Capture command, start time, end time, exit code, stdout/stderr path, and generated file counts.

## Validate output

Check the fixed layout:

```text
output_root/images/
output_root/records/
output_root/manifest.jsonl
```

For counted samples:

- every image has a same-ID JSON record
- every manifest row points to existing image and record files
- required fields are non-empty: `sample_id`, `source_type`, `source_name`, `capability_dimension`, `source_role`, `image_path`, `record_json_path`, `original_source_ref`, `source_card_path`
- filenames, paths, JSON, manifest, and logs do not contain placeholder tokens: `placeholder`, `dummy`, `mock`, `fake`, `todo`, `example_only`, `replace_me`
- no path points to another workspace, old `collected_data`, Downloads, cache, or undeclared external directory
- no script output wrote under `BENCHCLAW_ROOT`

Simulator extra validation:

- `simulator_started_at` and `simulator_start_command` are recorded
- `run_id` or `session_id` exists
- `frame_id` exists for counted samples
- `current_run_only` is true
- `old_data_reuse` is false
- file timestamps or runtime logs support current-run provenance when available

Do not delete raw files during validation. Mark problems in the result.

## Result JSON

Always write `result_path` from the job JSON. Schema:

```json
{
  "job_id": "...",
  "source_type": "...",
  "source_name": "...",
  "worker_skill": "benchmark-source-collect-worker",
  "status": "PASS|PARTIAL|NEEDS_RUNTIME|NEEDS_CARD|NEEDS_CARD_DETAIL|NEEDS_USER_INPUT|BLOCKED|FAIL|NEEDS_REVIEW",
  "samples_counted": 0,
  "samples_written_total": 0,
  "output_root": "...",
  "manifest_path": "...",
  "log_root": "...",
  "command": "...",
  "exit_code": null,
  "started_at": "...",
  "ended_at": "...",
  "runtime_evidence": {},
  "traceability_checks": {
    "image_json_pairs": false,
    "manifest_paths_exist": false,
    "source_card_traceable": false,
    "no_placeholder_detected": false,
    "no_old_data_reuse_detected": false,
    "benchclaw_root_readonly_respected": false
  },
  "errors": [],
  "warnings": []
}
```

## Verdict rules

- `PASS`: script succeeded and validation passed for all counted samples.
- `PARTIAL`: some real samples are valid, but some records need review.
- `NEEDS_RUNTIME`: simulator runtime/session cannot be started or verified.
- `NEEDS_CARD`, `NEEDS_CARD_DETAIL`, `NEEDS_USER_INPUT`, `BLOCKED`: source was blocked before execution.
- `NEEDS_REVIEW`: data exists but traceability/license/metadata issues require review.
- `FAIL`: placeholder data, old data reuse, missing required outputs, or writes to `BENCHCLAW_ROOT` are detected.

## Forbidden

Do not process multiple sources. Do not clean/filter/delete raw samples. Do not fabricate data to make the job pass.
