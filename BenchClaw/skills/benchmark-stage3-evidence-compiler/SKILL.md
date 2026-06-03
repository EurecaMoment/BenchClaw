# Benchmark Stage3 Evidence Compiler Skill — 证据编译、清洗与 GT 整理

## 角色

读取 Stage2 已物化数据，按真实图片、已有 benchmark、仿真器三类数据源分别完成清洗、标注与 GT 整理，输出给 Stage4 使用的三类 annotated bundle。

## 关键规则

- 只有本文件 DAG 表中的 4 个节点是本阶段外显节点；用户、Stage2 输入和各节点内部 subskills 都不是 DAG 节点。
- 三类数据源节点内部必须按自己的 `subskills/cleaning/SKILL.md` 与 `subskills/annotation/SKILL.md` 执行；不得把清洗或标注拆成独立外显节点。
- 三类数据源节点的 cleaning 必须读取并调用 `BENCHCLAW_ROOT/data-juicer_card/SKILL.md`，通过 Data-Juicer pipeline 产出清洗后的 JSONL；不得只用手写过滤替代 Data-Juicer。
- `real-image-evidence-compilation` 与 `existing-benchmark-evidence-compilation` 执行 annotation 时必须调用 `BENCHCLAW_ROOT/annotation-tool/default-annotation/SKILL.md` 描述的默认标注流程；默认标注输出只能作为 `tool_generated_candidate` 或复核候选，不能直接当最终 GT。
- `simulator-evidence-compilation` 可以优先使用仿真器自带 privileged GT；只有当 stage plan 明确要求额外视觉伪标注时，才调用默认标注。
- 内部 cleaning 结果只能写入所属数据源节点自己的工作目录，不得注册成 stage-level artifact；终端 artifact 只能是 `data_17`、`data_18`、`data_19`。
- 本阶段所有图像、文字、官方标签、默认标注候选、privileged GT 和复核队列必须真实落盘到 `WORKSPACE_ROOT/stage3/artifacts/<data-id>/...`；不得只登记 Stage2 外部路径、聊天上下文、工具说明、未执行样例、空 JSONL 或占位文件。
- 每个数据源节点必须为每个 work unit 保存真实执行证明：Data-Juicer 配置、输入 manifest、执行命令、stdout/stderr 或日志、退出码、输出 manifest、默认标注或 GT 整理命令/调用记录、工具版本、执行时间和样本计数。缺少执行证明时不得写 `DONE.json`。
- `data_17`、`data_18`、`data_19` 的根目录和每个隔离 work unit 目录都必须包含可供 Stage4 直接消费的图文与 GT 文件：媒体或观测文件、文本字段 JSONL、清洗后样本 JSONL、标注/GT JSONL、review queue、evidence manifest；所有 JSONL 记录必须能追溯到 Stage2 输入记录和本阶段清洗/标注运行。
- `stage3-plan-generation` 必须在 `stage3_execution_plan.yaml` 中写出 `parallel_dag.nodes[]` 与 `parallel_dag.edges[]`，把每个实际发现的数据源 work unit 展开成精确 `cleaning -> annotation` subskill 调用节点；执行者必须按该显式 DAG 的 ready set 并行运行，不得把各数据源隐式串行化。
- 启动本 stage 时，必须接收并复述冻结的 `PROJECT_ROOT`、`BENCHCLAW_ROOT`、`WORKSPACE_PARENT`、`WORKSPACE_ROOT` 实际值，并与 `WORKSPACE_ROOT/path_resolution.json` 对齐。
- 本 stage 只能写入 `WORKSPACE_ROOT/stage3/`。
- 每个外显节点完成后必须写：`nodes/<node-id>/USED_INPUTS.json`、`nodes/<node-id>/DONE.json`、`nodes/<node-id>/NODE_REPORT.md`。
- 继承总入口和 pipeline 的长任务 `tmux` 执行协议：任何下载、检索、外部工具调用、批处理、模型推理、训练、仿真、清洗、标注或全量评测等可能长时间运行的命令，必须在 `tmux` 会话中执行、写入 `nodes/<node-id>/run_logs/` 并定期监控；未使用 `tmux` 必须在 `NODE_REPORT.md` 说明短任务依据和实际耗时。
- 每个编号终端数据必须写入：`artifacts/<data-id>/`。
- 写 `DONE.json` 前必须检查：清洗后的 JSONL 非空，除非 stage plan 显式允许该类别为空；每条记录引用的 workspace 媒体存在且非空；图片可解码并记录尺寸/sha256；文本字段完整；GT 或标注候选来源明确；`evidence_manifest.json` 覆盖全部 work unit、执行命令、日志、输入输出路径、样本计数和阻塞/复核原因。
- 缺少必需输入、真实数据、真实清洗执行、真实标注执行、GT、落盘媒体、落盘文字、落盘标注记录或模型输出时，必须写 `BLOCKED.json` 与 `BLOCKED.md`，并停止相关节点或本 stage。

