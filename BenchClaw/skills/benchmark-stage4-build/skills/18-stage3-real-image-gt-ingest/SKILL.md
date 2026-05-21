# Skill 18 — Stage3 真实图+半监督GT输入

全局路径约束：`BENCHCLAW_ROOT` 仅作只读输入；`WORKSPACE_ROOT` 是本次流程唯一总工作目录，所有写操作和流程产物只能落在其下。

## 输入

读取 `contracts/node_io_contracts.json` 中 `18.may_read` 声明的路径。

## 任务

读取 Stage3 node-18 的真实图片记录、半监督 GT、置信度和工具溯源。

本节点是 Stage4 根节点，只做输入接入与清单化，不生成题目，不改写 GT。

## 输出

写入 `WORKSPACE_ROOT/stage4/18-stage3-real-image-gt-ingest/`：

```text
WORKSPACE_ROOT/stage4/stage4.db
source_manifest.sqlite_export.jsonl
source_summary.md
USED_INPUTS.json
DONE.json
```

规范真相源应写入 `stage4.db.stage3_real_inputs`；`source_manifest.sqlite_export.jsonl` 仅作为兼容性导出。

## DONE 要求

`DONE.json` 必须包含：

```json
{"node_id":"18","status":"done","outputs":["..."]}
```


---

## I/O 合同摘要

```text
node_id: 18
parents: []
output_dir: WORKSPACE_ROOT/stage4/18-stage3-real-image-gt-ingest
```

完整白名单以 `contracts/node_io_contracts.json` 为准。
