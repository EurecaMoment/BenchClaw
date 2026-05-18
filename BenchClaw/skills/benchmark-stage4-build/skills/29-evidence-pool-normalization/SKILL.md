# Skill 29 — 证据池规范化

## 父节点

`18`, `19`, `20`

## 任务

把三条 Stage3 数据分支合并为 typed evidence pool，但必须保留来源：

- `source_branch = real_image | existing_benchmark | simulator`；
- `gt_source_type = simulator_privileged_gt | official_label | tool_generated_candidate | derived_geometry`；
- media path、GT 字段、置信度、工具版本、清洗日志、失败原因。

输出不是最终题目，只是可供模板绑定的证据索引。

## 输出

```text
WORKSPACE_ROOT/stage4/29-evidence-pool-normalization/evidence_pool.jsonl
WORKSPACE_ROOT/stage4/29-evidence-pool-normalization/evidence_manifest.json
WORKSPACE_ROOT/stage4/29-evidence-pool-normalization/source_balance_report.md
USED_INPUTS.json
DONE.json
```


---

## I/O 合同摘要

```text
node_id: 29
parents: ['18', '19', '20']
output_dir: WORKSPACE_ROOT/stage4/29-evidence-pool-normalization
```

完整白名单以 `contracts/node_io_contracts.json` 为准。
