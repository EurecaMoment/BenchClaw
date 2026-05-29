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

- `PROJECT_ROOT`：外层总项目根目录，即同时包含 `BenchClaw/`、`thirty_part/`、`workspaces/`、`README.md` 等目录或文件的目录。在当前截图结构中，VS Code 最外层显示的 `BENCHCLAW` 目录就是 `PROJECT_ROOT`。

- `BENCHCLAW_ROOT`：BenchClaw 代码根目录，固定解析为：

```text
BENCHCLAW_ROOT = PROJECT_ROOT/BenchClaw
```

`BENCHCLAW_ROOT` 必须包含 `skills/`、`simulatorCards/`、`annotation-tool/` 等目录。当前 pipeline skill 的实际位置必须是：

```text
BENCHCLAW_ROOT/skills/benchmark-pipeline/SKILL.md
```

Stage skills 必须从 `BENCHCLAW_ROOT/skills/` 下解析，例如：

```text
BENCHCLAW_ROOT/skills/benchmark-stage1-draft/SKILL.md
BENCHCLAW_ROOT/skills/benchmark-stage2-data-collect/SKILL.md
BENCHCLAW_ROOT/skills/benchmark-stage3-evidence-compiler/SKILL.md
BENCHCLAW_ROOT/skills/benchmark-stage4-build/SKILL.md
BENCHCLAW_ROOT/skills/benchmark-stage5-eval/SKILL.md
```

禁止把 `PROJECT_ROOT` 误当成 `BENCHCLAW_ROOT`；否则会错误地寻找 `PROJECT_ROOT/skills/...`。

- `WORKSPACE_PARENT`：默认 workspace 父目录，固定解析为：

```text
WORKSPACE_PARENT = PROJECT_ROOT/workspaces
```

也就是说，`workspaces/` 与 `BenchClaw/` 是兄弟目录；workspace 不在 `BENCHCLAW_ROOT` 内部。

正确位置是：

```text
PROJECT_ROOT/workspaces/
```

错误位置是：

```text
BENCHCLAW_ROOT/workspaces/
PROJECT_ROOT/BenchClaw/workspaces/
BENCHCLAW_ROOT/workspace*
```

- `WORKSPACE_ROOT`：本次流程唯一总工作目录。若用户未提供 workspace，则在 `WORKSPACE_PARENT` 下扫描已有 `workspace{i}` 目录，取现有最大编号的下一个未占用目录作为新工作区，例如：

```text
PROJECT_ROOT/workspaces/workspace1
PROJECT_ROOT/workspaces/workspace2
PROJECT_ROOT/workspaces/workspace3
```

若当前最大编号为 `workspace3`，则新建并冻结：

```text
WORKSPACE_ROOT = PROJECT_ROOT/workspaces/workspace4
```

如果用户提供了其他 workspace，必须全程沿用同一个目录。

- 所有派生产物只写入 `WORKSPACE_ROOT/stage1` 到 `WORKSPACE_ROOT/stage5`，不得写入 `BENCHCLAW_ROOT`。
- 读取边界约束：只允许读取 `PROJECT_ROOT` 中本 skill 明确允许的项目结构、`BENCHCLAW_ROOT`、`WORKSPACE_ROOT` 以及本 skill 文本中显式提到的文件或目录；严禁主动读取这些范围之外的任何无关文件夹、用户目录、其他项目目录或其他 workspace。若确有必要读取额外路径，必须先得到用户明确授权并记录原因。
- 全局路径约束：`BENCHCLAW_ROOT` 仅作只读输入；`WORKSPACE_ROOT` 是本次流程唯一总工作目录，所有写操作和流程产物只能落在其下。

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

1. 冻结用户原始 benchmark idea，解析并确定 `PROJECT_ROOT`、`BENCHCLAW_ROOT`、`WORKSPACE_PARENT` 与 `WORKSPACE_ROOT`，并在 `WORKSPACE_ROOT/pipeline_state.json` 中记录当前 run。
2. 在任何 stage 启动前，必须先执行路径合法性检查并把结果写入 `WORKSPACE_ROOT/path_resolution.json`：