## 输入

- `data_13_execution_plan`
- `data_14_real_image_collection_bundle`
- `data_15_existing_benchmark_collection_bundle`
- `data_16_simulator_collection_bundle`

## DAG 节点

| Node ID | 椭圆节点名称 | Parents | 输入数据 | 输出数据 |
|---|---|---|---|---|
| `stage3-plan-generation` | 本阶段执行计划生成 | 无 | `data_13`, `data_14`, `data_15`, `data_16` | `stage3_execution_plan` |
| `real-image-evidence-compilation` | 真实图片清洗与标注 | `stage3-plan-generation` | `stage3_execution_plan`, `data_14` | `data_17_annotated_real_image_bundle` |
| `existing-benchmark-evidence-compilation` | 已有 benchmark 清洗与标注 | `stage3-plan-generation` | `stage3_execution_plan`, `data_15` | `data_18_annotated_existing_benchmark_bundle` |
| `simulator-evidence-compilation` | 仿真器清洗与标注 | `stage3-plan-generation` | `stage3_execution_plan`, `data_16` | `data_19_annotated_simulator_bundle` |

## Ready-set 调度

1. 从 `dag.json` 读取节点依赖。
2. 首先运行 `stage3-plan-generation`。
3. `stage3-plan-generation` 完成后，先读取 `stage3_execution_plan.yaml` 的 `parallel_dag`；`parallel_dag.nodes[]` 中 `substage: cleaning` 且 `parents: []` 的所有数据源 subskill 节点必须组成同一 ready set 并行启动，且必须精确调用节点声明的 `subskill_path`。
4. 每个 work unit 的 annotation 节点只依赖同一 `work_unit_id` 的 cleaning 节点；不同数据源之间不得互相等待，除非 `parallel_dag.edges[]` 明确声明且原因写入计划。
5. 三个类别 summary barrier 只等待本类别 work unit 的 annotation 节点；Stage3 最终完成门才等待三个 terminal artifacts。
6. 每个数据源节点内部只在本节点工作目录中按 `parallel_dag` 运行 `subskills/cleaning` 再运行 `subskills/annotation`；同一数据源下的不同 dataset/work unit 可以并行，但只能写各自隔离目录。
7. 本 stage 只在三个 terminal artifacts 完成、图像/文字/GT 均完整落盘、执行证明齐全且质量门通过后写 `_STAGE_DONE.json` 与 `_stage_report.md`。

## 终端数据

- `data_17_annotated_real_image_bundle`
- `data_18_annotated_existing_benchmark_bundle`
- `data_19_annotated_simulator_bundle`

## 标准目录

```text
WORKSPACE_ROOT/stage3/
  nodes/<node-id>/
    run_logs/
  artifacts/
  _STAGE_DONE.json
  _stage_report.md
```
