# Node Skill — 模板/指标/代码生成

## 角色

本节点把 Stage1 的模板/指标初稿和 Stage3 的证据 bundle 编译成可执行的 `data_20_template_metric_code_bundle`。产物必须能被后续 `grey-batch-validation` 直接批量实例化、评分和复核；不得只输出自然语言说明、空壳 manifest、不可运行的伪代码或未绑定证据的题目模板。

## 内部层级

按顺序运行下列 subskill；任一环节发现必需输入、字段契约或可执行性无法满足时，必须写本节点 `BLOCKED.json` 与 `BLOCKED.md`，停止本节点。

```text
subskills/template-compilation/SKILL.md
subskills/metric-compilation/SKILL.md
subskills/answer-program-generation/SKILL.md
subskills/contract-checking/SKILL.md
```

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
- `BLOCKED.schema.json`：约束阻塞记录；缺字段、缺媒体、缺 GT、代码不可运行或评分不可执行时使用。
- `_stage_report.md`：本节点 `NODE_REPORT.md` 的章节结构参考，尤其要记录冻结路径、输入、输出、阻塞和质量门。

若 `BENCHCLAW_ROOT/templates/` 统一模板包存在，可作为增强参考读取：优先使用其中的模板库、题型、指标、质量门和样例，但不得覆盖本 stage 的本地 schema 与目录契约。若该目录不存在，本节点仍必须仅凭 Stage1 初稿、Stage3 证据和本 stage `templates/` 完成编译。

## 输入

- `data_11_template_metric_initial_draft`
- `data_17_annotated_real_image_bundle`
- `data_18_annotated_existing_benchmark_bundle`
- `data_19_annotated_simulator_bundle`
- `stage4_execution_plan.yaml`

## 只读输入发现

1. 从冻结的 `WORKSPACE_ROOT/path_resolution.json` 校验 `PROJECT_ROOT`、`BENCHCLAW_ROOT`、`WORKSPACE_PARENT`、`WORKSPACE_ROOT`。
2. 从 `WORKSPACE_ROOT/stage4/nodes/stage4-plan-generation/stage4_execution_plan.yaml` 读取 Stage4 计划。
3. 从上游 artifact 或配置映射中定位 `data_11`、`data_17`、`data_18`、`data_19`；不得使用聊天上下文替代文件读取。
4. 动态枚举 Stage3 bundle 中的 manifest、jsonl、媒体和 GT 文件；不要硬编码数据集名、仿真器名或字段名。
5. 生成字段目录和证据索引，记录每条可用 evidence 的来源、媒体路径、GT 字段、可见性/唯一性约束和可用于哪些模板。

若任一必需输入目录不存在、关键 json/jsonl/yaml 不可读、媒体路径越界或 GT 字段无法追溯，必须阻塞。

## 处理流程

### 1. 模板编译

调用 `subskills/template-compilation/SKILL.md`：

- 将 `data_11` 的模板初稿与本 stage `benchmark_item.schema.json`、Stage3 字段目录、可选统一模板包对齐。
- 为每个候选模板生成机器可读模板定义，至少包含 `template_id`、`template_family`、`question_pattern`、`source_types`、`required_evidence_fields`、`required_media`、`answer_format`、`metric_id`、`capability_tags`、`instantiation_algorithm`、`quality_gates`、`failure_conditions`、`grey_quota` 和 `full_quota_hint`。
- 禁用或阻塞无法由 Stage3 证据唯一回答的模板；不得为了覆盖率编造 GT、常识答案或虚构媒体。

### 2. 指标编译

调用 `subskills/metric-compilation/SKILL.md`：

- 为每个 `answer_format` 和 `metric_id` 生成指标定义与可执行评分入口。
- 指标必须声明输入解析、归一化、容差、聚合维度、不适用条件和失败返回。
- 优先使用可自动评分指标：exact/accuracy、set exact、F1、数值误差/容差、排序、IoU、成对 Accuracy+。开放问答或 LLM-as-judge 只能作为辅助指标，且必须有固定 rubric、judge 配置和人工抽查说明。

### 3. 答案程序与批量合成代码生成

调用 `subskills/answer-program-generation/SKILL.md`：

