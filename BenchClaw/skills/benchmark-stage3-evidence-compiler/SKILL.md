# BenchClaw Stage3 Skill — 数据清洗、统一格式与半监督 GT 标注（Opencode-ready DAG 版）

## 0. 任务边界

本 Skill 对应手绘图中的 **Stage3**。它接收 Stage2 的三个终端输出：

1. `15`：真实图片数据；
2. `16`：已有 benchmark 图文/QA/标签数据；
3. `17`：仿真器多模态观测与 privileged GT。

Stage3 的目标不是制造最终评测集，而是把三类原始数据变成 **可清洗、可追踪、可供 Stage4 合成题目的高可信数据资产**：

- `18`：真实图片 + 半监督 GT；
- `19`：已有 benchmark 图 + 官方标签/QA + 半监督 GT；
- `20`：仿真器多模态数据 + 清洗后的 privileged GT。

严禁把本阶段写成 `15→16→17→18→19→20` 串行链。编号是节点 ID，不是执行顺序。

---

## 1. DAG 结构

```text
          ┌──────┐          ┌──────┐          ┌──────┐
          │  15  │          │  16  │          │  17  │
          │真实图│          │旧bench│          │仿真GT│
          └──┬───┘          └──┬───┘          └──┬───┘
             │                 │                 │
             v                 v                 v
          ┌──────┐          ┌──────┐          ┌──────┐
          │  21  │          │  22  │          │  23  │
          │统一格│          │统一格│          │统一格│
          └──┬───┘          └──┬───┘          └──┬───┘
             │                 │                 │
             v                 v                 v
          ┌──────┐          ┌──────┐          ┌──────┐
          │  24  │          │  25  │          │  26  │
          │DJ清洗│          │DJ清洗│          │DJ清洗│
          └──┬───┘          └──┬───┘          └──┬───┘
             │                 │                 │
             │        ┌────────┴───────┐         │
             │        │ 27 半监督工具契约│         │
             │        └────────┬───────┘         │
             v                 v                 v
          ┌──────┐          ┌──────┐          ┌──────┐
          │  18  │          │  19  │          │  20  │
          │真图+ │          │旧bench│          │仿真器│
          │半GT │          │+半GT │          │+GT  │
          └──────┘          └──────┘          └──────┘
```

等价依赖表：

```text
15.parents = []
16.parents = []
17.parents = []
27.parents = []
21.parents = [15]
22.parents = [16]
23.parents = [17]
24.parents = [21]
25.parents = [22]
26.parents = [23]
18.parents = [24, 27]
19.parents = [25, 27]
20.parents = [26]
terminal_nodes = [18, 19, 20]
```

---

## 2. Opencode 调度要求

### 2.1 必须按 ready-set 执行

开始时读取：

```bash
cat dag.json
cat contracts/node_io_contracts.json
python scripts/validate_dag.py dag.json
python scripts/ready_set_runner.py --workspace WORKSPACE_ROOT
```

初始 ready-set 必须是：

```text
READY: 15 16 17 27
```

如果 Opencode 支持 subagent，应并行启动：

```text
subagent-15 -> skills/15-stage2-real-image-source-ingest/SKILL.md
subagent-16 -> skills/16-stage2-existing-benchmark-source-ingest/SKILL.md
subagent-17 -> skills/17-stage2-simulator-gt-source-ingest/SKILL.md
subagent-27 -> skills/27-semi-supervised-tool-registry/SKILL.md
```

之后按 ready-set 自动推进：

```text
L0: 15 | 16 | 17 | 27
L1: 21 | 22 | 23
L2: 24 | 25 | 26
L3: 18 | 19 | 20
```

### 2.2 不支持 subagent 时的降级

允许在同一 ready-set 内顺序执行，但不得改变依赖关系。尤其禁止：

```text
15 → 16 → 17 → 21 → 22 → 23 → 24 → 25 → 26 → 18 → 19 → 20
```

---

## 3. 总输入

默认读取 Stage2 输出：

```text
WORKSPACE_ROOT/stage2/15-real-image-acquisition/
WORKSPACE_ROOT/stage2/16-existing-benchmark-acquisition/
WORKSPACE_ROOT/stage2/17-simulator-multimodal-gt-acquisition/
```

如果路径不同，在以下文件声明映射：

```text
WORKSPACE_ROOT/config/stage3_input_paths.json
```

---

## 4. 总输出

```text
WORKSPACE_ROOT/stage3/
  18-real-image-semi-supervised-gt/
  19-benchmark-image-semi-supervised-gt/
  20-simulator-clean-gt-pack/
```

最终完成条件：

```bash
python scripts/check_stage3_outputs.py --workspace WORKSPACE_ROOT
```

---

## 5. GT 原则

1. 仿真器分支 `20` 以 simulator privileged state / metadata / physics query / sensor pose 为最高优先级 GT；小模型输出不得覆盖它。
2. 真实图与旧 benchmark 图像分支中的 YOLOE、SAM3、Depth Anything 3 等输出是 **半监督 GT 候选**，必须记录工具、版本、参数、置信度、失败原因和证据路径。
3. LLM 或 VLM 只能用于路由、字段建议、弱标签解释或冲突报告，不能把纯文本判断写成最终 GT。
4. 所有 GT 字段必须有 `source_type`：`official_label`、`simulator_privileged_gt`、`tool_generated_candidate`、`human_verified`、`derived_geometry` 之一。

---

## 6. 子 Skill 列表

```text
skills/15-stage2-real-image-source-ingest/SKILL.md
skills/16-stage2-existing-benchmark-source-ingest/SKILL.md
skills/17-stage2-simulator-gt-source-ingest/SKILL.md
skills/21-real-image-unified-format/SKILL.md
skills/22-benchmark-unified-format/SKILL.md
skills/23-simulator-unified-format/SKILL.md
skills/24-real-image-data-juicer-cleaning/SKILL.md
skills/25-benchmark-data-juicer-cleaning/SKILL.md
skills/26-simulator-data-juicer-cleaning/SKILL.md
skills/27-semi-supervised-tool-registry/SKILL.md
skills/18-real-image-semi-supervised-gt/SKILL.md
skills/19-benchmark-image-semi-supervised-gt/SKILL.md
skills/20-simulator-clean-gt-pack/SKILL.md
```

---

## 7. 强制检查

```bash
python scripts/validate_dag.py dag.json
python scripts/ready_set_runner.py --workspace WORKSPACE_ROOT
python scripts/check_stage3_outputs.py --workspace WORKSPACE_ROOT
```

若 `validate_dag.py` 发现该图被改写为单链串行图，本 Skill 必须停止执行。
