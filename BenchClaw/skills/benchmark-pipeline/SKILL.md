---
name: benchclaw-pipeline
description: Use for top-level BenchClaw orchestration across Stage1-Stage5, workspace freezing, stage gates, and pipeline state handoff.
---

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

## Registered Stage Skill Names

当 pipeline 需要调度 stage skill 时，必须通过 opencode 中 `subtask: true` 的 stage 命令派发子 agent，而不是依赖相对路径字符串碰运气。显式 skill 名仍作为被调度目标的身份校验：

- `benchclaw-stage1-draft`
- `benchclaw-stage2-data-collect`
- `benchclaw-stage3-evidence-compiler`
- `benchclaw-stage4-build`
- `benchclaw-stage5-eval`

## Opencode 子 agent 调度契约

pipeline 只作为顶层 primary orchestrator。每次进入 Stage1 到 Stage5 时，必须使用 `BENCHCLAW_ROOT/opencode.json` 中的对应命令创建 stage manager 子 agent：

- Stage1: `/benchclaw-stage1` -> `stage1-draft-manager`
- Stage2: `/benchclaw-stage2` -> `stage2-data-collect-manager`
- Stage3: `/benchclaw-stage3` -> `stage3-data-clean-manager`
- Stage4: `/benchclaw-stage4` -> `stage4-build-manager`
- Stage5: `/benchclaw-stage5` -> `stage5-eval-manager`

stage manager 内部的每个 `skills/<node-id>/SKILL.md` 或 `subskills/<subskill-id>/SKILL.md` 必须继续通过 `/benchclaw-subskill` 派发到 `child-skill-module-runner` 子 agent。pipeline 和 stage manager 禁止在自身上下文内直接内联执行 child skill；只允许收集每个子 agent 返回的 `status`、artifact 路径、证据摘要、gate verdict 与 blockers。

## Stage Context Return Protocol

每个 stage skill 返回给 pipeline 时，只允许回传结构化摘要，不允许把 stage 内部长日志、完整 tool response、整段 SKILL.md 正文或大量中间产物全文继续塞回主流程。推荐返回：

```json
{
  "stage": "stage1 | stage2 | stage3 | stage4 | stage5",
  "status": "DONE | BLOCKED",
  "artifact_root": "...",
  "artifacts": {},
  "gate_verdict": "PASS | FAIL | BLOCKED",
  "blocking_issues": [],
  "summary": "..."
}
```

如果需要继续下游 stage，只把路径、manifest、gate verdict 和简短摘要带入后续上下文。

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
- `WORKSPACE_ROOT`：本次流程唯一总工作目录，路径必须严格解析为 `PROJECT_ROOT/workspaces/workspace{I}`，其中 `{I}` 是十进制整数目录编号。若用户未提供合法 workspace 路径，则在 `WORKSPACE_PARENT` 下扫描已有 `workspace{i}` 目录，取现有最大编号的下一个未占用目录作为新工作区；若用户提供的路径不满足 `PROJECT_ROOT/workspaces/workspace{I}`，必须视为非法并阻塞。
- `WORKSPACE_ROOT/EVALSET_DATASET`：最终统一评测包目录。无论 Stage4 中间 artifact 如何组织，最终可直接评测的完整数据集都必须收口到这个固定目录，直接包含完整图像文件、问题、答案/GT 与评测指标代码；严禁使用链接、symlink、placeholder 或目录外路径冒充评测图片。

所有派生产物只写入 `WORKSPACE_ROOT/stage1` 到 `WORKSPACE_ROOT/stage5`，不得写入 `BENCHCLAW_ROOT`。

## Workspace 隔离

默认只允许读取和写入本次冻结的 `WORKSPACE_ROOT`。若无用户明确要求，严禁查看、搜索、读取、比较、复制、复用或总结 `WORKSPACE_PARENT` 下其他 workspace 的任何内容。

唯一默认例外是创建新 workspace 前，为分配下一个编号而只读取 `WORKSPACE_PARENT` 的直属目录名；不得进入这些目录，不得读取文件名、manifest、报告、日志、数据集或图片。若用户显式要求复用/对比/审计其他 workspace，必须把授权的 workspace 路径、允许访问范围和目的写入 `WORKSPACE_ROOT/path_resolution.json.workspace_isolation.authorized_external_workspaces`，且访问只限该范围。

Stage skill 与 subskill 均继承该隔离规则。任何 stage 输入如果看起来来自其他 workspace，必须先确认它是否在授权清单中；未授权时立即 `BLOCKED`，不得靠“看一下是否可用”来探测。

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

## 长任务 tmux 执行协议

任何预计耗时较长、结束时间不确定、可能等待下载/标注/清洗/仿真/模型推理/训练/全量评测、或一旦前台 shell 中断会丢失数据的命令，都必须按本协议执行。Stage skill 与 subskill 均继承本协议。

