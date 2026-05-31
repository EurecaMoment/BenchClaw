# BenchClaw Pipeline Skill — Stage1 到 Stage5 总控

## 角色

本 skill 是 BenchClaw 的总领 pipeline。它只负责大阶段串行编排：

```text
Stage1 草稿与执行计划
  -> Stage2 原始数据采集
  -> Stage3 证据编译、清洗与半监督 GT
  -> Stage4 评测集合成与指标构建
  -> Stage5 模型评测与报告
```

Stage1 到 Stage5 必须按上述顺序执行。每个 stage 内部仍遵守自己的 `dag.json`、`contracts/node_io_contracts.json` 和 ready-set 调度规则；pipeline 不得把 stage 内部节点强行改成串行链。

## DAG 解释规则

- 手绘图中只有椭圆包裹的模块是 DAG 节点。
- 圆圈编号 `01` 到 `23` 是阶段间或节点间流动的数据编号，不是节点编号。
- 用户输入不是 DAG 节点；流程结束状态也不是 DAG 节点。
- 代码工程中，节点写入 `WORKSPACE_ROOT/stageN/nodes/<node-id>/`，编号数据写入 `WORKSPACE_ROOT/stageN/artifacts/<data-id>/`。

## 路径解析

本 pipeline 必须显式区分外层项目根目录、BenchClaw 代码根目录和 workspace 根目录，禁止把三者混用。

按当前目录结构，应理解为：

```text
PROJECT_ROOT/
  BenchClaw/
    annotation-tool/
    benchmarkDatasetCards/
    data-juicer_card/
    modelNeedMeasured/
    realDataCards/
    realDatasetCards/
    simulator-skill-registry/
    simulatorCards/
    skills/
      benchmark-pipeline/
      benchmark-stage1-draft/
      benchmark-stage2-data-collect/
      benchmark-stage3-evidence-compiler/
      benchmark-stage4-build/
      benchmark-stage5-eval/
    opencode.json
    workspace.csv
  thirty_part/
  workspaces/
  .gitignore
  .gitmodules
  example.jsonl
  LICENSE
  README.md
```

- `PROJECT_ROOT`：外层总项目根目录，即同时包含 `BenchClaw/`、`thirty_part/`、`workspaces/`、`README.md` 等目录或文件的目录。
- `BENCHCLAW_ROOT`：BenchClaw 代码根目录，固定解析为 `PROJECT_ROOT/BenchClaw`。
- `WORKSPACE_PARENT`：默认 workspace 父目录，固定解析为 `PROJECT_ROOT/workspaces`。
- `WORKSPACE_ROOT`：本次流程唯一总工作目录。若用户未提供 workspace，则在 `WORKSPACE_PARENT` 下扫描已有 `workspace{i}` 目录，取现有最大编号的下一个未占用目录作为新工作区。

所有派生产物只写入 `WORKSPACE_ROOT/stage1` 到 `WORKSPACE_ROOT/stage5`，不得写入 `BENCHCLAW_ROOT`。

## 总体依赖

```text
S1.parents = []
S2.parents = [S1]
S3.parents = [S2]
S4.parents = [S1, S3]
S5.parents = [S1, S4]
terminal_stage = S5
```

Stage4 同时读取 Stage1 的模板/指标初稿与 Stage3 的 GT/evidence 输出；Stage5 同时读取 Stage1 的执行计划与 Stage4 的全量数据集。由于 pipeline 是大阶段串行执行，实际执行顺序仍是 `S1 -> S2 -> S3 -> S4 -> S5`。

## Stage 串行计划

| Stage | Skill | 输入 | 完成检查 |
|---|---|---|---|
| S1 | `BENCHCLAW_ROOT/skills/benchmark-stage1-draft/SKILL.md` | `data_01_user_idea`、能力卡、工具卡、外部资源卡 | `stage1/artifacts/data_13_execution_plan/stage2_handoff.yaml` 与 `stage1/nodes/execution-plan-generation/DONE.json` |
| S2 | `BENCHCLAW_ROOT/skills/benchmark-stage2-data-collect/SKILL.md` | `data_13_execution_plan` | `stage2/artifacts/data_14_real_image_collection_bundle/`、`data_15_existing_benchmark_collection_bundle/`、`data_16_simulator_collection_bundle/` 与对应节点 `DONE.json` |
| S3 | `BENCHCLAW_ROOT/skills/benchmark-stage3-evidence-compiler/SKILL.md` | `data_14`、`data_15`、`data_16` | `stage3/artifacts/data_17_annotated_real_image_bundle/`、`data_18_annotated_existing_benchmark_bundle/`、`data_19_annotated_simulator_bundle/` 与对应节点 `DONE.json` |
| S4 | `BENCHCLAW_ROOT/skills/benchmark-stage4-build/SKILL.md` | `data_11_template_metric_initial_draft`、`data_13_execution_plan`、`data_17`、`data_18`、`data_19` | `stage4/artifacts/data_22_full_benchmark_dataset/` 与 `stage4/nodes/full-synthesis/DONE.json` |
| S5 | `BENCHCLAW_ROOT/skills/benchmark-stage5-eval/SKILL.md` | `data_13_execution_plan`、`data_22_full_benchmark_dataset` | `stage5/artifacts/data_23_evaluation_report/` 与 `stage5/nodes/full-evaluation/DONE.json` |

## 执行协议

