# Skill 34 — 灰度测试占位节点（按要求留空）

全局路径约束：`BENCHCLAW_ROOT` 仅作只读输入；`WORKSPACE_ROOT` 是本次流程唯一总工作目录，所有写操作和流程产物只能落在其下。

## 父节点

`33`

## 任务

本节点 **必须留空**。不要灰度跑模型，不要计算 CTT/IRT/CDM/scope 数值。

只写：

```text
WORKSPACE_ROOT/stage4/34-gray-test-placeholder/WAIVED.json
WORKSPACE_ROOT/stage4/34-gray-test-placeholder/README_EMPTY.md
WORKSPACE_ROOT/stage4/34-gray-test-placeholder/USED_INPUTS.json
WORKSPACE_ROOT/stage4/34-gray-test-placeholder/DONE.json
```

`WAIVED.json` 建议内容：

```json
{"node_id":"34","status":"waived","reason":"user requested gray test to be left blank"}
```


---

## I/O 合同摘要

```text
node_id: 34
parents: ['33']
output_dir: WORKSPACE_ROOT/stage4/34-gray-test-placeholder
```

完整白名单以 `contracts/node_io_contracts.json` 为准。
