---
name: benchclaw-stage5-eval
description: Use for the BenchClaw skill `stage5-eval` when the workflow is explicitly entering this stage or manager.
---

# Benchmark Stage5 Eval Skill — 模型评测与报告

## 角色

读取 `WORKSPACE_ROOT/EVALSET_DATASET/` 这一份最终完整评测包，完成真实模型评测或读取用户提供的已物化预测文件，生成最终评测报告。

## 关键规则

- 只有本文件 DAG 表中的节点是本阶段节点；编号数据只进入 `artifacts/`，不得进入 `nodes/`。
- 启动本 stage 时，必须接收并复述冻结的 `PROJECT_ROOT`、`BENCHCLAW_ROOT`、`WORKSPACE_PARENT`、`WORKSPACE_ROOT` 实际值，并与 `WORKSPACE_ROOT/path_resolution.json` 对齐。
- 本 stage 只能写入 `WORKSPACE_ROOT/stage5/`。
- 每个节点完成后必须写：`nodes/<node-id>/USED_INPUTS.json`、`nodes/<node-id>/DONE.json`、`nodes/<node-id>/NODE_REPORT.md`。
- 继承总入口和 pipeline 的长任务 `tmux` 执行协议：任何下载、检索、外部工具调用、批处理、模型推理、训练、仿真、清洗、标注或全量评测等可能长时间运行的命令，必须在 `tmux` 会话中执行、写入 `nodes/<node-id>/run_logs/` 并定期监控；未使用 `tmux` 必须在 `NODE_REPORT.md` 说明短任务依据和实际耗时。
- 每个编号数据必须写入：`artifacts/<data-id>/`。
- Stage5 默认且必须以 `WORKSPACE_ROOT/EVALSET_DATASET/` 作为完整评测包入口；该目录必须直接包含完整的评测图像文件、问题、答案/GT 和评测指标代码。若只存在 `stage4/artifacts/data_22_full_benchmark_dataset/` 而 `WORKSPACE_ROOT/EVALSET_DATASET/` 缺失或不完整，Stage5 必须阻塞。
- `WORKSPACE_ROOT/EVALSET_DATASET/` 严禁用链接、URL、symlink、placeholder 文件或目录外路径来冒充图片物料；Stage5 只能消费该目录内部真实落盘的图像文件。
- `WORKSPACE_ROOT/EVALSET_DATASET/data/*.jsonl` 中的图像路径必须统一写成 `./images/...` 这种相对路径格式，供评测包内部直接解析访问；不得写成绝对路径、`images/...`、`../...`、URL 或其它非标准形式。
- `WORKSPACE_ROOT/EVALSET_DATASET/images/` 中的真实图片数量必须与评测集规模大体匹配；允许多图问答或一图多问，但不得只有极少数图片却支撑明显更大规模的数据集。
- 本仓库中的灰度测试与全量测试模型配置必须统一从 `BENCHCLAW_ROOT/modelNeedMeasured/model_config.json` 读取；Stage5 使用其中 `full_test`，不得切换到 `skills/` 目录内的局部模型配置。
- Stage5 完成必须有真实预测或真实模型调用来源，且输出 `evaluation_report.md`、`metrics.json`、`prediction_audit.jsonl`、`error_taxonomy.jsonl` 均非空；不得只用 Stage4 原始 artifact、自然语言摘要或占位目录冒充评测。
- 在写 `stage5/_STAGE_DONE.json` 或向 pipeline 返回 `PASS` 前，必须运行可执行质量门：

```bash
python3 "$BENCHCLAW_ROOT/skills/validate_stage_gate.py" \
  --workspace-root "$WORKSPACE_ROOT" \
  --stage stage5 \
  --report "$WORKSPACE_ROOT/stage5/stage5_gate_report.json"
```

只有该命令退出码为 0 且报告 `status: PASS` 时，才允许写 `_STAGE_DONE.json`；报告路径和摘要必须写入 `_stage_report.md` 与 `_STAGE_DONE.json.quality_gate.validator`。若 validator 失败，必须写 `BLOCKED.json` 与 `BLOCKED.md`，不得写 pipeline 完成标记。
- 缺少必需输入、真实数据、标注结果、GT 或模型输出时，必须写 `BLOCKED.json` 与 `BLOCKED.md`，并停止本 stage。

## Registered Node Skill Names

本 stage 调度 ready 节点时，必须使用下面这些显式 skill 名：

- `full-evaluation` -> `benchclaw-stage5-full-evaluation`

## Node Context Return Protocol

节点返回时只保留：评测状态、报告路径、关键分数摘要、阻塞原因和一句总结。不要回灌全量 prediction log、长错误明细或整份报告正文。

## 输入

- `data_13_execution_plan`
- `data_22_full_benchmark_dataset`
- `WORKSPACE_ROOT/EVALSET_DATASET`
- `BENCHCLAW_ROOT/modelNeedMeasured/model_config.json`

## DAG 节点

| Node ID | 椭圆节点名称 | Parents | 输出数据 |
|---|---|---|---|
| `full-evaluation` | 全量评测 | 无 | `data_23_evaluation_report` |

## Ready-set 调度

1. 从 `dag.json` 读取节点依赖。
2. 每轮选择所有 parents 已完成且未执行的 ready 节点。
3. 对 ready 节点调用对应的已注册 skill 名：`full-evaluation -> benchclaw-stage5-full-evaluation`。
4. 并行分支可以并行处理，但共享输入必须只读，共享输出必须写入各自 artifact 目录。
5. 本 stage 只在所有 terminal artifacts 完成且 `validate_stage_gate.py --stage stage5` 通过后写 `_STAGE_DONE.json` 与 `_stage_report.md`。

## 终端数据

- `data_23_evaluation_report`

## 标准目录

```text
WORKSPACE_ROOT/stage5/
  nodes/<node-id>/
    run_logs/
  artifacts/
  _STAGE_DONE.json
  _stage_report.md
```
