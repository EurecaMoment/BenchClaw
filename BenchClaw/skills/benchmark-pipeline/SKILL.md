---
name: benchmark-pipeline
description: "BenchClaw 六阶段流水线总控。按顺序编排 Stage1 草稿、Stage2 原始数据采集、Stage3 清洗与置信度提升、Stage4 评测集构建、Stage5 模型评测、Stage6 诊断维护；负责阶段调度、输入输出契约、单元测试门控和阶段间确认。"
argument-hint: [benchmark-idea]
allowed-tools: Bash(*), Read, Write, Edit, Grep, Glob, WebSearch, WebFetch, Skill
---

## `~/benchclaw` 只读约束

- **BENCHCLAW_READONLY = true**：`~/benchclaw/` 只能作为共享只读资源根。
- 严禁在 `~/benchclaw/` 下创建、编辑、覆盖、删除、移动、重命名、复制写入、初始化 git、提交、打 tag、写日志、写缓存或写临时文件。
- 所有派生产物、补丁、快照、报告、脚本、配置、日志和测试输出必须写入 active `WORKSPACE_ROOT`。
- 如必须修改 `~/benchclaw/` 中的资源，只能在 workspace 中生成 patch 或修改建议，等待用户在外部处理；当前 skill 不得直接应用。

# Benchmark Pipeline Orchestrator

面向：*$ARGUMENTS*

本 skill 只做六阶段流水线编排，不重写各阶段内部逻辑。每个大 Stage 完成后必须停止，展示阶段结果和可选下一步，由用户自己选择；不能自动跳到下一 Stage。

## Workspace 边界

- 当前运行目录为 `WORKSPACE_ROOT = ~/bench_workspace/workspace{i}`，其中 `i` 是递增整数。
- 初始化流水线时，必须先创建新的 active workspace：扫描 `~/bench_workspace/workspace*`，取现有最大编号 `max_i`，创建 `~/bench_workspace/workspace{max_i+1}`；若不存在任何 workspace，则创建 `~/bench_workspace/workspace1`。
- 若用户或父流程已经显式传入 `WORKSPACE_ROOT`，必须沿用该目录，不得重新选择“最新 workspace”或另建目录。
- 初始阶段必须在 active workspace 下创建 `stage1/` 到 `stage6/` 目录；后续阶段只能在这些目录内写入产物。
- 所有中间过程文件、阶段产物、日志、临时 manifest、生成脚本、测试文件和报告都必须写在 active `WORKSPACE_ROOT` 下。
- 只能读写当前 workspace 的 `stage1/` 到 `stage6/` 目录。
- 不得读取、复用、比较或借鉴其它 `workspace{j}` 的产物，除非用户明确给出路径和复用范围。
- 共享资源只允许读取明确列出的全局目录，例如 `~/benchclaw/simulator_cards/`、`~/benchclaw/dataset_cards/`、`~/benchclaw/realdata_cards/`、`~/benchclaw/templates/`、`~/benchclaw/model_api/`、`~/benchclaw/skills/`；不得向这些共享资源目录写入本轮中间产物。
- `~/benchclaw/` 是全局不可变共享资源根，只能只读访问；严禁在其中创建、编辑、覆盖、删除、移动、重命名、复制写入、初始化仓库、提交、打 tag 或写入任何日志/缓存/临时文件。
- 不得把运行产物写入 skill 源码目录、Downloads、当前项目目录、缓存目录或任意非 active workspace 路径。

## Workspace 初始化

流水线开始时必须执行以下逻辑：

```text
1. Resolve BENCH_WORKSPACE_ROOT = ~/bench_workspace
2. List only BENCH_WORKSPACE_ROOT/workspace*
3. Parse numeric suffix i
4. Create WORKSPACE_ROOT = ~/bench_workspace/workspace{max_i+1}
5. Create stage1/, stage2/, stage3/, stage4/, stage5/, stage6/
6. Pass this exact WORKSPACE_ROOT to every downstream stage skill
```

