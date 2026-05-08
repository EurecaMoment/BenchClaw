---
name: benchmark-collect-codegen
description: "Stage 2 Phase 4：采集/接入代码生成。按三类数据源分别生成 simulator 采集脚本、existing_dataset 接入脚本、real_data 登记脚本，并生成统一 DATA_SCHEMA.md。Use when user says '生成采集脚本', 'codegen collection scripts', '写采集代码'."
argument-hint: [stage2-context]
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

# 采集、接入与登记代码生成（三类数据同一 Skill 并行）

面向：**$ARGUMENTS**

本 skill 只生成代码、配置和 schema，不执行全量采集或质检。

重要约束：本 skill 是三类数据源共同使用的唯一 Phase 4 skill。不得拆出独立 codegen skill；必须在同一次执行中为 `simulator`、`existing_dataset`、`real_data` 并行生成对应脚本，并写入同一个 `DATA_SCHEMA.md`。

## 输入

必需：

- `~/bench_workspace/workspace{i}/stage2/COLLECTION_GUIDANCE_PLAN.md`
- `~/bench_workspace/workspace{i}/stage2/TEMPLATE_REFINEMENT_REPORT.md`
- `~/bench_workspace/workspace{i}/stage2/templates/*.yaml`
- `~/bench_workspace/workspace{i}/stage2/SOURCE_CAPABILITY_SURVEY.md`

## 三类代码生成策略

执行方式：读取全部模板和 `COLLECTION_GUIDANCE_PLAN.md`，按 source_type 分组并行生成脚本。脚本目录可以按类型分开，但 schema、命名规范、manifest 字段必须统一。

### 仿真器 `simulator`

生成：

- `collect_scripts/simulator/{source_name}/collect.py`
- `config.yaml`（若采集脚本需要独立配置）
- `README.md`
- `utils/`

脚本必须支持：

- 初始化仿真器环境
- 按配置遍历场景、轨迹、视角
- 逐帧采集 observation 和 GT
- 校验 frame-level GT 对齐
- 异常帧检测
- 日志记录
- `resume_state.json` 断点续采
- 将运行日志写入 `logs/{source_name_lower}_server.log` 或 `logs/{source_name_lower}_collect.log`
- 将采集输出约定为 `collected_data/simulator/{source_name}/images/{scene_or_town}/{shard_or_run}/...` 和 `collected_data/simulator/{source_name}/manifest.jsonl`
- 若按 town/scene 采集，脚本必须记录跳过项，例如 `collected_data/simulator/{source_name}/skipped_towns.json`

### 已有数据集 `existing_dataset`

生成：

- `ingest_scripts/existing_dataset/{source_name}/ingest.py`
- `field_mapping.yaml`
- `README.md`

脚本必须支持：

- 读取原始数据集目录或 manifest
- copy/link 图片和附属文件
- 生成 benchmark manifest
- 映射 QA、caption、label、metadata 字段
- 保留 original ID、split、annotation provenance
- 检查路径存在、字段缺失、重复样本和标注一致性
- 将接入输出约定为 `collected_data/existing_dataset/{source_name}/images/` 和 `collected_data/existing_dataset/{source_name}/manifest.jsonl`
- 生成 `collected_data/existing_dataset/{source_name}/ingest_errors.jsonl`，即使为空也保留文件，便于单元测试与审计
- 若数据集中存在 QA 或 question type 字段，生成 `question_type_histogram.json`

### 真实数据 `real_data`

生成：

- 若 `DATA_SOURCE_MAPPING.md` 没有选中真实数据源，仍需生成 `register_scripts/README.md`，说明本轮无 real_data source，不得强行创建伪真实数据目录。
- `register_scripts/real_data/{source_name}/register.py`
- `quality_config.yaml`
- `README.md`

脚本必须支持：

- 登记图片和已有 metadata
- 生成 manifest
- 检查文件损坏、重复、模糊、曝光、分辨率
- 抽取 EXIF/文件 metadata（若存在）
- 生成 `annotation_gap_manifest.jsonl`
- 标记 `needs_annotation`、`needs_human_review`、`not_observable`

## 统一 DATA_SCHEMA.md

必须定义：

- 通用字段：`source_type`、`source_name`、`sample_id`、`source_path`、`capability_dimension`
- 仿真器字段：`scene_id`、`frame_id`、`timestamp`、`gt.*`
- 已有数据集字段：`original_sample_id`、`original_split`、`qa`、`caption`、`label`、`annotation_provenance`
- 真实数据字段：`asset_id`、`metadata`、`quality_flags`、`annotation_gap`、`review_priority`

## 输出

- `~/bench_workspace/workspace{i}/stage2/collect_scripts/`
- `~/bench_workspace/workspace{i}/stage2/ingest_scripts/`
- `~/bench_workspace/workspace{i}/stage2/register_scripts/`
- `~/bench_workspace/workspace{i}/stage2/logs/`
- `~/bench_workspace/workspace{i}/stage2/DATA_SCHEMA.md`

## 完成标准

- 每个 source 都有对应脚本或明确的无需脚本说明。
- 脚本目录与图片示例一致：仿真器脚本在 `collect_scripts/simulator/{source_name}/`，已有数据集脚本在 `ingest_scripts/existing_dataset/{source_name}/`，真实数据登记脚本在 `register_scripts/real_data/{source_name}/`；无真实数据源时 `register_scripts/README.md` 可作为占位。
- 脚本类型与 `source_type` 匹配。
- `DATA_SCHEMA.md` 同时覆盖三类数据。
- 不对 existing_dataset / real_data 生成仿真器控制代码。
- 三类脚本由同一个 Phase 4 skill 生成，且共享同一份 `DATA_SCHEMA.md`。
