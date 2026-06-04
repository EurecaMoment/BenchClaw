# Subskill — 答案程序生成

## 目标

为每个 enabled 模板生成可运行的答案程序和批量合成代码，使 `grey-batch-validation` 能直接从 `data_20_template_metric_code_bundle` 生成小批量 item、验证标准答案、运行评分脚本并追溯每道题的证据来源。

## 输入

- `templates/<template_id>.json`
- `metrics/<metric_id>.json`
- `selected_template_sources.jsonl`
- `metric_manifest.jsonl`
- `source_inventory.jsonl`
- `field_catalog.yaml`
- `evidence_index.jsonl`
- 本 stage `templates/benchmark_item.schema.json`

每个 enabled 模板必须先在 `selected_template_sources.jsonl` 中有 `selection_status=selected` 的统一模板来源记录；答案程序不得为没有 `unified_template_id` 来源的模板生成可运行入口。

## 代码产物

生成代码必须写入：

```text
artifacts/data_20_template_metric_code_bundle/answer_programs/<template_id>.py
artifacts/data_20_template_metric_code_bundle/scripts/generate_items.py
artifacts/data_20_template_metric_code_bundle/scripts/score_predictions.py
artifacts/data_20_template_metric_code_bundle/scripts/validate_bundle.py
artifacts/data_20_template_metric_code_bundle/tests/smoke_test.py
artifacts/data_20_template_metric_code_bundle/code_manifest.json
artifacts/data_20_template_metric_code_bundle/synthesis_plan.yaml
artifacts/data_20_template_metric_code_bundle/contracts/runtime_contract.json
```

代码优先使用 Python 标准库。确需第三方库时，必须写入 `code_manifest.json` 的 `runtime_dependencies` 并在 `validate_bundle.py` 中给出清晰缺依赖错误；不得静默降级或联网安装。

## 每模板答案程序接口

每个 `answer_programs/<template_id>.py` 必须暴露：

```python
TEMPLATE_ID = "<template_id>"

def supports(record, template_config):
    """Return (ok: bool, reason: str)."""

def build_item(record, template_config, *, rng=None, item_index=0):
    """Return a benchmark item dict compatible with benchmark_item.schema.json."""

def compute_answer(record, template_config):
    """Return the gold answer derived from GT/evidence."""

def evidence_refs(record, template_config):
    """Return stable evidence references used by this item."""
```

`build_item` 生成的 item 必须至少包含：

```python
item_id
media
question
answer
capability_tags
template_id
evidence_refs
metric_id
```

允许额外写入 `source_sample_id`、`options`、`answer_format`、`answer_derivation`、`quality_gate`、`metadata` 等字段，但不能缺少本 stage schema 必需字段。

## 答案生成规则

- 答案只能来自 record 中的官方 label、人工标注、仿真器 privileged GT、Stage3 明确授权 GT 或可复现计算。
- `compute_answer` 必须是确定性的；同一 record、同一模板、同一 seed 下输出一致。
- 单选题必须构造且只构造一个正确选项；干扰项要来自同场景、同数据源、同语义层级或相近数值范围。
- 判断题应尽量支持正负成对构造，并记录 pair/group id，便于 Accuracy+。
- 多选题的 gold answer 必须是去重集合；输出顺序不得影响评分。
- 数值题必须写明单位和容差来源；没有单位或容差无法解释时禁用该模板。
- 需要媒体的题必须验证 `media` 中每个路径存在、在 `WORKSPACE_ROOT` 内或是已登记的稳定 workspace 相对路径。
- 视觉题若目标不可见、过小、遮挡、同类实例不可区分或字段无法确认可见性，必须由 `supports` 返回失败，不得生成 item。

## 批量合成入口

`scripts/generate_items.py` 必须支持：

```bash
python scripts/generate_items.py \
  --bundle <data_20_bundle_dir> \
  --evidence-index <evidence_index.jsonl> \
  --out <items.jsonl> \
  --limit <N> \
  --seed <int> \
  --template-id <optional_template_id>
```