除非用户明确指定已有 `WORKSPACE_ROOT` 继续运行，否则不得使用最高编号的旧 workspace 作为新任务工作区。所有 stage 的相对路径，例如 `stage2/RAW_DATA_COLLECTION_REPORT.md`，都表示 `WORKSPACE_ROOT/stage2/RAW_DATA_COLLECTION_REPORT.md`。

## Stage 边界人工决策门

- **STAGE_BOUNDARY_STOP = true**：每个大 Stage 结束后必须停下来，不能自动调用下一 Stage。
- **USER_CHOOSES_NEXT = true**：下一步必须由用户明确选择，不能由 pipeline 根据 `PASS`、`NEEDS_REVIEW` 或默认策略自行推进。
- 每个 Stage 完成时必须展示：
  - 当前 Stage 的 summary 路径和 gate verdict。
  - 关键产物路径。
  - blocking issues 或 waiver 需求。
  - 可选下一步列表。
- 可选下一步至少包含：
  - 进入下一 Stage。
  - 回退并重跑当前 Stage 的某个 phase。
  - 查看或审查当前 Stage 产物。
  - 暂停 pipeline。
- 即使 gate verdict 为 `PASS`，也只能说明“可以进入下一 Stage”，不得直接执行下一 Stage。
- 若 gate verdict 为 `NEEDS_REVIEW`，必须先由用户明确选择 waiver 或回退修复。
- 若 gate verdict 为 `FAIL` 或 `BLOCKED`，不得提供“直接进入下一 Stage”作为默认动作，只能提供修复、重跑、审查或暂停。

## 总流程

下图只表示合法顺序，不表示自动连续执行。每个箭头处都必须经过 Stage 边界人工决策门。

```text
/benchmark-stage1-draft
-> /benchmark-stage2-data-collect
-> /benchmark-stage3-data-clean
-> /benchmark-stage4-build
-> /benchmark-stage5-eval
-> /benchmark-stage6-diagnosis-maintenance
-> BENCHMARK_PIPELINE_REPORT.md
```

## Stage 1: 草稿生成 + 单元测试

调用：

```text
/benchmark-stage1-draft "$raw_idea"
```

内部链路：

```text
raw_idea
-> /1-idea-target-refine - 问题扩充重述
-> /2-benchmark-literature-survey - 文献调研
-> /3-benchmark-capability-scope - 能力维度界定
-> /4-benchmark-data-source-selection - 数据源选择
-> /5-benchmark-evalset-prototype-gen - 评测集原型生成
-> /6-benchmark-draft-gen - 草稿生成
-> /7-benchmark-execution-plan-gen - 执行计划生成
-> /8-benchmark-unit-test-stage1 - Stage 1 单元测试
```

必需产物：

- `stage1/IDEA_TARGET.md`
- `stage1/LITERATURE_REVIEW.md`
- `stage1/CAPABILITY_SCOPE.md`
- `stage1/DATA_SOURCE_MAPPING.md`
- `stage1/SIMULATOR_MAPPING.md`
- `stage1/DATASET_MAPPING.md`
- `stage1/REALDATA_MAPPING.md`
- `stage1/EVALSET_PROTOTYPE.md`
- `stage1/evalset_template_drafts/`
- `stage1/evalset_template_drafts/TEMPLATE_DRAFT_INDEX.md`
- `stage1/evalset_template_drafts/TEMPLATE_DRAFT_LINEAGE.md`
- `stage1/evalset_template_drafts/ANTI_COPY_DECLARATION.md`
- `stage1/BENCHMARK_DRAFT.md`
- `stage1/EXECUTION_PLAN.md`
- `stage1/STAGE1_UNIT_TEST_REPORT.md`
- `stage1/STAGE1_SUMMARY.md`

Gate 1：`STAGE1_UNIT_TEST_REPORT.md` verdict 必须为 `PASS`，或 `NEEDS_REVIEW` 且用户明确确认 waiver，才具备进入 Stage 2 的条件。Stage 1 结束后必须停止，展示 `STAGE1_SUMMARY.md`、verdict 和下一步选项，等待用户选择是否进入 Stage 2、回退修订 Stage 1、审查产物或暂停。

## Stage 2: 原始数据采集 + 单元测试

调用：

```text
/benchmark-stage2-data-collect "$STAGE1_DIR"
```

