---
name: benchmark-stage4-build
description: "Stage 4 子流程：评测集构建、模板审查、指标实现与联调验证。编排评测蓝图与路由 → 评测集批量合成 → 指标体系与可执行 metric library 建立 → 联调验证 → Stage 4 单元测试。基于 Stage 1 的能力维度和 benchmark 草稿、Stage 2 的模板、Stage 3 的 final cleaned data，构建 HuggingFace 友好的评测集和可执行评分协议；不负责数据采集、数据清洗或模型评测执行。"
argument-hint: [stage3-dir]
allowed-tools: Bash(*), Read, Write, Edit, Grep, Glob, WebSearch, WebFetch, Skill
---

## `~/benchclaw` 只读约束

- **BENCHCLAW_READONLY = true**：`~/benchclaw/` 只能作为共享只读资源根。
- 严禁在 `~/benchclaw/` 下创建、编辑、覆盖、删除、移动、重命名、复制写入、初始化 git、提交、打 tag、写日志、写缓存或写临时文件。
- 所有派生产物、补丁、快照、报告、脚本、配置、日志和测试输出必须写入 active `WORKSPACE_ROOT`。
- 如必须修改 `~/benchclaw/` 中的资源，只能在 workspace 中生成 patch 或修改建议，等待用户在外部处理；当前 skill 不得直接应用。

# Benchmark Stage 4: 评测集构建与指标实现

面向：*$ARGUMENTS*

本 skill 是 Stage 4 的总控编排器，按 Stage1、Stage2、Stage3 同样的 phase-by-phase 方式调度 Stage 4 子 skill。Stage 4 的目标是把 Stage 3 的可信 cleaned data 路由到合适的评测模板和指标，生成 HuggingFace 友好的评测集，并实现可自动评分的 metric library。

Stage 4 不做数据采集，不做 Data-Juicer 清洗，不运行模型评测。模型评测属于 Stage 5。

## Overview

```text
Stage 1 + Stage 2 + Stage 3 artifacts
  |
  v
[1 评测蓝图、模板审查与 Stage3 数据路由]
  |
  v
[2 评测集批量合成与 HuggingFace 数据集落盘]
  |
  v
[3 指标体系与可执行 metric library 建立]
  |
  v
[4 评测集与指标联调验证]
  |
  v
[5 Stage 4 单元测试]
  |
  v
STAGE4_SUMMARY.md
```

每个 phase 都必须建立在前序 phase 的产物之上。不得跳过模板审查直接合成评测集，不得跳过指标实现只写指标文档，不得跳过联调验证进入 Stage 5。

## Workspace

- 当前运行目录为 `WORKSPACE_ROOT = ~/bench_workspace/workspace{i}`。
- Stage 4 必须继承 `/benchmark-pipeline`、Stage 1、Stage 2 或 Stage 3 已经创建并使用的 active `WORKSPACE_ROOT`，不得自行创建新的 `workspace{i}`，不得自动切换到序号最高的旧 workspace。
- 所有 Stage 4 中间过程文件、模板库、评测集、指标库、dry-run 输出、测试文件和报告都必须写入 `WORKSPACE_ROOT/stage4/`。
- 只能读写当前 workspace 的 `stage1/`、`stage2/`、`stage3/`、`stage4/`。
- 允许只读访问明确需要的全局资源，例如 `~/benchclaw/templates/`、`~/benchclaw/model_api/`、`~/benchclaw/skills/`。
- `~/benchclaw/` 下任何内容都不能被创建、编辑、覆盖、删除、移动、重命名、复制写入或作为日志/缓存/临时输出目录；模板库、评测集、指标库和验证结果必须写入 `WORKSPACE_ROOT/stage4/`。
- 不得读取、复用、比较或借鉴其它 `workspace{j}` 的产物，除非用户明确指定路径和复用范围。
- 不得把 Stage 4 运行产物写入 skill 源码目录、Downloads、当前项目目录、缓存目录或任意非 active workspace 路径。

## Constants

