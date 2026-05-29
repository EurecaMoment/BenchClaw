# BenchClaw Stage5 Skill: Evaluation and Evaluation Report

全局路径约束：`BENCHCLAW_ROOT` 仅作只读输入；`WORKSPACE_ROOT` 是本次流程唯一总工作目录，所有写操作和流程产物只能落在其下。

## 路径入口校验

开始执行前必须先确认：

- 本次收到的 `BENCHCLAW_ROOT` 与 `WORKSPACE_ROOT` 与上游 pipeline 冻结值完全一致，不得在 Stage5 内重新推导。
- `BENCHCLAW_ROOT` 必须仍然解析为当前 BenchClaw 项目根目录。
- `WORKSPACE_ROOT` 必须是独立于 `BENCHCLAW_ROOT` 的外部工作目录，不能位于 `BENCHCLAW_ROOT` 内，不能等于 `BENCHCLAW_ROOT`，不能写成 `BENCHCLAW_ROOT/workspace*`。
- 若路径校验失败，Stage5 必须立即阻塞并报错，不能继续读取 Stage4 或写任何 Stage5 输出。

## Purpose
This skill executes **Stage5** of the BenchClaw pipeline exactly as shown in the handwritten Stage5 diagram:

Stage5 的内部结构化真相源统一使用 JSONL。推荐主库位置：

```text
WORKSPACE_ROOT/stage5/38-evaluation-run/eval_results.json
```

模型调用、预测、失败样本、聚合分数、报告载荷等都应以 JSONL 表为准；`prediction_logs.jsonl`、`failure_cases.jsonl`、`leaderboard.csv` 等只保留为导出或报告面向的副本。

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
EVALSET_DATASET/README.md
EVALSET_DATASET/data/test.jsonl
EVALSET_DATASET/images/
EVALSET_DATASET/metrics/evaluate.py
FINAL_BENCHMARK_CARD.md
DONE.json
```

Model roster and API calling contract must come from:

```text
BENCHCLAW_ROOT/modelNeedMeasured/model_roster.yaml
BENCHCLAW_ROOT/modelNeedMeasured/SKILL.md
BENCHCLAW_ROOT/modelNeedMeasured/yeysai_multimodal_client.py
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
- Stage5 must evaluate the full fixed candidate roster declared in `BENCHCLAW_ROOT/modelNeedMeasured/model_roster.yaml`; it must not silently subset, replace, or rename the required models.
- All metrics must be reproducible from logged predictions and scoring scripts.
- No simulated, pseudo-random, rule-based, hash-based, or manually fabricated predictions/scores are allowed. If real model outputs are unavailable, Stage5 must block instead of reporting completion.
