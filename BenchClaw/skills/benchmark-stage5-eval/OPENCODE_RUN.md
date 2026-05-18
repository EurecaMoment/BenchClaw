# Opencode Run Guide for BenchClaw Stage5

## Objective
Run final benchmark evaluation and generate the Stage5 evaluation report.

## Canonical DAG

```text
External Stage4 node 37
        |
        v
38-evaluation-run
        |
        v
39-evaluation-report
```

This DAG is serial because the user's Stage5 diagram contains only `评测 -> 评测报告`. Do not parallelize it and do not add unrequested nodes.

## Recommended Commands

```bash
python scripts/validate_dag.py
python scripts/ready_set_runner.py --workspace WORKSPACE_ROOT
```

Then execute:

```bash
# 1. Run 38-evaluation-run according to skills/38-evaluation-run/SKILL.md
# 2. Run 39-evaluation-report according to skills/39-evaluation-report/SKILL.md
```

Final check:

```bash
python scripts/check_stage5_outputs.py --workspace WORKSPACE_ROOT
```

## Guardrail

Node 39 must not directly inspect:

```text
WORKSPACE_ROOT/stage4/37-benchmark-artifact-pack/
```

If report generation needs Stage4 metadata, node 38 must have copied or summarized it into:

```text
WORKSPACE_ROOT/stage5/38-evaluation-run/report_payload.json
```
