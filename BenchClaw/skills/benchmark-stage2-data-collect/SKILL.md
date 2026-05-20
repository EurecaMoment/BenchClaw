# BenchClaw Stage2 Skill — 数据采集（Opencode-ready DAG 版）

全局路径约束：`BENCHCLAW_ROOT` 仅作只读输入；`WORKSPACE_ROOT` 是本次流程唯一总工作目录，所有写操作和流程产物只能落在其下。

## 路径入口校验

开始执行前必须先确认：

- 本次收到的 `BENCHCLAW_ROOT` 与 `WORKSPACE_ROOT` 来自上游 pipeline 已冻结的实际值，而不是子 skill 自行推导的新值。
- `BENCHCLAW_ROOT` 必须是包含 `skills/`、`simulatorCards/`、`annotation-tool/` 的 BenchClaw 项目根目录。
- `WORKSPACE_ROOT` 必须是本次唯一工作目录，且不能位于 `BENCHCLAW_ROOT` 内部，不能等于 `BENCHCLAW_ROOT`，不能形如 `BENCHCLAW_ROOT/workspace*`。
- 若收到的路径不满足这些条件，Stage2 必须立即阻塞并报错，不能继续执行任何节点。

## 0. 任务边界

本 Skill 对应手绘图中的 **Stage2 数据采集**。它不是线性流水线，而是一个按 ready-set 调度的 DAG。  
核心目标是把 Stage1 的执行计划落到三类原始数据源：

1. **真实图片分支**：真实图片 + 期望/目标标注要求；
2. **已有 benchmark 分支**：已有 benchmark + 已有标注/QA + 期望额外标注；
3. **仿真器分支**：仿真器多模态观测/轨迹 + simulator privileged GT。

严禁把 Stage2 写成 `13→14→15→16→17` 串行链。编号只是节点编号，不是执行顺序。
仿真器分支的额外运行约束：若某仿真器通过本地端口提供服务，则 Stage2 只能连接用户已启动的本地仿真器端口执行采集，不得在采集流程中再次启动、重启或拉起新的仿真器进程。

数量执行约束同样是强制的，而不是建议：

- `13` 若声明了某个真实数据源或已有 benchmark 数据集被选中，则 `15/16` 必须把其图文数据全量采纳并落盘到 Stage2，不得二次抽样缩减；
- `13` 若声明了某个仿真器场景被选中，则 `17` 必须对该场景至少采集 50 个时刻帧的数据；一个时刻可对应多张图像或多模态观测，因此最小约束是“50 个时刻帧”，而不是“50 张图像”。

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
WORKSPACE_ROOT/stage1/13_execution_plan/
```

最低需要：

```text
execution_plan.md
benchmark_draft.md 或 benchmark_traceability.*
```

如果 Stage1 使用了不同目录，先在 `WORKSPACE_ROOT/config/stage2_input_paths.json` 中声明；Stage2 只允许读取该配置文件中由用户或上游明确声明的额外输入根路径，不得自行扩展到其他外部目录。

### 3.2 总输出

Stage2 不制造最终 eval set，也不做清洗标注；它只输出三类原始采集结果，供 Stage3 使用。

但 Stage2 的“原始采集结果”必须是 **后续 stage 可直接消费的已物化数据资产**，而不只是指向外部目录的清单、摘要、统计或说明文档。

对三类 image-based 数据，Stage2 必须在 `WORKSPACE_ROOT/stage2` 内真实落盘，且图像数据必须以可复用、可追溯的目录树保存；尤其仿真器采集得到的 RGB/depth/semantic/instance 等观测图像必须全量保存，不得只保留抽样帧、缩略图、统计结果、视频摘要或示例图片。

```text
WORKSPACE_ROOT/stage2/
  13-execution-plan-ingest/
  14-simulator-skill-registry/
  15-real-image-acquisition/
  16-existing-benchmark-acquisition/
  17-simulator-multimodal-gt-acquisition/
```

推荐的数据落盘子树应与节点输出目录对齐，并统一整理为：

```text
stage2/
├── 15-real-image-acquisition/
│   └── realdata/
│       └── <real_scene_or_source>/
├── 16-existing-benchmark-acquisition/
│   └── benchmarkdataset/
│       └── <dataset_name>/
│           └── <existing_dataset_split_or_category>/
└── 17-simulator-multimodal-gt-acquisition/
    └── simulator/
        └── <simulator_id>/
            └── <scene_or_map_id>/
```

其中：

- `real_scene_or_source` 可以是真实场景名、采集批次名或 realDataCard 中声明的稳定来源名；
- `existing_dataset_split_or_category` 应优先复用数据集内部已有的 split、category、subset 或官方目录层级，而不是 Stage2 自行发明分类；
- `scene_or_map_id` 应对应 execution-plan 中声明的 scene/map/task context；同一仿真器下不得把多个场景的图像混写到同一目录。

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

Stage2 也不得只交付 manifest/summary 而不物化数据本体：

- 真实图片分支必须把后续要用的图像复制、链接或以其他稳定方式物化到 `WORKSPACE_ROOT/stage2/15-real-image-acquisition/images/`；
- 已有 benchmark 分支必须把后续要用的原始样本和官方标签物化到 `WORKSPACE_ROOT/stage2/16-existing-benchmark-acquisition/raw/` 或其声明的稳定子路径；
- 仿真器分支必须把观测、多模态记录和 GT 物化到 `WORKSPACE_ROOT/stage2/17-simulator-multimodal-gt-acquisition/observations/` 与 `provenance/`；
- 对应三条分支的数据子树应分别落在 `15-real-image-acquisition/realdata/`、`16-existing-benchmark-acquisition/benchmarkdataset/`、`17-simulator-multimodal-gt-acquisition/simulator/` 下；manifest 中引用的图像/样本路径应优先指向这些子树中的实际文件。
- 对仿真器分支，execution-plan 要求采集的图像型观测（至少包括 RGB，以及被要求的 depth/semantic/instance 等）必须全量保存；不得只保留视频、摘要、统计表或部分抽样帧来代替完整图像观测集。
- 若仿真器通过本地端口提供服务，17 号节点必须复用已启动的本地 endpoint，并在 workspace 产物中记录实际连接到的 `host:port`；不得把“启动仿真器”作为 Stage2 产物的一部分。
- 14 号节点（simulator skill registry）只负责登记 simulator skill 的能力、连接方式与 adapter 合同；不得为了“验证目录里还有什么脚本”而对 simulator skill 目录做无谓的通配扫描。读取 simulator 能力时以明确列出的 `SKILL.md` 和其中点名的少量关键脚本路径为准。
- 任何仅包含外部绝对路径、样本摘要、统计数字而没有本地可消费数据的输出，都不得视为 Stage2 完成。

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
