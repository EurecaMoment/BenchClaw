---
name: benchclaw-stage4-template-compilation
description: Use for the specific BenchClaw subskill `stage4-template-compilation` only when its parent node explicitly dispatches to it.
---

## Opencode 子 agent 触发契约

本文件是 BenchClaw child skill module。父级 stage、node 或 pipeline 调度到本文件时，必须通过 opencode 命令 `/benchclaw-subskill` 启动隔离子 agent；该命令在 `BENCHCLAW_ROOT/opencode.json` 中配置为 `subtask: true`，并绑定 `mode: "subagent"` 的 `child-skill-module-runner`。禁止父级 manager 直接在自己的对话上下文中内联执行本文件步骤。

调用 `/benchclaw-subskill` 时必须传入：目标 `SKILL.md` 绝对路径、注册 skill 名、冻结的 `PROJECT_ROOT` / `BENCHCLAW_ROOT` / `WORKSPACE_PARENT` / `WORKSPACE_ROOT`、当前 node 或 work_unit id、已满足的输入 artifact 路径、期望输出 artifact 路径、父级 DAG 依赖与完成判据。子 agent 只返回 `status`、artifact 路径、证据摘要和 blockers，不回灌长日志或完整中间内容。

如果当前执行上下文不是 `/benchclaw-subskill` 产生的 `child-skill-module-runner` 子 agent，本文件不得继续执行；应立即返回 `BLOCKED`，说明必须由父级使用 `/benchclaw-subskill` 重新派发。

# Subskill — 模板编译

## 目标

根据 Stage4 plan、父类模板 registry、能力维度、GT kinship 难度支持和作答图像处理结果，生成 `template_manifest.jsonl`、`synthesis_plan.yaml` 与 `contrib/template_registry/template_registry.json`。模板编译只选择模板和约束，不生成完整 item 代码。

模板编译必须遵守 `reference_library/BENCHMARK_QUALITY_CONTRACT.md`：只有同时具备可见锚点、确定性答案规则、隐藏审计字段和 deterministic metric 的模板才允许 enabled。

## 输入

- `stage4_execution_plan.yaml`
- `gt_kinship/*`
- `image_processing/image_manifest.jsonl`
- 父类 runtime registry：`build_default_template_registry()`
- `reference_library/BENCHMARK_QUALITY_CONTRACT.md`
- `reference_library/template_family_registry.yaml`
- `reference_library/answer_type_metric_registry.json`

## 模板轨道

- `easy`：单字段/单对象/单类证据即可程序化唯一作答。
- `medium`：需要图像标识、两到三个对象或空间/尺度/深度组合证据。
- `hard`：需要多对象排序、集合选择、跨属性组合或远血缘多跳证据。
- `disabled`：字段不足、媒体不足、答案不唯一、无法确定性评分、题干不自然或破坏难度配比的模板。

## 编译要求

- enabled 模板必须来自父类 registry 或允许的 reference library。
- 每个 enabled 模板必须声明 `difficulty_level`、`kinship_level`、`required_evidence_fields`、`capability_tags`、`answer_type`、`metric_id`。
- enabled 模板集合必须能覆盖 easy/medium/hard 最低比例目标；不能只启用简单模板。
- 需要对象、区域、轨迹、视角、时刻或候选标识的模板必须确认 `image_processing/image_manifest.jsonl` 中有对应 processed asset，并声明 `visual_marker_policy`；题干或选项只能引用中性标记（如 A/B/C/D、P1/P2、View 1/2、Step 1/2），不得直接暴露 object_id、bbox、深度字段或隐藏 GT 名称。
- 每个 enabled 模板都必须写明 `visible_anchor_source` 或等价字段，指向 safe copy、bbox/point overlay、crop/panel、multi-view grid、trajectory panel 等模型可见锚点来源。
- 每个 enabled 模板必须写明 `answerability_proof_required: true`，并声明 `private_gt_fields_used` 与 `required_visible_transform`。若 `private_gt_fields_used` 包含 simulator pose、coordinate、depth、distance、bbox/mask、area、trajectory、frame id、scene id、object id 等字段，`required_visible_transform` 不能是 raw/safe RGB；必须是能把该私有字段变成模型可见证据的 transform。
- 模板不得把 source scene name、file stem、record id、frame id、simulator coordinate bin 作为模型从图像中“识别”的目标，除非这些信息以中性可见标签/地图/面板方式出现在模型输入中。仅凭 hidden scene label 生成 scene-choice 题是不合格模板。
- choice 模板必须检查答案分布与 distractor 可用性：任何选项在该模板灰度样本中从不可能为正确答案，必须删除或重新采样；不得保留 `fallback`、`unknown`、格式异常或明显不属于同一候选集的选项。

## 人类题干质量门