- **TEMPLATE_REVIEW_REQUIRED = true**：模板发布前必须完成适配性、区分度、抗捷径和能力维度对齐审查。
- **OBSERVATION_GROUNDED = true**：非 text-only 任务必须依赖图像、视频帧、深度图、观察载荷或其它声明的 multimodal evidence。
- **HF_DATASET_REQUIRED = true**：最终评测集必须写入 `stage4/EVALSET_DATASET/`，并符合 HuggingFace 友好结构。
- **EXECUTABLE_METRICS_REQUIRED = true**：指标必须有可导入、可运行、带测试的 Python 实现；不能只有文档。
- **NO_GT_LEAKAGE = true**：答案、GT token、别名、坐标、计数、场景标签和可泄露 metadata 不得出现在模型可见输入、选项、文件名或路径中。
- **NO_BENCHCLAW_WRITE = true**：`~/benchclaw/` 下所有内容只读，严禁增删改。
- **STAGE_BOUNDARY_STOP = true**：Stage 4 完成 `STAGE4_SUMMARY.md` 后必须停止，由用户选择下一步；不得自动进入 Stage 5。

## Required Inputs

Stage 4 启动前必须读取：

- `stage1/BENCHMARK_DRAFT.md`
- `stage1/EVALSET_PROTOTYPE.md`
- `stage1/CAPABILITY_SCOPE.md`
- `stage2/TEMPLATE_REFINEMENT_REPORT.md`
- `stage2/templates/*.yaml`
- `stage3/CLEANING_QUALITY_REPORT.md`
- `stage3/final/CLEANED_DATA_SCHEMA.md`
- `stage3/final/STAGE4_INPUT_MANIFEST.jsonl`
- `stage3/final/cleaned_data/`
- `stage3/final/CLEANING_LINEAGE.jsonl`
- `stage3/STAGE3_UNIT_TEST_REPORT.md`

若 Stage 3 的清洗验证或单元测试 verdict 为 `FAIL`，不得进入 Stage 4。若为 `NEEDS_REVIEW`，必须有用户明确 waiver。

## Pipeline

### Phase 1: Evalset Plan Route — 评测蓝图、模板审查与数据路由

调用：

```text
/1-benchmark-evalset-plan-route "$STAGE3_DIR"
```

输入：

- Stage 1 能力维度、benchmark 草稿和评测集原型。
- Stage 2 模板细化报告和模板文件。
- Stage 3 final manifest、cleaned data schema、confidence evidence 和 cleaned data。

执行内容：

- 为每个能力维度整理候选评测模板和指标接口候选。
- 在发布任何模板前，逐个执行 `Template Fitness Review`：
  - 是否符合用户意图和 benchmark 目标。
  - 是否具备区分不同模型能力水平的区分度。
  - 是否抗捷径，尤其是不给图像/观察载荷也能作答的情况。
  - 是否与能力维度、GT 字段、metric interface 对齐。
- 将 Stage3 cleaned samples 路由到 `{capability_dimension, template_id, metric_ids}`。
- 仅允许 `stage4_ready_status=ready`、置信度证据充分、字段完整、grounding 安全且模板审查通过的样本进入 `routing_status=ready`。

输出：

- `stage4/EVALSET_BLUEPRINT.md`
- `stage4/CAPABILITY_TEMPLATE_METRIC_MAP.json`
- `stage4/STAGE3_TO_EVALSET_ROUTING.jsonl`

Checkpoint：

- `EVALSET_BLUEPRINT.md` 必须包含 `Template Fitness Review`。
- `CAPABILITY_TEMPLATE_METRIC_MAP.json` 中每个可发布模板必须有 `template_review.verdict=PASS`。
- `FAIL` 或 `NEEDS_REVIEW` 模板不得用于 official routing。
- 若能力维度没有模板或指标候选，必须列入 blocking gaps。

### Phase 2: Evalset Generate — 评测集批量合成

调用：

```text
/2-benchmark-evalset-generate "$STAGE4_CONTEXT"
```

输入：

- `stage4/EVALSET_BLUEPRINT.md`
- `stage4/CAPABILITY_TEMPLATE_METRIC_MAP.json`
- `stage4/STAGE3_TO_EVALSET_ROUTING.jsonl`
- Stage 1、Stage 2、Stage 3 必需上下文。

执行内容：

- 只消费 `routing_status=ready` 的路由记录，不得直接遍历全部 Stage3 manifest 合成样本。
- 生成任务专属模板库，模板必须继承 Phase 1 的 `template_review.verdict=PASS`。
- 制定可复现的合成规则，包括采样策略、难度分级、source 平衡、去重、grounding 检查、泄露检查和 quarantine 行为。
- 生成 official eval questions，并执行 observation grounding 检查：
  - 非 text-only 任务必须需要声明的图片或观察载荷才能作答。
  - GT 字符串、别名、答案线索不得出现在可见输入、选项、文件名、路径或 public metadata 中。
  - 每道题必须有 `grounding_check.verdict=PASS` 才能进入 official dataset。
