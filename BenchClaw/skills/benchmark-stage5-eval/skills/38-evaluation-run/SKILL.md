# 38-evaluation-run

## Role
Execute model evaluation on the final Stage4 benchmark package and produce machine-readable evaluation results.

## Parents

```text
external parent: 37-benchmark-artifact-pack
```

## Inputs
Allowed input root:

```text
WORKSPACE_ROOT/stage4/37-benchmark-artifact-pack/
```

Expected artifacts:

```text
EVALSET_DATASET/eval_dataset.jsonl
EVALSET_DATASET/metric_registry.json
EVALSET_DATASET/answer_programs.py
model_roster.yaml or equivalent model list
FINAL_BENCHMARK_CARD.md
DONE.json
```

## Outputs
Write only to:

```text
WORKSPACE_ROOT/stage5/38-evaluation-run/
```

Required outputs:

```text
eval_results.json
prediction_logs.jsonl
failure_cases.jsonl
report_payload.json
run_config.yaml
DONE.json
```

## Required Procedure

1. Validate Stage4 handoff completeness.
2. Load the eval dataset and scoring specification.
3. Run target models or consume already materialized prediction files.
4. Score every sample with the declared metric code or the generic scorer.
5. Emit full prediction logs.
6. Emit failure cases, grouped by model and capability dimension.
7. Package all report-facing metadata into `report_payload.json` so node 39 does not need to read Stage4 directly.
8. Write `DONE.json` only after all required outputs exist.

## Reproducibility Requirements

Every evaluated model must have:

```text
model_name
model_version_or_endpoint
run_time
sample_count
missing_count
scoring_method
prediction_log_path
```

Every prediction log row must include:

```json
{
  "sample_id": "...",
  "model": "...",
  "prediction": "...",
  "gold": "...",
  "score": 0.0,
  "dimension": "...",
  "metadata": {}
}
```

## Hard Constraints

- Do not fabricate model answers.
- Do not silently drop invalid samples.
- If model calls fail, log the failure and compute `missing_count`.
- Do not modify the Stage4 eval dataset.
- Do not generate the final prose report here; that is node 39.
