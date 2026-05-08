---
name: benchmark-evalset-generate
description: "Atomic module: stage4 Phase 1 评测集合成模块。只负责构建任务专属模板库、制定合成规则、批量合成评测集并定义评测集 schema，不负责指标体系设计、指标代码实现或联调验证。Use when user says '合成评测集generate evalset'生成评测数据'"
argument-hint: [stage3-dir]
allowed-tools: Bash(*), Read, Write, Edit, Grep, Glob
metadata:
  openclaw:
    emoji: ""
    requires:
      bins: [python3]
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

# Benchmark Evalset Generation

Execute evalset synthesis for: **$ARGUMENTS**

This skill is an **atomic single-responsibility skill**.
It must **only** do the work scoped to this module.

---

## Critical Hotfix: Question Grounding And Visual-Dependence Gate

This module owns eval-question quality. A generated sample is invalid if the
answer can be inferred from the instruction text, file name, metadata, template
wording, answer options, or common language/world priors without inspecting the
required observation payload.

For any image/video/spatial benchmark sample, enforce:

- The question must require the provided image, video frame, depth/segmentation,
  trajectory, map, or other declared observation artifact.
- The instruction must not contain the answer, near-answer synonyms, object
  counts, direction labels, scene labels, floor-plan IDs, coordinates, or source
  metadata that make the answer derivable without the observation.
- Multiple-choice distractors must be plausible under the same task type and
  must not reveal the answer through length, grammar, order, naming convention,
  or one option being uniquely specific.
- GT must be derived from observation-linked annotation fields, not from template
  constants or textual metadata alone.
- If a task intentionally measures text-only reasoning, mark it explicitly as
  `modality_requirement: text_only_allowed`; otherwise default to
  `visual_or_observation_required`.

Every template YAML must include a `quality_constraints` block:

```yaml
quality_constraints:
  modality_requirement: visual_or_observation_required | multimodal_required | text_only_allowed
  required_observation_fields: [image_path]
  answer_not_in_instruction: true
  answer_not_in_metadata: true
  requires_observation_to_answer: true
  distractor_policy: plausible_same_type
  leakage_checks:
    - no_gt_string_in_instruction
    - no_answer_in_filename_or_path
    - no_metadata_only_solution
    - no_option_pattern_giveaway
```

Every generated sample `metadata.json` or manifest entry must record:

- `grounding_check.requires_observation_to_answer`
- `grounding_check.required_observation_files`
- `grounding_check.gt_source_fields`
- `grounding_check.instruction_leakage_status`
- `grounding_check.metadata_leakage_status`
- `grounding_check.text_only_baseline_expected`
- `grounding_check.verdict` = `PASS | FAIL | NEEDS_REVIEW`

Synthesis must run a deterministic text-only baseline check: hide all
observation files and judge whether the answer is still recoverable from
instruction + options + public metadata. If the expected text-only baseline
accuracy is above chance or any exact GT token appears in visible text, mark the
sample `FAIL` and exclude it from `EVALSET_DATASET/`, or keep it only in a
quarantine directory with an explicit waiver. Do not silently include it.

---

## Purpose

- 本模块负责以 Stage 1 评测集原型和 Stage 2 修整后模板为起点，构建任务专属模板库、制定可复现的合成规则、批量合成评测集并定义评测集 schema- 本模块维护从 `EVALSET_PROTOTYPE.md` ->`TEMPLATE_REFINEMENT_REPORT.md` ->本模块产出的模板变更追溯链- 本模块位Stage 4 第一环节，直接产物是 `EVALSET_TEMPLATE_LIBRARY/`、`EVALSET_SYNTHESIS_RULES.md`、`EVALSET_DATASET/`、`EVALSET_SCHEMA.md`- 本模块不负责指标体系设计、指标代码实现或联调验证
---

## Inputs

