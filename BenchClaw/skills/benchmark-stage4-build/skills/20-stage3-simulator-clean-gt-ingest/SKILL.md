# Skill 20 — Stage3 仿真器GT输入

全局路径约束：`BENCHCLAW_ROOT` 仅作只读输入；`WORKSPACE_ROOT` 是本次流程唯一总工作目录，所有写操作和流程产物只能落在其下。

## 输入

读取 `contracts/node_io_contracts.json` 中 `20.may_read` 声明的路径。

## 任务

读取 Stage3 node-20 的仿真器多模态观测、轨迹、pose、privileged GT。

本节点是 Stage4 根节点，只做输入接入与清单化，不生成题目，不改写 GT。

## 输出

写入 `WORKSPACE_ROOT/stage4/20-stage3-simulator-clean-gt-ingest/`：

```text
WORKSPACE_ROOT/stage4/stage4.db
source_manifest.sqlite_export.jsonl
source_summary.md
USED_INPUTS.json
DONE.json
```

规范真相源应写入 `stage4.db.stage3_simulator_inputs`；`source_manifest.sqlite_export.jsonl` 仅作为兼容性导出。

## DONE 要求

`DONE.json` 必须包含：

```json
{"node_id":"20","status":"done","outputs":["..."]}
```


---

## I/O 合同摘要

```text
node_id: 20
parents: []
output_dir: WORKSPACE_ROOT/stage4/20-stage3-simulator-clean-gt-ingest
```

完整白名单以 `contracts/node_io_contracts.json` 为准。
