---
name: benchclaw-stage4-invalid-item-screening
description: Use for the specific BenchClaw subskill `stage4-invalid-item-screening` only when its parent node explicitly dispatches to it.
---

## Opencode 子 agent 触发契约

本文件是 BenchClaw child skill module。父级 stage、node 或 pipeline 调度到本文件时，必须通过 opencode 命令 `/benchclaw-subskill` 启动隔离子 agent；该命令在 `BENCHCLAW_ROOT/opencode.json` 中配置为 `subtask: true`，并绑定 `mode: "subagent"` 的 `child-skill-module-runner`。禁止父级 manager 直接在自己的对话上下文中内联执行本文件步骤。

调用 `/benchclaw-subskill` 时必须传入：目标 `SKILL.md` 绝对路径、注册 skill 名、冻结的 `PROJECT_ROOT` / `BENCHCLAW_ROOT` / `WORKSPACE_PARENT` / `WORKSPACE_ROOT`、当前 node 或 work_unit id、已满足的输入 artifact 路径、期望输出 artifact 路径、父级 DAG 依赖与完成判据。子 agent 只返回 `status`、artifact 路径、证据摘要和 blockers，不回灌长日志或完整中间内容。

如果当前执行上下文不是 `/benchclaw-subskill` 产生的 `child-skill-module-runner` 子 agent，本文件不得继续执行；应立即返回 `BLOCKED`，说明必须由父级使用 `/benchclaw-subskill` 重新派发。

# Subskill — 无效题筛除

## 目标

在任何模型评测或全量合成前，筛掉媒体缺失、答案缺失、选项错误、评分契约缺失、题干泄漏 GT 或证据不可追溯的 item。

## 推荐命令

```bash
python scripts/screen_invalid_items.py \
  --items artifacts/data_21_grey_validation_report/per_template_batch/generated_items.jsonl \
  --out-dir artifacts/data_21_grey_validation_report/invalid_item_screening \
  --workspace-root "$WORKSPACE_ROOT" \
  --require-media
```

## 检查项

- `question` 非空，且不含 object_id、bbox、mask、depth_median、metadata、annotation、无法判断等泄漏/不可答表达。
- `answer` 存在，choice 类答案必须在 options 中。
- options 文本不得重复；重复是 error，不是 warning。
- `media` 真实存在且非空，可解码时必须可解码。
- `template_id`、`metric_id`、追溯字段存在。
- hidden audit 中必须有 `answerability_proof` 或等价字段；proof 必须指向模型可见媒体和 visible anchor。若题目消费 depth、pose、coordinate、trajectory、bbox/mask、area、object id 等 private GT，而 proof 只写 raw RGB/safe copy，判为 error。
- 媒体必须通过信息量检查：全黑、全白、近空、极小、低方差图像默认 invalid，除非 Stage4 plan 明确该任务就是检测空白/遮挡。
- choice 题的候选项必须来自同一候选空间；固定 fallback、从不为正确答案的 distractor、格式异常选项、或答案可由表面缺陷推断，均为 error。

## 输出

```text
invalid_item_screening/valid_items.jsonl
invalid_item_screening/invalid_items.jsonl
invalid_item_screening/item_level_findings.jsonl
invalid_item_screening/template_status.csv
invalid_item_screening/screening_report.json
```

## 阻塞条件

- 输入不存在或为空。
- 所有 item invalid。
- valid 集仍含 error 级 finding。
