# Subskill — 模板编译

## 目标

把 `data_10_capability_dimension_doc` 中的能力维度规划和 `data_11_template_metric_initial_draft` 中的模板/指标初稿，编译为可由程序实例化的模板 JSON。模板选择必须先根据 Stage1 能力维度划分，从 `BENCHCLAW_ROOT/templates/` 统一模板包中选取需要的模板；不得直接把自然语言初稿改写成未登记来源的 enabled 模板。

```text
BENCHCLAW_ROOT/skills/benchmark-stage4-build/templates/benchmark_item.schema.json
BENCHCLAW_ROOT/skills/benchmark-stage4-build/templates/BLOCKED.schema.json
BENCHCLAW_ROOT/skills/benchmark-stage4-build/templates/DONE.schema.json
```

统一模板包是必需选择源，必须读取并登记：

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
BENCHCLAW_ROOT/templates/schemas/question_template.schema.json
```

同时必须读取本 skill 的外挂参考库并登记到 USED_INPUTS：

```text
reference_library/BENCHCLAW_IMAGE_VIDEO_TEMPLATE_METRIC_LIBRARY.md
reference_library/template_family_registry.yaml
reference_library/answer_type_metric_registry.json
reference_library/schema_patch_notes.md
```

最终输出必须同时满足：统一模板包决定模板来源与硬约束，本 stage `benchmark_item.schema.json` 决定 item 兼容格式。

## 输入

- `data_10_capability_dimension_doc/capability_dimensions.md`
- `data_10_capability_dimension_doc/q_matrix_seed.csv` 或等价能力/Q-matrix 文件
- `data_11_template_metric_initial_draft/templates.yaml` 或等价模板初稿文件
- `data_11_template_metric_initial_draft/metrics.yaml`
- `stage4_execution_plan.yaml`
- `source_inventory.jsonl`、`field_catalog.yaml`、`evidence_index.jsonl`；若尚未存在，本 subskill 必须先从 Stage3 bundle 建立它们
- 本 stage `templates/benchmark_item.schema.json`
- 统一模板包的 registry、index、coverage、能力映射、实例化规则和质量门文件
- 本 skill `reference_library/` 中的图像/视频适配模板族、answer type、metric registry 和 schema patch notes

## 处理

### 1. 读取能力维度与统一模板库

1. 解析 `data_10_capability_dimension_doc`，建立 Stage1 能力需求表，至少包含：
   - `capability_id`、能力名称、定义和排除项；
   - 计划题型、输入模态、答案格式、GT/字段依赖；
   - `q_matrix_seed.csv` 中声明的能力维度到题目/模板族关系；
   - `data_11` 中每个模板初稿对能力维度的引用。
2. 读取 `benchclaw_fixed_template_registry.yaml`、`templates_100_unified.index.json` 和 `executable_template_coverage.*`，建立统一模板表，至少包含：
   - `template_id`、`template_set`、`primary_capability`、`canonical_question_type`；
   - `status`、`agent_selectable`、`deprecated_locked`/replacement 信息；
   - `required_fields`、`evidence_policy`、`hard_constraints` 和覆盖统计。
3. 读取 `reference_library/template_family_registry.yaml` 和 `answer_type_metric_registry.json`，建立 BenchClaw 图像/视频适配表，至少包含保留 `template_family`、允许 `media_types`、允许 `answer_types`、主指标、GT 来源和 required evidence examples。
4. 必须运行或复核统一模板包校验：

```bash
cd "$BENCHCLAW_ROOT/templates" && python tools/validate_strict_template_library.py
```

校验失败、命令不存在、registry/index 解析失败或模板包内部声明互相矛盾时，必须向主节点报告 `BLOCKED`。

### 2. 建立字段目录

从 Stage3 三类 bundle 动态提取字段，不硬编码数据集名称：

- `data_17_annotated_real_image_bundle`：媒体、清洗样本、标注记录、review queue、evidence manifest。
- `data_18_annotated_existing_benchmark_bundle`：媒体、官方 label、新增标注、review queue、evidence manifest。
- `data_19_annotated_simulator_bundle`：观测、cleaned state logs、privileged GT、标注记录、evidence manifest。

写入或更新：

```text
artifacts/data_20_template_metric_code_bundle/source_inventory.jsonl
artifacts/data_20_template_metric_code_bundle/field_catalog.yaml
artifacts/data_20_template_metric_code_bundle/evidence_index.jsonl
```

字段目录至少记录：

- 字段路径和数据类型；
- 字段来源 artifact、数据源类型、样本 id；
- 是否为官方 GT、人工标注、仿真器 privileged GT、工具生成辅助字段或普通元数据；
- 媒体路径是否存在、是否在 workspace 内；
- 是否能支持唯一答案、候选项构造、可见性检查和评分。

### 3. 根据能力维度选择统一模板

对每个 Stage1 能力维度，必须执行下列选择流程：

1. 先用能力维度的 `capability_id`、名称、定义、q-matrix 标签和 `data_11` 引用，与统一模板表的 `primary_capability` 和 `template_system/01_capability_map.md` 做映射；映射不是精确同名时，必须在选择记录中写明推断依据。
2. 默认候选只来自 registry 的 `template_sets.strict_core`；若某能力维度在 `strict_core` 中无覆盖，才可查看 `strict_all_supported` 中同 `primary_capability` 的模板。
3. 只有 `field_catalog.yaml` 证明存在可靠 depth/depth-derived 字段时，才允许选入 `strict_depth` 模板；temporal、pose、3D、mask、bbox、segmentation、nav/action 类模板必须逐项证明 `required_fields` 在 Stage3 真实 evidence 中可追溯。
4. 先按外挂参考库过滤候选：候选模板必须能映射到 10 类保留模板族之一，媒体类型必须为 image/multi_image/video/image_pair/video_clip，answer_format 必须能映射到 `choice`、`bool`、`number`、`point2d`、`bbox2d`、`mask`、`ordered_list`、`action_sequence` 或 `relation_tuple`，主指标必须能映射到保留 deterministic metric。
5. 排除所有 `deprecated_locked`、`agent_selectable: false`、状态为 `DEPRECATED`/locked、存在替代模板但未使用替代、违反硬约束、题面会泄漏 GT 字段名、或 required fields 不能被真实 evidence 支撑的模板。
6. 对每个能力维度选择满足字段和证据条件的最小模板集合：优先覆盖核心能力、可自动评分、答案唯一、证据样本充足的模板；不得为了增加数量选择与能力维度无关的模板。
7. 如果某能力维度没有任何可选模板，必须写 disabled/blocked 记录，说明是能力映射缺失、字段缺失、证据不足、模板被锁定，还是答案唯一性无法保证。

写入：

```text
artifacts/data_20_template_metric_code_bundle/selected_template_sources.jsonl
```

每行记录一个能力维度到统一模板的选择或禁用结果，至少包含：

- `capability_id`、`capability_name`、`stage1_refs`；
- `unified_template_id`、`template_set`、`primary_capability`、`canonical_question_type`；
- `required_fields`、`field_coverage_status`、`missing_fields`；
- `reference_template_family`、`reference_answer_type`、`reference_metric_id`、`reference_policy_status`；
- `evidence_sample_count`、`source_types`、`answer_uniqueness_status`；
- `selection_status`：`selected`、`disabled` 或 `blocked`；
- `selection_reason` 和 `template_package_refs`。

### 4. 编译模板定义

只允许对 `selected_template_sources.jsonl` 中 `selection_status=selected` 的统一模板生成 enabled 模板 JSON。对 disabled/blocked 记录不得生成 enabled 运行时模板。

对每个选中的统一模板生成一个 JSON 文件：

```text
artifacts/data_20_template_metric_code_bundle/templates/<template_id>.json
```

每个模板 JSON 至少包含：

- `template_id`：稳定 id；优先沿用 Stage1 id，冲突时加可追溯后缀。
- `unified_template_id`：必须对应 `BENCHCLAW_ROOT/templates/template_library/templates_100_unified.index.json` 中的 `template_id`。
- `capability_dimension_refs`：来自 `data_10` 的能力维度 id/名称/证据引用。
- `template_family`：题型/模板族，不等同于能力维度；必须能映射到外挂参考库保留模板族。
- `reference_template_family`：外挂参考库中的 T1–T10 模板族 id/name，用于说明本模板为何适配 BenchClaw 图像/视频数据边界。
- `source_template_refs`：来自 `data_10`、Stage1 初稿、本 stage 模板文件和统一模板包的引用，必须包含统一模板包文件路径和 `unified_template_id`。
- `question_pattern`：可填槽题面，槽位名称必须能从 evidence record 中解析。
- `slot_schema`：每个槽位的数据类型、来源字段、唯一性要求和格式化规则。
- `source_types`：允许的数据源类型，如 real_image、existing_benchmark、simulator。
- `required_evidence_fields`：必需 GT/证据字段。
- `optional_evidence_fields`：可改善质量但不阻塞的字段。
- `required_media`：需要的图像/视频媒体类型和数量；enabled 模板必须声明 image、multi_image、video、image_pair 或 video_clip 中至少一种媒体需求。
- `answer_format`：与指标和评分解析器一致，且能映射到外挂参考库保留 answer type。
- `metric_id`：必须能在 `metrics/` 找到实现，且主指标能映射到外挂参考库保留 deterministic metric。
- `capability_tags`：来自 Stage1 能力维度或执行计划。
- `instantiation_algorithm`：从 evidence record 生成 question/options/answer/media/evidence_refs 的步骤。
- `quality_gates`：字段可得性、答案唯一性、视觉可辨性、候选项质量、可追溯性。
- `failure_conditions`：触发过滤或阻塞的条件。
- `grey_quota`：小批量验证最小样本数。
- `full_quota_hint`：全量合成建议上限或采样策略。
- `status`：`enabled`、`disabled` 或 `blocked`。
- `blocked_reason`：仅当模板无法实例化时填写。

同时生成：

```text
artifacts/data_20_template_metric_code_bundle/contracts/template_contract.schema.json
```

该 contract schema 必须把上述字段列为模板定义的 required 或 conditional required 字段，并约束：

- `status=enabled` 时必须有 `metric_id`、`instantiation_algorithm`、`quality_gates`、`grey_quota` 和至少 1 条可用 evidence 统计。
- `required_evidence_fields` 必须为非空数组；若缺 GT，只能把模板置为 `blocked` 或 `disabled` 并说明原因，不能生成 enabled 评测题。
- `source_template_refs` 必须记录 Stage1 初稿引用；若使用了统一模板包，也要记录具体文件或 template id。
- `unified_template_id` 和 `capability_dimension_refs` 必须为 required 字段；`status=enabled` 时二者不得为空。
- `reference_template_family`、`reference_answer_type`、`reference_metric_id` 必须为 enabled 模板的 required 字段；无法映射时只能 disabled/blocked。

### 5. 模板筛选原则

启用模板必须满足：

- 已在 `selected_template_sources.jsonl` 中标为 `selected`，且可追溯到统一模板包中的可选模板，并通过外挂参考库适配过滤。
- 能生成符合 `benchmark_item.schema.json` 的 `item_id`、`media`、`question`、`answer`、`capability_tags`、`template_id`、`evidence_refs` 和 `metric_id`。
- 至少能在 Stage3 证据中找到 1 条真实样本通过所有 required 字段检查。
- 标准答案能由 GT、官方 label、人工标注、仿真器 privileged GT 或可复现计算得到。
- 单选、判断、帧选择、排序和区域题必须有唯一可验证答案；不唯一时进入过滤记录，不得随机选一个。
- 候选项必须来自同场景、同数据源、同语义层级或相近数值范围，不能用明显无关项凑数。
- 模板不得要求当前数据源没有的 navmesh、动作标签、3D 坐标、mask、depth 或语义地图；除非 Stage3 字段目录明确提供。即使存在仿真器 3D 状态，也只能作为 GT/证据来源编译成图像/视频可观察题，不应要求模型直接输出 point-cloud instance id 或 3D bbox。
- 模板题面不得出现 GT 字段名、object_id、depth_median 等隐藏元数据；数值题必须按统一模板包要求区间化。

### 6. 输出汇总

写入：

```text
artifacts/data_20_template_metric_code_bundle/selected_template_sources.jsonl
artifacts/data_20_template_metric_code_bundle/template_manifest.jsonl
artifacts/data_20_template_metric_code_bundle/traceability.csv
```

`template_manifest.jsonl` 每行记录一个模板的状态、能力、题型、指标、所需字段、可用样本数和统一模板来源。

`traceability.csv` 至少包含列：

```text
template_id,unified_template_id,template_set,template_family,reference_template_family,reference_answer_type,reference_metric_id,metric_id,capability_tags,capability_dimension_refs,stage1_ref,stage4_template_refs,source_types,required_evidence_fields,enabled_sample_count,status,blocked_reason
```

## 失败与阻塞

以下情况必须向主节点报告阻塞：

- `data_11` 模板初稿缺失或无法解析。
- `data_10` 能力维度文档缺失、无法解析，或没有可供模板选择的能力维度。
- 本 stage `benchmark_item.schema.json` 缺失或无法读取。
- `BENCHCLAW_ROOT/templates/` 统一模板包、registry、index、coverage 或校验命令缺失/失败。
- Stage3 三类证据 bundle 全部不可用，且执行计划没有明确允许空分支。
- 所有模板都无法找到真实 evidence 或可验证 GT。
- 所有候选模板都无法映射到外挂参考库保留模板族、answer type 或 deterministic metric。
- 所有 Stage1 能力维度都无法映射到统一模板包中的可选模板。
- 模板需要的关键字段来自工具推断，但没有官方/人工/仿真器 GT 支撑。

只有部分模板失败时，不阻塞整个节点；将失败模板写为 `blocked` 或 `disabled`，并保留可执行模板继续后续子 skill。
