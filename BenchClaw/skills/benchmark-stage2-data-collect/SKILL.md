# BenchClaw Stage2 Skill — 数据采集（Opencode-ready DAG 版）

## 0. 任务边界

本 Skill 对应手绘图中的 **Stage2 数据采集**。它不是线性流水线，而是一个按 ready-set 调度的 DAG。  
核心目标是把 Stage1 的执行计划落到三类原始数据源：

1. **真实图片分支**：真实图片 + 期望/目标标注要求；
2. **已有 benchmark 分支**：已有 benchmark + 已有标注/QA + 期望额外标注；
3. **仿真器分支**：仿真器多模态观测/轨迹 + simulator privileged GT。

严禁把 Stage2 写成 `13→14→15→16→17` 串行链。编号只是节点编号，不是执行顺序。

---

## 1. DAG 结构

```text
                 ┌──────────────┐
                 │ 13 执行计划入口 │
                 └──────┬───────┘
                        │
        ┌───────────────┼────────────────┐
        │               │                │
        v               v                v
  ┌──────────┐    ┌─────────────┐   ┌──────────────┐
  │15 真实图片│    │16 已有benchmark│   │17 仿真器多模态│
  │  数据采集 │    │   数据采集    │   │ GT 数据采集   │
  └──────────┘    └─────────────┘   └──────▲───────┘
                                            │
                                   ┌────────┴───────┐
                                   │14 各仿真器 skill│
                                   │   注册/适配     │
                                   └────────────────┘
```

等价依赖表：

```text
13.parents = []
14.parents = []
15.parents = [13]
16.parents = [13]
17.parents = [13,14]
terminal_nodes = [15,16,17]
```

动态 ready-set：

```text
初始 ready: 13, 14
13 完成后 ready: 15, 16
13 和 14 均完成后 ready: 17
最终完成条件: 15, 16, 17 全部 DONE
```

---

## 2. Opencode 调度要求

### 2.1 必须使用 ready-set

执行时先读取：

```bash
cat dag.json
cat contracts/node_io_contracts.json
```

然后按 `scripts/ready_set_runner.py` 输出的 ready nodes 启动子任务。  
如果环境支持 subagent，必须把同一 ready-set 中的节点交给不同 subagent 并行执行。

推荐过程：

```bash
python scripts/validate_dag.py dag.json
python scripts/ready_set_runner.py --workspace WORKSPACE_ROOT
```

初始会得到：

```text
READY: 13 14
```

此时应并行启动：

```text
subagent-13 -> skills/13-stage1-execution-plan-ingest/SKILL.md
subagent-14 -> skills/14-simulator-skill-registry/SKILL.md
```

当 13 完成后，不要等 14 才启动全部后续；应立即启动 15、16：

```text
subagent-15 -> skills/15-real-image-acquisition/SKILL.md
subagent-16 -> skills/16-existing-benchmark-acquisition/SKILL.md
```

17 必须等 13 和 14 都完成：

```text
subagent-17 -> skills/17-simulator-multimodal-gt-acquisition/SKILL.md
```

### 2.2 不支持 subagent 时的降级

可以顺序执行 ready-set 内节点，但不得改变依赖：

```text
允许: 13,14 任意顺序；13 后可跑 15/16；13+14 后跑 17
禁止: 13→14→15→16→17 被写死为唯一流程
```

---

## 3. 输入输出约束

### 3.1 总输入

Stage2 默认读取 Stage1 末端输出：

```text
WORKSPACE_ROOT/stage1/13-execution-plan/
```

最低需要：

```text
execution_plan.md
benchmark_draft.md 或 benchmark_traceability.*
```

如果 Stage1 使用了不同目录，先在 `WORKSPACE_ROOT/config/stage2_input_paths.json` 中声明。

### 3.2 总输出

Stage2 不制造最终 eval set，也不做清洗标注；它只输出三类原始采集结果，供 Stage3 使用。

```text
WORKSPACE_ROOT/stage2/
  13-execution-plan-ingest/
  14-simulator-skill-registry/
  15-real-image-acquisition/
  16-existing-benchmark-acquisition/
  17-simulator-multimodal-gt-acquisition/
```

完成条件：

```bash
python scripts/check_stage2_outputs.py --workspace WORKSPACE_ROOT
```

该脚本必须看到：

```text
15-real-image-acquisition/DONE.json
16-existing-benchmark-acquisition/DONE.json
17-simulator-multimodal-gt-acquisition/DONE.json
```

---

## 4. GT 原则

Stage2 只采集和搬运数据。  
**不得把 LLM 生成的描述、判断、推测当作 GT。**

允许的 GT 来源：

```text
1. 仿真器 privileged state / metadata / physics query / rendered sensor pose；
2. 已有 benchmark 的官方 label、QA、split、metadata；
3. 真实图片自带的人工标注、设备元数据或后续 Stage3 小模型/几何工具生成的半监督标注。
```

真实图片分支在 Stage2 只能写“期望标注字段/目标标注任务”，不能伪造标签。

---

## 5. 子 Skill 列表

每个手绘图编号节点都有自己的 Skill：

```text
skills/13-stage1-execution-plan-ingest/SKILL.md
skills/14-simulator-skill-registry/SKILL.md
skills/15-real-image-acquisition/SKILL.md
skills/16-existing-benchmark-acquisition/SKILL.md
skills/17-simulator-multimodal-gt-acquisition/SKILL.md
```

---

## 6. 强制检查

在开始前：

```bash
python scripts/validate_dag.py dag.json
```

在每个节点完成后：

```bash
python scripts/ready_set_runner.py --workspace WORKSPACE_ROOT
```

在 Stage2 结束后：

```bash
python scripts/check_stage2_outputs.py --workspace WORKSPACE_ROOT
```

如果 `validate_dag.py` 报告该图是 serial chain，本 Skill 不能继续执行。
