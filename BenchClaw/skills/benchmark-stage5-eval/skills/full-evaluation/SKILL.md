---
name: benchclaw-stage5-full-evaluation
description: Use for the specific BenchClaw node skill `stage5-full-evaluation` only when its parent stage explicitly dispatches to it.
---

# Node Skill — 全量评测

## 输入

- `WORKSPACE_ROOT/EVALSET_DATASET`
- `data_22_full_benchmark_dataset`
- `data_13_execution_plan` 中的评测模型配置
- 用户提供的已物化预测文件，或可实际调用的模型 endpoint 配置

## 处理

1. 优先校验并读取 `WORKSPACE_ROOT/EVALSET_DATASET/`；确认其中包含可直接评测的图文、答案/GT 和指标代码。若该目录缺失、不完整，或与 `data_22_full_benchmark_dataset` 评测语义不一致，必须阻塞。
2. 校验全量 benchmark 数据集、媒体、GT、指标配置和答案程序。
3. 若用户提供预测文件，检查 item_id 覆盖率、模型名、时间戳和预测格式。
4. 若调用模型 endpoint，记录 endpoint 配置、模型名、请求参数、响应日志和失败重试记录。
5. 执行指标计算，生成 overall、capability-wise、source-wise、template-wise、error taxonomy 和可复现评测记录。
6. 缺少真实预测或真实模型调用结果时，必须阻塞，不得生成完成状态。
7. 写 `DONE.json` 前，`USED_INPUTS.json` 与 `NODE_REPORT.md` 必须能追溯真实预测文件或真实模型 endpoint/API 调用记录，并且明确记录本次评测实际消费的 `WORKSPACE_ROOT/EVALSET_DATASET/` 路径；`artifacts/data_23_evaluation_report/metrics.json`、`prediction_audit.jsonl`、`error_taxonomy.jsonl` 必须非空且可解析。
8. Stage5 收口前必须能通过：

```bash
python3 "$BENCHCLAW_ROOT/skills/validate_stage_gate.py" \
  --workspace-root "$WORKSPACE_ROOT" \
  --stage stage5 \
  --report "$WORKSPACE_ROOT/stage5/stage5_gate_report.json"
```

## 输出

- `artifacts/data_23_evaluation_report/evaluation_report.md`
- `artifacts/data_23_evaluation_report/metrics.json`
- `artifacts/data_23_evaluation_report/prediction_audit.jsonl`
- `artifacts/data_23_evaluation_report/error_taxonomy.jsonl`
- 节点执行记录文件