- 按 HuggingFace 友好结构写入 `EVALSET_DATASET/`。

输出：

- `stage4/EVALSET_TEMPLATE_LIBRARY/`
- `stage4/EVALSET_SYNTHESIS_RULES.md`
- `stage4/EVALSET_DATASET/`
- `stage4/EVALSET_SCHEMA.md`

`EVALSET_DATASET/` 固定结构：

```text
EVALSET_DATASET/
  README.md
  dataset_info.json
  data.jsonl
  manifest.json
  statistics.json
  gt_generators/
  {source_type}/{source_name}/{capability_dimension}/{question_id}/
    images/image_0001.{ext}
    images/image_0002.{ext}
    question.json
    question.md
    answer.json
    ground_truth.json
    gt_code_ref.json
    metadata.json
```

每道题必须有独立子文件夹。`gt_code_ref.json` 必须指明该题 GT 由哪个 generator 文件、函数、版本、输入字段和输出字段生成。`data.jsonl` 每行必须使用相对路径，并至少包含 `question_id`、`source_type`、`source_name`、`capability_dimension`、`question_dir`、`images`、`question_path`、`answer_path`、`ground_truth_path`、`gt_generator_file`、`gt_generator_function`、`metadata_path`、`template_id`、`metric_ids`、`split`。

Checkpoint：

- 不得输出扁平 evalset。
- 每题图片必须在该题自己的 `images/` 目录下编号。
- 未通过 grounding 或泄露检查的题不得进入 official dataset。
- 缺 HuggingFace root files、per-question folders 或 GT generator references 时，Phase 2 不得完成。

### Phase 3: Metric Establish — 指标体系与可执行评分库

调用：

```text
/3-benchmark-metric-establish "$STAGE4_CONTEXT"
```

输入：

- `stage4/EVALSET_DATASET/`
- `stage4/EVALSET_SCHEMA.md`
- `stage4/CAPABILITY_TEMPLATE_METRIC_MAP.json`
- `stage4/EVALSET_BLUEPRINT.md`
- Stage 1 的能力维度和评测原型。

执行内容：

- 为每个能力维度建立 primary、auxiliary 和 aggregate metric。
- 将模板声明的 `downstream_metrics`、Phase 1 的 metric interface candidates 和 `EVALSET_SCHEMA.md` 对齐。
- 写出指标定义、评分规则、能力维度到指标的覆盖映射。
- 实现可执行 `METRIC_LIBRARY/`，包括 metrics、aggregators、interfaces 和 tests。
- 生成 `tools/evaluate_evalset.py`，供 Stage 5 自动评分调用。
- 运行 metric tests 和 smoke eval，至少覆盖 GT-copy、empty prediction 和基础边界情况。

输出：

- `stage4/CAPABILITY_METRIC_MAP.md`
- `stage4/METRIC_SPEC.md`
- `stage4/SCORING_RULES.md`
- `stage4/METRIC_LIBRARY/metrics/*.py`
- `stage4/METRIC_LIBRARY/aggregators/*.py`
- `stage4/METRIC_LIBRARY/tests/test_*.py`
- `stage4/METRIC_LIBRARY/interfaces.py`
- `stage4/METRIC_LIBRARY/README.md`
- `stage4/tools/evaluate_evalset.py`

Checkpoint：

- `METRIC_LIBRARY/metrics/`、`aggregators/`、`tests/` 不得为空。
- 每个声明指标都必须有可导入实现。
- `tools/evaluate_evalset.py` 必须存在并通过 smoke run。
- 指标库只有文档、伪代码或空目录时，Phase 3 必须失败。

### Phase 4: Validate Stage4 — 评测集与指标联调验证

调用：

```text
/4-benchmark-validate-stage4 "$STAGE4_CONTEXT"
```

输入：

- `stage4/EVALSET_DATASET/`
- `stage4/EVALSET_SCHEMA.md`
- `stage4/METRIC_SPEC.md`
- `stage4/SCORING_RULES.md`
- `stage4/METRIC_LIBRARY/`
- `stage4/CAPABILITY_METRIC_MAP.md`
- `stage4/tools/evaluate_evalset.py`

