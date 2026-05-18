# BenchClaw Stage5 Skill: Evaluation and Evaluation Report

## Purpose
This skill executes **Stage5** of the BenchClaw pipeline exactly as shown in the handwritten Stage5 diagram:

```text
Stage5: 评测  ->  评测报告
        38        39
```

This stage is intentionally short. Do **not** invent extra branches, gray tests, small-batch synthesis, data cleaning, or template rewriting in Stage5. Those belong to earlier stages.

## DAG Contract

Stage5 consumes the final Stage4 benchmark package from node **37** as an external input, then executes:

```text
L0: 38-evaluation-run
L1: 39-evaluation-report
```

The dependency is strict:

```text
37 external input -> 38 -> 39
```

Node **39** may only read the normalized outputs of node **38**. It must not directly bypass node 38 to reinterpret Stage4 artifacts.

## Required External Input
Expected Stage4 handoff directory:

```text
WORKSPACE_ROOT/stage4/37-benchmark-artifact-pack/
```

Minimum required files:

```text
EVALSET_DATASET/eval_dataset.jsonl
EVALSET_DATASET/metric_registry.json
EVALSET_DATASET/answer_programs.py
FINAL_BENCHMARK_CARD.md
DONE.json
```

If the exact filenames differ, node 38 must create a local `input_mapping.yaml` explaining the mapping before evaluation starts; it must not rewrite Stage4 artifacts.

## Stage5 Outputs

```text
WORKSPACE_ROOT/stage5/38-evaluation-run/
  eval_results.json
  prediction_logs.jsonl
  failure_cases.jsonl
  report_payload.json
  run_config.yaml
  DONE.json

WORKSPACE_ROOT/stage5/39-evaluation-report/
  report.md
  leaderboard.csv
  per_dimension.csv
  error_analysis.md
  DONE.json
```

## Opencode Execution Rules

1. Run `scripts/validate_dag.py` before executing the stage.
2. Run `scripts/ready_set_runner.py --workspace WORKSPACE_ROOT` to determine executable nodes.
3. Execute node 38 first.
4. Execute node 39 only after node 38 has emitted `DONE.json`.
5. Do not allow node 39 to read Stage4 files directly. Node 38 must package all required evidence into `report_payload.json`.
6. Finish by running `scripts/check_stage5_outputs.py --workspace WORKSPACE_ROOT`.

## Child Skills

- `skills/38-evaluation-run/SKILL.md`
- `skills/39-evaluation-report/SKILL.md`

## Non-negotiable Constraints

- Stage5 has only two subprocesses: evaluation and report generation.
- Node 39 depends only on node 38.
- No direct model-result fabrication is allowed.
- All scored answers must come from model predictions, model API calls, or already materialized prediction files.
- All metrics must be reproducible from logged predictions and scoring scripts.
