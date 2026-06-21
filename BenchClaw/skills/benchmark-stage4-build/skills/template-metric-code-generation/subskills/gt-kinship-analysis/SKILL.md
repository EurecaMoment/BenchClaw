---
name: benchclaw-stage4-gt-kinship-analysis
description: Use for the specific BenchClaw subskill `stage4-gt-kinship-analysis` only when its parent node explicitly dispatches to it.
---

# Subskill — GT 血缘亲疏分析

## 目标

读取 Stage3 的 evidence index、field catalog、source inventory、annotated bundle 和 simulator privileged state 中的 GT 字段，建立 GT 节点图谱、亲疏关系和远血缘可答推理链，并将结果写入 `artifacts/data_20_template_metric_code_bundle/gt_kinship/`，供后续 `template-compilation` 优先选择高深度模板。

本 subskill 的输出不是给评测模型看的 chain-of-thought，而是给模板编译、答案程序和审计逻辑使用的 `evidence_reasoning_chain` / `reasoning_chain_plan`。

## 输入

- `artifacts/data_20_template_metric_code_bundle/source_inventory.jsonl`
- `artifacts/data_20_template_metric_code_bundle/field_catalog.yaml`
- `artifacts/data_20_template_metric_code_bundle/evidence_index.jsonl`
- `data_17_annotated_real_image_bundle`
- `data_18_annotated_existing_benchmark_bundle`
- `data_19_annotated_simulator_bundle`
- `stage4_execution_plan.yaml`

## 输出

必须写入：

```text
artifacts/data_20_template_metric_code_bundle/
  gt_kinship/
    gt_node_catalog.jsonl
    gt_edge_catalog.jsonl
    gt_kinship_matrix.jsonl
    gt_distant_reasoning_chains.jsonl
    gt_chain_filter_log.jsonl
    gt_kinship_report.md
```

### `gt_node_catalog.jsonl`

每行是一个 GT 节点，至少包含：

```json
{
  "gt_node_id": "...",
  "source_sample_id": "...",
  "source_type": "real_image | existing_benchmark | simulator",
  "scene_id": "...",
  "media_refs": [],
  "entity_refs": [],
  "field_path": "...",
  "field_family": "object | relation | spatial | temporal | action | affordance | visibility | depth | pose | count | region | label | state | other",
  "value_type": "scalar | categorical | set | list | bbox | mask | point2d | point3d | relation | text",
  "gt_origin": "official_label | human_annotation | simulator_privileged_gt | reproducible_computation | tool_auxiliary",
  "is_answerable_source": true,
  "visibility_status": "visible | invisible | uncertain | not_visual",
  "answerability_notes": "..."
}
```

### `gt_edge_catalog.jsonl`

每行是 GT 节点之间的一条边，至少包含：

```json
{
  "src_gt_node_id": "...",
  "dst_gt_node_id": "...",
  "edge_type": "same_sample | same_scene | same_entity | same_object_category | same_region | same_relation_family | derived_from | spatially_related | temporally_adjacent | action_affordance_related | co_visible | semantic_related | answer_dependency",
  "edge_weight": 1.0,
  "evidence": "...",
  "confidence": 1.0
}
```

### `gt_kinship_matrix.jsonl`

每行是一对 GT 节点的亲疏评估，至少包含：

```json
{
  "gt_a": "...",
  "gt_b": "...",
  "shortest_path_length": 0,
  "kinship_score": 0.0,
  "distance_level": "near | medium | far | unreachable",
  "shared_scene": true,
  "shared_entity": false,
  "shared_field_family": false,
  "can_jointly_support_question": true,
  "risk": "low | medium | high",
  "risk_reason": "..."
}
```

### `gt_distant_reasoning_chains.jsonl`

每行是一条可用于出题的远血缘 GT 推理链，至少包含：

```json
{
  "chain_id": "...",
  "source_sample_id": "...",
  "source_type": "...",
  "media_refs": [],
  "gt_nodes": ["gt1", "gt2", "gt3"],
  "gt_edges": ["edge1", "edge2"],
  "distance_profile": {
    "min_pair_distance_level": "far",
    "avg_shortest_path_length": 0.0,
    "max_shortest_path_length": 0
  },
  "reasoning_hops": [
    {
      "hop_id": 1,
      "operation": "identify | compare | count | order | spatial_relation | filter | aggregate | infer_relation | verify_constraint",
      "input_gt_nodes": [],
      "output_intermediate": "...",
      "answerable_by": "visible_media | official_label | human_annotation | simulator_gt | reproducible_computation"
    }
  ],
  "final_answer_type": "single_choice | boolean | numeric | ordering | set_answer | region | short_answer",
  "candidate_template_families": [],
  "answerability_proof": {
    "all_required_gt_present": true,
    "all_media_present": true,
    "unique_answer": true,
    "no_hidden_gt_leakage_needed": true,
    "visual_evidence_sufficient": true,
    "programmatic_answer_computable": true
  },
  "difficulty_profile": {
    "reasoning_depth": 0,
    "gt_distance_score": 0.0,
    "distractor_hardness": 0.0,
    "estimated_discriminability": "low | medium | high"
  },
  "natural_language_constraints": {
    "must_avoid_field_names": true,
    "must_use_human_scene_description": true,
    "must_not_expose_gt_values_in_question": true
  },
  "status": "selected | disabled | blocked",
  "filter_reason": ""
}
```

