---
name: benchmark-stage2-data-collect
description: "Stage 2 子流程：数据收集与原始资产接入。根据 Stage 1 的 DATA_SOURCE_MAPPING.md 同时处理三类数据源：仿真器 simulator、已有数据集 existing_dataset、真实数据 real_data；生成采集/接入方案、模板、脚本或登记工具、原始数据目录与质量报告。Use when user says '开始 stage2', '数据采集', '采集数据', 'data collection stage'."
argument-hint: [stage1-dir]
allowed-tools: Bash(*), Read, Write, Edit, Grep, Glob, WebSearch, WebFetch, Skill
---


## Workspace and File Access Boundary

This skill must operate only inside the current run workspace.

- Before reading or writing any run artifact, resolve and record the active `WORKSPACE_ROOT = ~/bench_workspace/workspace{i}` from the current task, parent stage, or pipeline state.
- Read and write only files under the active `WORKSPACE_ROOT` and the explicitly required global resource roots named by this skill, such as `~/benchclaw/simulator_cards/`, `~/benchclaw/dataset_cards/`, `~/benchclaw/realdata_cards/`, `~/benchclaw/templates/`, `~/benchclaw/model_api/`, `~/benchclaw/data-juicer_card/`, `~/benchclaw/annotation-tool/`, or `~/benchclaw/skills/` when the current skill explicitly requires them.
- Never read, list, grep, summarize, compare, copy, or infer from any other `~/bench_workspace/workspace{j}` where `j != i`, even if the current artifact is missing or another workspace appears newer or more complete.
- Never scan broad server directories such as `~`, `/`, `/home`, `/mnt`, `/data`, `/tmp`, `C:\Users`, `C:\`, or arbitrary project/download folders to discover context. Only inspect the exact current workspace paths and exact allowlisted resource roots needed for this skill.
- If an expected input is missing from the active workspace or an allowlisted resource root, stop and report the missing path. Do not search unrelated folders or borrow replacement artifacts from another workspace.
- Outputs must be written only to the active `WORKSPACE_ROOT` paths declared by this skill. Do not mirror or cache run artifacts into other workspaces or unrelated server folders.
- If the user explicitly provides an external path, use it only when it is directly relevant to this skill, record it as a user-provided exception, and do not expand access to sibling or parent directories.

This boundary overrides convenience behaviors such as auto-discovery, resume from latest workspace, reuse of previous artifacts, broad recursive grep/list, and fallback search.

# Benchmark Stage 2：同一套 Skill 的三类数据并行收集与接入

面向：**$ARGUMENTS**

本 skill 是 Stage 2 的编排器，只负责按顺序调度同一套子 skill，不在主流程中重写子 skill 的细节逻辑。

重要约束：Stage 2 不为三类数据源拆分三套 skill。`simulator`、`existing_dataset`、`real_data` 必须在同一套 Phase 1-6 skill 内并行处理，每个 phase 读入同一个 `DATA_SOURCE_MAPPING.md`，内部按 `source_type` 分支工作，最后合并成统一产物。

## 中文优先原则

- 任务说明、决策依据、报告正文必须以中文为主。
- 英文只作为辅助，用于保留命令名、文件名、字段名、source type、API 名称和必要术语。
- 若中文说明和英文术语冲突，以中文任务目标和 Stage 1 数据源映射为准。

## 三类数据源总契约

Stage 2 必须读取 `~/bench_workspace/workspace{i}/stage1/DATA_SOURCE_MAPPING.md`。该文件来自 Stage 1 Phase 4，是本阶段的权威路由表。若缺失，立即停止并要求先完成 Stage 1 Phase 4。

三类数据源的处理方式不同，但执行入口相同：

| source_type | 中文名称 | Stage 2 处理目标 | 禁止行为 |
|-------------|----------|------------------|----------|
| `simulator` | 仿真器数据 | 通过程序/API 生成图像、多模态观测和完整真值 GT；记录环境、脚本、对齐率和可复现配置 | 不得跳过 GT 对齐质检 |
| `existing_dataset` | 已有数据集 | 接入已有图片、QA 对、caption、label、metadata；做 schema 映射、抽样、去重和标注一致性检查 | 不得假装生成仿真器级真值 |
| `real_data` | 真实数据 | 登记真实图片或不完整记录；做文件完整性、图像质量、metadata 抽取和 annotation gap 清单 | 不得把推断结果当作真值 |

所有 Stage 2 产物必须保留这些字段：`source_type`、`source_name`、`source_path`、`capability_dimension`、`gt_availability`、`annotation_status`、`sample_id`。

推荐状态值：

- `gt_availability`: `full_gt`、`partial_gt`、`provided_annotation`、`missing_or_derived`、`not_observable`
- `annotation_status`: `complete`、`provided`、`derived`、`needs_annotation`、`needs_human_review`

## 流程

```text
Stage 1 artifacts
-> /benchmark-sim-capability-survey
-> /benchmark-collection-guidance
-> /benchmark-template-refinement
-> /benchmark-collect-codegen
-> /benchmark-batch-collect
-> /benchmark-unit-test-stage2
```

说明：第一个子 skill 名称保留为 `benchmark-sim-capability-survey`，但在本版本中它承担“数据源能力与资产盘点”的职责：仿真器盘点 GT API，已有数据集盘点字段与标注，真实数据盘点资产与缺口。

## 同一套 Skill 的并行处理方式

每个 Phase 都必须执行以下模式：

1. 读取 `DATA_SOURCE_MAPPING.md` 中全部 source 条目。
2. 按 `source_type` 分成三组：`simulator`、`existing_dataset`、`real_data`。
3. 在同一个 skill 内并行或等价并行地处理三组数据；如果执行环境不支持真实并行，也必须在同一轮 phase 内完成三组处理，不得拆成独立阶段。
4. 输出一个统一报告，同时保留三类数据各自的小节和 manifest。
5. 下游 phase 只读取统一产物，不直接依赖某一类数据的私有产物。

统一产物包括：

- Phase 1: `SOURCE_CAPABILITY_SURVEY.md`
- Phase 1 兼容产物: `SIM_CAPABILITY_SURVEY.md`
- Phase 2: `COLLECTION_GUIDANCE_PLAN.md`
- Phase 3: `TEMPLATE_REFINEMENT_REPORT.md` + `templates/*.yaml`
- Phase 4: `DATA_SCHEMA.md` + 三类脚本目录 + `logs/`
- Phase 5: `DATA_QUALITY_REPORT.md` + `collected_data/{source_type}/{source_name}/`
- Phase 6: `STAGE2_UNIT_TEST_REPORT.md`

## Stage 2 目录契约（必须与产物树一致）

Stage 2 的目录结构必须采用下列形态；未选中的数据源类型可以只保留对应脚本目录的 `README.md` 占位，但已选中的 source 必须有完整子目录。

```text
stage2/
  collect_scripts/
    simulator/{source_name}/collect.py
    simulator/{source_name}/README.md
  ingest_scripts/
    existing_dataset/{source_name}/ingest.py
    existing_dataset/{source_name}/field_mapping.yaml
    existing_dataset/{source_name}/README.md
  register_scripts/
    README.md
    real_data/{source_name}/register.py        # 仅当存在 real_data source 时必需
  collected_data/
    simulator/{source_name}/images/{scene_or_town}/{shard_or_run}/...
    simulator/{source_name}/manifest.jsonl
    simulator/{source_name}/skipped_towns.json # 若存在 town/scene 跳过情况
    existing_dataset/{source_name}/images/...
    existing_dataset/{source_name}/manifest.jsonl
    existing_dataset/{source_name}/ingest_errors.jsonl
    existing_dataset/{source_name}/question_type_histogram.json # 若有 QA/question_type 字段
    real_data/{source_name}/manifest.jsonl     # 仅当存在 real_data source 时必需
  logs/
    {source_or_service}.log
  templates/
    {source_type}_{source_name}_EVAL_TEMPLATE.yaml
  unit_tests/
    test_stage2_contract.py
    results.json
  SOURCE_CAPABILITY_SURVEY.md
  SIM_CAPABILITY_SURVEY.md
  COLLECTION_GUIDANCE_PLAN.md
  TEMPLATE_REFINEMENT_REPORT.md
  DATA_SCHEMA.md
  DATA_QUALITY_REPORT.md
  STAGE2_SUMMARY.md
  STAGE2_UNIT_TEST_REPORT.md
```

示例对齐：若 Stage 1 选中 `simulator=CARLA`、`simulator=PGIBench`、`existing_dataset=ERQA`，则 Stage 2 至少应出现 `collect_scripts/simulator/CARLA/`、`collect_scripts/simulator/PGIBench/`、`collected_data/simulator/CARLA/`、`collected_data/simulator/PGIBench/`、`ingest_scripts/existing_dataset/ERQA/`、`collected_data/existing_dataset/ERQA/`、`templates/simulator_CARLA_EVAL_TEMPLATE.yaml`、`templates/simulator_PGIBench_EVAL_TEMPLATE.yaml`、`templates/existing_dataset_ERQA_EVAL_TEMPLATE.yaml`。

## Phase 0：读取上下文

必须检查：

- `~/bench_workspace/workspace{i}/stage1/CAPABILITY_SCOPE.md`
- `~/bench_workspace/workspace{i}/stage1/DATA_SOURCE_MAPPING.md`
- `~/bench_workspace/workspace{i}/stage1/EVALSET_PROTOTYPE.md`
- `~/bench_workspace/workspace{i}/stage1/BENCHMARK_DRAFT.md`
- `~/bench_workspace/workspace{i}/stage1/EXECUTION_PLAN.md`

可选检查：

- `~/benchclaw/simulator_cards/`、`~/benchclaw/simulators/`
- `~/benchclaw/dataset_cards/`、`~/benchclaw/datasets/`
- `~/benchclaw/realdata_cards/`、`~/benchclaw/realdatas/`
- workspace 内已有的 `datasets/`、`realdatas/`、`templates/`

## Phase 1：数据源能力与资产盘点

调用：

```text
/benchmark-sim-capability-survey "$ARGUMENTS"
```

输出：`~/bench_workspace/workspace{i}/stage2/SOURCE_CAPABILITY_SURVEY.md`

兼容输出：若下游旧流程仍读取 `SIM_CAPABILITY_SURVEY.md`，应同时写出一个摘要版或软链接说明，内容只覆盖 `source_type=simulator` 的部分。

## Phase 2：收集与接入指导方案

调用：

```text
/benchmark-collection-guidance "$ARGUMENTS"
```

输出：`~/bench_workspace/workspace{i}/stage2/COLLECTION_GUIDANCE_PLAN.md`

该计划必须按三类 source_type 分段描述：仿真器采集、已有数据集接入、真实数据登记。

## Phase 3：模板与 schema 修整

调用：

```text
/benchmark-template-refinement "$ARGUMENTS"
```

输出：

- `~/bench_workspace/workspace{i}/stage2/TEMPLATE_REFINEMENT_REPORT.md`
- `~/bench_workspace/workspace{i}/stage2/templates/{source_type}_{source_name}_EVAL_TEMPLATE.yaml`

## Phase 4：采集/接入代码生成

调用：

```text
/benchmark-collect-codegen "$ARGUMENTS"
```

输出：

- `~/bench_workspace/workspace{i}/stage2/collect_scripts/`
- `~/bench_workspace/workspace{i}/stage2/ingest_scripts/`
- `~/bench_workspace/workspace{i}/stage2/register_scripts/`
- `~/bench_workspace/workspace{i}/stage2/logs/`
- `~/bench_workspace/workspace{i}/stage2/DATA_SCHEMA.md`

## Phase 5：批量采集、接入与质检

调用：

```text
/benchmark-batch-collect "$ARGUMENTS"
```

输出：

- `~/bench_workspace/workspace{i}/stage2/collected_data/simulator/{source_name}/`
- `~/bench_workspace/workspace{i}/stage2/collected_data/existing_dataset/{source_name}/`
- `~/bench_workspace/workspace{i}/stage2/collected_data/real_data/{source_name}/`
- `~/bench_workspace/workspace{i}/stage2/DATA_QUALITY_REPORT.md`

其中已选中的 source 必须生成 `manifest.jsonl`；已有数据集 source 还应生成 `ingest_errors.jsonl`，若存在 QA 或 question type 字段，还应生成 `question_type_histogram.json`。仿真器 source 若按 town/scene 批量采集，应将图片放在 `images/{scene_or_town}/{shard_or_run}/` 下，并记录跳过项，例如 `skipped_towns.json`。

## Phase 6：Stage 2 单元测试

调用：

```text
/benchmark-unit-test-stage2 "$STAGE2_DIR"
```

输出：

- `~/bench_workspace/workspace{i}/stage2/unit_tests/test_stage2_contract.py`
- `~/bench_workspace/workspace{i}/stage2/unit_tests/results.json`
- `~/bench_workspace/workspace{i}/stage2/STAGE2_UNIT_TEST_REPORT.md`

## 最终总结

写入：`~/bench_workspace/workspace{i}/stage2/STAGE2_SUMMARY.md`

必须包含：

- 三类数据源的数量、名称和路径
- 每个能力维度对应的数据来源
- 每类数据的样本规模和质量状态
- GT / annotation 缺口
- 是否允许进入 Stage 3

## 关键规则

- 不得为三类数据源拆出三套独立 skill；必须使用同一套 Stage 2 skill 并行处理。
- 不得只按仿真器路径处理全部数据。
- 不得为已有数据集或真实数据伪造 `full_gt`。
- 不得覆盖 Stage 1 文件。
- 不得执行 Stage 3 的 Data-Juicer 清洗。
- 所有路径、manifest、报告必须可追溯到 `DATA_SOURCE_MAPPING.md` 的 source 条目。
