---
name: benchclaw-stage4-full-synthesis
description: Use for the specific BenchClaw node skill `stage4-full-synthesis` only when its parent stage explicitly dispatches to it.
---

## Opencode 子 agent 触发契约

本文件是 BenchClaw child skill module。父级 stage、node 或 pipeline 调度到本文件时，必须通过 opencode 命令 `/benchclaw-subskill` 启动隔离子 agent；该命令在 `BENCHCLAW_ROOT/opencode.json` 中配置为 `subtask: true`，并绑定 `mode: "subagent"` 的 `child-skill-module-runner`。禁止父级 manager 直接在自己的对话上下文中内联执行本文件步骤。

调用 `/benchclaw-subskill` 时必须传入：目标 `SKILL.md` 绝对路径、注册 skill 名、冻结的 `PROJECT_ROOT` / `BENCHCLAW_ROOT` / `WORKSPACE_PARENT` / `WORKSPACE_ROOT`、当前 node 或 work_unit id、已满足的输入 artifact 路径、期望输出 artifact 路径、父级 DAG 依赖与完成判据。子 agent 只返回 `status`、artifact 路径、证据摘要和 blockers，不回灌长日志或完整中间内容。

如果当前执行上下文不是 `/benchclaw-subskill` 产生的 `child-skill-module-runner` 子 agent，本文件不得继续执行；应立即返回 `BLOCKED`，说明必须由父级使用 `/benchclaw-subskill` 重新派发。

# Node Skill — 全量合成

## 目标

使用通过灰度、通过小批量结果评测、通过 CDM/IRT 诊断、且满足难度配比的模板和运行时生成器合成全量 benchmark，并同时输出审计包 `data_22_full_benchmark_dataset` 与 Stage5 默认消费包 `WORKSPACE_ROOT/EVALSET_DATASET`。

审计包必须包含类似 `/home/maqiang/libero_temporal_benchmark_final` 的通用格式：

```text
audit_format/benchmark_items.jsonl
audit_format/template_registry.json
audit_format/generation_report.json
audit_format/benchmark_assets/
```

这里参考的是格式和质量报告结构，不是要求把所有数据源都做成 LIBERO temporal 任务。模板、能力和 sequence semantics 必须来自当前数据源的 Stage1/Stage3/Stage4 plan。

## 输入

- `data_20_template_metric_code_bundle`
- `data_21_grey_validation_report/invalid_item_screening/valid_items.jsonl`
- `data_21_grey_validation_report/template_status.csv`
- `data_21_grey_validation_report/small_model_eval/score_matrix.jsonl`
- `data_21_grey_validation_report/cdm_irt/cdm_irt_summary.json`
- `data_21_grey_validation_report/difficulty_mix_report.json`
- Stage3 evidence index 或 bundle 内 `evidence_index.jsonl`

## 处理

1. 读取灰度通过模板；fail 模板不得进入全量。
2. 确认 small-batch-result-evaluation 已产出非空 score matrix。
3. 确认 cdm-irt-analysis 已产出非空诊断，且 status 为 `PASS` 或 `LIMITED_PASS`。
4. 确认灰度 valid items 满足难度配比；全量生成后再次检查难度配比。
5. 用 `scripts/generate_items.py` 对全量 evidence 生成 items；小样本场景可直接使用 valid_items 作为 full input，但必须在报告中说明。
6. 如果 bundle 提供 `scripts/one_click_generate_evalset.py`，只能把它作为 `generate_items.py` + `check_difficulty_mix.py` + `package_evalset.py` 的编排入口；不得绕过灰度通过模板、scorer 或泄漏检查。
7. 再运行一次 invalid-item-screening，确保全量 item 无 error。
8. 使用 `scripts/package_evalset.py` 从同一批 full audit items 打包到：

```text
WORKSPACE_ROOT/stage4/artifacts/data_22_full_benchmark_dataset/
WORKSPACE_ROOT/EVALSET_DATASET/
```
   推荐命令形态：

