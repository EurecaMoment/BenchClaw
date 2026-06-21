---
name: benchclaw-stage4-template-compilation
description: Use for the specific BenchClaw subskill `stage4-template-compilation` only when its parent node explicitly dispatches to it.
---

# Subskill — 模板编译

## 目标

把 `data_10_capability_dimension_doc` 中的能力维度规划和 `data_11_template_metric_initial_draft` 中的模板/指标初稿，编译为可由程序实例化的模板 JSON。模板选择必须先根据 Stage1 能力维度划分，从 `BENCHCLAW_ROOT/templates/` 统一模板包中选取需要的模板；不得直接把自然语言初稿改写成未登记来源的 enabled 模板。

本 subskill 新增 GT 血缘/亲疏关系约束：模板选择不再只看字段覆盖，而必须优先从 `gt_distant_reasoning_chains.jsonl` 中绑定可回答、可审计、远血缘、多跳的证据推理链。

## 必读契约

```text
BENCHCLAW_ROOT/skills/benchmark-stage4-build/templates/benchmark_item.schema.json
BENCHCLAW_ROOT/skills/benchmark-stage4-build/templates/BLOCKED.schema.json
BENCHCLAW_ROOT/skills/benchmark-stage4-build/templates/DONE.schema.json
BENCHCLAW_ROOT/templates/SKILL.md
BENCHCLAW_ROOT/templates/manifest.json
BENCHCLAW_ROOT/templates/template_library/benchclaw_fixed_template_registry.yaml
BENCHCLAW_ROOT/templates/template_library/templates_100_unified.index.json
BENCHCLAW_ROOT/templates/template_library/executable_template_coverage.json 或 executable_template_coverage.csv
BENCHCLAW_ROOT/templates/template_system/01_capability_map.md
BENCHCLAW_ROOT/templates/template_system/04_instantiation_rules.md
BENCHCLAW_ROOT/templates/template_system/06_quality_gates.md
BENCHCLAW_ROOT/templates/template_system/07_stage1_stage4_usage.md
BENCHCLAW_ROOT/templates/schemas/question_template.schema.json
reference_library/BENCHCLAW_IMAGE_VIDEO_TEMPLATE_METRIC_LIBRARY.md
reference_library/template_family_registry.yaml
reference_library/answer_type_metric_registry.json
reference_library/schema_patch_notes.md
```

## 新增输入

除现有输入外，必须读取：

- `artifacts/data_20_template_metric_code_bundle/gt_kinship/gt_node_catalog.jsonl`
- `artifacts/data_20_template_metric_code_bundle/gt_kinship/gt_edge_catalog.jsonl`
- `artifacts/data_20_template_metric_code_bundle/gt_kinship/gt_kinship_matrix.jsonl`
- `artifacts/data_20_template_metric_code_bundle/gt_kinship/gt_distant_reasoning_chains.jsonl`
- `artifacts/data_20_template_metric_code_bundle/gt_kinship/gt_chain_filter_log.jsonl`
- `artifacts/data_20_template_metric_code_bundle/gt_kinship/gt_kinship_report.md`

若 `gt_distant_reasoning_chains.jsonl` 不存在、为空或没有 `status=selected` 的链，本 subskill 不得启用高深度模板。

## GT 亲疏绑定总规则

- 模板选择不再只看字段覆盖。
- 对每个候选模板，必须优先匹配 `gt_distant_reasoning_chains.jsonl` 中 `status=selected` 的 `chain_id`。
- 每个 enabled 模板至少绑定 1 条 selected chain。
- 每条绑定链必须：
  - `min_pair_distance_level = far`
  - `reasoning_hops >= 3`
  - `answerability_proof.all_required_gt_present = true`
  - `answerability_proof.all_media_present = true`
  - `answerability_proof.unique_answer = true`
  - `answerability_proof.no_hidden_gt_leakage_needed = true`
  - `answerability_proof.programmatic_answer_computable = true`