Stage 2 只负责原始数据采集、已有数据集接入和真实数据登记。它不得清洗、过滤、去重删除或拒收可访问样本。所有采集的原始数据都要以记录、manifest、日志和 `RAW_DATA_COLLECTION_REPORT.md`的形式保存。并且严禁不采集任何数据就跳过本阶段，严禁拷贝其他workspace的旧数据。

内部链路：

```text
Stage 1 artifacts
-> /1-benchmark-data-capability-survey - 数据能力调研
-> /2-benchmark-collection-guidance - 采集指导生成
-> /3-benchmark-template-refinement - 模板细化
-> /4-benchmark-collect-codegen - 采集脚本生成
-> /5-benchmark-batch-collect - 批量采集执行
-> /6-benchmark-unit-test-stage2 - Stage 2 单元测试
```

必需产物：

- `stage2/SOURCE_CAPABILITY_SURVEY.md`
- `stage2/COLLECTION_GUIDANCE_PLAN.md`
- `stage2/TEMPLATE_REFINEMENT_REPORT.md`
- `stage2/templates/*.yaml`
- `stage2/DATA_SCHEMA.md`
- `stage2/collect_scripts/`
- `stage2/ingest_scripts/`
- `stage2/register_scripts/`
- `stage2/collected_data/{source_type}/{source_name}/images/{sample_id}.{ext}`
- `stage2/collected_data/{source_type}/{source_name}/records/{sample_id}.json`
- `stage2/collected_data/{source_type}/{source_name}/manifest.jsonl`
- `stage2/logs/`
- `stage2/RAW_DATA_COLLECTION_REPORT.md`
- `stage2/unit_tests/test_stage2_contract.py`
- `stage2/unit_tests/results.json`
- `stage2/STAGE2_UNIT_TEST_REPORT.md`
- `stage2/STAGE2_SUMMARY.md`

Stage 2 的三类数据源 `simulator`、`existing_dataset`、`real_data` 必须使用同一套 skill 并行或等价并行处理。`source_name` 可以表示一次处理的数据批次、一个仿真器场景/地图/任务配置、一个已有数据集切片或一个真实采集批次；它必须能作为稳定目录名，并在 manifest、JSON 记录、报告和日志中保持一致。

Gate 2：Stage 2 单元测试只检查原始采集契约、文件格式、可追溯性和禁止过滤规则；不得因为数据质量低、缺少 GT、重复、模糊或需要标注而阻断进入 Stage 3。Stage 2 结束后必须停止，展示 `STAGE2_SUMMARY.md`、`STAGE2_UNIT_TEST_REPORT.md`、`RAW_DATA_COLLECTION_REPORT.md` 和下一步选项，等待用户选择是否进入 Stage 3、回退重采、审查数据或暂停。

## Stage 3: 数据清洗 + 置信度提升 + 单元测试

调用：

```text
/benchmark-stage3-data-clean "$STAGE2_DIR"
```

Stage 3 的核心目的，是提升 Stage 2 采集到的图文数据的可信度、可用性、一致性和可评测性。清洗、过滤、去重、异常处理、半自动标注、Data-Juicer 配置与执行、样本拒收、Stage4 readiness 判断都属于 Stage 3。

Stage 3 必须保持图像与元数据一一对应。如果处理后的图片与原图不同，例如 YOLO 画框、深度图生成、掩码叠加、裁剪增强等，必须同时保存原图和处理后图片，并在元数据 JSON 中明确对应关系、处理代码、参数和来源。

必需产物包括：

- `stage3/CLEANING_PLAN.md`
- `stage3/datajuicer_configs/`
- `stage3/clean_scripts/`
- `stage3/cleaned_data/{source_type}/{source_name}/images/`
- `stage3/cleaned_data/{source_type}/{source_name}/records/`
- `stage3/cleaned_data/{source_type}/{source_name}/manifest.jsonl`
- `stage3/CONFIDENCE_IMPROVEMENT_REPORT.md`
- `stage3/STAGE3_UNIT_TEST_REPORT.md`
- `stage3/STAGE3_SUMMARY.md`

