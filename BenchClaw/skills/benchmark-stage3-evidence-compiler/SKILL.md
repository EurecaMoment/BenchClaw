# BenchClaw Stage3 Skill — 数据清洗、统一格式与半监督 GT 标注（Opencode-ready DAG 版）

全局路径约束：`BENCHCLAW_ROOT` 仅作只读输入；`WORKSPACE_ROOT` 是本次流程唯一总工作目录，所有写操作和流程产物只能落在其下。

## 路径入口校验

开始执行前必须先确认：

- 本次收到的 `BENCHCLAW_ROOT` 与 `WORKSPACE_ROOT` 与上游 pipeline 冻结值完全一致，不得在 Stage3 内重新猜测或重写。
- `BENCHCLAW_ROOT` 必须仍然解析为当前 BenchClaw 项目根目录。
- `WORKSPACE_ROOT` 必须是独立于 `BENCHCLAW_ROOT` 的外部工作目录，不能落在 `BENCHCLAW_ROOT` 内，不能等于 `BENCHCLAW_ROOT`，不能使用 `BENCHCLAW_ROOT/workspace*` 这类错误路径。
- 若路径校验失败，Stage3 必须立即阻塞并报错，不能继续读取 Stage2 或写任何 Stage3 输出。

## 0. 任务边界

本 Skill 对应手绘图中的 **Stage3**。它接收 Stage2 的三个终端输出：

1. `15`：真实图片数据；
2. `16`：已有 benchmark 图文/QA/标签数据；
3. `17`：仿真器多模态观测与 privileged GT。

Stage3 的目标不是制造最终评测集，而是把三类原始数据变成 **可清洗、可追踪、可供 Stage4 合成题目的高可信数据资产**：

- `18`：真实图片 + 半监督 GT；
- `19`：已有 benchmark 图 + 官方标签/QA + 半监督 GT；
- `20`：仿真器多模态数据 + 清洗后的 privileged GT。

这些“高可信数据资产”必须是 **真实落盘并可被后续节点直接消费的清洗结果、标注文件、融合记录和证据文件**，而不是只含有 `pending`、`candidate only`、说明文字或空目录的结构壳子。

Stage3 的数据来源是 **只读继承 Stage2 已经采集并落盘好的结果**，而不是重新采集流程。换句话说：

- Stage3 不得重新采集真实数据；
- Stage3 不得重新下载或重新获取已有 benchmark 数据；
- Stage3 不得重新运行仿真器去补采新的原始观测或 GT；
- Stage3 只能读取 `WORKSPACE_ROOT/stage2/15-*`、`16-*`、`17-*` 中已经物化好的数据，并在其基础上做 ingest、统一格式、清洗、半监督标注和 GT 打包。

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
  realdata/
    <real_scene_or_source>/
      original/
      semantic_entity_segmentation/
      depth/
      gt/
  benchmarkdataset/
    <dataset_name>/
      <existing_dataset_split_or_category>/
        original/
        semantic_entity_segmentation/
        depth/
        gt/
  simulator/
    <simulator_id>/
      <scene_or_map_id>/
        original/
        semantic_entity_segmentation/
        depth/
        gt/
  18-real-image-semi-supervised-gt/
  19-benchmark-image-semi-supervised-gt/
  20-simulator-clean-gt-pack/
```

其中三类图像的语义必须统一为：

1. `original/`: 原图或原始视觉观测；
2. `semantic_entity_segmentation/`: 语义实体分割图。对 realdata 与 benchmarkdataset 分支，它应来自 `YOLOE + LLM -> SAM3` 链路的实体分割结果渲染；对 simulator 分支，它应来自仿真器原生 semantic/instance render 或与 privileged GT 对齐后的等价语义实体分割图；
3. `depth/`: 深度图。对 realdata 与 benchmarkdataset 分支，它应来自 Depth Anything 3；对 simulator 分支，它应来自仿真器深度观测或等价 depth render。

所有保留样本都必须把这三类图像与对应 GT 一并落盘到 `WORKSPACE_ROOT/stage3` 下的上述目录树中。不得只保存 JSON、统计表、缩略图、抽样帧、样例图片或“可按需重新生成”的说明。

最终完成条件：

```bash
python scripts/check_stage3_outputs.py --workspace WORKSPACE_ROOT
```

并且该检查不能只在终端打印通过或失败，必须把结构化验证结果落盘到：

```text
WORKSPACE_ROOT/stage3/STAGE3_VALIDATION_REPORT.json
WORKSPACE_ROOT/stage3/STAGE3_VALIDATION_REPORT.md
```

Stage3 只有在这两个验证报告存在、且明确表明 Stage2→L1→L2→L3 的数量闭合、四类产物闭合、目录树闭合全部通过时，才允许把本阶段视为完成。

---

## 5. GT 原则

1. 仿真器分支 `20` 以 simulator privileged state / metadata / physics query / sensor pose 为最高优先级 GT；小模型输出不得覆盖它。
2. 真实图与旧 benchmark 图像分支中的 YOLOE、SAM3、Depth Anything 3 等输出是 **半监督 GT 候选**，必须记录工具、版本、参数、置信度、失败原因和证据路径。
3. LLM 或 VLM 只能用于路由、字段建议、弱标签解释或冲突报告，不能把纯文本判断写成最终 GT。
4. 所有 GT 字段必须有 `source_type`：`official_label`、`simulator_privileged_gt`、`tool_generated_candidate`、`human_verified`、`derived_geometry` 之一。
5. `tool_generated_candidate` 只表示来源类型，不表示可以不实跑。若某条记录声称来自 YOLOE/SAM3/DA3，则对应逐样本工具输出文件必须真实存在并能被后续节点读取。
6. 若工具执行失败、产物缺失或数量不足，节点必须阻塞并写失败/冲突报告，不得使用 `pending`、`to_be_generated`、空 annotation 目录、样例条目或说明文档冒充完成。
7. 对 image-based 半监督 GT，18 与 19 必须执行同一条共享链路：`输入图像 -> YOLOE + LLM -> SAM3 -> Depth Anything 3 -> 融合`，最终产出带语义/深度信息的实体分割结果；27 只负责登记这条链路的工具契约，不代替逐图执行。
8. 对 realdata、benchmarkdataset、simulator 三条 image-based 分支，保留下来的样本必须在 `WORKSPACE_ROOT/stage3` 下全量保存三类图像：原图、语义实体分割图、深度图。尤其 simulator 分支的图像型观测不得只保留抽样帧、摘要视频、统计结果或代表样例，必须对被保留样本全量落盘。
9. Stage3 不承担新的原始数据采集职责；若 Stage2 没有提供足够的已落盘样本、观测或 GT，Stage3 必须阻塞并记录缺口，而不是自行回到数据源、数据集官网、仿真器端口或其他外部路径重新采集。

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
python scripts/init_stage3_workspace.py --workspace WORKSPACE_ROOT --dag dag.json
python scripts/validate_dag.py dag.json
python scripts/ready_set_runner.py --workspace WORKSPACE_ROOT
python scripts/check_stage3_outputs.py --workspace WORKSPACE_ROOT
```

`init_stage3_workspace.py` 只负责创建 Stage3 节点目录；结构化记录由各节点写入对应的 JSON/JSONL 清单，checker 直接校验这些文件。

若 `validate_dag.py` 发现该图被改写为单链串行图，本 Skill 必须停止执行。
