# 38-evaluation-run

全局路径约束：`BENCHCLAW_ROOT` 仅作只读输入；`WORKSPACE_ROOT` 是本次流程唯一总工作目录，所有写操作和流程产物只能落在其下。

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
EVALSET_DATASET/README.md
EVALSET_DATASET/data/test.jsonl
EVALSET_DATASET/images/
EVALSET_DATASET/metrics/evaluate.py
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
WORKSPACE_ROOT/stage5/stage5.db
prediction_logs.sqlite_export.jsonl
failure_cases.sqlite_export.jsonl
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

When Stage5 performs real model calls itself, it must use `BENCHCLAW_ROOT/modelNeedMeasured/yeysai_multimodal_client.py` and the fixed candidate roster in `BENCHCLAW_ROOT/modelNeedMeasured/model_roster.yaml`.

## Additional Hard Constraints

- Do not simulate predictions, scores, missing cases, leaderboard values, or failure patterns.
- Do not derive predictions from `item_id`, hashes, templates, expected difficulty, or any handcrafted heuristic.
- If no real model API output or no already materialized prediction file is available, this node must fail/block and must not emit a completion marker.
- If the Stage4 artifact pack is not self-contained enough to resolve media and metric inputs inside the workspace, this node must fail/block rather than guessing or rewriting the benchmark.
- For image-based eval items, node 38 must send real multimodal requests to `https://yeysai.com/v1/chat/completions` using the required model roster from `modelNeedMeasured`; it must not degrade such items to text-only unless the item truly has no image/media refs.
- Node 38 must evaluate all required candidate models: `qwen3-vl-235b-a22b-instruct`, `kimi-k2.5`, `llama-4-maverick-17b-128e-instruct`, `grok-4-fast`, `gpt-5.4-mini-2026-03-17`, `glm-4.5v`, `gemini-3-flash-preview`, `claude-haiku-4-5-20251001-thinking`, `claude-sonnet-4-5-20250929`.

规范真相源应把样本级预测、失败样本、调用统计与聚合结果写入 `stage5.db`；`prediction_logs.sqlite_export.jsonl` 与 `failure_cases.sqlite_export.jsonl` 仅作为兼容性导出。

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