Gate 3：只有通过 Stage3 readiness 检查的数据才具备进入 Stage 4 的条件。Stage 3 结束后必须停止，展示 `STAGE3_SUMMARY.md`、`STAGE3_UNIT_TEST_REPORT.md`、`CLEANING_QUALITY_REPORT.md` 和下一步选项，等待用户选择是否进入 Stage 4、回退重清洗、审查 final 数据或暂停。

## Stage 4: 评测集构建 + 模板发布检查

调用：

```text
/benchmark-stage4-build "$STAGE3_DIR"
```

内部链路：

```text
Stage 3 artifacts
-> /1-benchmark-evalset-plan-route - 评测模板、指标与数据路由规划
-> /2-benchmark-evalset-generate - 评测集批量合成
-> /3-benchmark-metric-establish - 指标实现与评分协议固化
-> /4-benchmark-validate-stage4 - 评测集与指标联调验证
-> /5-benchmark-unit-test-stage4 - Stage 4 单元测试
```

Stage 4 必须读取 `stage1/EVALSET_PROTOTYPE.md` 和 `stage1/evalset_template_drafts/` 作为模板候选来源，但不能直接发布 Stage 1 初稿；必须先判断模板是否符合评测要求，再发布模板并批量合成评测集。检查项至少包括：模板是否符合用户意图、是否具有区分度、是否抗捷径、不给图片是否无法稳定作答、能力维度是否对应、指标是否可执行且可复现。

评测集最终必须符合 HuggingFace dataset 组织方式，并放入 `stage4/EVALSET_DATASET/`。每道题必须有独立子文件夹，包含答题所需图片、问题、候选答案或参考答案、ground truth、生成 GT 的代码引用和元数据。上级目录组织方式需与 Stage2、Stage3 的 `{source_type}/{source_name}` 思路保持一致。

示例结构：

```text
stage4/EVALSET_DATASET/
  README.md
  dataset_info.json
  data.jsonl
  {source_type}/{source_name}/{question_id}/
    images/{image_id}.{ext}
    question.json
    answer.json
    ground_truth.json
    metadata.json
    gt_code_ref.json
  gt_code/{code_file}
```

Gate 4：模板审查、数据路由、题目文件结构、GT 代码引用和运行器测试全部通过后，才具备进入 Stage 5 的条件。Stage 4 结束后必须停止，展示 `STAGE4_SUMMARY.md`、`STAGE4_UNIT_TEST_REPORT.md`、`VALIDATION_REPORT.md` 和下一步选项，等待用户选择是否进入 Stage 5、回退重建评测集/指标、审查评测集或暂停。

## Stage 5: 灰度评测 + 全量模型评测 + 结果质检

调用：

```text
/benchmark-stage5-eval "$STAGE4_DIR"
```

Stage 5 负责把 Stage 4 的官方评测集和可执行指标库用于真实模型评测。它必须先通过灰度/金丝雀评测验证 prompt、API、schema、metric、成本、解析稳定性和 GT 泄露风险，再决定是否进入全量评测。Stage 5 不得修改 Stage 4 的评测集、GT、指标代码或 scoring rules；发现问题只能写报告、定位回退点或停止。

内部链路：

```text
Stage 4 artifacts
-> /1-benchmark-build-eval-system-prompt - 评测 system prompt、输出格式与运行配置
-> /2-benchmark-canary-eval - 灰度/金丝雀评测
-> /3-benchmark-canary-localize-rollback - 灰度失败定位与回退计划（仅灰度失败或 NEEDS_REVIEW 无 waiver 时）
-> /4-benchmark-call-model-api - 全量模型 API 推理（仅灰度 PASS 或用户确认 waiver 后）
-> /5-benchmark-run-metrics - 调用 Stage4 metric library 打分与聚合
-> /6-benchmark-check-scores - 分数异常、污染、失败案例与报告生成
-> STAGE5_SUMMARY.md
```

启动前必需输入：

