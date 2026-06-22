---
name: benchclaw-stage4-contract-checking
description: Use for the specific BenchClaw subskill `stage4-contract-checking` only when its parent node explicitly dispatches to it.
---

# Subskill — 契约检查

## 目标

对 `data_20_template_metric_code_bundle` 做静态契约检查和运行时 smoke test。只有当模板、指标、答案程序、批量合成代码、GT kinship 输出和自然语言质量门都通过时，主节点才能写 `DONE.json`。

## 输入

- `artifacts/data_20_template_metric_code_bundle/`
- 本 stage `templates/benchmark_item.schema.json`
- 本 stage `templates/DONE.schema.json`
- 本 stage `templates/BLOCKED.schema.json`
- `stage4_execution_plan.yaml`
- Stage3 证据 bundle 的已登记路径
- `artifacts/data_20_template_metric_code_bundle/references/`

## 静态检查

### 1. 目录完整性

必须新增检查：

- `gt_kinship/`

### 2. Manifest 完整性

除原有文件外，必须检查：

- `gt_kinship/gt_node_catalog.jsonl`
- `gt_kinship/gt_edge_catalog.jsonl`
- `gt_kinship/gt_kinship_matrix.jsonl`
- `gt_kinship/gt_distant_reasoning_chains.jsonl`
- `gt_kinship/gt_chain_filter_log.jsonl`
- `gt_kinship/gt_kinship_report.md`

### 3. Enabled 模板新增检查

每个 enabled 模板必须满足：

- 有非空 `reasoning_chain_plan`
- 有合法 `chain_id`
- `chain_id` 存在于 `gt_distant_reasoning_chains.jsonl`
- 对应 chain 的 `status` 为 `selected`
- `reasoning_hop_count >= 3`
- 至少一个 GT pair 的 `distance_level` 是 `far`
- `answerability_proof` 全部为 `true`
- 模板 `question_pattern` 不包含 forbidden terms
- `template_quality_profile.answerability_score == 1.0`
- `template_quality_profile.human_language_score >= 0.8`

### 4. Dry-run item 新增检查

每条 dry-run item 必须满足：

- 题干不是空字符串
- 题干不是纯模板变量拼接
- 不包含 forbidden terms
- 不出现未填充槽位，如 `{object_a}`、`<target>`
- 不出现字段路径，如 `a.b.c`
- 不出现 `JSON` / `metadata` / `annotation` 术语
- 题干长度不过短，也不过长
- 单选题选项文本自然，不是 `object_id`
- `metadata.chain_id` 与模板一致
- `metadata.reasoning_hop_count >= 3`
- `metadata.gt_distance_level = far`，除非模板显式声明 `depth_role = baseline_low_depth`
- 若 item 包含 `source_media`，则 `source_media` 与 `media` 必须长度一致，分别表示原图列与最终作答图列
- 若 item 启用了 visual marker，则 `metadata.visual_marker.map_paths` 中的每个映射文件都必须存在
- 若映射文件中声明了 label，则这些 label 不能在图上泄漏答案性词汇，只能是中性标识
- 若模板声明 `require_label_references = true`，则题干、答案解析和映射文件中的 label 集合必须一致

如果自然语言检查失败，不能写 `DONE`；必须 `blocked` 或 `disabled` 对应模板。

## forbidden terms

统一检查词：

```text
object_id
bbox
mask
depth_median
depth_value
gt
GT
field
json
JSON
metadata
annotation
privileged
simulator state
record
evidence_index
source_sample_id
center_x
center_y
x_min
y_min
IoU
```

## 运行时检查

沿用原有命令，并要求 `validate_bundle.py` 或 smoke test 额外覆盖：

- `gt_kinship_analysis`
- `human_language_lint`
- `answerability_chain_check`
- `enabled_high_depth_template_count`
- `distant_chain_count`

## 通过条件

整体 bundle 必须满足：

- `py_compile` 通过
- `validate_bundle.py` 退出码为 0
- `smoke_test.py` 退出码为 0
- 完美预测评分整体满分
- 负例评分低于完美预测
- `gt_kinship/` 全套文件存在且可解析
- `distant_chain_count > 0`
- `enabled_high_depth_template_count > 0`
- `human_language_lint = PASS`
- `answerability_chain_check = PASS`

## 完成记录

`DONE.json` 的 `quality_gate` 至少新增：

```json
{
  "gt_kinship_analysis": "PASS",
  "distant_chain_count": 0,
  "enabled_high_depth_template_count": 0,
  "human_language_lint": "PASS",
  "answerability_chain_check": "PASS"
}
```

## 节点报告要求

`NODE_REPORT.md` 必须新增：

- GT 亲疏关系概览
- 远血缘链数量
- 各能力维度的远血缘链覆盖
- enabled high-depth 模板数量
- disabled / blocked 原因分布
- 自然语言题干检查结果
- 可回答性检查结果
- 典型高深度模板示例
- 后续 `grey-batch-validation` 如何按 `--min-reasoning-hops` 和 `--min-gt-distance-level` 生成题目
