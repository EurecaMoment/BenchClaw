# Skill 37 — 最终 benchmark artifact 打包

全局路径约束：`BENCHCLAW_ROOT` 仅作只读输入；`WORKSPACE_ROOT` 是本次流程唯一总工作目录，所有写操作和流程产物只能落在其下。

## 父节点

`36`

## 任务

把 Stage4 产物整理为 Stage5 可直接评测的数据包。

该数据包必须是 **自包含或在 workspace 内稳定可解析** 的评测包：不得只复制 `eval_dataset.jsonl` 而省略其引用的真实媒体/标签资产。

本节点必须把最终 benchmark 整理成一个类 HuggingFace 的 benchmark 文件夹 `EVALSET_DATASET/`，供科研评测直接消费。

## 输出

```text
WORKSPACE_ROOT/stage4/37-benchmark-artifact-pack/EVALSET_DATASET/README.md
WORKSPACE_ROOT/stage4/37-benchmark-artifact-pack/EVALSET_DATASET/data/test.jsonl
WORKSPACE_ROOT/stage4/37-benchmark-artifact-pack/EVALSET_DATASET/images/
WORKSPACE_ROOT/stage4/37-benchmark-artifact-pack/EVALSET_DATASET/metrics/evaluate.py
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
- 数据包内媒体、标签和 evidence 引用是否已在 workspace 内物化，且 Stage5 无需回读外部原始数据目录即可评测。
- `EVALSET_DATASET/README.md`、`data/test.jsonl`、`images/`、`metrics/evaluate.py` 是否完整，且能作为科研风格 benchmark 文件夹被直接消费。


---

## I/O 合同摘要

```text
node_id: 37
parents: ['36']
output_dir: WORKSPACE_ROOT/stage4/37-benchmark-artifact-pack
```

完整白名单以 `contracts/node_io_contracts.json` 为准。