- `stage4/EVALSET_DATASET/`
- `stage4/EVALSET_SCHEMA.md`
- `stage4/METRIC_LIBRARY/`
- `stage4/METRIC_SPEC.md`
- `stage4/SCORING_RULES.md`
- `stage4/tools/evaluate_evalset.py`
- `stage4/VALIDATION_REPORT.md`，verdict 必须为 `PASS`
- `stage4/STAGE4_UNIT_TEST_REPORT.md`，verdict 必须为 `PASS`，或 `NEEDS_REVIEW` 且用户明确确认 waiver
- `stage1/BENCHMARK_DRAFT.md`
- `stage1/CAPABILITY_SCOPE.md`
- `stage2/STAGE2_UNIT_TEST_REPORT.md`
- `stage3/STAGE3_UNIT_TEST_REPORT.md`
- `stage5/MODEL_API_CONFIG.json` 或 workspace 根目录下的 `MODEL_API_CONFIG.json`；若缺失，可只按 Stage5 skill 明确允许的 `LOCAL_MODEL_API_AWARE` 规则读取 `~/benchclaw/model_api/`

必需产物：

- `stage5/EVAL_SYSTEM_PROMPT.md`
- `stage5/RUN_CONFIG.json`
- `stage5/MODEL_API_CONFIG.snapshot.json`
- `stage5/CANARY_SAMPLE_MANIFEST.jsonl`
- `stage5/CANARY_RAW_OUTPUTS.jsonl`
- `stage5/CANARY_METRICS.json`
- `stage5/CANARY_VERDICT.json`
- `stage5/CANARY_EVAL_REPORT.md`
- `stage5/CANARY_ROLLBACK_PLAN.md`（灰度失败或需要回退时）
- `stage5/ROLLBACK_STATE_PATCH.json`（灰度失败或需要回退时）
- `stage5/RAW_MODEL_OUTPUTS.jsonl`（仅灰度 PASS 或用户确认 waiver 后）
- `stage5/API_RUN_SUMMARY.json`（全量推理执行时）
- `stage5/API_FAILURES.jsonl`（全量推理执行时）
- `stage5/FULL_EVAL_ABORT_REPORT.md`（全量 API 失败率超阈值时）
- `stage5/SCORES.jsonl`
- `stage5/AGGREGATED_METRICS.json`
- `stage5/DIMENSION_WISE_ANALYSIS.md`
- `stage5/SCORE_CHECK_REPORT.md`
- `stage5/FAILURE_CASES.md`
- `stage5/EVALUATION_REPORT.md`
- `stage5/STAGE5_SUMMARY.md`

Stage 5 必须遵守：

- **Canary first.** `CANARY_REQUIRED = true`，没有 `CANARY_VERDICT.json` 和 `CANARY_EVAL_REPORT.md` 不得进入全量评测。
- **No full eval on canary fail.** 灰度 `FAIL` 必须运行 `/benchmark-canary-localize-rollback`，生成回退计划，并停止全量评测。
- **Waiver explicit.** 灰度 `NEEDS_REVIEW` 只有在用户明确确认 waiver 后才能进入全量评测。
- **No GT leakage.** 评测 prompt、模型输入、选项、路径、metadata 和模型可见上下文不得泄露 GT、评分公式或 metric implementation。
- **Keep raw outputs.** `RAW_MODEL_OUTPUTS.jsonl` 必须保留每条模型原始输出、解析状态、API 状态、延迟、重试和失败原因；不得静默丢弃失败样本。
- **Use Stage4 metrics only.** 打分必须调用 Stage 4 的 `METRIC_LIBRARY/` 和 `SCORING_RULES.md`，不得在 Stage 5 重新实现或改写指标。
- **Pause on API failure.** 全量 API 失败率超过阈值时必须写 `FULL_EVAL_ABORT_REPORT.md` 并暂停，不得继续打分制造假完整结果。
- **Contamination check.** 结果质检必须检查 GT 泄露、prompt 回显、模板污染、异常高分、异常低分、拒答模式、格式违规和维度覆盖缺口。

Gate 5：