- `$ARGUMENTS`：合成的补充要求（如采样比例偏好、难度分布偏好）- 必需输入->  - `~/bench_workspace/workspace{i}/stage1/EVALSET_PROTOTYPE.md` ->评测集模板草稿与指标设计草稿（追溯起点）
  - `~/bench_workspace/workspace{i}/stage1/CAPABILITY_SCOPE.md` ->能力维度列表及操作性定义  - `~/bench_workspace/workspace{i}/stage1/BENCHMARK_DRAFT.md` ->任务目标、能力边界、场景覆盖约->  - `~/bench_workspace/workspace{i}/stage2/templates/{sim_name}_EVAL_TEMPLATE.yaml` ->修整后的仿真器评测模板  - `~/bench_workspace/workspace{i}/stage3/final/CLEANED_DATA_SCHEMA.md` ->数据存储结构、GT/annotation 标注格式
  - `~/bench_workspace/workspace{i}/stage3/final/STAGE4_INPUT_MANIFEST.jsonl` ->Stage 4 权威样本索引
  - `~/bench_workspace/workspace{i}/stage3/final/cleaned_data/` ->Stage 3 合并后的可用数据
- 可选输入：
  - `~/bench_workspace/workspace{i}/stage2/TEMPLATE_REFINEMENT_REPORT.md` ->模板修整变更记录（用于追溯链->  - `~/bench_workspace/workspace{i}/stage3/CLEANING_QUALITY_REPORT.md` ->数据质量状况与已知缺陷（用于质量过滤- **若任一必需输入缺失，应立即停止并报告缺失文件，提示用户先完成对stage*

---

## Procedure

1. **读取上游产出**->   - ->`EVALSET_PROTOTYPE.md` 提取任务原型结构（指令模板、输入输出规格、难度分级草稿）
   - ->`CAPABILITY_SCOPE.md` 提取能力维度列表
   - ->`BENCHMARK_DRAFT.md` 提取场景覆盖约束与数据构造方法   - ->`templates/*.yaml` 提取各数据源的最终模板字段   - ->`final/CLEANED_DATA_SCHEMA.md` 提取 GT/annotation 标注格式与目录结构   - ->`final/STAGE4_INPUT_MANIFEST.jsonl` 扫描实际可用数据规模、source_type/source_name 分布和 stage4_ready_status
2. **构建任务专属模板库（子步1.1*->   - ->`EVALSET_PROTOTYPE.md` 的任务原型为起点，结合仿真器模板，为每个能力维度 × 仿真器组合生成最终评测任务模板   - 每个模板定义：任务指令格式、输入字段列表（从采集数据取哪些字段）、期望输出格式、GT 参考答案来源字段   - 记录模板`EVALSET_PROTOTYPE.md` ->`TEMPLATE_REFINEMENT_REPORT.md` ->本模板的变更链，写入 `TEMPLATE_LINEAGE.md`
   - 输出`EVALSET_TEMPLATE_LIBRARY/`

3. **制定合成规则（子步骤 1.2*->   - 定义采样策略：全部vs 按条件筛vs 分层抽样
   - 定义难度分级规则：基于场景复杂度（物体数量、遮挡率、光照条件等->   - 定义跨仿真器平衡策略：各仿真器样本量与维度覆盖比->   - 定义质量过滤规则：排除异常帧、低质量 GT、重复场景（参`DATA_QUALITY_REPORT.md`->   - 定义去重规则
   - 确保可复现性：固定随机种子、排序规则等
   - 输出`EVALSET_SYNTHESIS_RULES.md`

4. **批量合成评测集（子步1.3*->   - 按合成规则遍历 `final/STAGE4_INPUT_MANIFEST.jsonl` 和 `final/cleaned_data/`，逐样本生成评测数据   - 每个样本包含：输入数据（给被评测系统的信息）、GT/annotation 参考信息（用于评分或标记 NEEDS_REVIEW）、元数据（source_type、source_name、场景/样本 ID、能力维度标签、难度等级）
   - 按统一 schema 组织存储
   - 生成 `manifest.json`（全量样本索引）`statistics.json`（统计摘要）
   - 输出`EVALSET_DATASET/`

5. **定义评测集schema（子步骤 1.4*->   - 将评测集的目录结构、文件格式、字段定义、元数据规范写入文档
   - 定义下游契约（Downstream Contract）：指标算法期望的输入格式与schema 的对齐说->   - 输出`EVALSET_SCHEMA.md`

6. **校验**->   - 确认每个能力维度`EVALSET_DATASET/` 中都有样->   - 确认 `manifest.json` 中的样本数与实际文件数一->   - 确认目录结构`EVALSET_SCHEMA.md` 定义一->   - 确认 `TEMPLATE_LINEAGE.md` 追溯链完成
---

## Expected Outputs

