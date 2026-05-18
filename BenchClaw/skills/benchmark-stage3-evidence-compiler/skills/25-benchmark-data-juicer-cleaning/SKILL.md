# Node 25 — benchmark-data-juicer-cleaning

## Role

Run Data-Juicer-style deduplication, legality, metadata, and image/text filters on existing benchmark unified records.

## Parents

```text
22
```

## May read

- `WORKSPACE_ROOT/stage3/22-benchmark-unified-format/**`
- `templates/data_juicer_recipe.example.yaml`
- `schemas/unified_multimodal_record.schema.json`

## Must write

- `WORKSPACE_ROOT/stage3/25-benchmark-data-juicer-cleaning/cleaned_records.jsonl`
- `WORKSPACE_ROOT/stage3/25-benchmark-data-juicer-cleaning/rejected_records.jsonl`
- `WORKSPACE_ROOT/stage3/25-benchmark-data-juicer-cleaning/data_juicer_recipe.yaml`
- `WORKSPACE_ROOT/stage3/25-benchmark-data-juicer-cleaning/data_juicer_report.json`
- `WORKSPACE_ROOT/stage3/25-benchmark-data-juicer-cleaning/cleaning_report.md`
- `WORKSPACE_ROOT/stage3/25-benchmark-data-juicer-cleaning/DONE.json`
- `WORKSPACE_ROOT/stage3/25-benchmark-data-juicer-cleaning/USED_INPUTS.json`

## Must not read

- `(none)`

## Data-Juicer 清洗约束

- 可使用 Data-Juicer；若未安装，必须生成等价的可复现清洗脚本/报告，而不是跳过清洗；
- 任何被过滤记录都要写入 `rejected_records.jsonl` 并给出原因；
- 不得在清洗阶段生成新的 GT，只能过滤、规范化、去重、补齐 provenance。

## Completion

完成后必须写：

```json
{
  "node_id": "25",
  "status": "DONE",
  "output_dir": "WORKSPACE_ROOT/stage3/25-benchmark-data-juicer-cleaning",
  "timestamp_utc": "<ISO-8601>"
}
```

并运行：

```bash
python scripts/check_used_inputs.py --node 25
python scripts/ready_set_runner.py --workspace WORKSPACE_ROOT
```