- `CANARY_VERDICT.json.verdict = PASS`，或 `NEEDS_REVIEW` 且用户确认 waiver，才允许全量评测。
- 全量评测完成时，`RAW_MODEL_OUTPUTS.jsonl`、`SCORES.jsonl`、`AGGREGATED_METRICS.json`、`SCORE_CHECK_REPORT.md`、`FAILURE_CASES.md`、`EVALUATION_REPORT.md` 和 `STAGE5_SUMMARY.md` 必须存在。
- 若灰度失败，必须存在 `CANARY_ROLLBACK_PLAN.md` 和 `ROLLBACK_STATE_PATCH.json`，且不得存在被标记为完成的全量评测结果。
- 只有 `STAGE5_SUMMARY.md` 明确写明 `handoff_to_stage6 = allowed`，才具备进入 Stage 6 的条件。
- Stage 5 结束后必须停止，展示 `STAGE5_SUMMARY.md`、`CANARY_EVAL_REPORT.md`、`EVALUATION_REPORT.md` 或 `CANARY_ROLLBACK_PLAN.md`，以及下一步选项，等待用户选择是否进入 Stage 6、按回退计划修复、审查评测结果或暂停。

## Stage 6: 诊断维护 + 回归测试

调用：

```text
/benchmark-stage6-diagnosis-maintenance "$STAGE5_DIR"
```

Stage 6 负责评价整个 Stage 1-5 流程本身，定位流程缺陷、测试缺口和 skill 规则缺口，并在用户确认后对 skill 做最小手术刀式修订与回归验证。Stage 6 不是再次评测模型，也不得改写 Stage 1-5 的历史评测结果。

内部链路：

```text
Stage 1-5 artifacts
-> /benchmark-process-evaluate - 全流程质量评价
-> /benchmark-root-cause-analyze - 根因定位到 stage/phase/skill/artifact/rule gap
-> /benchmark-skill-version-control - 建立 skill 修改前版本控制基线
-> /benchmark-skill-surgical-revision - 手术刀式 skill 修改（需用户确认）
-> /benchmark-skill-regression-verify - 修改后回归验证
-> STAGE6_SUMMARY.md
```

启动前必需输入：

- `stage1/STAGE1_SUMMARY.md`
- `stage1/STAGE1_UNIT_TEST_REPORT.md`
- `stage2/STAGE2_SUMMARY.md`
- `stage2/STAGE2_UNIT_TEST_REPORT.md`
- `stage3/STAGE3_SUMMARY.md`
- `stage3/STAGE3_UNIT_TEST_REPORT.md`
- `stage4/STAGE4_SUMMARY.md`
- `stage4/STAGE4_UNIT_TEST_REPORT.md`
- `stage5/STAGE5_SUMMARY.md`
- `stage5/CANARY_EVAL_REPORT.md`
- `stage5/CANARY_ROLLBACK_PLAN.md`（灰度失败或回退模式）
- `stage5/EVALUATION_REPORT.md`
- `stage5/SCORE_CHECK_REPORT.md`
- `stage5/FAILURE_CASES.md`

Stage 6 可以在两种模式下运行：

- `post-full-eval mode`：全量评测完成后，基于完整 Stage 1-5 证据做流程复盘和 skill 维护。
- `rollback-diagnosis mode`：灰度失败、全量中断或 Gate 5 阻塞时，基于失败证据提前定位根因和维护建议。

必需产物：

- `stage6/PROCESS_EVALUATION_REPORT.md`
- `stage6/PROCESS_METRICS.json`
- `stage6/ROOT_CAUSE_ANALYSIS.md`
- `stage6/DEFECT_TRIAGE_MATRIX.json`
- `stage6/SKILL_FIX_CANDIDATES.md`
- `stage6/VERSION_CONTROL_LOG.md`
- `stage6/SKILL_BASELINE_MANIFEST.json`
- `stage6/GIT_BASELINE.diff`
- `stage6/ALLOWED_SKILL_EDIT_LIST.txt`
- `stage6/SKILL_REVISION_PLAN.md`（若执行 skill 修改）
- `stage6/SKILL_PATCH.diff`（若执行 skill 修改）
- `stage6/SKILL_CHANGELOG.md`（若执行 skill 修改）
- `stage6/UPDATED_SKILL_MANIFEST.json`（若执行 skill 修改）
- `stage6/SKILL_REGRESSION_REPORT.md`
- `stage6/REGRESSION_COMMANDS.sh`
- `stage6/REGRESSION_RESULTS.json`
- `stage6/VERSION_CONTROL_BLOCKED.md`（版本控制不可用时）
- `stage6/STAGE6_SUMMARY.md`

