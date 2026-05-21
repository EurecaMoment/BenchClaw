# Node 25 — benchmark-data-juicer-cleaning
## Role: Run Data Juicer cleaning on benchmark records
## Parents: 22
## Must write: stage3.db, cleaned_records.sqlite_export.jsonl, cleaning_report.md, filter_counts.json, DONE.json, USED_INPUTS.json

数量闭合要求：

- `stage3.db.cleaned_benchmark_records` 与 `filter_counts.json` 必须真实反映 node 22 的输入规模；
- 若无明确拒绝证据，不得把大规模输入缩减成少量清洗结果；
- node 25 输出的保留 `record_id` 集合必须与后续 node 19 的处理覆盖范围一致。