```text
- PROJECT_ROOT 必须解析为同时包含 BenchClaw/、thirty_part/、workspaces/、README.md 的外层总项目根目录。
- BENCHCLAW_ROOT 必须解析为 PROJECT_ROOT/BenchClaw；其下必须能看到 skills/、simulatorCards/、annotation-tool/。
- 当前 pipeline skill 必须位于 BENCHCLAW_ROOT/skills/benchmark-pipeline/SKILL.md。
- WORKSPACE_PARENT 必须解析为 PROJECT_ROOT/workspaces。
- WORKSPACE_ROOT 必须是本次 run 唯一工作目录，默认位于 PROJECT_ROOT/workspaces/workspace{i}，或位于用户明确提供的其他合法目录。
- WORKSPACE_ROOT 绝不能落在 BENCHCLAW_ROOT 内部，也不能等于 BENCHCLAW_ROOT，禁止出现 BENCHCLAW_ROOT/workspace*、BENCHCLAW_ROOT/workspaces/* 这一类路径。
- WORKSPACE_ROOT 必须与 PROJECT_ROOT、BENCHCLAW_ROOT 指向不同目录；若任一路径解析失败、目录结构不符、二者重叠或包含关系错误，pipeline 必须立即停止，不得继续调用任何子 skill。
```
3. 每次调用 Stage1/Stage2/Stage3/Stage4/Stage5 主 skill 或任何子 skill 时，必须在调用上下文中再次显式传递已经冻结的 `PROJECT_ROOT`、`BENCHCLAW_ROOT`、`WORKSPACE_PARENT` 和 `WORKSPACE_ROOT` 实际值，不得只传占位符名字，更不得让子 skill 自行猜测或重新推导。
4. 每个 stage 启动时，必须先对照 `WORKSPACE_ROOT/path_resolution.json` 重新确认本次接收到的 `PROJECT_ROOT`、`BENCHCLAW_ROOT`、`WORKSPACE_PARENT`、`WORKSPACE_ROOT` 与冻结值完全一致；若不一致，必须立即阻塞并记录错误，不能继续执行。
5. 执行 Stage1。Stage1 内部按自己的 ready-set/DAG 运行；pipeline 只等待 Stage1 终端节点完成。
6. Stage1 完成后，检查 Stage2 所需输入路径。若 Stage2 skill 的默认路径与 Stage1 实际输出目录不同，写入 `WORKSPACE_ROOT/config/stage2_input_paths.json`，不得复制或改写 Stage1 产物。
7. 执行 Stage2。Stage2 完成后必须看到真实图片、已有 benchmark、仿真器三个终端输出；缺一则 pipeline 停止并写 `WORKSPACE_ROOT/pipeline_blocked.md`。
8. 执行 Stage3。Stage3 必须从 Stage2 三个终端输出读取，并生成真实图半监督 GT、已有 benchmark 半监督 GT、仿真器 clean GT 三个终端输出。
9. 仿真器、真实数据、已有 benchmark 等数据源都必须实际采集到满足执行计划要求的充足数量，严禁以留空、占位、waiver、样例代替全量采集，也严禁直接跳过任一必需数据分支。标注工具必须对已采集数据进行充分利用并完成计划要求的全量处理，严禁留空、只做小样 smoke、只产出 placeholder/candidate 结构或以 deferred/waived 形式替代实际运行。
10. 执行 Stage4。Stage4 必须同时读取 Stage1 node 09 和 Stage3 18/19/20；不得恢复已移除的空占位节点或伪造 pilot/model-response 指标。
11. 执行 Stage5。Stage5 只读取 `WORKSPACE_ROOT/stage4/37-benchmark-artifact-pack`，先跑评测，再生成报告。
12. Stage5 完成后写 `WORKSPACE_ROOT/PIPELINE_DONE.json` 和 `WORKSPACE_ROOT/PIPELINE_REPORT.md`，汇总每个 stage 的输入、输出、检查结果和阻塞/waiver 记录。

额外强约束：

- Stage2 必须把 Stage3/Stage4 后续需要消费的真实图片、已有 benchmark 原始样本、仿真器观测与 GT 物化到 `WORKSPACE_ROOT` 下，不能只写外部路径、摘要、manifest 或统计报告了事。
- Stage3 必须对 Stage2 已物化的数据真实执行清洗、统一格式、标注与融合；若工具失败，只能显式阻塞并记录失败，不能用 `pending`、`placeholder`、`candidate only`、空 annotations 目录或说明文档冒充完成。
- Stage4 生成的 benchmark artifact pack 必须包含可实际消费的图文/多模态评测资产或其在 workspace 内的稳定物化副本；不得仅在 `eval_dataset.jsonl` 中写字符串路径、虚构图像引用或未落盘媒体引用。
- Stage5 只能基于真实模型 API 调用结果或已物化预测文件完成评测；严禁模拟预测、伪造分数、按哈希/规则生成假结果，或在缺少真实预测时继续产出完成报告。

## Handoff 规则

- 大阶段之间只通过 workspace 产物交接，不通过聊天上下文隐式传递事实。
- 大阶段之间传递上下文时，除了业务输入外，必须显式重复传递已经冻结的 `PROJECT_ROOT`、`BENCHCLAW_ROOT`、`WORKSPACE_PARENT` 和 `WORKSPACE_ROOT` 实际值，并要求下游 stage/子 skill 在开头复述确认；不得让下游重新猜测路径。
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
- 不允许把 `PROJECT_ROOT` 误当成 `BENCHCLAW_ROOT`；不允许把 `WORKSPACE_ROOT` 解析到 `BENCHCLAW_ROOT` 内部、解析为 `BENCHCLAW_ROOT` 自身、解析为 `PROJECT_ROOT` 自身，或在任何 stage/子 skill prompt、报告、DONE 文件中把这些路径混写、串写或互相替代。
- 不读取 `PROJECT_ROOT` 中本 skill 未授权的无关目录、`BENCHCLAW_ROOT`、`WORKSPACE_ROOT` 与本 skill 明示路径之外的无关目录或文件，除非用户明确授权。
- 不允许将任何必需数据源分支留空、跳过、降级为占位产物，或用样例/小批量运行冒充完成；不允许对已采集数据只做部分标注、空标注、placeholder 标注或其他未实跑的替代处理。
- 不允许只写 manifest、summary、report、jsonl 外壳而不物化后续 stage 必需消费的真实媒体、标注或评测输入。
- 不允许在 benchmark item、answer program、prediction log、leaderboard、pipeline report 中写入虚构的媒体引用、虚构的 GT 解析逻辑或虚构的模型评测结果。
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
