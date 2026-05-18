# 39-evaluation-report

## Role
Generate the final Stage5 evaluation report from node 38 outputs.

## Parents

```text
38-evaluation-run
```

## Inputs
Allowed input root only:

```text
WORKSPACE_ROOT/stage5/38-evaluation-run/
```

Allowed files:

```text
eval_results.json
prediction_logs.jsonl
failure_cases.jsonl
report_payload.json
run_config.yaml
DONE.json
```

## Outputs
Write only to:

```text
WORKSPACE_ROOT/stage5/39-evaluation-report/
```

Required outputs:

```text
report.md
leaderboard.csv
per_dimension.csv
error_analysis.md
DONE.json
```

## Required Procedure

1. Read node 38 `DONE.json`.
2. Load `eval_results.json` and `report_payload.json`.
3. Create a leaderboard table.
4. Create per-dimension performance tables.
5. Summarize refusal, missing, invalid, and failure cases.
6. Generate `error_analysis.md` from `failure_cases.jsonl`.
7. Generate final `report.md`.
8. Write `DONE.json` after all outputs exist.

## Hard Constraints

- This node must not read `WORKSPACE_ROOT/stage4/37-benchmark-artifact-pack/` directly.
- It must not rescore samples.
- It must not change model predictions.
- It must not invent evaluation numbers missing from `eval_results.json`.
