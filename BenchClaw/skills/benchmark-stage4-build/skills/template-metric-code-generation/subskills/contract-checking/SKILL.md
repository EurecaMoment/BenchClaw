# Subskill — 契约检查

## 目标

对 `data_20_template_metric_code_bundle` 做静态契约检查和运行时 smoke test。只有当模板、指标、答案程序、批量合成代码和评分代码都可执行且能生成符合本 stage schema 的 item 时，主节点才能写 `DONE.json`。

## 输入

- `artifacts/data_20_template_metric_code_bundle/`
- 本 stage `templates/benchmark_item.schema.json`
- 本 stage `templates/DONE.schema.json`
- 本 stage `templates/BLOCKED.schema.json`
- `stage4_execution_plan.yaml`
- Stage3 证据 bundle 的已登记路径
- `artifacts/data_20_template_metric_code_bundle/references/` 中复制的外挂参考库文件

## 静态检查

必须检查：

1. 目录完整性：
   - `templates/`
   - `metrics/`
   - `answer_programs/`
   - `scripts/`
   - `contracts/`
   - `tests/`
   - `self_test/`
   - `references/`
2. Manifest 完整性：
   - `template_manifest.jsonl`
   - `selected_template_sources.jsonl`
   - `metric_manifest.jsonl`
   - `code_manifest.json`
   - `traceability.csv`
3. Schema 兼容性：
   - `contracts/benchmark_item.schema.json` 必须包含本 stage `benchmark_item.schema.json` 的 required 字段。
   - 每个 dry-run item 必须包含 `item_id`、`media`、`question`、`answer`、`capability_tags`、`template_id`、`evidence_refs`、`metric_id`，并能通过 `references/answer_type_metric_registry.json` 的 answer type 与 metric 映射检查。
4. 引用完整性：
   - 每个 enabled 模板引用的 `metric_id` 存在。
   - 每个 enabled 模板有 `answer_programs/<template_id>.py`。
   - 每个 enabled metric 有 JSON 定义和 Python 实现，或有明确外部评估协议且不是主指标。
   - 每个 enabled 模板必须有非空 `unified_template_id`、`capability_dimension_refs`，并且该 `unified_template_id` 在 `selected_template_sources.jsonl` 中为 `selection_status=selected`。
   - 每个 enabled 模板必须有非空 `reference_template_family`、`reference_answer_type`、`reference_metric_id` 或等价映射字段，并且能在 `references/template_family_registry.yaml` 与 `references/answer_type_metric_registry.json` 中找到。
   - `selected_template_sources.jsonl` 必须覆盖每个 Stage1 能力维度，状态为 selected、disabled 或 blocked，且每个 selected 记录包含 `primary_capability`、`required_fields`、`template_set`、字段覆盖、证据样本统计和外挂参考库适配状态。
   - `traceability.csv` 可从模板追溯到 Stage1 能力维度、Stage1 初稿、统一模板包模板 id、外挂参考库模板族、Stage4 模板参考和 Stage3 evidence。
   - `synthesis_plan.yaml` 中的 enabled template 列表必须与 `template_manifest.jsonl` 一致。
   - `contracts/runtime_contract.json` 中声明的 entrypoint 文件必须真实存在。
5. 输入路径安全：
   - 生成代码不得包含 machine-specific 绝对路径。
   - 媒体、GT、fixture 和 dry-run item 引用必须位于 `WORKSPACE_ROOT` 或 bundle 内；image_pair、multi_image、video_clip 的所有子路径或帧引用必须可追溯。
   - 代码不得联网下载依赖，不得写入 `BENCHCLAW_ROOT`。
   - 生成 item 的题面不得包含 object_id、depth_median、privileged_gt 等隐藏 GT 字段名；发现时必须阻塞或禁用对应模板。

## 运行时检查

在 bundle 根目录或以 `--bundle` 参数运行以下命令，并把 stdout/stderr、退出码和关键结果写入 `self_test/self_test_report.md`：