1. 启动前必须在当前节点目录下创建 `run_logs/`，日志固定写入 `WORKSPACE_ROOT/stageN/nodes/<node-id>/run_logs/<task>.log`，不得只依赖终端滚动输出。
2. `tmux` 会话名必须可追踪，格式为 `benchclaw_s<stage>_<node-id>_<task>_<YYYYMMDDHHMMSS>`；同一节点多个 work unit 可在 `<task>` 中加入 `work_unit_id`。
3. 启动命令必须使用后台会话并重定向 stdout/stderr：

```text
tmux new-session -d -s <session_name> "<command> > <log_path> 2>&1"
```

4. 启动后必须立即检查会话和日志是否存在：`tmux has-session -t <session_name>`、`tail -n 50 <log_path>`。
5. 执行期间必须周期性监控：用 `tmux capture-pane -pt <session_name>` 查看最近输出，用 `tail -n 100 <log_path>` 或 `tail -f <log_path>` 查看日志增长；长于 30 分钟的任务至少每 10-15 分钟检查一次，长于 2 小时的任务至少每 30 分钟检查一次。
6. 任务结束时必须确认会话退出、日志落盘、退出码或完成标记可追溯；若命令本身不能直接写退出码，必须在 tmux 命令中追加写入 `EXIT_CODE:$?` 到同一日志。
7. `NODE_REPORT.md` 必须记录：tmux session name、完整命令、日志路径、开始/结束时间、监控时间点、退出状态、产物路径和样本计数。`USED_INPUTS.json` 或节点 report 中必须能追溯日志文件。
8. 若系统没有 `tmux`，长任务必须 `BLOCKED` 并写明原因；只有确定为短任务的命令才允许前台执行，且必须在 `NODE_REPORT.md` 写明“未使用 tmux 的短任务依据”和实际耗时。
9. 禁止用“稍后再看”“后台应该在跑”“聊天上下文里有输出”等方式替代会话检查、日志检查和真实产物检查；拿不到日志或产物时不得写 `DONE.json`。

## Stage 串行计划

| Stage | Skill | 输入 | 完成检查 |
|---|---|---|---|
| S1 | `BENCHCLAW_ROOT/skills/benchmark-stage1-draft/SKILL.md` | 根输入 `data_01`、`data_05`、`data_06`、`data_09`，以及离线节点 `scope-preprocess-analysis` 物化的 `data_08` | `stage1/artifacts/data_13_execution_plan/stage2_handoff.yaml` 与 `stage1/nodes/execution-plan-generation/DONE.json` |
| S2 | `BENCHCLAW_ROOT/skills/benchmark-stage2-data-collect/SKILL.md` | `data_13_execution_plan` | `stage2/artifacts/data_14_real_image_collection_bundle/`、`data_15_existing_benchmark_collection_bundle/`、`data_16_simulator_collection_bundle/` 与对应节点 `DONE.json` |
| S3 | `BENCHCLAW_ROOT/skills/benchmark-stage3-evidence-compiler/SKILL.md` | `data_14`、`data_15`、`data_16` | `validate_stage_gate.py --stage stage3` 返回 `PASS`，且三类 annotated bundle 与对应节点 `DONE.json` 均存在 |
| S4 | `BENCHCLAW_ROOT/skills/benchmark-stage4-build/SKILL.md` | `data_11_template_metric_initial_draft`、`data_13_execution_plan`、`data_17`、`data_18`、`data_19` | `validate_stage_gate.py --stage stage4` 返回 `PASS`，且 `data_22_full_benchmark_dataset/` 与 `stage4/nodes/full-synthesis/DONE.json` 均存在 |
| S5 | `BENCHCLAW_ROOT/skills/benchmark-stage5-eval/SKILL.md` | `data_13_execution_plan`、`WORKSPACE_ROOT/EVALSET_DATASET`、`data_22_full_benchmark_dataset` | `validate_stage_gate.py --stage stage5` 返回 `PASS`，且 `data_23_evaluation_report/` 与 `stage5/nodes/full-evaluation/DONE.json` 均存在 |

## 执行协议

