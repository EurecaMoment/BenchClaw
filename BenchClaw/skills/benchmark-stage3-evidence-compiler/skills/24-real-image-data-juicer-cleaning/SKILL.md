# Node 24 — real-image-data-juicer-cleaning
## Role: Run Data Juicer cleaning on real-image records
## Parents: 21
## Must write: Stage3 JSON/JSONL manifests, cleaned_records.jsonl, cleaning_report.md, filter_counts.json, DONE.json, USED_INPUTS.json

数量闭合要求：

- `cleaned_records.jsonl` 与 `filter_counts.json` 必须真实反映 node 21 的输入规模；
- 若无明确拒绝证据，不得把大规模输入缩减成少量清洗结果；
- node 24 输出的保留 `record_id` 集合必须与后续 node 18 的处理覆盖范围一致。