执行内容：

- 验证 HuggingFace evalset folder contract：root files、`data.jsonl`、per-question folders、numbered images、GT generator references。
- 抽样检查 official questions 的 observation grounding、GT leakage、text-only baseline 风险。
- 验证评测集 schema 与 metric input/output interface 一致。
- 对抽样样本运行评分 dry-run，至少包含 random、zero/empty、GT-copy prediction。
- 验证每个指标值域、边界情况、维度级聚合、overall 聚合和可复现性。
- 验证能力维度覆盖率是否达到 `COVERAGE_THRESHOLD`，未覆盖维度必须有明确豁免。

输出：

- `stage4/VALIDATION_REPORT.md`
- `stage4/DRY_RUN_RESULTS.md`

Checkpoint：

- `VALIDATION_REPORT.md` verdict 必须为 `PASS` 才能进入 Phase 5；`FAIL` 必须列出 blocking issues 和 suggested fix phase。
- dry-run 必须实际调用 metric code，不能只做静态 schema 检查。
- 未实现指标、未 grounded 问题、HF 目录结构错误均为 hard fail。

### Phase 5: Unit Test — Stage 4 契约单元测试

调用：

```text
/5-benchmark-unit-test-stage4 "$STAGE4_DIR"
```

输入：

- Stage 4 全部产物。
- `stage3/STAGE3_UNIT_TEST_REPORT.md`。

执行内容：

- 生成并执行 `stage4/unit_tests/test_stage4_contract.py`。
- 测试 HuggingFace evalset 结构、`data.jsonl` 必备字段、per-question folder、local images、GT generator reference。
- 测试模板 `quality_constraints`、样本 `grounding_check.verdict=PASS`、GT leakage 和 text-only baseline。
- 测试 metric library 非空、声明指标实现、interfaces 导入、scoring smoke test。
- 测试 `VALIDATION_REPORT.md` verdict、dry-run 结果、能力维度覆盖和下游 Stage5 可用性。

输出：

- `stage4/unit_tests/test_stage4_contract.py`
- `stage4/unit_tests/results.json`
- `stage4/STAGE4_UNIT_TEST_REPORT.md`

Verdict 规则：

- `PASS`：评测集、模板、指标库、验证报告和下游接口全部满足，可进入 Stage 5。
- `NEEDS_REVIEW`：存在可解释缺口但不破坏评测集结构、指标可执行性或 grounding 安全，用户可确认 waiver。
- `FAIL`：HF 目录错误、问题不 grounded、GT 泄露、指标不可执行、声明指标缺实现、dry-run 失败、验证未通过或 Stage5 无法自动评分。

### Final Summary

完成 Phase 5 后必须写入：

- `stage4/STAGE4_SUMMARY.md`

`STAGE4_SUMMARY.md` 必须包含：

```markdown
# Stage4 Summary

## Executive Summary

## Phase Results
### Phase 1: Evalset Plan Route
### Phase 2: Evalset Generate
### Phase 3: Metric Establish
### Phase 4: Validate Stage4
### Phase 5: Unit Test

## Evalset Summary
| Split | Questions | Source Types | Capability Dimensions |
|-------|-----------|--------------|-----------------------|

## Metric Summary
| Capability Dimension | Primary Metrics | Auxiliary Metrics | Coverage Status |
|----------------------|-----------------|-------------------|-----------------|

## Validation Summary

## Final Deliverables

## Handoff To Stage 5
```

Stage 4 完成后必须停在这里，展示下一步选项：

1. Proceed to Stage 5
2. Rerun a Stage 4 phase
3. Review evalset, template review, metric library, validation report, or tests
4. Pause pipeline

不得自动调用 `/benchmark-stage5-eval`。即使 Gate 4 为 `PASS`，也只能说明“可以进入 Stage 5”，必须等待用户选择。

## Gate 4 — Evalset And Metric Checkpoint

进入 Stage 5 前必须满足：

- `STAGE4_UNIT_TEST_REPORT.md` verdict 为 `PASS`，或为 `NEEDS_REVIEW` 且用户明确确认 waiver。
- `VALIDATION_REPORT.md` verdict 为 `PASS`。
- `EVALSET_DATASET/` 满足 HuggingFace 一题一目录契约。
- 所有 official questions 都有 `grounding_check.verdict=PASS`，无 GT leakage。
- `METRIC_LIBRARY/` 含可执行 metrics、aggregators、interfaces 和 tests。
- `tools/evaluate_evalset.py` 可运行 smoke eval。

