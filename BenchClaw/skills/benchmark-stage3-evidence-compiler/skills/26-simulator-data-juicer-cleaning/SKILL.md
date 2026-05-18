# Node 26 — simulator-data-juicer-cleaning

## Role

Run Data-Juicer-style sensor, trajectory, GT-completeness, and provenance filters on simulator unified records.

## Parents

```text
23
```

## May read

- `WORKSPACE_ROOT/stage3/23-simulator-unified-format/**`
- `templates/data_juicer_recipe.example.yaml`
- `schemas/unified_multimodal_record.schema.json`

## Must write

- `WORKSPACE_ROOT/stage3/26-simulator-data-juicer-cleaning/cleaned_records.jsonl`
- `WORKSPACE_ROOT/stage3/26-simulator-data-juicer-cleaning/rejected_records.jsonl`
- `WORKSPACE_ROOT/stage3/26-simulator-data-juicer-cleaning/data_juicer_recipe.yaml`
- `WORKSPACE_ROOT/stage3/26-simulator-data-juicer-cleaning/data_juicer_report.json`
- `WORKSPACE_ROOT/stage3/26-simulator-data-juicer-cleaning/cleaning_report.md`
- `WORKSPACE_ROOT/stage3/26-simulator-data-juicer-cleaning/DONE.json`
- `WORKSPACE_ROOT/stage3/26-simulator-data-juicer-cleaning/USED_INPUTS.json`

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
  "node_id": "26",
  "status": "DONE",
  "output_dir": "WORKSPACE_ROOT/stage3/26-simulator-data-juicer-cleaning",
  "timestamp_utc": "<ISO-8601>"
}
```

并运行：

```bash
python scripts/check_used_inputs.py --node 26
python scripts/ready_set_runner.py --workspace WORKSPACE_ROOT
```
