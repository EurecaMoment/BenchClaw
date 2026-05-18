# BenchClaw Pipeline Skill — Stage1 到 Stage5 总控

## 角色

本 skill 是 BenchClaw 的总领 pipeline。它只负责 **大阶段串行编排**：

```text
Stage1 草稿与执行计划
  -> Stage2 原始数据采集
  -> Stage3 证据编译、清洗与半监督 GT
  -> Stage4 评测集合成与指标构建
  -> Stage5 模型评测与报告
```

Stage1 到 Stage5 必须按上述顺序执行。每个 stage 内部仍遵守自己的 `dag.json`、`contracts/node_io_contracts.json` 和 ready-set 调度规则；pipeline 不得把 stage 内部节点强行改成串行链。

## 路径解析

- `BENCHCLAW_ROOT`：当前 skill 所在的 BenchClaw 根目录，也就是包含 `skills/`、`simulatorCards/`、`annotation-tool/` 等目录的父级目录。
- `WORKSPACE_ROOT`：当前 benchmark run 的工作区。若用户未提供 workspace，则在默认 workspace 父目录下扫描已有 `workspace{i}` 目录，取现有最大编号的下一个未占用目录作为新工作区；若尚无任何 workspace，则使用 `workspace1`。如果用户提供了其他 workspace，必须全程沿用同一个目录。
- 所有派生产物只写入 `WORKSPACE_ROOT/stage1` 到 `WORKSPACE_ROOT/stage5`，不得写入 `BENCHCLAW_ROOT`。

## 总体依赖

```text
S1.parents = []
S2.parents = [S1]
S3.parents = [S2]
S4.parents = [S3, S1]
S5.parents = [S4]
terminal_stage = S5
```

Stage4 需要同时读取 Stage1 的模板/指标初稿和 Stage3 的 GT/evidence 输出，因此它的大阶段父节点是 `S1` 与 `S3`；但由于 pipeline 是串行的，实际执行顺序仍是 `S1 -> S2 -> S3 -> S4 -> S5`。

## Stage 串行计划

| Stage | Skill | 输入 | 完成检查 |
|---|---|---|---|
| S1 | `BENCHCLAW_ROOT/skills/benchmark-stage1-draft/SKILL.md` | 用户 benchmark idea、能力卡、工具卡 | `WORKSPACE_ROOT/stage1/13_execution_plan/stage2_handoff.yaml` 与 `WORKSPACE_ROOT/stage1/_stage1_report.md` |
| S2 | `BENCHCLAW_ROOT/skills/benchmark-stage2-data-collect/SKILL.md` | Stage1 执行计划与 handoff | Stage2 的 15/16/17 三个终端节点 `DONE.json` |
| S3 | `BENCHCLAW_ROOT/skills/benchmark-stage3-evidence-compiler/SKILL.md` | Stage2 的 15/16/17 输出 | Stage3 的 18/19/20 三个终端节点 `DONE.json` |
| S4 | `BENCHCLAW_ROOT/skills/benchmark-stage4-build/SKILL.md` | Stage1 node 09 模板/指标 + Stage3 的 18/19/20 输出 | `WORKSPACE_ROOT/stage4/37-benchmark-artifact-pack/DONE.json` |
| S5 | `BENCHCLAW_ROOT/skills/benchmark-stage5-eval/SKILL.md` | Stage4 node 37 benchmark artifact pack | `WORKSPACE_ROOT/stage5/39-evaluation-report/DONE.json` |

## 执行协议

1. 冻结用户原始 benchmark idea，确定 `WORKSPACE_ROOT`，并在 `WORKSPACE_ROOT/pipeline_state.json` 中记录当前 run。
2. 执行 Stage1。Stage1 内部按自己的 ready-set/DAG 运行；pipeline 只等待 Stage1 终端节点完成。
3. Stage1 完成后，检查 Stage2 所需输入路径。若 Stage2 skill 的默认路径与 Stage1 实际输出目录不同，写入 `WORKSPACE_ROOT/config/stage2_input_paths.json`，不得复制或改写 Stage1 产物。
4. 执行 Stage2。Stage2 完成后必须看到真实图片、已有 benchmark、仿真器三个终端输出；缺一则 pipeline 停止并写 `WORKSPACE_ROOT/pipeline_blocked.md`。
5. 执行 Stage3。Stage3 必须从 Stage2 三个终端输出读取，并生成真实图半监督 GT、已有 benchmark 半监督 GT、仿真器 clean GT 三个终端输出。
6. 执行 Stage4。Stage4 必须同时读取 Stage1 node 09 和 Stage3 18/19/20；小批量合成与灰度测试节点按 Stage4 skill 约定留空。
7. 执行 Stage5。Stage5 只读取 `WORKSPACE_ROOT/stage4/37-benchmark-artifact-pack`，先跑评测，再生成报告。
8. Stage5 完成后写 `WORKSPACE_ROOT/PIPELINE_DONE.json` 和 `WORKSPACE_ROOT/PIPELINE_REPORT.md`，汇总每个 stage 的输入、输出、检查结果和阻塞/waiver 记录。

## Handoff 规则

- 大阶段之间只通过 workspace 产物交接，不通过聊天上下文隐式传递事实。
- 若某 stage 的输入目录命名与上游实际输出不一致，优先写对应的 `WORKSPACE_ROOT/config/stage{N}_input_paths.json` 映射文件。
- 不允许从其他 workspace 复用产物，除非用户显式给出路径和复用范围。
- 不允许跳过 Stage1 到 Stage4 直接运行 Stage5；除非用户提供一个已经完成且自洽的 Stage4 artifact pack，并明确要求只跑 Stage5。

## 质量门

每个 stage 完成后，pipeline 至少检查：

- 终端节点 `DONE.json` 是否存在；
- `USED_INPUTS.json` 是否存在，能否追溯到上游 stage；
- 当前 stage 的输出是否位于 `WORKSPACE_ROOT/stage{N}/`；
- 是否存在当前 stage 明确禁止的 GT 覆盖、路径越界、placeholder 或伪造评测结果。

`FAIL` 或缺失关键终端产物时必须停止；`NEEDS_REVIEW` 或 waiver 只能在用户明确确认后继续。

## 禁止事项

- 不把 Stage1、Stage2、Stage3、Stage4 内部 DAG 改写成节点级串行链。
- 本 pipeline 的终点是 Stage5 评测报告。
- 不写入 `BENCHCLAW_ROOT`。
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
  PIPELINE_DONE.json
  PIPELINE_REPORT.md
```

## Skills Path Hygiene

- Files under `BENCHCLAW_ROOT/skills/` must not contain machine-specific absolute paths for model stores, simulator installs, or Data-Juicer installs.
- Stage skills may reference those external dependencies only indirectly through capability cards outside `BENCHCLAW_ROOT/skills/`, such as `BENCHCLAW_ROOT/annotation-tool`, `BENCHCLAW_ROOT/simulatorCards`, or `BENCHCLAW_ROOT/data-juicer_card`.
- If a stage needs a concrete external install path at runtime, it must read it from the corresponding external card, environment variable, or user-provided config, then record the resolved value only under `WORKSPACE_ROOT`.
