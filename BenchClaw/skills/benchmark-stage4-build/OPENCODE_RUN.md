# OPENCODE_RUN — Stage4 ready-set 执行说明

## 1. 启动前

```bash
python scripts/validate_dag.py dag.json
python scripts/ready_set_runner.py --workspace WORKSPACE_ROOT
```

必须看到：

```text
READY: 09 18 19 20
```

## 2. 并行调度

同一 ready-set 内节点必须尽量用 subagent 并行：

```text
L0: 09 | 18 | 19 | 20
L1: 28 | 29
L2: 30
L3: 31 | 32
L4: 33   # 小批量合成留空
L5: 34   # 灰度测试留空
L6: 35
L7: 36
L8: 37
```

## 3. 每个 subagent 的固定动作

1. 读取自己的 `skills/<node>/SKILL.md`；
2. 读取 `contracts/node_io_contracts.json` 中自己的 `may_read/must_write/must_not_read`；
3. 只读取父节点输出；
4. 写入自己的 output_dir；
5. 写 `USED_INPUTS.json`；
6. 写 `DONE.json`。

## 4. 留空节点约束

- `33-small-batch-synthesis-placeholder` 只允许写 `WAIVED.json`、`README_EMPTY.md`、`USED_INPUTS.json`、`DONE.json`。
- `34-gray-test-placeholder` 只允许写 `WAIVED.json`、`README_EMPTY.md`、`USED_INPUTS.json`、`DONE.json`。
- 不得在这两个节点中生成题目、运行模型或填 pilot 数值。

## 5. 结束

```bash
python scripts/check_stage4_outputs.py --workspace WORKSPACE_ROOT
```