如果模板只能依赖 near GT，则默认 `disabled`。只有 Stage4 plan 明确允许 low-depth baseline template 时，才可保留为辅助模板，并在 manifest 中写：

```json
{
  "depth_role": "baseline_low_depth"
}
```

## 人类自然语言质量门

每个模板必须包含 `question_pattern`，但它不能是字段拼接模板，而必须是自然场景问题。

题干必须满足：

- 像人会问的问题。
- 可以自然表达多跳线索，但不能变成机械步骤列表。
- 默认控制在 1 到 3 句话。
- 若超过 80 个中文字或 55 个英文词，必须显式检查是否可简化。
- 不能出现未填充槽位，如 `{object_a}`、`<target>`。
- 不能出现字段路径、JSON、annotation、metadata 或 simulator state 术语。

统一 forbidden terms：

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

高层自然化规则：

- 可说“更靠近画面中央”，不能说“center_x 更小”。
- 可说“被挡住一部分”，不能说“occlusion_ratio > 0.3”。
- 可说“离观察者更近”，不能说“depth_median 更小”。
- 可说“先看门口附近那把椅子，再判断它旁边桌面上的物体”，不能写成“根据字段 X 和字段 Y 判断”。

## 处理

### 1. 读取能力维度、统一模板库与 GT kinship 输出

1. 解析 `data_10_capability_dimension_doc`，建立 Stage1 能力需求表。
2. 读取统一模板包 registry、index 和 coverage，建立候选模板表。
3. 读取外挂参考库，建立保留模板族、保留 answer type 和保留 deterministic metric。
4. 读取 `gt_kinship/` 输出，建立：
   - `chain_id -> gt_nodes/gt_edges/reasoning_hops/final_answer_type`
   - `chain_id -> distance_profile`
   - `chain_id -> answerability_proof`
   - `chain_id -> natural_language_constraints`
   - `chain_id -> difficulty_profile`
5. 必须运行或复核统一模板包校验：

```bash
cd "$BENCHCLAW_ROOT/templates" && python tools/validate_strict_template_library.py
```

### 2. 建立字段目录

沿用现有字段目录输出：

- `source_inventory.jsonl`
- `field_catalog.yaml`
- `evidence_index.jsonl`

并要求字段目录中的每个 GT 字段都可追溯到 `gt_node_catalog.jsonl` 中的一个或多个 `gt_node_id`。

### 3. 根据能力维度选择统一模板

对每个 Stage1 能力维度，执行下列流程：

1. 先做能力维度到统一模板的映射。
2. 默认候选只来自 `strict_core`；需要 depth 或扩展模态时，必须逐项证明字段可追溯。
3. 用外挂参考库过滤候选，保留图像/视频可执行模板。
4. 用 GT kinship 输出过滤候选：
   - 候选模板必须能绑定至少一条 `status=selected` 的 chain；
   - 该 chain 必须与模板的 `final_answer_type`、`candidate_template_families` 和 `required_fields` 一致；
   - 若模板需要的 GT 组合只有 near/medium，默认不作为高深度 enabled 模板。
5. 对每个候选模板计算：
   - `gt_distance_score`
   - `reasoning_depth_score`
   - `distractor_quality_score`
   - `human_language_score`
   - `answerability_score`
   - `overall_template_quality_score`

建议计算：

```text
overall_template_quality_score =
  0.30 * answerability_score
+ 0.25 * reasoning_depth_score
+ 0.20 * gt_distance_score
+ 0.15 * distractor_quality_score
+ 0.10 * human_language_score
```

高深度模板硬门槛：

- `answerability_score == 1.0`
- `human_language_score >= 0.8`
- `reasoning_depth_score >= 0.6`
- `gt_distance_score >= 0.6`

否则不得作为 `high_depth` enabled template。

### 4. 编译模板定义

只允许对 `selected_template_sources.jsonl` 中 `selection_status=selected` 的统一模板生成 enabled 模板 JSON。每个模板 JSON 除原有字段外，必须新增：