### `gt_chain_filter_log.jsonl`

记录所有被过滤的链，原因必须来自清晰枚举，例如：

- `media_missing`
- `visibility_proof_missing`
- `answer_not_unique`
- `requires_hidden_gt_leakage`
- `gt_too_near`
- `question_not_natural`
- `candidate_options_unconstructable`
- `reasoning_chain_too_long_to_read`
- `programmatic_answer_not_computable`

### `gt_kinship_report.md`

必须包括：

- GT 节点数量
- GT 边数量
- near / medium / far / unreachable 分布
- 可用远血缘链数量
- 被过滤链的主要原因
- 各能力维度可覆盖的远血缘链数量
- 后续 `template-compilation` 可使用的 `chain_id` 列表

## 构图原则

- 每个可追溯 GT 字段、对象、关系、区域、动作、可见性、空间属性、计数属性、深度/距离属性、状态属性都视为节点。
- 按以下关系连边：
  - 同一样本：`same_sample`
  - 同一场景：`same_scene`
  - 同一实体：`same_entity`
  - 同一对象类别：`same_object_category`
  - 同一空间区域：`same_region`
  - 同一关系族：`same_relation_family`
  - 一个字段由另一个字段计算而来：`derived_from`
  - 空间相关：`spatially_related`
  - 时间邻接：`temporally_adjacent`
  - 动作/可供性相关：`action_affordance_related`
  - 同时可见：`co_visible`
  - 语义相关：`semantic_related`
  - 答案依赖：`answer_dependency`

## 距离计算规则

必须至少计算：

- 图最短路径长度
- 是否同实体
- 是否同字段族
- 是否同场景
- 是否同媒体
- 是否派生关系
- 是否可共同支持一道题
- 是否存在唯一答案

距离等级要求：

- `near`
  - `shortest_path_length <= 1`
  - 或 `same_entity = true`
  - 或 `derived_from = true`
  - 或 `same_field_family = true && same_sample = true`
- `medium`
  - `same_sample = true 或 same_scene = true`
  - 且不是 `same_entity`
  - 且 `shortest_path_length` 在 2 到 3 之间
- `far`
  - `same_sample = true 或 same_scene = true`
  - 且不是 `same_entity`
  - 且不是 `same_field_family`
  - 且 `shortest_path_length >= 2`
  - 且 `can_jointly_support_question = true`
  - 且 `unique_answer = true`
- `unreachable`
  - 无共同媒体
  - 或无共同场景
  - 或无法形成答案
  - 或答案不唯一
  - 或只能靠隐藏 GT 猜答案

远血缘链不是越远越好，必须满足“远但可答”。不能把两个毫无关系的 GT 硬拼成一道题。

## 推理链规则

- 每条 `selected` chain 默认至少包含 3 个 `reasoning_hops`。
- 除非题型天然只需要 2 hop 且具有强区分度，否则少于 3 hop 的链不得进入高深度模板。
- 推荐 hop 类型：
  - 识别目标实体
  - 从多个候选中筛选满足条件的对象
  - 比较两个对象的空间/距离/大小/数量关系
  - 聚合同类对象
  - 先定位再判断关系
  - 先判断可见性再判断空间关系
  - 先从局部关系推出全局排序
  - 先排除不满足条件的候选，再计算答案
  - 先构造中间集合，再求最终答案

每条 `selected` chain 必须能证明：

- `all_required_gt_present = true`
- `all_media_present = true`
- `unique_answer = true`
- `programmatic_answer_computable = true`
- `no_hidden_gt_leakage_needed = true`

否则不得进入 `template-compilation`。

## 题目自然语言约束

每条 `selected` chain 都必须附带：

- `must_avoid_field_names = true`
- `must_use_human_scene_description = true`
- `must_not_expose_gt_values_in_question = true`

禁止在链级约束或示例中出现：

```text
object_id
depth_median
bbox
mask_path
gt_field
privileged_state
record
evidence_index
根据字段 X
从 JSON 中判断
请比较字段 a.b.c
```

## 处理步骤

1. 从 `field_catalog.yaml` 和 `evidence_index.jsonl` 提取所有可追溯 GT 节点。
2. 建立 `gt_node_catalog.jsonl`。
3. 基于样本、场景、实体、字段族、空间/时间/语义关系和派生关系建边，生成 `gt_edge_catalog.jsonl`。
4. 对候选节点对计算最短路径和亲疏等级，写 `gt_kinship_matrix.jsonl`。
5. 搜索可组成问题的多跳链，优先保留：
   - 至少一个 `far` GT pair
   - 至少 3 个 reasoning hops
   - 可构造唯一答案
   - 可程序化验证
   - 可自然语言表述
6. 对所有被筛掉的链写 `gt_chain_filter_log.jsonl`。
7. 生成 `gt_kinship_report.md`。

## 阻塞条件

以下情况必须阻塞或导致后续高深度模板全部 disabled：

- 无法建立 GT 节点目录
- 无法建立场景/实体/字段族关系
- 无任何 `far` 链能同时满足可见、可答、唯一答案和可程序化计算
- 链虽存在，但自然语言约束无法满足
- 所有可用链都只能依赖隐藏 GT 泄漏答案
