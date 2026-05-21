# Node 26 — simulator-data-juicer-cleaning
## Role: Run Data Juicer cleaning on simulator records
## Parents: 23
## Must write: stage3.db, cleaned_records.sqlite_export.jsonl, cleaning_report.md, filter_counts.json, DONE.json, USED_INPUTS.json

数量闭合要求：

- `stage3.db.cleaned_simulator_records` 与 `filter_counts.json` 必须真实反映 node 23 的输入规模；
- 若无明确拒绝证据，不得把大规模输入缩减成少量清洗结果；
- node 26 输出的保留 `record_id` 集合必须与后续 node 20 的处理覆盖范围一致。
