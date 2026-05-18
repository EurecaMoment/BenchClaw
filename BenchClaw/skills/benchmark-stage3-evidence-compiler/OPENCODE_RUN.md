# OPENCODE_RUN — Stage3 ready-set 执行说明

## 1. 启动前

```bash
python scripts/validate_dag.py dag.json
python scripts/ready_set_runner.py --workspace WORKSPACE_ROOT
```

必须看到：

```text
READY: 15 16 17 27
```

## 2. 并行调度

同一 ready-set 内节点必须尽量用 subagent 并行。

```text
L0: 15 | 16 | 17 | 27
L1: 21 | 22 | 23
L2: 24 | 25 | 26
L3: 18 | 19 | 20
```

## 3. 每个 subagent 的固定动作

每个节点 subagent：

1. 读取自己的 `skills/<node>/SKILL.md`；
2. 读取 `contracts/node_io_contracts.json` 中自己的 `may_read/must_write/must_not_read`；
3. 只读取父节点输出；
4. 写入自己的 output_dir；
5. 写 `USED_INPUTS.json`；
6. 写 `DONE.json`。

## 4. 禁止行为

- 不得把 15/16/17 写成互相依赖；
- 不得让 18 依赖 19 或 20；
- 不得让 19 依赖 18 或 20；
- 不得让 20 依赖 18 或 19；
- 不得让半监督小模型覆盖 simulator privileged GT；
- 不得把 LLM 文本判断当 GT。

## 5. 结束

```bash
python scripts/check_stage3_outputs.py --workspace WORKSPACE_ROOT
```