1. 冻结用户原始 benchmark idea，解析并确定 `PROJECT_ROOT`、`BENCHCLAW_ROOT`、`WORKSPACE_PARENT` 与 `WORKSPACE_ROOT`，并在 `WORKSPACE_ROOT/pipeline_state.json` 中记录当前 run。
2. 在任何 stage 启动前，必须先执行路径合法性检查并把结果写入 `WORKSPACE_ROOT/path_resolution.json`。该文件必须包含 `workspace_isolation`，记录是否只做了 workspace 编号所需的直属目录名扫描、是否存在用户授权的外部 workspace、以及未授权外部 workspace 内容未被读取的结论。
3. 每次调用 Stage1/Stage2/Stage3/Stage4/Stage5 主 skill 必须使用对应 `/benchclaw-stage*` 子 agent 命令；调用任何 node skill 或 nested subskill 必须使用 `/benchclaw-subskill`。调用上下文中必须再次显式传递已经冻结的 `PROJECT_ROOT`、`BENCHCLAW_ROOT`、`WORKSPACE_PARENT`、`WORKSPACE_ROOT` 实际值，以及本文件的长任务 `tmux` 执行协议；任何 subskill 直接执行长任务时也必须写 `run_logs/`、监控记录和 `NODE_REPORT.md` 证据。
4. 每个 stage 启动时，必须先对照 `WORKSPACE_ROOT/path_resolution.json` 重新确认路径与冻结值完全一致；若不一致，立即阻塞并记录错误。
5. 每个 stage gate 通过后，必须立即更新 `WORKSPACE_ROOT/pipeline_state.json` 的 `current_stage`、`stages_completed`、stage gate 报告路径和时间戳；不得在下游 stage 或最终 `PIPELINE_DONE.json` 才回填上游完成状态。
6. 执行 Stage1。Stage1 内部按自己的 ready-set/DAG 运行；用户和外部资源不是节点；`data_05` 与 `data_06` 是根输入能力数据，`data_09` 是根输入 benchmark 数据，`scope-preprocess-analysis` 是 offline 节点并只负责从 `data_09` 物化 `data_08`。正常在线 pipeline 不调度 offline 节点，只校验 `data_08` 已存在；pipeline 只等待 Stage1 终端节点完成。通过后把 `stage1` 写入 `pipeline_state.json.stages_completed`。
7. Stage1 完成后，检查 Stage2 所需输入路径。若 Stage2 skill 的默认路径与 Stage1 实际输出目录不同，写入 `WORKSPACE_ROOT/config/stage2_input_paths.json`，不得复制或改写 Stage1 产物。
8. 执行 Stage2。Stage2 完成后必须看到真实图片、已有 benchmark、仿真器三个终端输出；缺一则 pipeline 停止并写 `WORKSPACE_ROOT/pipeline_blocked.md`；通过后把 `stage2` 写入 `pipeline_state.json.stages_completed`。
9. 执行 Stage3。Stage3 必须从 Stage2 三个终端输出读取，并生成真实图半监督 GT、已有 benchmark 半监督 GT、仿真器 clean GT 三个终端输出。Stage3 返回后必须运行：

```bash
python3 "$BENCHCLAW_ROOT/skills/validate_stage_gate.py" \
  --workspace-root "$WORKSPACE_ROOT" \
  --stage stage3 \
  --report "$WORKSPACE_ROOT/stage3/stage3_gate_report.json"
```

失败时立即停止并写 `WORKSPACE_ROOT/pipeline_blocked.md`，不得启动 Stage4；通过后把 `stage3` 和 gate report 路径写入 `pipeline_state.json.stages_completed`。
10. 执行 Stage4。Stage4 必须同时读取 Stage1 的 `data_11`、`data_13` 和 Stage3 的 `data_17`、`data_18`、`data_19`。Stage4 除了写 `stage4/artifacts/data_22_full_benchmark_dataset/` 外，还必须把最终可直接评测的完整包收口到 `WORKSPACE_ROOT/EVALSET_DATASET/`，其中必须包含真实落盘的评测图像文件、问题、答案/GT 和评测指标代码，且目录内容与 Stage5 实际消费内容一致；严禁链接型图片、placeholder 文件或外部路径引用。Stage4 返回后必须运行：

```bash
python3 "$BENCHCLAW_ROOT/skills/validate_stage_gate.py" \
  --workspace-root "$WORKSPACE_ROOT" \
  --stage stage4 \
  --report "$WORKSPACE_ROOT/stage4/stage4_gate_report.json"
```

失败时立即停止并写 `WORKSPACE_ROOT/pipeline_blocked.md`，不得启动 Stage5；通过后把 `stage4` 和 gate report 路径写入 `pipeline_state.json.stages_completed`。
11. 执行 Stage5。Stage5 默认读取 `data_13_execution_plan`、`WORKSPACE_ROOT/EVALSET_DATASET/`、真实模型调用结果或用户提供的已物化预测文件；`data_22_full_benchmark_dataset` 仅作为 Stage4 artifact 追溯目录，不能替代 `WORKSPACE_ROOT/EVALSET_DATASET/` 的完整评测包。Stage5 返回后必须运行：

```bash
python3 "$BENCHCLAW_ROOT/skills/validate_stage_gate.py" \
  --workspace-root "$WORKSPACE_ROOT" \
  --stage stage5 \
  --report "$WORKSPACE_ROOT/stage5/stage5_gate_report.json"
```

