# Benchmark Stage2 Data Collect Skill — 原始数据采集

## 角色

根据 Stage1 执行计划，分别采集并分析真实图片、已有 benchmark 和仿真器数据，并把后续阶段需要消费的媒体、元数据、标注需求与 GT 物化到 workspace。

## 关键规则

- 只有本文件 DAG 表中的节点是本阶段节点；编号数据只进入 `artifacts/`，不得进入 `nodes/`。
- 启动本 stage 时，必须接收并复述冻结的 `PROJECT_ROOT`、`BENCHCLAW_ROOT`、`WORKSPACE_PARENT`、`WORKSPACE_ROOT` 实际值，并与 `WORKSPACE_ROOT/path_resolution.json` 对齐。
- 本 stage 只能写入 `WORKSPACE_ROOT/stage2/`。
- 每个节点完成后必须写：`nodes/<node-id>/USED_INPUTS.json`、`nodes/<node-id>/DONE.json`、`nodes/<node-id>/NODE_REPORT.md`。
- 继承总入口和 pipeline 的长任务 `tmux` 执行协议：任何下载、检索、外部工具调用、批处理、模型推理、训练、仿真、清洗、标注或全量评测等可能长时间运行的命令，必须在 `tmux` 会话中执行、写入 `nodes/<node-id>/run_logs/` 并定期监控；未使用 `tmux` 必须在 `NODE_REPORT.md` 说明短任务依据和实际耗时。
- 每个编号数据必须写入：`artifacts/<data-id>/`。
- `real-image-collection-analysis` 必须运行时动态枚举 `BENCHCLAW_ROOT/realDataCards` 下的直接子文件夹，并按每个文件夹内的 `SKILL.md` 作为独立真实图片数据卡处理；不得硬编码数据集名称或修改数据卡目录。
- `existing-benchmark-collection-analysis` 必须运行时动态枚举 `BENCHCLAW_ROOT/benchmarkDatasetCards` 下的直接子文件夹，并按每个文件夹内的 `SKILL.md` 作为独立 benchmark 数据集卡处理；不得硬编码数据集名称或修改数据集卡目录。
- `simulator-collection-analysis` 必须运行时动态枚举 `BENCHCLAW_ROOT/simulatorCards` 下的直接子文件夹，并按每个文件夹内的 `SKILL.md` 作为独立仿真器卡处理；计划要求执行的仿真器必须真实运行并采集本次运行产生的观测、状态、动作和 GT，不得硬编码仿真器名称或修改仿真器卡目录。
- `stage2-plan-generation` 必须在 `stage2_execution_plan.yaml` 中固化三类数据源的唯一 card 根目录、唯一消费节点、唯一输出 bundle 和同一并行 ready group：真实图片只能来自 `BENCHCLAW_ROOT/realDataCards` 并进入 `data_14_real_image_collection_bundle`，已有 benchmark 只能来自 `BENCHCLAW_ROOT/benchmarkDatasetCards` 并进入 `data_15_existing_benchmark_collection_bundle`，仿真器只能来自 `BENCHCLAW_ROOT/simulatorCards` 并进入 `data_16_simulator_collection_bundle`；任何跨类别读取、错分输出或未进入并行 ready group 的计划都必须 BLOCKED。
- `stage2-plan-generation` 必须在 `stage2_execution_plan.yaml` 中写出 `parallel_dag.nodes[]` 与 `parallel_dag.edges[]`，把每个实际发现的数据源展开成精确 subskill 调用节点；执行者必须按该显式 DAG 的 ready set 并行运行，不得把各数据源隐式串行化。
- 三类数据源的规整与物化都必须遵守 `templates/collection_bundle_contract.md`：媒体真实落盘，图片必须可解码并记录尺寸/sha256，样本必须保留来源、原始字段、关键标签或 GT，不得写 placeholder、空数据或虚假数据。
- 缺少必需输入、真实数据、标注结果、GT 或模型输出时，必须写 `BLOCKED.json` 与 `BLOCKED.md`，并停止本 stage。

## 输入

- `data_13_execution_plan`

## DAG 节点

| Node ID | 椭圆节点名称 | Parents | 输出数据 |
|---|---|---|---|
| `stage2-plan-generation` | 本阶段执行计划生成 | 无 | `stage2_execution_plan` |
| `real-image-collection-analysis` | 真实图片采集与分析 | `stage2-plan-generation` | `data_14_real_image_collection_bundle` |
| `existing-benchmark-collection-analysis` | 已有 benchmark 采集与分析 | `stage2-plan-generation` | `data_15_existing_benchmark_collection_bundle` |
| `simulator-collection-analysis` | 仿真器采集与分析 | `stage2-plan-generation` | `data_16_simulator_collection_bundle` |

## Ready-set 调度

1. 从 `dag.json` 读取节点依赖。
2. 每轮选择所有 parents 已完成且未执行的 ready 节点。
3. 对 ready 节点调用 `skills/<node-id>/SKILL.md`。
4. `stage2-plan-generation` 完成后，先读取 `stage2_execution_plan.yaml` 的 `parallel_dag`；`parallel_dag.nodes[]` 中 `parents: []` 的所有数据源 subskill 节点必须组成同一 ready set 并行启动，且必须精确调用节点声明的 `subskill_path`。
5. 每个 work unit 的后续 subskill 只依赖同一 `work_unit_id` 的前置 subskill；不同数据源之间不得互相等待，除非 `parallel_dag.edges[]` 明确声明且原因写入计划。
6. 三个类别 summary barrier 只等待本类别 work unit 的末端 subskill；Stage2 最终完成门才等待三个 terminal artifacts。
7. 并行分支共享输入必须只读，共享输出必须写入各自 artifact 目录；各类别内部也必须按自身 card 类别拆分 work unit 并行处理，完成后再串行汇总根 bundle。
8. 本 stage 只在所有 terminal artifacts 完成且质量门通过后写 `_STAGE_DONE.json` 与 `_stage_report.md`。

## 终端数据

- `data_14_real_image_collection_bundle`
- `data_15_existing_benchmark_collection_bundle`
- `data_16_simulator_collection_bundle`

## 标准目录

```text
WORKSPACE_ROOT/stage2/
  nodes/<node-id>/
    run_logs/
  artifacts/
  _STAGE_DONE.json
  _stage_report.md
```