```bash
python scripts/package_evalset.py \
  --bundle data_20_template_metric_code_bundle \
  --items full_items.jsonl \
  --out "$WORKSPACE_ROOT/EVALSET_DATASET" \
  --audit-format-out "$WORKSPACE_ROOT/stage4/artifacts/data_22_full_benchmark_dataset/audit_format"
```

9. 在 `data_22_full_benchmark_dataset` 内保留 `dataset.jsonl` 或 `media/` 兼容旧审计流程时，必须能追溯到同一批 full audit items；不得另起采样。
10. 对 `data_22_full_benchmark_dataset` 和 `WORKSPACE_ROOT/EVALSET_DATASET` 分别运行 `scripts/audit_evalset_quality.py --evalset ...`，两个报告都必须 PASS。`data_22_full_benchmark_dataset/audit_format` 还必须通过 audit-format 自检：asset path 在 `benchmark_assets/`、registry/report 非空、items 保留 answer/provenance/quality_flags。

## 输出契约

`data_22_full_benchmark_dataset` 必须包含：

```text
audit_format/benchmark_items.jsonl
audit_format/template_registry.json
audit_format/generation_report.json
audit_format/benchmark_assets/
dataset.jsonl
media/
data/test.jsonl
ground_truth/answers.jsonl
ground_truth/audit_items_with_answers.jsonl
metrics/score_predictions.py
cards/benchmark_card.md
checksums.json
manifest.json
```

`WORKSPACE_ROOT/EVALSET_DATASET` 必须包含：

```text
README.md
data/test.jsonl
images/
ground_truth/answers.jsonl
ground_truth/audit_items_with_answers.jsonl
metrics/score_predictions.py
cards/benchmark_card.md
checksums.json
manifest.json
```

`WORKSPACE_ROOT/EVALSET_DATASET` 根目录不得包含带答案或审计字段的 `dataset.jsonl`、`items.jsonl`、`audit_items.jsonl` 等 JSONL；这些文件如果需要保留，只能存在于 `stage4/artifacts/data_22_full_benchmark_dataset/` 或 `ground_truth/` 内。Stage5 默认消费包必须让误传 `EVALSET_DATASET/*.jsonl` 给模型也不会泄漏答案。

## 隐藏答案规则

- `data/test.jsonl` 是模型输入文件，绝不能含 `answer`、`metadata`、`evidence_refs`、object provenance、bbox、depth、area 等隐藏 GT。
- scorer 使用 `ground_truth/answers.jsonl`；若内部审计版 `dataset.jsonl` 存在，只能在 `data_22_full_benchmark_dataset` 下，不得作为 `EVALSET_DATASET` 根文件。
- 媒体路径必须是 `./images/...`，不得是绝对路径、URL、symlink 或目录外引用。
- hidden audit 必须覆盖每个 item 的 `answerability_proof`，证明模型可见媒体/锚点足以确定答案。

## 阻塞条件

- 没有任何灰度通过 item。
- small-batch-result-evaluation 未执行或没有 score matrix。
- cdm-irt-analysis 未执行或没有 item/model/capability diagnostics。
- 难度配比检查失败。
- 打包后 `images/`、`ground_truth/`、`metrics/` 为空。
- `data/test.jsonl` 泄漏答案或隐藏 GT。
- `EVALSET_DATASET` 根目录存在 answer-bearing JSONL。
- hidden audit 缺少 answerability proof，或 private-GT-only 题目未提供可见 transform。
- 全量包包含全黑/全白/近空/极小/不可解码图像。
- benchmark card 不能说明 source、采集/合成参数、任务定义、hidden/visible 边界、scorer CLI、限制和分布。
- `audit_format/benchmark_items.jsonl` 缺少 answer、provenance、quality_flags、answerability_proof，或图像路径不在 `benchmark_assets/`。
- `audit_format/template_registry.json` 不是从当前 `template_manifest.jsonl`/`contrib/template_registry` 派生，而是复制固定示例模板。
- `audit_evalset_quality.py` FAIL，包括但不限于：正确答案可由残缺选项表面格式识别、answers 缺 audit/evidence、scorer 允许漏答满分、同一图片哈希被多个 scene 身份复用。
- Stage gate validator 未 PASS。
