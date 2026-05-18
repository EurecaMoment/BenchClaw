# Skill 33 — 小批量合成占位节点（按要求留空）

## 父节点

`31`, `32`

## 任务

本节点 **必须留空**。不要生成小批量样本，不要运行模型，不要填充 pilot 统计。

只写：

```text
WORKSPACE_ROOT/stage4/33-small-batch-synthesis-placeholder/WAIVED.json
WORKSPACE_ROOT/stage4/33-small-batch-synthesis-placeholder/README_EMPTY.md
WORKSPACE_ROOT/stage4/33-small-batch-synthesis-placeholder/USED_INPUTS.json
WORKSPACE_ROOT/stage4/33-small-batch-synthesis-placeholder/DONE.json
```

`WAIVED.json` 建议内容：

```json
{"node_id":"33","status":"waived","reason":"user requested small-batch synthesis to be left blank"}
```


---

## I/O 合同摘要

```text
node_id: 33
parents: ['31', '32']
output_dir: WORKSPACE_ROOT/stage4/33-small-batch-synthesis-placeholder
```

完整白名单以 `contracts/node_io_contracts.json` 为准。
