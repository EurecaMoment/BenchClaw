---
name: benchclaw-stage4-template-metric-code-generation
description: Use for the specific BenchClaw node skill `stage4-template-metric-code-generation` only when its parent stage explicitly dispatches to it.
---

# Node Skill — 模板/指标/代码生成

## 角色

本节点把 Stage1 的模板/指标初稿和 Stage3 的证据 bundle 编译成可执行的 `data_20_template_metric_code_bundle`。产物必须能被后续 `grey-batch-validation` 直接批量实例化、评分和复核；不得只输出自然语言说明、空壳 manifest、不可运行的伪代码或未绑定证据的题目模板。

本节点新增 GT 血缘亲疏分析与高深度模板约束机制：模板编译不再只根据字段覆盖或统一模板来源决定是否启用，而必须优先利用 GT 图谱中“血缘较远但仍能共同支撑唯一答案”的推理链来构造高思维深度、高区分度、但仍然可回答的题目。

## Registered Subskill Names

本节点的内部流程在 opencode 中必须按顺序显式调用以下 skill 名：

- `gt-kinship-analysis` -> `benchclaw-stage4-gt-kinship-analysis`
- `template-compilation` -> `benchclaw-stage4-template-compilation`
- `metric-compilation` -> `benchclaw-stage4-metric-compilation`
- `answer-program-generation` -> `benchclaw-stage4-answer-program-generation`
- `contract-checking` -> `benchclaw-stage4-contract-checking`

## Subskill Context Return Protocol

每个 subskill 只返回：`status`、新增或更新的 artifact 路径、质量门 verdict、阻塞原因和一句摘要。不要把 GT 图谱长表、模板全文、答案程序全文、smoke test 长日志或整个 traceability 文件完整回灌到父节点。

## 总体原则

- 不得破坏现有 `data_20_template_metric_code_bundle` 目录结构、manifest、runtime_contract、synthesis_plan、smoke test、score_predictions 和 self-test 契约。
- 新增能力必须向后兼容。允许新增字段、新增 manifest、新增报告、新增 subskill 和新增 contract 校验，但不能让现有 enabled template 的基本字段失效。
- 远血缘 GT 链默认优先于仅字段覆盖驱动的浅层模板；但远血缘不是越远越好，必须满足“远但可答”。
- 不允许为了复杂而复杂。任何无法由现有媒体、证据和 GT 唯一推出答案的远血缘链都必须 `disabled` 或 `blocked`。
- 题干必须符合人类自然语言习惯；禁止字段名式、日志式、元数据泄漏式、机械翻译式表达。

## 内部层级

按顺序运行下列 subskill；运行时必须优先按已注册 skill 名调度，下面的路径仅用于源码定位。任一环节发现必需输入、字段契约、GT 血缘链契约、自然语言质量门或可执行性无法满足时，必须写本节点 `BLOCKED.json` 与 `BLOCKED.md`，停止本节点。

```text
subskills/gt-kinship-analysis/SKILL.md
subskills/template-compilation/SKILL.md
subskills/metric-compilation/SKILL.md
subskills/answer-program-generation/SKILL.md
subskills/contract-checking/SKILL.md
```

`gt-kinship-analysis` 必须先于 `template-compilation` 运行。`template-compilation` 只能优先从 `gt_distant_reasoning_chains.jsonl` 中 `status=selected` 的链里绑定可实例化模板。

## 必读模板与契约

启动本节点后，必须先读取并在 `nodes/template-metric-code-generation/USED_INPUTS.json` 中登记以下本 stage 模板文件。它们是本节点的硬契约，不是可选参考：

```text
BENCHCLAW_ROOT/skills/benchmark-stage4-build/templates/benchmark_item.schema.json
BENCHCLAW_ROOT/skills/benchmark-stage4-build/templates/DONE.schema.json
BENCHCLAW_ROOT/skills/benchmark-stage4-build/templates/BLOCKED.schema.json
BENCHCLAW_ROOT/skills/benchmark-stage4-build/templates/_stage_report.md
```

使用方式：

- `benchmark_item.schema.json`：定义每个可合成题目的最小字段集合；所有模板、答案程序和批量合成代码都必须能生成兼容该 schema 的 item。
- `DONE.schema.json`：约束节点完成记录；质量门未通过时不得写 `DONE.json`。
- `BLOCKED.schema.json`：约束阻塞记录；缺字段、缺媒体、缺 GT、代码不可运行、自然语言 lint 不通过或评分不可执行时使用。
- `_stage_report.md`：本节点 `NODE_REPORT.md` 的章节结构参考，尤其要记录冻结路径、输入、输出、GT 亲疏分析、自然语言检查、阻塞和质量门。