```json
{
  "gt_kinship_requirements": {
    "requires_distant_gt": true,
    "min_distance_level": "far",
    "min_reasoning_hops": 3,
    "allowed_chain_ids": [],
    "disallow_near_only_gt": true
  },
  "reasoning_chain_plan": {
    "chain_id": "...",
    "gt_nodes": [],
    "reasoning_hops": [],
    "final_answer_type": "...",
    "answerability_proof": {}
  },
  "difficulty_design": {
    "reasoning_depth_score": 0.0,
    "gt_distance_score": 0.0,
    "distractor_hardness_policy": "...",
    "estimated_discriminability": "medium | high"
  },
  "human_question_style": {
    "style": "natural_human_scene_question",
    "forbidden_expressions": [],
    "required_naturalization_rules": []
  },
  "template_quality_profile": {
    "answerability_score": 1.0,
    "gt_distance_score": 0.0,
    "reasoning_depth_score": 0.0,
    "distractor_quality_score": 0.0,
    "human_language_score": 0.0,
    "overall_template_quality_score": 0.0
  }
}
```

其中：

- `allowed_chain_ids` 必须来自 `gt_distant_reasoning_chains.jsonl` 中 `status=selected` 的链。
- `reasoning_chain_plan.chain_id` 必须是实际绑定的链。
- `reasoning_chain_plan.reasoning_hops` 必须和链内 hops 对齐，不得只写空占位。
- `human_question_style.required_naturalization_rules` 必须明确约束禁止字段名腔、日志腔、元数据泄漏腔、机械提示词腔。

### 5. 模板启用条件

一个模板要 `enabled`，必须同时满足：

- 来自统一模板包；
- Stage3 evidence 字段满足；
- 至少绑定 1 条 selected GT reasoning chain；
- 该 chain 至少包含 3 个 reasoning hops；
- GT 节点之间至少存在一个 `far` 关系；
- `final_answer` 可由 answer program 计算；
- 题目不需要外部常识才能作答；
- 题目不会因为图像模糊、目标不可见、同类实例不可区分而不可答；
- 干扰项可构造且不明显；
- `question_pattern` 与预期自然语言样例不包含 forbidden terms。

### 6. 输出汇总

写入：

- `selected_template_sources.jsonl`
- `template_manifest.jsonl`
- `traceability.csv`

`selected_template_sources.jsonl` 每行新增字段：

```json
{
  "gt_chain_id": "...",
  "gt_distance_level": "far",
  "reasoning_hop_count": 3,
  "answerability_status": "proved | failed",
  "human_language_status": "passed | failed",
  "depth_role": "high_depth | medium_depth | baseline_low_depth"
}
```

`template_manifest.jsonl` 每行新增字段：

```json
{
  "chain_id": "...",
  "reasoning_hop_count": 0,
  "gt_distance_score": 0.0,
  "reasoning_depth_score": 0.0,
  "human_language_quality_gate": "PASS | FAIL",
  "answerability_quality_gate": "PASS | FAIL"
}
```

`traceability.csv` 必须新增列：

```text
chain_id,gt_nodes,gt_distance_level,reasoning_hop_count,reasoning_depth_score,answerability_status,human_language_status,depth_role
```

## 失败与阻塞

以下情况必须向主节点报告阻塞：

- `gt_kinship/` 输出缺失或不可解析。
- 所有 selected 统一模板都无法绑定任何 selected chain。
- 远血缘链存在，但没有一条可证明唯一答案、可计算答案且可自然表述。
- 题干 naturalization 无法通过，仍然保留字段名腔或元数据泄漏腔。
- 所有候选模板都只能依赖 near GT，且 Stage4 plan 未允许 baseline low-depth 保底模板。

只有部分模板失败时，不阻塞整个节点；将失败模板写为 `blocked` 或 `disabled`，并保留可执行模板继续后续子 skill。
