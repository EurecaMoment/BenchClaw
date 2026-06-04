# Subskill — 指标编译

## 目标

为每个 enabled 模板编译可执行、可解释、可聚合的评分指标。指标必须能被 `answer_programs/` 和 `scripts/score_predictions.py` 调用，并能对后续合成出的 item 进行自动评分或明确声明外部评估协议。

## 输入

- `artifacts/data_20_template_metric_code_bundle/templates/<template_id>.json`
- `artifacts/data_20_template_metric_code_bundle/selected_template_sources.jsonl`
- `artifacts/data_20_template_metric_code_bundle/template_manifest.jsonl`
- `data_11_template_metric_initial_draft/metrics.yaml`
- `stage4_execution_plan.yaml`
- 本 stage `templates/benchmark_item.schema.json`
- 统一模板包中的 `template_system/05_metrics_and_scoring.md`，以及已选模板的 `unified_template_id`、`canonical_question_type`、`answer_format` 来源记录

## 指标契约

每个指标写入：

```text
artifacts/data_20_template_metric_code_bundle/metrics/<metric_id>.json
artifacts/data_20_template_metric_code_bundle/metrics/<metric_id>.py
artifacts/data_20_template_metric_code_bundle/contracts/metric_contract.schema.json
```

指标 JSON 至少包含：

- `metric_id`
- `metric_family`
- `answer_formats`
- `input_gold_type`
- `input_prediction_type`
- `normalization`
- `parser_contract`
- `score_range`
- `aggregation`
- `failure_policy`
- `not_applicable_conditions`
- `primary_or_auxiliary`
- `template_ids`
- `implementation_entrypoint`

指标 Python 必须暴露稳定接口：

```python
def parse_prediction(raw):
    ...

def score_one(gold, prediction, item=None, metric_config=None):
    ...

def aggregate(item_scores):
    ...
```

`score_one` 返回结构必须至少包含：

```python
{
    "score": 0.0,
    "passed": False,
    "details": {},
    "error": None
}
```

不得因为预测缺失、格式错误或指标不适用而抛出未捕获异常；必须返回可记录的失败结构。

`metric_contract.schema.json` 必须约束每个 metric JSON：

- `metric_id`、`metric_family`、`answer_formats`、`score_range`、`aggregation`、`primary_or_auxiliary`、`template_ids`、`implementation_entrypoint` 必填。
- `primary_or_auxiliary=primary` 时必须有本地 Python 实现，不能只写外部说明。
- `metric_family=llm_match` 或 `rubric_match` 时必须包含 `rubric`、`judge_config`、`manual_review_policy`，且默认只能作为 auxiliary。
- 数值指标必须包含 `tolerance_policy` 或明确声明 exact numeric scoring。
- 区域/mask 指标必须包含候选区域来源或 mask/bbox 字段契约。

## 推荐指标映射

优先使用可自动评分指标：

| answer_format | 主指标 | 辅助指标 |
|---|---|---|
| single_choice / boolean / short_answer | exact_match 或 accuracy | normalized_em、Accuracy+ |
| multi_choice / set_answer | set_exact_match | precision、recall、f1 |
| count / numeric / distance / size | absolute_error、tolerance_accuracy | relative_error |
| ordering / trajectory_order | exact_order 或 pairwise_accuracy | kendall_tau |
| region / bbox / mask | exact_candidate_match 或 IoU | mIoU、threshold_accuracy |
| frame_selection | exact_match | top_k_accuracy |
| open_answer / explanation | rubric_match 或 llm_match | 人工抽查 |

开放题、解释题或 LLM-as-judge 只能作为辅助指标或专门子集指标；若执行计划要求开放题为主评测，必须写明不可完全自动评分的风险、rubric、judge prompt、模型版本、temperature、人工抽查比例和复核路径。

## 处理

1. 读取所有 enabled 模板，按 `answer_format` 和 `metric_id` 分组。
2. 对照 Stage1 `metrics.yaml`、`selected_template_sources.jsonl` 和统一模板包评分说明，保留同一 metric 的语义一致性；不要为同一题型重复发明多个同义指标。
3. 每个 metric 必须能追溯到使用它的 enabled 模板的 `unified_template_id` 和 `canonical_question_type`；若统一模板包对该题型有固定评分策略，必须采用或显式说明兼容映射，不能另造语义冲突的主指标。
4. 为每个指标定义解析规则：
   - 字符串：大小写、空白、标点、yes/no、中英文别名归一化。
   - 集合：分隔符、去重、排序和空集处理。
   - 数值：单位、容差、无法解析数字的失败返回。
   - 排序：长度不一致、缺项、多项并列的处理。
   - 区域：候选 id、bbox、mask 路径和 IoU 阈值。
5. 为每个指标定义聚合规则：
   - overall；
   - by template；
   - by capability；
   - by source_type；
   - by answer_format；
   - 需要时 by scene/dataset/simulator。
6. 生成或更新 `metric_manifest.jsonl`，列出每个指标覆盖的模板、主/辅角色、实现文件、不适用条件和统一模板来源覆盖。
7. 确认每个 enabled 模板的 `metric_id` 在 manifest 中存在，且对应 `.py` 可被 `scripts/score_predictions.py` 导入。

## 质量要求

- 指标必须只依赖 item 中的 `answer`、预测文件和必要的 schema 字段；不得读取 Stage3 私有 GT 重新判分，除非 item 明确携带了可审计 evidence_ref 并在 metric contract 中声明。
- 完美预测必须能得到满分或模板声明的确定性通过条件。
- 错误预测、空预测或格式错误必须降分并记录原因；不得默认为正确。
- 容差必须来自模板或指标配置，不得在评分时临时猜测。
- 对随机化候选项或负样本成对题，必须记录 `aggregation_group` 或等价字段，支持 Accuracy+ 类成组评分。

## 输出

- `artifacts/data_20_template_metric_code_bundle/metrics/<metric_id>.json`
- `artifacts/data_20_template_metric_code_bundle/metrics/<metric_id>.py`
- `artifacts/data_20_template_metric_code_bundle/metric_manifest.jsonl`
- 更新后的 `traceability.csv`

## 失败与阻塞

以下情况必须阻塞：

- enabled 模板存在但没有任何可执行主指标。
- 主指标只能依赖 LLM-as-judge，且没有固定 rubric/judge 配置/人工复核计划。
- 指标 Python 依赖未声明的第三方包，且后续 smoke test 无法导入。
- 指标定义与模板 `answer_format` 不兼容，例如数值题使用集合 F1、mask 题没有 mask 或候选区域。
