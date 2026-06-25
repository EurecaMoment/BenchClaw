---
name: benchclaw-stage4-per-template-batch-synthesis
description: Use for the specific BenchClaw subskill `stage4-per-template-batch-synthesis` only when its parent node explicitly dispatches to it.
---

## Opencode 子 agent 触发契约

本文件是 BenchClaw child skill module。父级 stage、node 或 pipeline 调度到本文件时，必须通过 opencode 命令 `/benchclaw-subskill` 启动隔离子 agent；该命令在 `BENCHCLAW_ROOT/opencode.json` 中配置为 `subtask: true`，并绑定 `mode: "subagent"` 的 `child-skill-module-runner`。禁止父级 manager 直接在自己的对话上下文中内联执行本文件步骤。

调用 `/benchclaw-subskill` 时必须传入：目标 `SKILL.md` 绝对路径、注册 skill 名、冻结的 `PROJECT_ROOT` / `BENCHCLAW_ROOT` / `WORKSPACE_PARENT` / `WORKSPACE_ROOT`、当前 node 或 work_unit id、已满足的输入 artifact 路径、期望输出 artifact 路径、父级 DAG 依赖与完成判据。子 agent 只返回 `status`、artifact 路径、证据摘要和 blockers，不回灌长日志或完整中间内容。

如果当前执行上下文不是 `/benchclaw-subskill` 产生的 `child-skill-module-runner` 子 agent，本文件不得继续执行；应立即返回 `BLOCKED`，说明必须由父级使用 `/benchclaw-subskill` 重新派发。

# Subskill — 每模板小批量合成

## 目标

逐模板调用 `data_20_template_metric_code_bundle/scripts/generate_items.py`，真实生成灰度 item，并记录失败、过滤和 0 产出模板。该 subskill 不写最终 benchmark。

## 推荐命令

```bash
python scripts/per_template_batch_synthesis.py \
  --bundle "$WORKSPACE_ROOT/stage4/artifacts/data_20_template_metric_code_bundle" \
  --out-dir "$WORKSPACE_ROOT/stage4/artifacts/data_21_grey_validation_report/per_template_batch" \
  --limit-per-template 8 \
  --seed 20260601
```

## 输出

```text
per_template_batch/generated_items.jsonl
per_template_batch/filtered_items.jsonl
per_template_batch/template_status.csv
per_template_batch/synthesis_manifest.json
per_template_batch/per_template/<template_id>/items.jsonl
per_template_batch/per_template/<template_id>/filtered_items.jsonl
per_template_batch/per_template/<template_id>/stdout.log
per_template_batch/per_template/<template_id>/stderr.log
```

## 规则

- 必须调用 bundle 内 `generate_items.py`，不得手写或伪造 item。
- 每个 enabled 模板独立运行，0 产出要写入 `template_status.csv`。
- 整个批次不能全部 0 产出。
