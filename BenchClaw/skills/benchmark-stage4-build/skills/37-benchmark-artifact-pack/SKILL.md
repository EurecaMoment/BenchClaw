# Skill 37 — 最终 benchmark artifact 打包

## 父节点

`36`

## 任务

把 Stage4 产物整理为 Stage5 可直接评测的数据包。

## 输出

```text
WORKSPACE_ROOT/stage4/37-benchmark-artifact-pack/EVALSET_DATASET/eval_dataset.jsonl
WORKSPACE_ROOT/stage4/37-benchmark-artifact-pack/EVALSET_DATASET/metric_registry.json
WORKSPACE_ROOT/stage4/37-benchmark-artifact-pack/EVALSET_DATASET/answer_programs.py
WORKSPACE_ROOT/stage4/37-benchmark-artifact-pack/FINAL_BENCHMARK_CARD.md
WORKSPACE_ROOT/stage4/37-benchmark-artifact-pack/STAGE4_REPORT.md
WORKSPACE_ROOT/stage4/37-benchmark-artifact-pack/USED_INPUTS.json
WORKSPACE_ROOT/stage4/37-benchmark-artifact-pack/DONE.json
```

## 报告必须说明

- 33 小批量合成已按要求留空；
- 34 灰度测试已按要求留空；
- CTT/IRT/CDM/scope 指标只是 deferred hooks，没有伪造数值；
- 最终 item 是否具备完整 traceability。


---

## I/O 合同摘要

```text
node_id: 37
parents: ['36']
output_dir: WORKSPACE_ROOT/stage4/37-benchmark-artifact-pack
```

完整白名单以 `contracts/node_io_contracts.json` 为准。