若任一 hard gate 失败，不得进入 Stage 5。

## 重新执行 Stage 4 的触发条件

| 问题 | 回退 phase |
|------|------------|
| 模板未审查、区分度不足、抗捷径失败或能力维度不匹配 | Phase 1 |
| Stage3 sample 路由缺字段、置信度证据不足或 routing 错误 | Phase 1 |
| evalset 目录不是 HuggingFace 结构、一题一目录缺失或 GT code ref 缺失 | Phase 2 |
| 问题可不看图作答、GT 泄露或 grounding 检查失败 | Phase 2 |
| 指标只有文档、缺实现、tests 为空或 smoke eval 失败 | Phase 3 |
| schema 与 metric interface 不一致、dry-run 或可复现性失败 | Phase 4 |
| 单元测试发现契约不一致 | Phase 5 |

## Key Rules

- **Do not skip phases.** 5 个 phase 严格顺序执行。
- **Review templates before publishing.** 模板通过 user-intent fit、discrimination power、shortcut resistance、capability alignment 检查后才能发布。
- **Questions must be observation-grounded.** 多模态任务必须需要声明的观察载荷才能作答。
- **No answer leakage.** GT、别名、可泄露 metadata、路径和文件名不得暴露答案。
- **HuggingFace dataset required.** 最终评测集必须在 `EVALSET_DATASET/`，并保留 `{source_type}/{source_name}/{capability_dimension}/{question_id}` 层级。
- **One question, one folder.** 每道题必须有独立文件夹、局部 `images/`、问题、答案、GT、GT code ref 和 metadata。
- **Executable metrics required.** 指标必须可运行、可测试、可供 Stage5 自动评分。
- **Validation is mandatory.** `VALIDATION_REPORT.md` 失败时不能进入 Stage5。
- **Trace lineage.** 模板、题目、GT、指标都必须能追溯到 Stage1/2/3 产物。
- **Never write to `~/benchclaw/`.** 参考模板、model_api 和 skills 只能只读；所有发布模板、评测集、GT generator、metric library 和报告必须写入 active workspace。
- **Stage boundary stop.** Stage 4 完成后必须停住，展示下一步选项，等待用户选择；不得自动进入 Stage 5。

## Fixed Artifact Format Contract

```text
stage4/
  EVALSET_BLUEPRINT.md
  CAPABILITY_TEMPLATE_METRIC_MAP.json
  STAGE3_TO_EVALSET_ROUTING.jsonl
  EVALSET_TEMPLATE_LIBRARY/
  EVALSET_SYNTHESIS_RULES.md
  EVALSET_SCHEMA.md
  EVALSET_DATASET/
    README.md
    dataset_info.json
    data.jsonl
    manifest.json
    statistics.json
    gt_generators/
    {source_type}/{source_name}/{capability_dimension}/{question_id}/
      images/image_0001.{ext}
      question.json
      question.md
      answer.json
      ground_truth.json
      gt_code_ref.json
      metadata.json
  CAPABILITY_METRIC_MAP.md
  METRIC_SPEC.md
  SCORING_RULES.md
  METRIC_LIBRARY/
    metrics/{metric_name}.py
    aggregators/dimension_aggregator.py
    aggregators/overall_aggregator.py
    tests/test_{metric_name}.py
    interfaces.py
    README.md
  tools/evaluate_evalset.py
  VALIDATION_REPORT.md
  DRY_RUN_RESULTS.md
  unit_tests/test_stage4_contract.py
  unit_tests/results.json
  STAGE4_UNIT_TEST_REPORT.md
  STAGE4_SUMMARY.md
```

`EVALSET_DATASET/data.jsonl` 每行必须至少包含：

```json
{
  "question_id": "...",
  "source_type": "simulator | existing_dataset | real_data",
  "source_name": "...",
  "capability_dimension": "...",
  "question_dir": "...",
  "images": [],
  "question_path": "...",
  "answer_path": "...",
  "ground_truth_path": "...",
  "gt_generator_file": "...",
  "gt_generator_function": "...",
  "metadata_path": "...",
  "template_id": "...",
  "metric_ids": [],
  "split": "train | validation | test"
}
```