题干必须自然、短、可回答。禁止出现：

```text
object_id, bbox, mask, depth_median, GT, json, metadata, annotation,
evidence_index, simulator state, center_x, center_y, x_min, y_min,
无法判断, 信息不足, 不能确定
```

## 输出字段

每个模板 manifest row 至少包含：

```json
{
  "template_id": "...",
  "status": "enabled|disabled",
  "difficulty_level": "easy|medium|hard",
  "kinship_level": "single_field|pair_spatial|multi_object_order|...",
  "capability_tags": [],
  "answer_type": "single_choice",
  "metric_id": "exact_choice",
  "requires_overlay": false,
  "visual_marker_policy": {
    "required": false,
    "marker_type": "bbox_or_point",
    "labels": ["A", "B"],
    "question_must_reference_labels": true
  },
  "visible_anchor_source": "safe_copy|bbox_label_overlay|point_label_overlay|crop_panel|multi_view_grid|candidate_panel|trajectory_panel",
  "requires_processed_image_manifest": true,
  "answerability_proof_required": true,
  "private_gt_fields_used": ["..."],
  "required_visible_transform": "rgb_depth_pair|pose_map_overlay|trajectory_panel|bbox_label_overlay|candidate_panel|safe_rgb",
  "required_evidence_fields": [],
  "reference_template_family": "T1",
  "gt_rule": "deterministic rule in human-readable form",
  "implementation_hint": "name of generator function or adapter hook expected in generate_items.py",
  "qwen_generation_notes": [
    "Only use evidence fields listed here.",
    "Do not create unsupported fallback templates."
  ],
  "disable_reason": ""
}
```

同时必须写 `contrib/template_registry/template_registry.json`，作为 `generate_items.py` 的 registry 输入和 `audit_format/template_registry.json` 的来源。该文件至少包含：

```json
{
  "schema_version": "benchclaw.stage4.template_registry.v1",
  "library_name": "dataset_specific_stage4_templates",
  "capabilities": {
    "C1": {"name": "...", "definition": "..."}
  },
  "question_types": {
    "single_choice": "Single choice",
    "ordered_list": "Ordered list"
  },
  "templates": {
    "TEMPLATE_ID": {
      "status": "enabled",
      "capability_id": "C1",
      "answer_type": "single_choice",
      "difficulty_level": "medium",
      "required_evidence_fields": [],
      "required_visible_transform": "bbox_label_overlay",
      "gt_rule": "deterministic rule",
      "implementation_hint": "gen_template_id",
      "invalid_conditions": ["missing visible anchor", "near tie"]
    }
  }
}
```

模板 registry 允许不同数据源拥有完全不同能力和题型；禁止复制 LIBERO 或 UAV 模板名作为默认任务集合。相同的是字段契约、可见锚点、确定性答案和审计输出。

`implementation_hint` 必须足够具体，使 `answer-program-generation` 或本地 Qwen 能写出类似 UAV synthesizer 的确定性函数，例如：`gen_spatial_left_of_yes_no`, `gen_count_interval`, `gen_area_order`。不能只写自然语言大类。

## 给 answer-program-generation 的交接

模板编译完成后，必须能回答以下问题并写入 `synthesis_plan.yaml` 或 `template_manifest.jsonl`：

- 每个 enabled 模板消费哪些 `gt_kinship` 节点/字段族。
- 是否必须引用 `image_processing/image_manifest.jsonl` 中的 neutral overlay、candidate panel 或 safe copy。
- 如果必须引用 neutral overlay，则写明 `visual_marker_policy`：候选 GT 对象数量、标记类型、标签集合、题干/选项怎样引用这些标签，以及 fallback 不可用时如何 filtered。
- 该模板的答案类型、metric id 和 scoring 函数是否已在 metric registry 中存在。
- 该模板在一键 synthesizer 中对应的函数名、最小候选数量、margin/去重规则和 invalid/filtered 条件。
- 如果本地 Qwen 生成代码，哪些字段可以作为 compact examples 输入提示，哪些隐藏 GT 绝不能进入模型可见题面。
- `audit_format/template_registry.json` 将如何从本 registry 派生；若某模板只存在于自然语言报告中而不在 registry 中，不能 enabled。

## 阻塞条件

- 没有任何 enabled 模板能产出真实 item。
- easy/medium/hard 任一难度无法达到计划最低比例且没有显式 plan 例外。
- 模板来源无法追溯到父类 registry 或允许的 reference library。
- requires_overlay 模板启用但无可处理作答图像。
- 模板答案依赖 private GT，但 `required_visible_transform` 仍是 raw/safe RGB 或缺少可见锚点。
- choice 候选集中存在从不为正确答案的固定 distractor、fallback 选项或格式异常选项。