要求：

- 按 template manifest、evidence index 和配额批量生成 item。
- 生成前校验 template manifest 与 `selected_template_sources.jsonl` 一致；没有统一模板来源、被 disabled/blocked 或 required fields 不满足的模板必须跳过并记录过滤原因。
- 支持按 `template_id` 单模板运行，方便灰度定位。
- 记录过滤原因到同目录 `filtered_items.jsonl` 或命令行指定路径。
- 对每个 enabled 模板至少尝试 `grey_quota` 条 evidence；不足时写入过滤/缺口记录。
- 输出 jsonl 的每一行都可被 `validate_bundle.py` 和 `tests/smoke_test.py` 校验。

`synthesis_plan.yaml` 必须把上述命令实例化为后续节点可直接执行的计划，至少包含：

```yaml
bundle_version: stage4-data20-v1
default_seed: 0
entrypoints:
  generate_items: scripts/generate_items.py
  score_predictions: scripts/score_predictions.py
  validate_bundle: scripts/validate_bundle.py
grey_batch:
  output: ../data_21_grey_validation_report/generated_items.jsonl
  filtered_output: ../data_21_grey_validation_report/filtered_items.jsonl
  per_template_quota_field: grey_quota
full_synthesis:
  per_template_quota_field: full_quota_hint
templates:
  - template_id: example
    status: enabled
    metric_id: example_metric
    source_types: []
    grey_quota: 1
```

路径可以是 bundle 相对路径、调用节点工作目录相对路径或命令行可覆盖路径；不得写死当前机器的绝对路径。

## 评分入口

`scripts/score_predictions.py` 必须支持：

```bash
python scripts/score_predictions.py \
  --bundle <data_20_bundle_dir> \
  --gold <items.jsonl> \
  --pred <predictions.jsonl> \
  --out <score_report.json>
```

预测文件每行至少包含：

```json
{"item_id": "...", "prediction": "..."}
```

评分报告至少包含：

- `overall`
- `by_template`
- `by_metric`
- `by_capability`
- `by_source_type`
- `items`
- `missing_predictions`
- `invalid_predictions`

## Bundle 校验入口

`scripts/validate_bundle.py` 必须检查：

- 必需目录和 manifest 是否存在。
- 模板、指标、答案程序互相引用是否完整。
- enabled 模板是否有可导入答案程序和可执行指标。
- `contracts/benchmark_item.schema.json` 是否与本 stage schema 兼容。
- smoke fixture 或 dry-run item 是否符合 schema。
- 媒体路径是否存在或被明确声明为无需媒体。
- `synthesis_plan.yaml` 和 `contracts/runtime_contract.json` 是否提供后续节点所需的公开入口。

## Smoke fixture

为每个 enabled 模板生成最小 fixture：

```text
tests/fixtures/<template_id>.record.json
tests/fixtures/<template_id>.expected_item.json
```

fixture 可以是从真实 Stage3 evidence 抽取的最小字段子集，但必须保留真实来源引用；不得构造与 Stage3 无关的虚假 GT。若真实 evidence 不足，模板必须标记为 disabled/blocked，而不是伪造 fixture。

## 自测输出

本 subskill 应准备或生成以下文件，供 `contract-checking` 运行：

```text
self_test/dry_run_items.jsonl
self_test/perfect_predictions.jsonl
self_test/negative_predictions.jsonl
```

`perfect_predictions.jsonl` 的 prediction 必须来自每条 item 的 gold answer；`negative_predictions.jsonl` 至少对每种主指标制造一个可降分预测。

## 失败与阻塞

以下情况必须向主节点报告阻塞：

- enabled 模板无法生成答案程序。
- 答案程序不能从真实 evidence 计算答案。
- 批量合成入口无法在无网络、只读输入条件下运行。
- 评分入口无法导入指标实现。
- 所有模板都无法生成 smoke fixture。

部分模板失败时，将该模板改为 `disabled` 或 `blocked`，更新 manifest 和 traceability，并继续处理其他模板。
