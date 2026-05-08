---
name: benchmark-unit-test-stage2
description: "Stage 2 Phase 6：Stage 2 契约单元测试。验证三类数据源的盘点、方案、模板、脚本、数据目录和质量报告是否完整且可追溯。Use when user says 'stage2 单元测试', 'unit test stage2', '检查 Stage 2 产物'."
argument-hint: [stage2-dir]
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

# Stage 2 契约单元测试（三类数据同一 Skill 并行）

面向：**$ARGUMENTS**

本 skill 只生成并执行 Stage 2 产物契约测试，不修改数据、不重新采集。

重要约束：本 skill 是三类数据源共同使用的唯一 Phase 6 skill。不得拆成三套测试 skill；必须在同一份测试脚本和同一份测试报告中并行验证三类数据源契约。

## 输入

必需：

- `~/bench_workspace/workspace{i}/stage1/DATA_SOURCE_MAPPING.md`
- `~/bench_workspace/workspace{i}/stage2/SOURCE_CAPABILITY_SURVEY.md`
- `~/bench_workspace/workspace{i}/stage2/COLLECTION_GUIDANCE_PLAN.md`
- `~/bench_workspace/workspace{i}/stage2/TEMPLATE_REFINEMENT_REPORT.md`
- `~/bench_workspace/workspace{i}/stage2/DATA_SCHEMA.md`
- `~/bench_workspace/workspace{i}/stage2/DATA_QUALITY_REPORT.md`
- `~/bench_workspace/workspace{i}/stage2/collected_data/`
- `~/bench_workspace/workspace{i}/stage2/collect_scripts/`
- `~/bench_workspace/workspace{i}/stage2/ingest_scripts/`
- `~/bench_workspace/workspace{i}/stage2/register_scripts/`
- `~/bench_workspace/workspace{i}/stage2/logs/`
- `~/bench_workspace/workspace{i}/stage2/templates/`

## 测试重点

执行方式：测试脚本先读取 `DATA_SOURCE_MAPPING.md` 的全部 source，再按 `source_type` 并行构造测试用例。最终 verdict 必须覆盖三类数据源，并给出统一 Stage 2 verdict。

### 通用契约

- 每个 source 都有 `source_type`、`source_name`、`source_path`。
- 每个 source 都能回溯到 `DATA_SOURCE_MAPPING.md`。
- 每个样本都有 `sample_id`。
- `DATA_SCHEMA.md` 覆盖实际 manifest 字段。
- `DATA_QUALITY_REPORT.md` 覆盖所有 source。
- 目录结构必须与 Stage 2 产物树一致：根目录保留报告文件，脚本放在 `collect_scripts/`、`ingest_scripts/`、`register_scripts/`，数据放在 `collected_data/{source_type}/{source_name}/`，日志放在 `logs/`，模板放在 `templates/`。
- `SOURCE_CAPABILITY_SURVEY.md` 必须存在；若存在 simulator source，`SIM_CAPABILITY_SURVEY.md` 也必须存在或有兼容占位说明。

### 仿真器 `simulator`

- 存在 `collected_data/simulator/{source_name}/`。
- 存在 `collect_scripts/simulator/{source_name}/collect.py` 和 `README.md`。
- 存在 `collected_data/simulator/{source_name}/manifest.jsonl`。
- manifest 中有 `scene_id`、`frame_id`、GT 字段引用。
- 若存在 `images/`，图片应按 `images/{scene_or_town}/{shard_or_run}/...` 或等价层级组织；例如 CARLA 可出现 `images/Town10HD_Opt/0/`。
- 若存在跳过 town/scene，必须有 `skipped_towns.json` 或等价记录。
- `logs/` 中必须有该 source 的采集或服务日志，除非报告明确说明该仿真器无需后台服务。
- GT 对齐检查有结果。
- 若未达标，报告中标记 `FAIL` 或 `NEEDS_REVIEW`。

### 已有数据集 `existing_dataset`

- 存在 `collected_data/existing_dataset/{source_name}/`。
- 存在 `ingest_scripts/existing_dataset/{source_name}/ingest.py`、`field_mapping.yaml` 和 `README.md`。
- 存在 `collected_data/existing_dataset/{source_name}/images/`。
- 存在 `collected_data/existing_dataset/{source_name}/manifest.jsonl`。
- 存在 `collected_data/existing_dataset/{source_name}/ingest_errors.jsonl`，即使为空也算有效。
- 若 manifest 或 schema 含 QA/question type 字段，存在 `question_type_histogram.json`。
- manifest 中有 `original_sample_id`、字段映射和 annotation provenance。
- 缺失字段标记为 `missing_or_derived`。
- 不要求仿真器 GT 对齐率。

### 真实数据 `real_data`

- 若 `DATA_SOURCE_MAPPING.md` 选中 real_data source，存在 `register_scripts/real_data/{source_name}/register.py` 和 `collected_data/real_data/{source_name}/`。
- 若未选中 real_data source，不要求 `collected_data/real_data/{source_name}/`，但 `register_scripts/README.md` 必须说明本轮无真实数据登记。
- 对已选中的 real_data source，manifest 中有图片路径、metadata、quality flags。
- 对已选中的 real_data source，存在 annotation gap 记录。
- 对已选中的 real_data source，缺失 GT 标记为 `needs_annotation` 或 `not_observable`。

## 输出

- `~/bench_workspace/workspace{i}/stage2/unit_tests/test_stage2_contract.py`
- `~/bench_workspace/workspace{i}/stage2/unit_tests/results.json`
- `~/bench_workspace/workspace{i}/stage2/STAGE2_UNIT_TEST_REPORT.md`

## Verdict

- `PASS`：三类数据源契约均满足，可进入 Stage 3。
- `NEEDS_REVIEW`：真实数据标注缺口、已有数据集弱标注或仿真器局部缺口需要用户确认 waiver。
- `FAIL`：缺失关键文件、source 无法追溯、schema 不匹配或仿真器 GT 对齐严重失败。

## 规则

- 不修改原始数据。
- 不自动补采。
- 不用单一仿真器标准评判所有数据源。
- 报告必须中文优先，英文只用于字段名和 verdict。
- 三类数据源必须由同一个 `test_stage2_contract.py` 测试入口覆盖。