失败时立即停止并写 `WORKSPACE_ROOT/pipeline_blocked.md`，不得写 pipeline 完成标记；通过后把 `stage5` 和 gate report 路径写入 `pipeline_state.json.stages_completed`。
12. Stage5 gate 通过并更新 `pipeline_state.json` 后，先运行最终 pipeline 门禁：

```bash
python3 "$BENCHCLAW_ROOT/skills/validate_stage_gate.py" \
  --workspace-root "$WORKSPACE_ROOT" \
  --stage pipeline \
  --report "$WORKSPACE_ROOT/pipeline_gate_report.json"
```

只有最终门禁通过，才允许写 `WORKSPACE_ROOT/PIPELINE_DONE.json` 和 `WORKSPACE_ROOT/PIPELINE_REPORT.md`，并在报告中汇总每个 stage gate 的输入、输出、检查结果和阻塞记录。

## Handoff 规则

- 大阶段之间只通过 workspace 产物交接，不通过聊天上下文隐式传递事实。
- 大阶段之间传递上下文时，除了业务输入外，必须显式重复传递已经冻结的路径实际值。
- 若某 stage 的输入目录命名与上游实际输出不一致，优先写对应的 `WORKSPACE_ROOT/config/stage{N}_input_paths.json` 映射文件。
- 不允许查看或从其他 workspace 复用产物，除非用户显式给出路径、访问目的和复用范围，并写入 `path_resolution.json.workspace_isolation.authorized_external_workspaces`。
- 不允许跳过 Stage1 到 Stage4 直接运行 Stage5；除非用户提供一个已经完成且自洽的 Stage4 artifact pack，并明确要求只跑 Stage5。

## 质量门

每个 stage 完成后，pipeline 至少检查：

- 终端节点 `DONE.json` 是否存在；
- `USED_INPUTS.json` 是否存在，能否追溯到上游 stage；
- 当前 stage 的输出是否位于 `WORKSPACE_ROOT/stage{N}/`；
- 编号数据目录是否与椭圆节点目录分离；
- 长任务是否存在 `nodes/<node-id>/run_logs/<task>.log`、`NODE_REPORT.md` tmux session 记录、监控时间点、退出状态和可追溯产物；
- 是否存在当前 stage 明确禁止的 GT 覆盖、路径越界、空壳产物或编造评测结果。
- 是否有未授权读取其他 workspace 的痕迹；若 `USED_INPUTS.json`、`NODE_REPORT.md`、日志、manifest 或命令参数中出现非当前 `WORKSPACE_ROOT` 的 workspace 路径，且不在 `path_resolution.json.workspace_isolation.authorized_external_workspaces` 中，必须判定失败。
- 对 Stage4 与 Stage5，必须额外检查 `WORKSPACE_ROOT/EVALSET_DATASET/` 是否真实存在且非空，并包含可直接评测的真实图像文件、问题、答案/GT 和指标代码；若发现链接型图片、symlink、placeholder 文件或只在 `stage4/artifacts/` 下留一份数据而不收口到 workspace 根目录时，必须判定失败。
- 对 Stage3/Stage4/Stage5，必须以 `BENCHCLAW_ROOT/skills/validate_stage_gate.py` 的退出码和 JSON 报告作为最终完成裁决；自然语言报告、`DONE.json` 或空目录不能替代该结果。

`FAIL` 或缺失关键终端产物时必须停止；`NEEDS_REVIEW` 只能在用户明确确认后继续。

## 禁止事项

- 不把 Stage1、Stage2、Stage3、Stage4 内部 DAG 改写成节点级串行链。
- 不把编号数据当成 DAG 节点。
- 不写入 `BENCHCLAW_ROOT`。
- 不读取无授权目录。
- 不查看、搜索、读取、复制、复用、比较或总结其他 workspace 内容；除非用户显式授权具体 workspace 路径、目的和范围。
- 不允许将任何必需数据源分支留空、跳过、降级为占位产物，或用小批量运行冒充全量完成。
- 不允许只写 manifest、summary、report、jsonl 外壳而不物化后续 stage 必需消费的真实媒体、标注或评测输入。
- 不允许在前台 shell 长时间运行下载、仿真、Data-Juicer、标注、模型推理、训练或全量评测；未按 `tmux` 协议留下日志和监控证据时，不得写 `DONE.json`。
- 不允许在 benchmark item、answer program、prediction log、leaderboard、pipeline report 中写入编造的媒体引用、GT 解析逻辑或模型评测结果。
- 不把 LLM 生成内容当作 GT、官方 label、仿真器 privileged GT 或真实模型输出。
- 不让 Stage5 报告节点绕过 Stage5 评测节点直接读取 Stage4 原始 artifact。

## 最终产物

```text
WORKSPACE_ROOT/
  EVALSET_DATASET/
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
