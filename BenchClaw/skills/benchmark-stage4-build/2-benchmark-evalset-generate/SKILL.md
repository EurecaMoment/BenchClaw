---
name: benchmark-evalset-generate
description: "Atomic module: stage4 Phase 2 评测集批量合成模块。只消费 benchmark-evalset-plan-route 产出的模板/指标/路由结果，制定合成规则、批量合成评测集并定义评测集 schema；不负责能力维度到模板/指标的前置路由，不实现指标代码。Use when user says '合成评测集generate evalset'生成评测数据'"
argument-hint: [stage3-dir]
allowed-tools: Bash(*), Read, Write, Edit, Grep, Glob
metadata:
  openclaw:
    emoji: ""
    requires:
      bins: [python3]
---

## `~/benchclaw` 只读约束

- **BENCHCLAW_READONLY = true**：`~/benchclaw/` 只能作为共享只读资源根。
- 严禁在 `~/benchclaw/` 下创建、编辑、覆盖、删除、移动、重命名、复制写入、初始化 git、提交、打 tag、写日志、写缓存或写临时文件。
- 所有派生产物、补丁、快照、报告、脚本、配置、日志和测试输出必须写入 active `WORKSPACE_ROOT`。
- 如必须修改 `~/benchclaw/` 中的资源，只能在 workspace 中生成 patch 或修改建议，等待用户在外部处理；当前 skill 不得直接应用。


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
It must **only** synthesize evalset samples from precomputed routing records.

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
template_review:
  user_intent_fit: PASS | FAIL | NEEDS_REVIEW
  discrimination_power: PASS | FAIL | NEEDS_REVIEW
  shortcut_resistance: PASS | FAIL | NEEDS_REVIEW
  capability_alignment: PASS | FAIL | NEEDS_REVIEW
  verdict: PASS | FAIL | NEEDS_REVIEW
  blocking_issues: []