`BENCHCLAW_ROOT/templates/` 统一模板包是本节点选择题目模板的必需来源，不是可选参考。启动本节点后，还必须读取并登记以下统一模板包文件；缺失、不可读或校验失败时必须写 `BLOCKED`，不得退回到临时自造模板：

```text
BENCHCLAW_ROOT/templates/SKILL.md
BENCHCLAW_ROOT/templates/manifest.json
BENCHCLAW_ROOT/templates/template_library/benchclaw_fixed_template_registry.yaml
BENCHCLAW_ROOT/templates/template_library/templates_100_unified.index.json
BENCHCLAW_ROOT/templates/template_library/executable_template_coverage.json 或 executable_template_coverage.csv
BENCHCLAW_ROOT/templates/template_system/01_capability_map.md
BENCHCLAW_ROOT/templates/template_system/04_instantiation_rules.md
BENCHCLAW_ROOT/templates/template_system/06_quality_gates.md
BENCHCLAW_ROOT/templates/template_system/07_stage1_stage4_usage.md
```

## 外挂参考库：BenchClaw 图像/视频模板-指标适配层

本 skill 随包提供 `reference_library/` 作为外挂参考库，用于把统一模板包中的候选模板适配到 BenchClaw 当前的数据制造边界：图像/视频观测 + 仿真器或半监督标注 GT + 结构化答案 + 确定性自动评分。启动本节点后，必须读取并在 `USED_INPUTS.json` 中登记：

```text
reference_library/README.md
reference_library/BENCHCLAW_IMAGE_VIDEO_TEMPLATE_METRIC_LIBRARY.md
reference_library/template_family_registry.yaml
reference_library/answer_type_metric_registry.json
reference_library/schema_patch_notes.md
```

## 输入

- `data_10_capability_dimension_doc`
- `data_11_template_metric_initial_draft`
- `data_17_annotated_real_image_bundle`
- `data_18_annotated_existing_benchmark_bundle`
- `data_19_annotated_simulator_bundle`
- `stage4_execution_plan.yaml`

## 只读输入发现

1. 从冻结的 `WORKSPACE_ROOT/path_resolution.json` 校验 `PROJECT_ROOT`、`BENCHCLAW_ROOT`、`WORKSPACE_PARENT`、`WORKSPACE_ROOT`。
2. 从 `WORKSPACE_ROOT/stage4/nodes/stage4-plan-generation/stage4_execution_plan.yaml` 读取 Stage4 计划。
3. 从上游 artifact 或配置映射中定位 `data_10`、`data_11`、`data_17`、`data_18`、`data_19`；不得使用聊天上下文替代文件读取。
4. 读取 `data_10_capability_dimension_doc/capability_dimensions.md`、`q_matrix_seed.csv` 或等价能力维度文件，提取 `capability_id`、能力名称、定义、GT/字段依赖、排除项和计划题型；无法解析能力维度时必须阻塞。
5. 读取并校验统一模板包，建立 `primary_capability`、`canonical_question_type`、`required_fields`、`template_set`、`agent_selectable`、硬约束和覆盖矩阵索引。
6. 读取 `reference_library/` 外挂参考库，建立保留模板族、保留 answer type、保留 metric、允许 GT 来源和适配过滤规则；参考库缺失或不可读时必须阻塞。
7. 动态枚举 Stage3 bundle 中的 manifest、jsonl、媒体和 GT 文件；不要硬编码数据集名、仿真器名或字段名。
8. 生成字段目录和证据索引，记录每条可用 evidence 的来源、媒体路径、GT 字段、可见性/唯一性约束和可用于哪些统一模板。
9. 在模板编译前，必须完成 GT 血缘亲疏分析并生成 `gt_kinship/` 全套输出；若 `distant_chain_count=0`，必须将高深度模板全部置为 `disabled` 或整体 `blocked`。

若任一必需输入目录不存在、关键 json/jsonl/yaml/csv 不可读、媒体路径越界、GT 字段无法追溯，或 Stage1 能力维度无法映射到统一模板库中的可选模板，必须阻塞或将对应能力维度写入 disabled 记录并说明原因。

## GT 血缘亲疏分析与高深度模板约束

本节点不仅生成可执行模板，还必须利用 GT 图谱分析 GT 之间的亲疏关系。高质量模板默认优先使用远血缘 GT 链；但远血缘链必须可回答，不允许为了复杂而复杂。

每个 enabled 高深度模板必须有：

- `chain_id`
- `reasoning_chain_plan`
- `answerability_proof`
- `human_question_style`
- `reasoning_depth_score`
- `gt_distance_score`
- `template_quality_profile`

如果缺少远血缘链，不能伪造；必须 `disabled` 或 `blocked`，并在 `NODE_REPORT.md` 中解释覆盖缺口。