- 为每个通过模板生成答案程序，能从单条 evidence record 计算 `answer`，并解释 `answer_derivation`。
- 生成批量合成入口，能按模板、数据源、配额和随机种子批量输出兼容 `benchmark_item.schema.json` 的 jsonl item。
- 生成评分入口，能读取 gold jsonl 与 prediction jsonl，输出 item 级和聚合指标。
- 生成最小 fixture 与 smoke test，覆盖每个模板至少 1 条成功样例；若真实 evidence 不足以覆盖某模板，该模板必须标为 blocked/disabled，不能用伪造真实样本冒充。
- 生成 `synthesis_plan.yaml`，明确后续 `grey-batch-validation` 和 `full-synthesis` 应调用哪些模板、脚本、配额、随机种子和过滤记录路径。

### 4. 契约与可执行性检查

调用 `subskills/contract-checking/SKILL.md`：

- 校验模板、指标、答案程序、批量合成代码和 traceability 是否互相引用完整。
- 对生成的 Python 代码执行语法检查和 smoke test。
- 使用本 stage `benchmark_item.schema.json` 校验 smoke test 生成的 item。
- 使用完美预测文件跑一次评分，必须得到可解释的满分或模板声明的确定性通过条件。
- 对至少一个错误预测或缺失预测跑负例检查，确认评分脚本不会恒定满分。

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

`contracts/benchmark_item.schema.json` 必须复制或等价保存本 stage `templates/benchmark_item.schema.json` 的内容，便于后续节点脱离 skill 源目录验证产物。所有生成代码必须使用相对 bundle 路径或命令行参数解析路径，不得写入 machine-specific 绝对路径。

## Handoff 契约

`grey-batch-validation` 只应通过 `data_20_template_metric_code_bundle` 中声明的公开入口消费本节点产物，不应重新解释 Stage1 初稿或直接读取 Stage3 私有字段。为此，本节点必须在 `synthesis_plan.yaml` 和 `contracts/runtime_contract.json` 中写清：

- `generate_command`：灰度和全量合成 item 的标准命令模板。
- `score_command`：评分预测文件的标准命令模板。
- `validate_command`：验证 bundle 与 item jsonl 的标准命令模板。
- `enabled_templates`：可运行模板列表、灰度配额、全量配额建议和 source type 限制。
- `disabled_templates`：禁用模板及原因，供报告解释覆盖缺口。
- `seed_policy`：默认 seed、按模板派生 seed 的方式，以及需要固定顺序的字段。
- `filter_log_policy`：过滤样本的 jsonl 路径、字段和原因枚举。
- `prediction_contract`：预测文件必需字段、允许的 answer 格式和无效预测处理。
- `score_report_contract`：评分报告必需字段和聚合维度。

`runtime_contract.json` 至少包含：

```json
{
  "bundle_version": "stage4-data20-v1",
  "entrypoints": {
    "generate_items": "scripts/generate_items.py",
    "score_predictions": "scripts/score_predictions.py",
    "validate_bundle": "scripts/validate_bundle.py"
  },
  "required_manifests": [
    "template_manifest.jsonl",
    "metric_manifest.jsonl",
    "code_manifest.json",
    "traceability.csv"
  ],
  "item_schema": "contracts/benchmark_item.schema.json"
}
```

## 质量门

写 `DONE.json` 前必须同时满足：

- 已登记所有实际读取的输入和模板参考文件。
- 至少有一个通过契约检查、可实例化、可评分的模板；若 stage4 计划要求的能力维度无法覆盖，必须在报告中说明缺口。
- 每个 enabled 模板都有对应模板 JSON、答案程序、指标定义、traceability 记录和 smoke fixture。
- 每个 enabled `metric_id` 都有可执行评分实现或明确的外部评估协议；主指标不得只有 LLM-as-judge。
- `python -m py_compile` 对生成的 `.py` 文件通过。
- `scripts/validate_bundle.py`、`tests/smoke_test.py`、完美预测评分和负例评分均已运行并记录结果。
- `self_test/dry_run_items.jsonl` 中每条 item 均符合本 stage `benchmark_item.schema.json`，且 `media` 路径存在或被明确标记为不需要媒体的可验证文本/状态题。

## 输出

- `artifacts/data_20_template_metric_code_bundle/templates/`
- `artifacts/data_20_template_metric_code_bundle/metrics/`
- `artifacts/data_20_template_metric_code_bundle/answer_programs/`
- `artifacts/data_20_template_metric_code_bundle/scripts/`
- `artifacts/data_20_template_metric_code_bundle/contracts/`
- `artifacts/data_20_template_metric_code_bundle/tests/`
- `artifacts/data_20_template_metric_code_bundle/self_test/`
- `artifacts/data_20_template_metric_code_bundle/traceability.csv`
- 节点执行记录文件