- `~/bench_workspace/workspace{i}/stage4/EVALSET_TEMPLATE_LIBRARY/`
  ```
  EVALSET_TEMPLATE_LIBRARY/
  ├── {dimension_1}/
  ->  ├── {sim_a}_task_template.yaml
  ->  └── {sim_b}_task_template.yaml
  ├── {dimension_2}/
  ->  └── {sim_a}_task_template.yaml
  └── TEMPLATE_LINEAGE.md
  ```
- `~/bench_workspace/workspace{i}/stage4/EVALSET_SYNTHESIS_RULES.md`
- `~/bench_workspace/workspace{i}/stage4/EVALSET_DATASET/`
  ```
  EVALSET_DATASET/
  ├── {dimension_1}/
  ->  ├── sample_{id}/
  ->  ->  ├── input/
  ->  ->  ├── gt/
  ->  ->  └── metadata.json
  ->  └── ...
  ├── {dimension_2}/
  ->  └── ...
  ├── manifest.json
  └── statistics.json
  ```
- `~/bench_workspace/workspace{i}/stage4/EVALSET_SCHEMA.md`

---

## Completion Criteria

- [ ] Every task template includes `quality_constraints`.
- [ ] Every official sample includes `grounding_check` metadata with verdict `PASS`.
- [ ] No official sample is answerable from instruction/options/public metadata alone unless explicitly marked `text_only_allowed`.
- [ ] Image/video/spatial tasks include required observation files and cannot be solved without them.
- [ ] `EVALSET_SYNTHESIS_RULES.md` documents leakage, text-only baseline, and observation-dependence filters.

- [ ] `EVALSET_TEMPLATE_LIBRARY/` 存在且为每个能力维度至少包含一个任务模板YAML- [ ] `TEMPLATE_LINEAGE.md` 存在，记录了`EVALSET_PROTOTYPE.md` 到最终模板的完整变更链- [ ] `EVALSET_SYNTHESIS_RULES.md` 存在且包含采样策略、难度分级、平衡策略、过滤规则、去重规则和可复现性保证- [ ] `EVALSET_DATASET/` 存在且每个能力维度子目录下至少有 1 个样本- [ ] `manifest.json` 中的样本数与实际文件数一致- [ ] `statistics.json` 包含各维度样本数和难度分布统计- [ ] `EVALSET_SCHEMA.md` 存在且包Downstream Contract 章节- [ ] 若任一必需输入缺失，不得标记完成功
---

## Rules

- Do not generate benchmark questions that do not require the declared observation payload.
- Do not expose answer-bearing metadata, scene IDs, coordinates, labels, counts, directions, or GT strings in `instruction.txt`, options, visible metadata, file names, or paths.
- Do not keep failed grounding/leakage samples in the official evalset; quarantine or exclude them with an explicit reason in `EVALSET_SYNTHESIS_RULES.md`.

- 不设计或实现指标体系——那Phase 2 `benchmark-metric-establish` 的职责- 不执行联调验证——那Phase 3 `benchmark-validate-stage4` 的职责- 不擅自改写任Stage 1 ->Stage 2 产出文件- 合成规则必须保证可复现：给定相同采集数据 + 相同规则 = 相同评测集。不可依赖运行时随机数而不固定种子- 追溯链不可断——`TEMPLATE_LINEAGE.md` 必须存在，模板的每一步变更必须记录来源与理由- 不可在合成过程中静默丢弃样本——所有过滤和排除必须`EVALSET_SYNTHESIS_RULES.md` 中有对应规则- 出错时必须明确指出阻塞原因（如某维度`collected_data/` 中无可用数据、模板字段与实际数据不匹配）- 如果 Write 因文件过大失败，立即 fallback ->Bash 分块写入，不要询问用户许可选
---

## Downstream Handoff

- `benchmark-metric-establish` 读取 `~/bench_workspace/workspace{i}/stage4/EVALSET_SCHEMA.md` 的字段定义确定指标输入接口，读取 `~/bench_workspace/workspace{i}/stage4/EVALSET_DATASET/` 抽样验证指标实现- `benchmark-validate-stage4` 读取 `~/bench_workspace/workspace{i}/stage4/EVALSET_DATASET/` + `~/bench_workspace/workspace{i}/stage4/EVALSET_SCHEMA.md` 做契约验证与 dry-run- 本模块只写交接关系，不调度下游模块
