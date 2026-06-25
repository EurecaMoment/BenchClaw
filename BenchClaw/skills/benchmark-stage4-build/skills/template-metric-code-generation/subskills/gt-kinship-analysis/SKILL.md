---
name: benchclaw-stage4-gt-kinship-analysis
description: Use for the specific BenchClaw subskill `stage4-gt-kinship-analysis` only when its parent node explicitly dispatches to it.
---

## Opencode 子 agent 触发契约

本文件是 BenchClaw child skill module。父级 stage、node 或 pipeline 调度到本文件时，必须通过 opencode 命令 `/benchclaw-subskill` 启动隔离子 agent；该命令在 `BENCHCLAW_ROOT/opencode.json` 中配置为 `subtask: true`，并绑定 `mode: "subagent"` 的 `child-skill-module-runner`。禁止父级 manager 直接在自己的对话上下文中内联执行本文件步骤。

调用 `/benchclaw-subskill` 时必须传入：目标 `SKILL.md` 绝对路径、注册 skill 名、冻结的 `PROJECT_ROOT` / `BENCHCLAW_ROOT` / `WORKSPACE_PARENT` / `WORKSPACE_ROOT`、当前 node 或 work_unit id、已满足的输入 artifact 路径、期望输出 artifact 路径、父级 DAG 依赖与完成判据。子 agent 只返回 `status`、artifact 路径、证据摘要和 blockers，不回灌长日志或完整中间内容。

如果当前执行上下文不是 `/benchclaw-subskill` 产生的 `child-skill-module-runner` 子 agent，本文件不得继续执行；应立即返回 `BLOCKED`，说明必须由父级使用 `/benchclaw-subskill` 重新派发。

# Subskill — GT 亲疏关系、证据图与难度支持分析

## 目标

把 Stage3 标注数据归一化为证据节点、证据边、证据组合、复杂 GT 血缘图和难度支持矩阵，为模板选择提供“哪些 GT 组合可答、证据亲疏如何、复杂 ground truth 之间如何多跳依赖、能构造 easy/medium/hard 哪些难度”的依据。该 subskill 不生成 benchmark item，也不直接启用模板。

## 输出

```text
data_20_template_metric_code_bundle/gt_kinship/
  gt_node_catalog.jsonl
  gt_edge_catalog.jsonl
  gt_kinship_graph.json
  gt_kinship_graph.dot
  gt_kinship_matrix.jsonl
  gt_distant_reasoning_chains.jsonl
  gt_chain_filter_log.jsonl
  difficulty_support.json
  difficulty_support_by_template.jsonl
  gt_kinship_report.md
```

同时必须把可被一键 synthesizer 直接消费的字段摘要写入 bundle 根目录：

```text
data_20_template_metric_code_bundle/field_catalog.yaml
data_20_template_metric_code_bundle/contrib/gt_adapter/adapter_contract.json
```

`field_catalog.yaml` 至少记录：canonical field name、候选源字段路径、value type、field family、answerability status、可支持的 template family、是否允许进入 Qwen prompt 的脱敏样例。

`adapter_contract.json` 是给 `answer-program-generation` 装配一键合成器用的机器可读 GT adapter 契约，至少包含：

```json
{
  "schema_version": "benchclaw.stage4.gt_adapter.v1",
  "canonical_record_id_fields": ["sample_id", "record_id", "id"],
  "canonical_media_fields": ["image_path", "media", "images"],
  "field_families": {
    "objects": {
      "source_paths": ["objects", "annotations"],
      "canonical_fields": ["category", "bbox_xyxy", "centroid_xy", "area_px", "depth"],
      "private_by_default": ["object_id", "bbox_xyxy", "area_px", "depth"]
    }
  },
  "supported_sequence_semantics": ["single_capture", "ordered_sequence", "multi_view"],
  "safe_prompt_sample_policy": "redacted_compact_examples_only"
}
```

该文件只描述字段归一化和可答证据，不写题目、不写答案、不选择模板。

## 难度定义

- `easy`：单字段或近邻证据即可唯一作答，如类别存在、单类计数区间、深度区间。
- `medium`：需要两到三个证据节点组合或显式作答图像标识，如左右/上下、九宫格、最大面积、最近深度。
- `hard`：需要多对象排序、跨属性组合、远血缘链或多跳证据一致性，如从左到右排序、面积排序、近远排序、类别集合多选。

## 规则

- 所有难度都必须有一定比例；默认 full/grey 最低比例为 easy ≥ 0.20，medium ≥ 0.25，hard ≥ 0.20。
- high-depth/远血缘链不是唯一高难来源；多对象排序、跨属性组合、集合题也可计为 hard，但必须在 `difficulty_support_by_template.jsonl` 解释其证据组合。
- 若某难度没有 GT 支持，必须输出 `coverage_gap`，并由 template-compilation 阻塞或请求 Stage3 补充证据；不得静默降级为单一难度 benchmark。
- 不能把“长思考链”理解为要求被测模型输出私有推理；这里只记录题目设计侧的 `evidence_reasoning_chain`。
- 对复杂 ground truth，必须额外输出血缘图：`gt_kinship_graph.json` 用 `nodes[]` 表示归一化 GT 证据节点、`edges[]` 表示同样本/同场景/同实体/同媒体/字段族/空间关系/答案依赖等血缘边、`complex_gt_subgraphs[]` 表示可被 hard 或多跳模板消费的复杂 GT 子图；同时输出 `gt_kinship_graph.dot` 作为可视化草图。
- `complex_gt_subgraphs[]` 优先回溯到 `gt_distant_reasoning_chains.jsonl` 中的 selected chain；若远链筛选过严，也必须从 `gt_kinship_matrix.jsonl` 中可共同支持题目的 far/medium GT pair 抽取局部血缘子图，并记录 `source_matrix_pair`。如果通用 entity 抽取导致同一样本跨字段族 pair 被归为 near，仍要为这些跨字段族复杂 GT 保留局部血缘子图，但不得把它们冒充为 high-depth 远血缘链。
- 每个复杂子图都必须记录 `gt_nodes`、`gt_edges`、pair 级亲疏信息、候选模板族、答案类型和 answerability proof，不能只给自然语言描述。
- `difficulty_support_by_template.jsonl` 必须给 `template-compilation` 和 `answer-program-generation` 使用：每行包含 candidate template family、difficulty_level、required_field_paths、minimum_candidate_count、deterministic_gt_rule、blocking_gap。不能只写报告文本。
- 给本地 Qwen 的字段样例必须脱敏且紧凑，只展示结构和少量值形态；不得把完整隐藏答案表当作提示上下文。

## 可执行工具

```text
subskills/gt-kinship-analysis/generate_gt_kinship.py
subskills/gt-kinship-analysis/gt_kinship_base.py
```

## 阻塞条件

- Stage3 GT 无法读取或没有任何可归一化证据节点。
- easy/medium/hard 任一难度完全无支持，且 Stage4 plan 未显式降低难度配比要求。
- 证据链声称可答但缺媒体、缺字段或无法程序化计算答案。