```

`template_review.verdict` must be `PASS` before a template can be published to
`EVALSET_TEMPLATE_LIBRARY/` or used to synthesize official samples. A template
must fail or be quarantined when it does not match the user intent, lacks
discrimination power, can be solved through shortcuts such as omitting the
image/observation, or maps poorly to the claimed capability dimension.

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

- 本模块只负责基于 `/benchmark-evalset-plan-route` 已确认的 `EVALSET_BLUEPRINT.md`、`CAPABILITY_TEMPLATE_METRIC_MAP.json` 和 `STAGE3_TO_EVALSET_ROUTING.jsonl` 进行评测集批量合成。
- 本模块不得重新决定能力维度到模板/指标的映射，不得直接遍历全部 Stage3 manifest 生成样本。
- 本模块负责以 Stage 1 评测集原型和 Stage 2 修整后模板为起点，构建任务专属模板库、制定可复现的合成规则、批量合成评测集并定义评测集 schema- 本模块维护从 `EVALSET_PROTOTYPE.md` ->`TEMPLATE_REFINEMENT_REPORT.md` ->本模块产出的模板变更追溯链- 本模块位Stage 4 第一环节，直接产物是 `EVALSET_TEMPLATE_LIBRARY/`、`EVALSET_SYNTHESIS_RULES.md`、`EVALSET_DATASET/`、`EVALSET_SCHEMA.md`- 本模块不负责指标体系设计、指标代码实现或联调验证
---

## Inputs

- 必须先由 `/benchmark-evalset-plan-route` 生成：
  - `~/bench_workspace/workspace{i}/stage4/EVALSET_BLUEPRINT.md`
  - `~/bench_workspace/workspace{i}/stage4/CAPABILITY_TEMPLATE_METRIC_MAP.json`
  - `~/bench_workspace/workspace{i}/stage4/STAGE3_TO_EVALSET_ROUTING.jsonl`
- `$ARGUMENTS`：合成的补充要求（如采样比例偏好、难度分布偏好）- 必需输入->  - `~/bench_workspace/workspace{i}/stage1/EVALSET_PROTOTYPE.md` ->评测集模板草稿与指标设计草稿（追溯起点）
  - `~/bench_workspace/workspace{i}/stage1/CAPABILITY_SCOPE.md` ->能力维度列表及操作性定义  - `~/bench_workspace/workspace{i}/stage1/BENCHMARK_DRAFT.md` ->任务目标、能力边界、场景覆盖约->  - `~/bench_workspace/workspace{i}/stage2/templates/{sim_name}_EVAL_TEMPLATE.yaml` ->修整后的仿真器评测模板  - `~/bench_workspace/workspace{i}/stage3/final/CLEANED_DATA_SCHEMA.md` ->数据存储结构、GT/annotation 标注格式
  - `~/bench_workspace/workspace{i}/stage3/final/STAGE4_INPUT_MANIFEST.jsonl` ->Stage 4 权威样本索引
  - `~/bench_workspace/workspace{i}/stage3/final/cleaned_data/` ->Stage 3 合并后的可用数据
- 可选输入：
  - `~/bench_workspace/workspace{i}/stage2/TEMPLATE_REFINEMENT_REPORT.md` ->模板修整变更记录（用于追溯链->  - `~/bench_workspace/workspace{i}/stage3/CLEANING_QUALITY_REPORT.md` ->数据质量状况与已知缺陷（用于质量过滤- **若任一必需输入缺失，应立即停止并报告缺失文件，提示用户先完成对stage*

---

## Procedure

0. **检查前置路由产物（强制门禁）**
   - 必须先读取 `EVALSET_BLUEPRINT.md`、`CAPABILITY_TEMPLATE_METRIC_MAP.json` 和 `STAGE3_TO_EVALSET_ROUTING.jsonl`。
   - 若三者任一缺失、格式非法或没有 `routing_status=ready` 的记录，立即停止并要求先运行 `/benchmark-evalset-plan-route`。
   - 本 skill 不得在本地补做或重算路由。

1. **读取上游产出**->   - ->`EVALSET_PROTOTYPE.md` 提取任务原型结构（指令模板、输入输出规格、难度分级草稿）
   - ->`CAPABILITY_SCOPE.md` 提取能力维度列表
   - ->`BENCHMARK_DRAFT.md` 提取场景覆盖约束与数据构造方法   - ->`templates/*.yaml` 提取各数据源的最终模板字段   - ->`final/CLEANED_DATA_SCHEMA.md` 提取 GT/annotation 标注格式与目录结构   - ->`final/STAGE4_INPUT_MANIFEST.jsonl` 扫描实际可用数据规模、source_type/source_name 分布和 stage4_ready_status
2. **构建任务专属模板库（子步1.1*->   - ->`EVALSET_PROTOTYPE.md` 的任务原型为起点，结合仿真器模板，为每个能力维度 × 仿真器组合生成最终评测任务模板   - 每个模板定义：任务指令格式、输入字段列表（从采集数据取哪些字段）、期望输出格式、GT 参考答案来源字段   - 记录模板`EVALSET_PROTOTYPE.md` ->`TEMPLATE_REFINEMENT_REPORT.md` ->本模板的变更链，写入 `TEMPLATE_LINEAGE.md`
   - Before writing any template to `EVALSET_TEMPLATE_LIBRARY/`, verify its upstream `template_review.verdict=PASS` in `CAPABILITY_TEMPLATE_METRIC_MAP.json`.
   - Re-check and record `template_review` in the template YAML: user-intent fit, discrimination power, shortcut resistance, and capability alignment.
   - If the review is `FAIL` or `NEEDS_REVIEW`, do not publish the template and do not synthesize official samples from routes that reference it.
   - 输出`EVALSET_TEMPLATE_LIBRARY/`

3. **制定合成规则（子步骤 1.2*->   - 定义采样策略：全部vs 按条件筛vs 分层抽样
   - 定义难度分级规则：基于场景复杂度（物体数量、遮挡率、光照条件等->   - 定义跨仿真器平衡策略：各仿真器样本量与维度覆盖比->   - 定义质量过滤规则：排除异常帧、低质量 GT、重复场景（参`DATA_QUALITY_REPORT.md`->   - 定义去重规则
   - 确保可复现性：固定随机种子、排序规则等
   - 输出`EVALSET_SYNTHESIS_RULES.md`

4. **批量合成评测集（子步1.3*->   - 按合成规则遍历 `STAGE3_TO_EVALSET_ROUTING.jsonl` 中 `routing_status=ready` 的记录，不得直接遍历全部 `final/STAGE4_INPUT_MANIFEST.jsonl` 进行合成   - 每个样本包含：输入数据（给被评测系统的信息）、GT/annotation 参考信息（用于评分或标记 NEEDS_REVIEW）、元数据（source_type、source_name、场景/样本 ID、能力维度标签、难度等级、template_id、metric_id、routing_id）
   - 按 HuggingFace dataset 友好格式组织存储：`EVALSET_DATASET/` 是 Stage 4 最终总文件夹，也是可发布的数据集根目录。
   - 每道题必须是一个独立子文件夹，并保持 Stage 2/3 一致的数据来源层级：`EVALSET_DATASET/{source_type}/{source_name}/{capability_dimension}/{question_id}/`。
   - 每道题目录必须包含 `images/`、`question.json`、`question.md`、`answer.json`、`ground_truth.json`、`gt_code_ref.json`、`metadata.json`；多图题的所有答题图像必须放入 `images/` 并显式编号为 `image_0001.{ext}`、`image_0002.{ext}`。
   - GT 生成代码可以多题共用，统一放入 `EVALSET_DATASET/gt_generators/`；每道题的 `gt_code_ref.json` 必须指明该题的 GT 由哪个代码文件、函数、版本和输入字段生成。
   - 生成 HuggingFace 入口文件：`data.jsonl`（一题一行，包含相对路径字段）、`dataset_info.json`、`README.md`、`manifest.json`（全量题目索引）和 `statistics.json`（统计摘要）。
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
  ├── README.md
  ├── dataset_info.json
  ├── data.jsonl
  ├── manifest.json
  ├── statistics.json
  ├── gt_generators/
  │   ├── {gt_generator_id}.py
  │   └── MANIFEST.json
  ├── simulator/
  │   └── {source_name}/
  │       └── {capability_dimension}/
  │           └── {question_id}/
  │               ├── images/
  │               │   ├── image_0001.{ext}
  │               │   └── image_0002.{ext}
  │               ├── question.json
  │               ├── question.md
  │               ├── answer.json
  │               ├── ground_truth.json
  │               ├── gt_code_ref.json
  │               └── metadata.json
  ├── existing_dataset/
  │   └── {source_name}/{capability_dimension}/{question_id}/...
  └── real_data/
      └── {source_name}/{capability_dimension}/{question_id}/...
  ```
- `~/bench_workspace/workspace{i}/stage4/EVALSET_SCHEMA.md`

Each question folder is normative and must contain:

- `images/`: all images required to answer this single question; use explicit stable numbering `image_0001.{ext}`, `image_0002.{ext}`, etc.
- `question.json`: machine-readable prompt, options if any, modality requirements, referenced image paths, answer format, capability dimension, template_id, metric_ids.
- `question.md`: human-readable question text for inspection.
- `answer.json`: canonical answer object or expected answer format used by scoring.
- `ground_truth.json`: ground-truth values, provenance, confidence evidence, and source annotation fields.
- `gt_code_ref.json`: `{ "generator_file": "gt_generators/{gt_generator_id}.py", "function": "...", "version": "...", "input_fields": [...], "output_fields": [...] }`.
- `metadata.json`: routing_id, source_type, source_name, source sample ids, difficulty, template_review, grounding_check, lineage, and relative paths for all files in the question folder.

`data.jsonl` must be HuggingFace-loadable. Each row represents one question and must include at least:

- `question_id`
- `source_type`
- `source_name`
- `capability_dimension`
- `question_dir`
- `images`
- `question_path`
- `answer_path`
- `ground_truth_path`
- `gt_generator_file`
- `gt_generator_function`
- `metadata_path`
- `template_id`
- `metric_ids`
- `split`

---

---

## Fixed Artifact Format Contract

All artifacts produced by this skill have fixed file formats. The format block under `Expected Outputs`, `Output`, `Output Structure`, `Unified Output`, or the nearest equivalent output section is normative, not illustrative.

Mandatory rules:

- Produce every declared artifact at the exact declared path and with the exact declared extension. Do not rename, relocate, split, merge, or substitute artifacts unless this skill explicitly permits it.
- Markdown artifacts (`.md`) must keep the declared top-level title and section heading order exactly. Required tables must keep the declared column names and column order exactly. If a value is unknown, write `UNKNOWN`; if it is not applicable, write `N/A`; do not omit the row, section, or column.
- JSON artifacts (`.json`) must be valid UTF-8 JSON with a single top-level object unless this skill explicitly declares a top-level array. Required keys must always be present. Use `null`, `[]`, or `{}` for empty values instead of deleting keys.
- JSONL artifacts (`.jsonl`) must contain exactly one valid JSON object per non-empty line. Every line must share the same required key set declared by this skill or by the upstream schema.
- CSV/TSV artifacts must include a header row. Header names and order are fixed. Quote fields when needed and keep one logical record per row.
- YAML artifacts must be parseable YAML and must preserve the declared top-level keys. Generated config YAML must include enough comments or companion fields to trace each operator, field, or rule back to the source artifact named by this skill.
- Directory artifacts must contain the declared files plus a `MANIFEST.json` or `manifest.jsonl` when the skill declares one. The manifest must enumerate relative paths, artifact type, source_type/source_name when applicable, producer skill name, and creation timestamp.
- Validation or gate reports must include a fixed `verdict` value from `PASS`, `FAIL`, `WARNING`, `BLOCKED`, or `NEEDS_REVIEW`, plus `checked_artifacts`, `blocking_issues`, and `next_action` sections or keys.
- Handoff artifacts consumed by downstream skills must be backward-compatible: add optional fields only under an `extras` section/key, never by changing or deleting required fields.
- Before marking the skill complete, perform a format check against this contract and mention any deviation explicitly in the completion or gate report.

## Completion Criteria

- [ ] Precomputed `EVALSET_BLUEPRINT.md`, `CAPABILITY_TEMPLATE_METRIC_MAP.json`, and `STAGE3_TO_EVALSET_ROUTING.jsonl` exist and were read before synthesis.
- [ ] `EVALSET_DATASET/` was generated only from `routing_status=ready` records.
- [ ] `EVALSET_DATASET/` is the final Stage 4 dataset root and contains HuggingFace entry files `README.md`, `dataset_info.json`, and `data.jsonl`.
- [ ] Every question is stored in exactly one independent folder under `EVALSET_DATASET/{source_type}/{source_name}/{capability_dimension}/{question_id}/`.
- [ ] Every question folder contains `images/`, `question.json`, `question.md`, `answer.json`, `ground_truth.json`, `gt_code_ref.json`, and `metadata.json`.
- [ ] Every required image is copied or linked under the question folder's `images/` directory with stable `image_0001.{ext}` numbering.
- [ ] Every question's `gt_code_ref.json` points to the exact shared or per-question GT generator code file and function used to produce its `ground_truth.json`.
- [ ] Every task template includes `quality_constraints`.
- [ ] Every task template includes `template_review` and has `template_review.verdict=PASS`.
- [ ] No template is published before checking user-intent fit, discrimination power, shortcut resistance, and capability alignment.
- [ ] Every official sample includes `grounding_check` metadata with verdict `PASS`.
- [ ] No official sample is answerable from instruction/options/public metadata alone unless explicitly marked `text_only_allowed`.
- [ ] Image/video/spatial tasks include required observation files and cannot be solved without them.
- [ ] `EVALSET_SYNTHESIS_RULES.md` documents leakage, text-only baseline, and observation-dependence filters.

- [ ] `EVALSET_TEMPLATE_LIBRARY/` 存在且为每个能力维度至少包含一个任务模板YAML- [ ] `TEMPLATE_LINEAGE.md` 存在，记录了`EVALSET_PROTOTYPE.md` 到最终模板的完整变更链- [ ] `EVALSET_SYNTHESIS_RULES.md` 存在且包含采样策略、难度分级、平衡策略、过滤规则、去重规则和可复现性保证- [ ] `EVALSET_DATASET/` 存在且每个能力维度子目录下至少有 1 个样本- [ ] `manifest.json` 中的样本数与实际文件数一致- [ ] `statistics.json` 包含各维度样本数和难度分布统计- [ ] `EVALSET_SCHEMA.md` 存在且包Downstream Contract 章节- [ ] 若任一必需输入缺失，不得标记完成功
---

## Rules

- Do not synthesize evalset samples before reading `EVALSET_BLUEPRINT.md`, `CAPABILITY_TEMPLATE_METRIC_MAP.json`, and `STAGE3_TO_EVALSET_ROUTING.jsonl`.
- Do not create, modify, or infer routing records in this skill; rerun `/benchmark-evalset-plan-route` instead.
- Do not invent metric implementations here.
- Do not emit a flat evalset that lacks per-question folders or HuggingFace entry files.
- Do not place question images outside the question folder's `images/` directory.
- Do not include a question unless its `gt_code_ref.json` names the GT generator file and function used for that question.
- Do not publish or use templates whose `template_review.verdict` is not `PASS`.
- Do not generate benchmark questions that do not require the declared observation payload.
- Do not expose answer-bearing metadata, scene IDs, coordinates, labels, counts, directions, or GT strings in `instruction.txt`, options, visible metadata, file names, or paths.
- Do not keep failed grounding/leakage samples in the official evalset; quarantine or exclude them with an explicit reason in `EVALSET_SYNTHESIS_RULES.md`.

- 不设计或实现指标体系——那Phase 2 `benchmark-metric-establish` 的职责- 不执行联调验证——那Phase 3 `benchmark-validate-stage4` 的职责- 不擅自改写任Stage 1 ->Stage 2 产出文件- 合成规则必须保证可复现：给定相同采集数据 + 相同规则 = 相同评测集。不可依赖运行时随机数而不固定种子- 追溯链不可断——`TEMPLATE_LINEAGE.md` 必须存在，模板的每一步变更必须记录来源与理由- 不可在合成过程中静默丢弃样本——所有过滤和排除必须`EVALSET_SYNTHESIS_RULES.md` 中有对应规则- 出错时必须明确指出阻塞原因（如某维度`collected_data/` 中无可用数据、模板字段与实际数据不匹配）- 如果 Write 因文件过大失败，立即 fallback ->Bash 分块写入，不要询问用户许可选
---

## Downstream Handoff

- `benchmark-metric-establish` 必须优先读取 `~/bench_workspace/workspace{i}/stage4/CAPABILITY_TEMPLATE_METRIC_MAP.json` 确定每个能力维度需要实现或绑定的 metric interface，再读取 `~/bench_workspace/workspace{i}/stage4/EVALSET_SCHEMA.md` 的字段定义确定指标输入接口，读取 `~/bench_workspace/workspace{i}/stage4/EVALSET_DATASET/` 抽样验证指标实现- `benchmark-validate-stage4` 读取 `~/bench_workspace/workspace{i}/stage4/STAGE3_TO_EVALSET_ROUTING.jsonl` + `~/bench_workspace/workspace{i}/stage4/EVALSET_DATASET/` + `~/bench_workspace/workspace{i}/stage4/EVALSET_SCHEMA.md` 做契约验证与 dry-run- 本模块只写交接关系，不调度下游模块
