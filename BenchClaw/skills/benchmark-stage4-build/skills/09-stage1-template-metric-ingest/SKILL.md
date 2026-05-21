# Skill 09 — Stage1 模板/指标输入

全局路径约束：`BENCHCLAW_ROOT` 仅作只读输入；`WORKSPACE_ROOT` 是本次流程唯一总工作目录，所有写操作和流程产物只能落在其下。

## 输入

读取 `contracts/node_io_contracts.json` 中 `09.may_read` 声明的路径。

## 任务

读取 Stage1 node-09 的模板初稿、指标初稿、模板-能力追踪表，形成只读 source_manifest。

本节点是 Stage4 根节点，只做输入接入与清单化，不生成题目，不改写 GT。

## 输出

写入 `WORKSPACE_ROOT/stage4/09-stage1-template-metric-ingest/`：

```text
WORKSPACE_ROOT/stage4/stage4.db
source_manifest.sqlite_export.jsonl
source_summary.md
USED_INPUTS.json
DONE.json
```

规范真相源应写入 `stage4.db.stage1_template_metric_inputs`；`source_manifest.sqlite_export.jsonl` 仅作为兼容性导出。

## DONE 要求

`DONE.json` 必须包含：

```json
{"node_id":"09","status":"done","outputs":["..."]}
```


---

## I/O 合同摘要

```text
node_id: 09
parents: []
output_dir: WORKSPACE_ROOT/stage4/09-stage1-template-metric-ingest
```

完整白名单以 `contracts/node_io_contracts.json` 为准。