1. 冻结用户原始 benchmark idea，解析并确定 `PROJECT_ROOT`、`BENCHCLAW_ROOT`、`WORKSPACE_PARENT` 与 `WORKSPACE_ROOT`，并在 `WORKSPACE_ROOT/pipeline_state.json` 中记录当前 run。
2. 在任何 stage 启动前，必须先执行路径合法性检查并把结果写入 `WORKSPACE_ROOT/path_resolution.json`。
3. 每次调用 Stage1/Stage2/Stage3/Stage4/Stage5 主 skill 或任何子 skill 时，必须在调用上下文中再次显式传递已经冻结的 `PROJECT_ROOT`、`BENCHCLAW_ROOT`、`WORKSPACE_PARENT` 和 `WORKSPACE_ROOT` 实际值。
4. 每个 stage 启动时，必须先对照 `WORKSPACE_ROOT/path_resolution.json` 重新确认路径与冻结值完全一致；若不一致，立即阻塞并记录错误。
5. 执行 Stage1。Stage1 内部按自己的 ready-set/DAG 运行；pipeline 只等待 Stage1 终端节点完成。
6. Stage1 完成后，检查 Stage2 所需输入路径。若 Stage2 skill 的默认路径与 Stage1 实际输出目录不同，写入 `WORKSPACE_ROOT/config/stage2_input_paths.json`，不得复制或改写 Stage1 产物。
7. 执行 Stage2。Stage2 完成后必须看到真实图片、已有 benchmark、仿真器三个终端输出；缺一则 pipeline 停止并写 `WORKSPACE_ROOT/pipeline_blocked.md`。
8. 执行 Stage3。Stage3 必须从 Stage2 三个终端输出读取，并生成真实图半监督 GT、已有 benchmark 半监督 GT、仿真器 clean GT 三个终端输出。
9. 执行 Stage4。Stage4 必须同时读取 Stage1 的 `data_11`、`data_13` 和 Stage3 的 `data_17`、`data_18`、`data_19`。
10. 执行 Stage5。Stage5 读取 `data_13_execution_plan`、`data_22_full_benchmark_dataset`、真实模型调用结果或用户提供的已物化预测文件。
11. Stage5 完成后写 `WORKSPACE_ROOT/PIPELINE_DONE.json` 和 `WORKSPACE_ROOT/PIPELINE_REPORT.md`，汇总每个 stage 的输入、输出、检查结果和阻塞记录。

## Handoff 规则

- 大阶段之间只通过 workspace 产物交接，不通过聊天上下文隐式传递事实。
- 大阶段之间传递上下文时，除了业务输入外，必须显式重复传递已经冻结的路径实际值。
- 若某 stage 的输入目录命名与上游实际输出不一致，优先写对应的 `WORKSPACE_ROOT/config/stage{N}_input_paths.json` 映射文件。
- 不允许从其他 workspace 复用产物，除非用户显式给出路径和复用范围。
- 不允许跳过 Stage1 到 Stage4 直接运行 Stage5；除非用户提供一个已经完成且自洽的 Stage4 artifact pack，并明确要求只跑 Stage5。

## 质量门

每个 stage 完成后，pipeline 至少检查：

- 终端节点 `DONE.json` 是否存在；
- `USED_INPUTS.json` 是否存在，能否追溯到上游 stage；
- 当前 stage 的输出是否位于 `WORKSPACE_ROOT/stage{N}/`；
- 编号数据目录是否与椭圆节点目录分离；
- 是否存在当前 stage 明确禁止的 GT 覆盖、路径越界、空壳产物或编造评测结果。

`FAIL` 或缺失关键终端产物时必须停止；`NEEDS_REVIEW` 只能在用户明确确认后继续。

## 禁止事项

- 不把 Stage1、Stage2、Stage3、Stage4 内部 DAG 改写成节点级串行链。
- 不把编号数据当成 DAG 节点。
- 不写入 `BENCHCLAW_ROOT`。
- 不读取无授权目录。
- 不允许将任何必需数据源分支留空、跳过、降级为占位产物，或用小批量运行冒充全量完成。
- 不允许只写 manifest、summary、report、jsonl 外壳而不物化后续 stage 必需消费的真实媒体、标注或评测输入。
- 不允许在 benchmark item、answer program、prediction log、leaderboard、pipeline report 中写入编造的媒体引用、GT 解析逻辑或模型评测结果。
- 不把 LLM 生成内容当作 GT、官方 label、仿真器 privileged GT 或真实模型输出。
- 不让 Stage5 报告节点绕过 Stage5 评测节点直接读取 Stage4 原始 artifact。

## 最终产物

```text
WORKSPACE_ROOT/
  stage1/
  stage2/
  stage3/
  stage4/
  stage5/
  pipeline_state.json
  path_resolution.json
  PIPELINE_DONE.json
  PIPELINE_REPORT.md
```

## Skills Path Hygiene

- Files under `BENCHCLAW_ROOT/skills/` must not contain machine-specific absolute paths for model stores, simulator installs, or Data-Juicer installs.
- Stage skills may reference those external dependencies only indirectly through capability cards outside `BENCHCLAW_ROOT/skills/`, such as `BENCHCLAW_ROOT/annotation-tool`, `BENCHCLAW_ROOT/simulatorCards`, or `BENCHCLAW_ROOT/data-juicer_card`.
- If a stage needs a concrete external install path at runtime, it must read it from the corresponding external card, environment variable, or user-provided config, then record the resolved value only under `WORKSPACE_ROOT`.