“长思考链”在本节点中必须写作 `evidence_reasoning_chain` 或 `reasoning_chain_plan`。它表示题目设计时必须依赖多个可验证证据步骤，而不是要求被评测模型显式输出私有 chain-of-thought。

## 处理流程

### 1. GT 血缘亲疏分析

调用已注册 skill `benchclaw-stage4-gt-kinship-analysis`：

- 从 Stage3 evidence index、field catalog、source inventory、annotated bundle 和 simulator privileged state 中建立 GT 节点、边和亲疏关系图谱。
- 产出 `near / medium / far / unreachable` 关系分布、可用远血缘链、过滤日志和报告。
- 只允许把 `status=selected` 且 `answerability_proof.*=true` 的链交给后续模板编译。

### 2. 模板编译

调用已注册 skill `benchclaw-stage4-template-compilation`：

- 以 `data_10` 的能力维度划分作为需求集合，逐个能力维度从 `BENCHCLAW_ROOT/templates/template_library/benchclaw_fixed_template_registry.yaml` 与 `templates_100_unified.index.json` 中选取需要的统一模板。
- 将选中的统一模板与 `data_11` 的模板/指标初稿、本 stage `benchmark_item.schema.json`、Stage3 字段目录、`gt_kinship/` 输出和 `reference_library/` 图像/视频适配规则对齐。
- 模板选择不再只看字段覆盖。对每个候选模板，必须优先绑定 `gt_distant_reasoning_chains.jsonl` 中 `status=selected` 的链。
- 每个 enabled 模板必须有 `gt_kinship_requirements`、`reasoning_chain_plan`、`difficulty_design`、`human_question_style` 和 `template_quality_profile`。
- 如果某个模板只能使用 near GT，则默认 `disabled`；只有 Stage4 plan 明确允许 low-depth baseline template 时，才可保留为辅助模板，并标注 `"depth_role": "baseline_low_depth"`。

### 3. 指标编译

调用已注册 skill `benchclaw-stage4-metric-compilation`：

- 为每个 `answer_format` 和 `metric_id` 生成指标定义与可执行评分入口。
- 指标仍只根据 item answer 与 prediction 判分。
- 链式信息只用于聚合和诊断，不得用于读取隐藏 GT 或为预测找补。
- 评分报告必须支持 `by_reasoning_hop_count`、`by_gt_distance_level`、`by_depth_role`、`by_chain_id`。

### 4. 答案程序与批量合成代码生成

调用已注册 skill `benchclaw-stage4-answer-program-generation`：

- 为每个通过模板生成答案程序，能从单条 evidence record 计算 `answer`，并解释 `answer_derivation`。
- 生成 `compute_reasoning_chain(record, template_config)`，用于输出可审计的紧凑证据推理链，而不是要求评测模型泄漏私有推理。
- `generate_items.py` 必须支持按 `--min-reasoning-hops`、`--min-gt-distance-level`、`--depth-role` 过滤生成样本。
- 对任何无法证明唯一答案、缺媒体、缺 GT、干扰项构造失败或题干不自然的样本，必须写入 `filtered_items.jsonl` 并给出明确原因。

### 5. 契约与可执行性检查

调用已注册 skill `benchclaw-stage4-contract-checking`：

- 校验模板、指标、答案程序、批量合成代码、GT kinship 输出和 traceability 是否互相引用完整。
- 对生成的 Python 代码执行语法检查和 smoke test。
- 使用本 stage `benchmark_item.schema.json` 校验 smoke test 生成的 item。
- 使用完美预测文件跑一次评分，必须得到可解释的满分或模板声明的确定性通过条件。
- 对至少一个错误预测或缺失预测跑负例检查，确认评分脚本不会恒定满分。
- 额外执行自然语言质量门与 answerability chain check；任一失败不得写 `DONE.json`。

## 产物结构

本节点只能写入：

```text
WORKSPACE_ROOT/stage4/
  nodes/template-metric-code-generation/
    USED_INPUTS.json
    DONE.json
    NODE_REPORT.md
    BLOCKED.json
    BLOCKED.md
  artifacts/data_20_template_metric_code_bundle/
    README.md
    source_inventory.jsonl
    field_catalog.yaml
    evidence_index.jsonl
    selected_template_sources.jsonl
    template_manifest.jsonl
    metric_manifest.jsonl
    code_manifest.json
    synthesis_plan.yaml
    traceability.csv
    templates/
      <template_id>.json
    metrics/
      <metric_id>.json
      <metric_id>.py
    answer_programs/
      <template_id>.py
    scripts/
      generate_items.py
      score_predictions.py
      validate_bundle.py
    contracts/
      benchmark_item.schema.json
      template_contract.schema.json
      metric_contract.schema.json
      runtime_contract.json
    references/
      BENCHCLAW_IMAGE_VIDEO_TEMPLATE_METRIC_LIBRARY.md
      template_family_registry.yaml
      answer_type_metric_registry.json
      schema_patch_notes.md
    gt_kinship/
      gt_node_catalog.jsonl
      gt_edge_catalog.jsonl
      gt_kinship_matrix.jsonl
      gt_distant_reasoning_chains.jsonl
      gt_chain_filter_log.jsonl
      gt_kinship_report.md
    tests/
      fixtures/
      smoke_test.py
    self_test/
      dry_run_items.jsonl
      perfect_predictions.jsonl
      negative_predictions.jsonl
      perfect_score_report.json
      negative_score_report.json
      py_compile.log
      self_test_report.md
```

