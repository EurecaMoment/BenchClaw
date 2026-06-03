# Subskill — 模板编译

## 目标

把 `data_11_template_metric_initial_draft` 中的自然语言模板初稿编译为可由程序实例化的模板 JSON。模板必须大量参考并服从本 stage 模板契约，尤其是：

```text
BENCHCLAW_ROOT/skills/benchmark-stage4-build/templates/benchmark_item.schema.json
BENCHCLAW_ROOT/skills/benchmark-stage4-build/templates/BLOCKED.schema.json
BENCHCLAW_ROOT/skills/benchmark-stage4-build/templates/DONE.schema.json
```

若 `BENCHCLAW_ROOT/templates/` 统一模板包存在，可读取其 `template_library/`、`template_system/04_instantiation_rules.md`、`template_system/06_quality_gates.md` 和 `schemas/question_template.schema.json` 作为模板族、质量门和题型参考；但最终输出必须以本 stage 的 `benchmark_item.schema.json` 为最低兼容目标。

## 输入

- `data_11_template_metric_initial_draft/templates.yaml` 或等价模板初稿文件
- `data_11_template_metric_initial_draft/metrics.yaml`
- `stage4_execution_plan.yaml`
- `source_inventory.jsonl`、`field_catalog.yaml`、`evidence_index.jsonl`；若尚未存在，本 subskill 必须先从 Stage3 bundle 建立它们
- 本 stage `templates/benchmark_item.schema.json`

## 处理

### 1. 建立字段目录

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

### 2. 编译模板定义

对每个候选模板生成一个 JSON 文件：

```text
artifacts/data_20_template_metric_code_bundle/templates/<template_id>.json
```

每个模板 JSON 至少包含：

- `template_id`：稳定 id；优先沿用 Stage1 id，冲突时加可追溯后缀。
- `template_family`：题型/模板族，不等同于能力维度。
- `source_template_refs`：来自 Stage1 初稿、本 stage 模板文件和可选统一模板包的引用。
- `question_pattern`：可填槽题面，槽位名称必须能从 evidence record 中解析。
- `slot_schema`：每个槽位的数据类型、来源字段、唯一性要求和格式化规则。
- `source_types`：允许的数据源类型，如 real_image、existing_benchmark、simulator。
- `required_evidence_fields`：必需 GT/证据字段。
- `optional_evidence_fields`：可改善质量但不阻塞的字段。
- `required_media`：需要的媒体类型和数量；不需要媒体时写明原因。
- `answer_format`：与指标和评分解析器一致。
- `metric_id`：必须能在 `metrics/` 找到实现。
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

### 3. 模板筛选原则

启用模板必须满足：

- 能生成符合 `benchmark_item.schema.json` 的 `item_id`、`media`、`question`、`answer`、`capability_tags`、`template_id`、`evidence_refs` 和 `metric_id`。
- 至少能在 Stage3 证据中找到 1 条真实样本通过所有 required 字段检查。
- 标准答案能由 GT、官方 label、人工标注、仿真器 privileged GT 或可复现计算得到。
- 单选、判断、帧选择、排序和区域题必须有唯一可验证答案；不唯一时进入过滤记录，不得随机选一个。
- 候选项必须来自同场景、同数据源、同语义层级或相近数值范围，不能用明显无关项凑数。
- 模板不得要求当前数据源没有的 navmesh、动作标签、3D 坐标、mask、depth 或语义地图；除非 Stage3 字段目录明确提供。

### 4. 输出汇总

写入：

```text
artifacts/data_20_template_metric_code_bundle/template_manifest.jsonl
artifacts/data_20_template_metric_code_bundle/traceability.csv
```

`template_manifest.jsonl` 每行记录一个模板的状态、能力、题型、指标、所需字段和可用样本数。

`traceability.csv` 至少包含列：

```text
template_id,template_family,metric_id,capability_tags,stage1_ref,stage4_template_refs,source_types,required_evidence_fields,enabled_sample_count,status,blocked_reason
```

## 失败与阻塞

以下情况必须向主节点报告阻塞：

- `data_11` 模板初稿缺失或无法解析。
- 本 stage `benchmark_item.schema.json` 缺失或无法读取。
- Stage3 三类证据 bundle 全部不可用，且执行计划没有明确允许空分支。
- 所有模板都无法找到真实 evidence 或可验证 GT。
- 模板需要的关键字段来自工具推断，但没有官方/人工/仿真器 GT 支撑。

只有部分模板失败时，不阻塞整个节点；将失败模板写为 `blocked` 或 `disabled`，并保留可执行模板继续后续子 skill。
