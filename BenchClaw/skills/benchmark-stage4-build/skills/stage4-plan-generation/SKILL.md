---
name: benchclaw-stage4-plan-generation
description: Use for the specific BenchClaw node skill `stage4-plan-generation` only when its parent stage explicitly dispatches to it.
---

## Opencode 子 agent 触发契约

本文件是 BenchClaw child skill module。父级 stage、node 或 pipeline 调度到本文件时，必须通过 opencode 命令 `/benchclaw-subskill` 启动隔离子 agent；该命令在 `BENCHCLAW_ROOT/opencode.json` 中配置为 `subtask: true`，并绑定 `mode: "subagent"` 的 `child-skill-module-runner`。禁止父级 manager 直接在自己的对话上下文中内联执行本文件步骤。

调用 `/benchclaw-subskill` 时必须传入：目标 `SKILL.md` 绝对路径、注册 skill 名、冻结的 `PROJECT_ROOT` / `BENCHCLAW_ROOT` / `WORKSPACE_PARENT` / `WORKSPACE_ROOT`、当前 node 或 work_unit id、已满足的输入 artifact 路径、期望输出 artifact 路径、父级 DAG 依赖与完成判据。子 agent 只返回 `status`、artifact 路径、证据摘要和 blockers，不回灌长日志或完整中间内容。

如果当前执行上下文不是 `/benchclaw-subskill` 产生的 `child-skill-module-runner` 子 agent，本文件不得继续执行；应立即返回 `BLOCKED`，说明必须由父级使用 `/benchclaw-subskill` 重新派发。

# Node Skill — Stage4 执行计划生成

## 目标

把 Stage1 评测意图和 Stage3 可用证据转成 Stage4 的可执行计划。该节点只做计划，不生成模板、指标或 item。

## 输入

- Stage1/Stage2/Stage3 已冻结 artifact 索引。
- `data_11_template_metric_initial_draft`
- `data_13_execution_plan`
- `data_17/18/19` 三类 Stage3 标注数据，至少一类可用。

## 必须输出

```text
WORKSPACE_ROOT/stage4/nodes/stage4-plan-generation/stage4_execution_plan.yaml
WORKSPACE_ROOT/stage4/nodes/stage4-plan-generation/USED_INPUTS.json
WORKSPACE_ROOT/stage4/nodes/stage4-plan-generation/DONE.json
WORKSPACE_ROOT/stage4/nodes/stage4-plan-generation/NODE_REPORT.md
```

`stage4_execution_plan.yaml` 至少包含：

```yaml
workspace:
  project_root: ...
  benchclaw_root: ...
  workspace_root: ...
inputs:
  stage3_sources: []
capability_targets:
  - capability_id: ...
    required: true
    allowed_answer_types: []
gt_policy:
  evidence_graph_required: true
  difficulty_support_required: true
  min_real_items_for_smoke: 1
  difficulty_min_ratios:
    easy: 0.20
    medium: 0.25
    hard: 0.20
image_policy:
  answer_image_processing_required: true
  overlay_required_for_instance_relation_templates: true
  model_visible_media_prefix: ./images/
  reject_blank_or_low_information_media: true
  private_gt_visible_transform_required: true
template_policy:
  allowed_template_source: parent_runtime_registry
  allow_runtime_adapter_overrides: true
  require_template_difficulty_tags: true
  require_answerability_proof: true
  private_gt_fields_requiring_visible_transform:
    - simulator_pose
    - simulator_coordinate
    - depth
    - distance
    - bbox
    - mask
    - area
    - trajectory
    - object_id
    - scene_id
qwen_generation_policy:
  local_qwen_allowed_for_runtime_code: true
  required_prompt_contract: reference_library/ONE_CLICK_SYNTHESIZER_CONTRACT.md
  output_must_be_one_click_synthesizer: true
  qwen_output_acceptance_gate: contract-checking
grey_policy:
  per_template_limit: 8
  deterministic_scorer_smoke_required: true
  small_batch_result_evaluation_required: true
  proxy_eval_allowed_when_external_models_missing: true
  cdm_irt_required: true
full_synthesis_policy:
  require_small_batch_eval_pass: true
  require_cdm_irt_pass_or_limited_pass: true
  require_difficulty_mix_pass: true
  model_visible_answers_removed: true
  evalset_media_path_prefix: ./images/
  evalset_root_answer_bearing_jsonl_forbidden: true
```

## 计划规则

- 必须把 GT kinship 转成多难度支持矩阵，而不是只检查远血缘链；easy/medium/hard 都必须有最低比例目标。
- 远血缘链仍可用于 hard/high-depth 模板，但 hard 也可以来自多对象排序、跨属性组合、集合多选等可程序化证据组合。
- `small-batch-result-evaluation` 和 `cdm-irt-analysis` 是 full-synthesis 前置门。没有外部模型配置时，计划必须允许 proxy eval，以保证 scorer、灰度矩阵和 CDM/IRT 诊断可执行。
- 必须把作答图像处理写入计划：图像可读、路径安全、overlay/crop 可生成，并最终保证模型可见媒体路径统一为 `./images/...`。
- 必须把 private GT 可见化策略写入计划：任何使用 simulator pose/coordinate、depth、bbox/mask、trajectory、object id、scene id 等字段的模板，都要指定 `required_visible_transform`，例如 RGB-depth pair、pose/map overlay、trajectory panel、candidate panel、bbox/point overlay；不能默认 raw RGB 足够。
- 必须写明 answerability proof schema 与阻塞规则：没有 proof 的 item 不进入灰度；proof 不能诚实说明模型可见证据时，模板 disabled。
- 必须写明图像低信息过滤策略：全黑/全白/近空/极小/不可解码图像不得进入 valid item。
- 必须把一键 synthesizer 写入计划：`generate_items.py` 是 canonical one-click item generator，本地 Qwen 只允许根据固定 contract 生成数据集专用薄 runtime，不能改变 Stage4 DAG、评分契约或隐藏答案规则。
- 必须把最终 `EVALSET_DATASET/data/test.jsonl` 无答案泄漏作为硬门，并声明 `EVALSET_DATASET` 根目录不保留带答案 JSONL，答案版只在 `ground_truth/` 或 Stage4 内部 artifact。

## 阻塞条件

- 无任何可用 Stage3 GT 或媒体。
- Stage1 能力目标完全无法映射到任何可执行父类模板族。
- easy/medium/hard 任一难度无可证据支持，且计划没有显式降低该难度目标。
- 冻结路径与 `WORKSPACE_ROOT/path_resolution.json` 冲突。