## Handoff 契约

`grey-batch-validation` 只应通过 `data_20_template_metric_code_bundle` 中声明的公开入口消费本节点产物，不应重新解释 Stage1 初稿或直接读取 Stage3 私有字段。为此，本节点必须在 `synthesis_plan.yaml` 和 `contracts/runtime_contract.json` 中写清：

- `generate_command`
- `score_command`
- `validate_command`
- `enabled_templates`
- `disabled_templates`
- `selected_template_sources`
- `seed_policy`
- `filter_log_policy`
- `prediction_contract`
- `score_report_contract`
- `reference_policy`
- `gt_kinship_policy`

`gt_kinship_policy` 至少包含：

```json
{
  "chain_manifest": "gt_kinship/gt_distant_reasoning_chains.jsonl",
  "matrix_manifest": "gt_kinship/gt_kinship_matrix.jsonl",
  "filter_log": "gt_kinship/gt_chain_filter_log.jsonl",
  "min_reasoning_hops_default": 3,
  "min_gt_distance_level_default": "far",
  "default_depth_role": "high_depth"
}
```

## 高区分度模板设计规则

高区分度题目必须满足：

- 不是单点识别题，不能只问“图中有什么”。
- 默认至少需要 3 个推理步骤，例如先定位区域、再筛选对象、再比较关系、最后选择答案。
- 优先使用远血缘 GT 组合，例如对象类别 GT + 空间关系 GT + 可见性 GT，或区域 GT + 计数 GT + 相对位置 GT。
- 干扰项必须来自同场景、同语义层级、相近位置、相似类别、相近数值范围或同样可见但不满足关键关系的对象。
- 禁止主观题，如“哪个更重要”“哪个更漂亮”“哪个更适合”，除非 GT 中有明确任务目标约束。
- 如果多个对象都满足条件，必须改写为多选题、增加限定条件，或过滤该样本。

## 质量门

写 `DONE.json` 前必须同时满足：

- 已登记所有实际读取的输入和模板参考文件。
- 已读取 `data_10_capability_dimension_doc`，且每个 Stage1 能力维度都有对应的 selected、disabled 或 blocked 模板选择记录。
- `selected_template_sources.jsonl` 非空，且每个 enabled 模板都能追溯到统一模板包中的 `unified_template_id`、`primary_capability`、`required_fields` 和 `template_set`，并能映射到外挂参考库保留模板族。
- 至少有一个通过契约检查、可实例化、可评分的模板；若 Stage4 计划要求的能力维度无法覆盖，必须在报告中说明缺口。
- `gt_kinship_analysis = PASS`
- `distant_chain_count > 0`
- `enabled_high_depth_template_count > 0`
- `human_language_lint = PASS`
- `answerability_chain_check = PASS`
- 每个 enabled 高深度模板都具有非空 `chain_id`、`reasoning_chain_plan`、`answerability_proof`、`human_question_style`、`reasoning_depth_score` 和 `gt_distance_score`。
- 没有真实 GT 支撑时必须 disabled/blocked，不能伪造样本或伪造远血缘链。
- `python -m py_compile` 对生成的 `.py` 文件通过。
- `scripts/validate_bundle.py`、`tests/smoke_test.py`、完美预测评分和负例评分均已运行并记录结果。

## 输出

- `artifacts/data_20_template_metric_code_bundle/templates/`
- `artifacts/data_20_template_metric_code_bundle/metrics/`
- `artifacts/data_20_template_metric_code_bundle/answer_programs/`
- `artifacts/data_20_template_metric_code_bundle/scripts/`
- `artifacts/data_20_template_metric_code_bundle/gt_kinship/`

## 节点报告要求

`NODE_REPORT.md` 与 bundle README 必须新增：

- GT 亲疏关系概览；
- near / medium / far / unreachable 分布；
- 远血缘链数量；
- 各能力维度的远血缘链覆盖；
- enabled high-depth 模板数量；
- disabled/blocked 原因分布；
- 自然语言题干检查结果；
- 可回答性检查结果；
- 典型高深度模板示例；
- 后续 `grey-batch-validation` 如何按 `--min-reasoning-hops` 和 `--min-gt-distance-level` 生成题目。