Stage 6 必须遵守：

- **Diagnose process, not model only.** 评价对象是流程质量，包括阶段契约、数据 lineage、单元测试有效性、灰度门控、评测集覆盖、指标可执行性、成本和失败案例诊断力。
- **Evidence chain required.** 每个根因必须引用具体证据路径，定位到 `stage -> phase -> skill -> artifact -> rule gap`。
- **No broad rewrite.** skill 修改必须是最小范围，默认单轮最多触碰 `MAX_SURGICAL_FILES` 个文件；不得大面积重写无关 skill。
- **User confirmation before edits.** 根因报告和修改计划必须展示给用户；未经确认不得执行 skill 源码修改。
- **Version control baseline first.** 修改前必须记录 git baseline、dirty worktree、分支、diff 和允许修改白名单。
- **Do not overwrite user changes.** 若 skill repo 存在用户未确认的 dirty changes，只能记录 baseline 和阻塞原因，不得覆盖。
- **Regression required.** 修改后必须生成并执行回归验证计划，至少覆盖 frontmatter、allowed-tools、I/O 契约、相关 stage gate、灰度失败定位链路和未触碰文件检查。
- **No commit on failed regression.** 回归未通过时不得提交或标记版本完成，只保留 patch、报告和下一步建议。

Gate 6：

- `PROCESS_EVALUATION_REPORT.md` 和 `PROCESS_METRICS.json` 必须覆盖 Stage 1-5。
- `ROOT_CAUSE_ANALYSIS.md` 必须把缺陷定位到最小负责单位，并标出证据强度；证据不足时不得强行修 skill。
- 若执行 skill 修改，`SKILL_PATCH.diff`、`SKILL_CHANGELOG.md`、`UPDATED_SKILL_MANIFEST.json` 必须存在。
- `SKILL_REGRESSION_REPORT.md` 必须给出 `PASS | FAIL | NEEDS_REVIEW | BLOCKED` verdict。
- `STAGE6_SUMMARY.md` 必须说明下一轮 pipeline 应如何使用修改后的 skill，以及是否允许发布/合并本轮修订。
- Stage 6 结束后必须停止，展示 `STAGE6_SUMMARY.md`、`PROCESS_EVALUATION_REPORT.md`、`ROOT_CAUSE_ANALYSIS.md`、`SKILL_REGRESSION_REPORT.md` 和下一步选项，等待用户选择是否发布/合并修订、继续修复、开启新 pipeline 或暂停。

## 全局固定格式规则

- 每个阶段都必须写入对应的阶段总结：`STAGE1_SUMMARY.md` 到 `STAGE6_SUMMARY.md`。
- Stage 1-4 必须写入 `STAGE{N}_UNIT_TEST_REPORT.md`；Stage 5 必须写入 `CANARY_EVAL_REPORT.md`、`SCORE_CHECK_REPORT.md` 和 `EVALUATION_REPORT.md`；Stage 6 必须写入 `PROCESS_EVALUATION_REPORT.md`、`ROOT_CAUSE_ANALYSIS.md` 和 `SKILL_REGRESSION_REPORT.md`。
- 每个阶段的主要产物文件名必须固定，不得用临时名称代替。
- 样本级图像数据必须通过 manifest 与 JSON 记录一一对应。
- Stage 2 不得出现清洗、过滤、质量拒收作为执行行为。
- Stage 3 必须明确践行“提升图文数据置信度”的目标。
- Stage 4 必须在发布模板前完成模板质量自检。
- Stage 5 必须先灰度再全量；灰度失败不得启动全量评测。
- Stage 6 必须先根因定位和版本控制基线，再做最小 skill 修改和回归验证。
- 每个大 Stage 结束后必须停止并等待用户选择下一步；不得自动串联进入下一 Stage。
- `~/benchclaw/` 下任何内容全局只读，所有需要保存的补丁、报告、快照、临时文件和运行产物都必须写入 active `WORKSPACE_ROOT`，不得对 `~/benchclaw/` 做任何增删改。