```bash
python -m py_compile metrics/*.py answer_programs/*.py scripts/*.py tests/*.py
python scripts/validate_bundle.py --bundle .
python scripts/generate_items.py --bundle . --evidence-index evidence_index.jsonl --out self_test/dry_run_items.jsonl --limit 1 --seed 0
python tests/smoke_test.py --bundle .
python scripts/score_predictions.py --bundle . --gold self_test/dry_run_items.jsonl --pred self_test/perfect_predictions.jsonl --out self_test/perfect_score_report.json
python scripts/score_predictions.py --bundle . --gold self_test/dry_run_items.jsonl --pred self_test/negative_predictions.jsonl --out self_test/negative_score_report.json
```

如项目环境不能直接运行 `python`，可使用当前 runtime 中可用的 Python 解释器，但必须在报告中记录完整命令。不得因为命令较慢而跳过；只有执行计划明确声明当前节点只做静态包生成时，才可将运行时检查降级为阻塞或待复核，而不是写 PASS。

## 通过条件

所有 enabled 模板必须满足：

- 答案程序可导入。
- `supports` 能对至少 1 条真实 evidence 返回通过。
- `build_item` 生成的 item 符合 `benchmark_item.schema.json`。
- `compute_answer` 与 item 中 `answer` 一致。
- 对应 metric 的 `score_one` 能处理正确、错误、缺失和格式错误预测。
- 模板的 answer type、primary metric 和 media type 均通过外挂参考库过滤。

整体 bundle 必须满足：

- `py_compile` 通过。
- `validate_bundle.py` 退出码为 0。
- `smoke_test.py` 退出码为 0。
- 完美预测评分整体满分，或所有非满分项都有模板声明的合理原因。
- 负例评分低于完美预测；若负例也满分，必须阻塞并修复指标。
- `dry_run_items.jsonl` 非空，且每条 item 都有 evidence_refs 和 metric_id。
- `selected_template_sources.jsonl` 非空，且 enabled 模板没有脱离统一模板包来源或外挂参考库适配范围。
- `synthesis_plan.yaml` 可作为后续节点 handoff 文件使用，包含灰度配额、全量配额建议和过滤记录路径。

## 阻塞记录

阻塞时按本 stage `templates/BLOCKED.schema.json` 写：

```text
WORKSPACE_ROOT/stage4/nodes/template-metric-code-generation/BLOCKED.json
WORKSPACE_ROOT/stage4/nodes/template-metric-code-generation/BLOCKED.md
```

`missing_or_invalid_inputs` 应列出精确文件、模板 id、metric id、命令或字段路径。例如：

- `templates/T012.json missing metric_id`
- `metrics/exact_match.py py_compile failed`
- `answer_programs/T034.py build_item missing evidence_refs`
- `self_test/dry_run_items.jsonl item does not satisfy benchmark_item.schema.json`
- `media path outside WORKSPACE_ROOT`
- `templates/T021.json reference_template_family not in references/template_family_registry.yaml`
- `metrics/llm_match.py used as primary metric in BenchClaw image/video mode`

阻塞报告必须包含：

- 失败命令和退出码；
- 最小复现路径；
- 影响的模板/指标；
- 可修复建议；
- 是否可以禁用单个模板后继续。

## 完成记录

通过时写：

```text
WORKSPACE_ROOT/stage4/nodes/template-metric-code-generation/DONE.json
WORKSPACE_ROOT/stage4/nodes/template-metric-code-generation/NODE_REPORT.md
```

`DONE.json` 必须符合本 stage `templates/DONE.schema.json`，`quality_gate` 至少包含：

```json
{
  "template_count": 0,
  "enabled_template_count": 0,
  "metric_count": 0,
  "dry_run_item_count": 0,
  "py_compile": "PASS",
  "bundle_validation": "PASS",
  "smoke_test": "PASS",
  "perfect_score_test": "PASS",
  "negative_score_test": "PASS"
}
```

`NODE_REPORT.md` 必须记录：

- 冻结路径；
- 实际读取的输入；
- 参考的本 stage 模板文件；
- 统一模板包校验结果、实际使用的文件和能力维度到统一模板的选择统计；
- enabled/disabled/blocked 模板统计；
- 外挂参考库保留模板族、answer type 和 deterministic metric 的覆盖统计；
- 指标覆盖统计；
- 自测命令和结果；
- 后续 `grey-batch-validation` 可直接使用的命令示例。
