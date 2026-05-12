---
name: benchmark-collect-codegen
description: "Stage 2 Phase 4：采集、接入和登记脚本生成。根据 COLLECTION_GUIDANCE_PLAN.md 中对每个 source 的逐源指导，为 simulator、existing_dataset、real_data 生成对应代码；仿真器必须生成实际采集控制代码，已有数据集和真实数据可以生成读写、映射、登记代码。脚本只保存原始数据和问题标记，不执行清洗或过滤。"
argument-hint: [stage2-context]
allowed-tools: Bash(*), Read, Write, Edit, Grep, Glob
---

## `~/benchclaw` 只读约束

- **BENCHCLAW_READONLY = true**：`~/benchclaw/` 只能作为共享只读资源根。
- 严禁在 `~/benchclaw/` 下创建、编辑、覆盖、删除、移动、重命名、复制写入、初始化 git、提交、打 tag、写日志、写缓存或写临时文件。
- 所有派生产物、补丁、快照、报告、脚本、配置、日志和测试输出必须写入 active `WORKSPACE_ROOT`。
- 如必须修改 `~/benchclaw/` 中的资源，只能在 workspace 中生成 patch 或修改建议，等待用户在外部处理；当前 skill 不得直接应用。

# 采集脚本生成

面向：*$ARGUMENTS*

本 phase 生成 Stage 2 的可执行脚本和 `DATA_SCHEMA.md`。它必须严格承接 Phase 2 的 `COLLECTION_GUIDANCE_PLAN.md` 和 Phase 3 的模板，不得只生成空壳脚本。每一个被 Stage 1 选中的 source 都必须有对应的代码、配置和 README。

## 输入

必须读取：

- `stage2/COLLECTION_GUIDANCE_PLAN.md`
- `stage2/TEMPLATE_REFINEMENT_REPORT.md`
- `stage2/templates/*.yaml`
- `stage2/SOURCE_CAPABILITY_SURVEY.md`
- `stage1/DATA_SOURCE_MAPPING.md`
- `stage1/CAPABILITY_SCOPE.md`
- `stage1/BENCHMARK_DRAFT.md`
- `stage1/EVALSET_PROTOTYPE.md`
- `~/benchclaw/simulator_cards/`
- `~/benchclaw/dataset_cards/`
- `~/benchclaw/realdata_cards/`

`COLLECTION_GUIDANCE_PLAN.md` 是本 phase 的主约束。脚本生成必须逐项落实其中的：

- `Capability-To-Source Routing`
- `Per-Source Collection Guidance`
- `Existing Benchmark Dataset Guidance`
- `Simulator Guidance`
- `Real Data Guidance`
- `Coverage Gaps And Compensation`
- `Source Card Basis`

source card 是运行方式、访问路径、字段 schema 和授权/隐私信息的权威依据。如果 `COLLECTION_GUIDANCE_PLAN.md` 与对应 card 冲突，必须在 README 和配置中报告冲突，并优先使用 card 中的可执行信息，除非用户给出显式 override。

对 `simulator`，脚本生成的最高优先级是“启动仿真器并采集本轮新数据”。不得生成只读取旧图片、旧 JSON、缓存目录、其它 workspace 或历史 `collected_data/` 的采集脚本。

`~/benchclaw/` 是只读资源根。生成的脚本、配置和 README 可以读取并引用 `source_card_path`，但不得包含任何会在 `~/benchclaw/` 下创建、编辑、覆盖、删除、移动、重命名、写日志或写缓存的逻辑。所有输出路径必须指向当前 `WORKSPACE_ROOT/stage2/`。

## 输出目录

```text
stage2/
  collect_scripts/
    simulator/{source_name}/collect.py
    simulator/{source_name}/config.yaml
    simulator/{source_name}/README.md
  ingest_scripts/
    existing_dataset/{source_name}/ingest.py
    existing_dataset/{source_name}/field_mapping.yaml
    existing_dataset/{source_name}/README.md
  register_scripts/
    real_data/{source_name}/register.py
    real_data/{source_name}/register_config.yaml
    real_data/{source_name}/README.md
  logs/
  DATA_SCHEMA.md
```

如果某类 source 当前没有实例，保留对应脚本根目录的 `README.md`，说明本轮未启用该类型；不得伪造 source 目录。

## 逐源代码生成要求

必须按 `DATA_SOURCE_MAPPING.md` 和 `COLLECTION_GUIDANCE_PLAN.md` 中的 source 列表逐个生成代码。不得只生成一个通用脚本后要求人工改写；可以抽取公共 helper，但每个 source 必须有自己的入口脚本、配置和 README。

每个 source 的 README 必须写明：

- 对应的 `source_type` 和 `source_name`。
- 对应的 Stage 1 能力维度和 `source_role`。
- `source_card_path`、card 中使用过的关键字段和 card 缺失项。
- 运行命令。
- 输入路径或外部接口。
- 输出目录。
- 已知风险和 `raw_observation_flags` 记录规则。

## 仿真器代码生成：`simulator`

对每个 `source_type=simulator` 的 source，必须生成实际采集控制代码：

```text
collect_scripts/simulator/{source_name}/collect.py
collect_scripts/simulator/{source_name}/config.yaml
collect_scripts/simulator/{source_name}/README.md
```

`collect.py` 至少必须包含以下逻辑：

1. 读取 `config.yaml` 和 Stage2 raw schema。
2. 读取并校验 `source_card_path`，按 simulator card 执行 `startup_command` 或 card 指定的启动流程，启动仿真器 runtime；仅连接一个旧运行服务不能算完成，除非 card 明确说明该仿真器是托管服务，并且脚本创建了新的 `run_id/session_id`。
3. 执行 runtime health check，记录 `simulator_started_at`、`simulator_start_command`、进程 ID 或服务 session、endpoint、版本和健康检查结果。
4. 生成本轮唯一 `run_id/session_id`，并在采集前记录 `collected_data/simulator/{source_name}/` 中已有文件清单；已有文件不得计入本轮成功样本。
5. 根据 simulator card 和 `COLLECTION_GUIDANCE_PLAN.md` 中的场景、地图、任务、seed、传感器和能力维度配置循环采集。
6. 采集图片和必要模态，例如 RGB、depth、segmentation、pose、state、event log；如果某模态不可用，记录到 `raw_observation_flags`。
7. 保存每张主图到 `collected_data/simulator/{source_name}/images/{sample_id}.{ext}`。
8. 为每张主图保存 `records/{sample_id}.json`，记录当前 `run_id/session_id`、场景、地图、任务、seed、frame、timestamp、sensor config、GT 引用、能力维度和原始问题标记。
9. 写入 `manifest.jsonl`，每行同时指向唯一图片和唯一 JSON。
10. 支持失败恢复时，只允许跳过本轮 `run_id/session_id` 已确认写入的样本；不得把旧 run 或其它目录样本纳入当前 manifest。
11. 将启动失败、连接失败、场景失败、传感器失败、GT 缺失、GT 对齐异常、空帧、损坏帧写入日志和 JSON 字段，不得删除可访问样本。
12. 明确拒绝从 `workspace{j}`、`Downloads`、缓存目录、旧 `collected_data/` 或任意非当前 simulator runtime 输出目录复制/登记图片和 JSON。

`config.yaml` 至少包含：

```yaml
source_type: simulator
source_name:
source_card_path:
source_card_fields_used: []
capability_dimensions: []
source_role:
simulator:
  name:
  startup_command:
  startup_required: true
  sdk_or_api:
  endpoint:
  version:
  dependencies: []
  scenes: []
  maps: []
  tasks: []
  seeds: []
  sensors: []
collection:
  target_samples:
  image_ext: png
  output_root: collected_data/simulator/{source_name}
  current_run_only: true
  forbid_old_data_reuse: true
raw_record:
  preserve_accessible_samples: true
  no_filtering: true
```

如果仿真器需要特定 SDK，而当前环境无法验证 SDK，仍必须生成结构完整、接口清晰、可补齐 SDK 调用的脚本，并在 README 中标注需要安装的 SDK、启动方式和未验证项。该 source 在 Phase 5 未真实启动前只能判为 `NEEDS_RUNTIME` 或 `FAIL`，不得用旧数据补齐。

## 已有 benchmark 数据集代码生成：`existing_dataset`

对每个 `source_type=existing_dataset` 的 source，生成读写和字段映射代码即可：

```text
ingest_scripts/existing_dataset/{source_name}/ingest.py
ingest_scripts/existing_dataset/{source_name}/field_mapping.yaml
ingest_scripts/existing_dataset/{source_name}/README.md
```

`ingest.py` 至少必须包含以下逻辑：

1. 读取 `field_mapping.yaml`。
2. 读取并校验 `source_card_path`，按 dataset card 中的数据根目录、访问方式、split 和字段 schema 遍历已有 benchmark 数据集的原始样本。
3. 复制、硬链接或登记图片到 `collected_data/existing_dataset/{source_name}/images/{sample_id}.{ext}`；如果只能保存外部路径，必须在 JSON 和 manifest 中明确记录。
4. 将 QA、caption、label、metadata、原始样本 ID、标注来源、授权信息写入 `records/{sample_id}.json`。
5. 将 `capability_dimension`、`source_role`、`stage1_requirement_ref` 写入 JSON 和 manifest。
6. 对缺字段、路径不存在、格式异常、授权不明、标注缺口只做记录，不做过滤删除。

`field_mapping.yaml` 至少包含：

```yaml
source_type: existing_dataset
source_name:
source_card_path:
source_card_fields_used: []
dataset_root:
access_method:
splits: []
capability_dimensions: []
source_role:
fields:
  image:
  question:
  answer:
  caption:
  label:
  metadata:
  original_sample_id:
  annotation_source:
license:
output:
  output_root: collected_data/existing_dataset/{source_name}
  image_ext_policy: preserve
raw_record:
  preserve_accessible_samples: true
  no_filtering: true
```

## 真实数据代码生成：`real_data`

对每个 `source_type=real_data` 的 source，生成登记和读写代码即可：

```text
register_scripts/real_data/{source_name}/register.py
register_scripts/real_data/{source_name}/register_config.yaml
register_scripts/real_data/{source_name}/README.md
```

`register.py` 至少必须包含以下逻辑：

1. 读取 `register_config.yaml`。
2. 读取并校验 `source_card_path`，按 realdata card 中的图片目录、清单文件、登记表和 metadata 字段遍历真实数据。
3. 复制、硬链接或登记图片到 `collected_data/real_data/{source_name}/images/{sample_id}.{ext}`；如果不能复制，必须保存可追溯原始路径。
4. 为每张图片写入 `records/{sample_id}.json`，包含采集批次、设备、时间、地点或可公开 metadata、授权/隐私状态、annotation gap、review priority。
5. 将 `capability_dimension`、`source_role`、`stage1_requirement_ref` 写入 JSON 和 manifest。
6. 对模糊、重复、缺少 GT、缺少标注、隐私待复核等问题只做标记，不做过滤删除。

`register_config.yaml` 至少包含：

```yaml
source_type: real_data
source_name:
source_card_path:
source_card_fields_used: []
input:
  image_root:
  manifest_or_sheet:
  registration_sheet:
capability_dimensions: []
source_role:
metadata_fields: []
license_and_privacy:
  license:
  consent_status:
  privacy_review_required:
output:
  output_root: collected_data/real_data/{source_name}
  image_ext_policy: preserve
raw_record:
  preserve_accessible_samples: true
  no_filtering: true
```

## 通用脚本行为契约

所有脚本必须：

- 只采集、接入或登记原始数据。
- 保存每张图片到 `collected_data/{source_type}/{source_name}/images/{sample_id}.{ext}`。
- 为每张图片保存一个 JSON 到 `collected_data/{source_type}/{source_name}/records/{sample_id}.json`。
- 写入 `manifest.jsonl`，每行同时指向唯一图片和唯一 JSON。
- 写入 `capability_dimension`、`source_role`、`stage1_requirement_ref`，确保样本能追溯回 Stage 1。
- 写入 `source_card_path`、`source_card_fields_used`，确保样本能追溯到实际数据源说明。
- 把问题写入 `raw_observation_flags`、`integrity_notes`、`annotation_gap`、`access_error`、`needs_human_review`。
- 记录失败、不可访问和跳过原因到 `logs/`。
- 对 simulator，记录本轮 runtime 启动证据和 `run_id/session_id`，并拒绝把旧 run、其它 workspace 或其它文件夹的样本写入当前 manifest。

所有脚本禁止：

- 对 `~/benchclaw/` 下任何文件或目录执行写入、覆盖、删除、移动、重命名、复制写入、缓存或日志输出。
- 调用清洗框架。
- 生成清洗阶段配置。
- 清洗、过滤、删除、质量拒收样本。
- 因缺少 GT、重复、模糊、低置信度或标注缺口而不保存可访问样本。
- 对 simulator，从旧文件夹、其它 workspace、历史 `collected_data/` 或缓存目录读取图片/JSON 来冒充本轮采集。

## DATA_SCHEMA.md 必须包含

```markdown
# Stage 2 Raw Data Schema

## Directory Contract
collected_data/{source_type}/{source_name}/images/{sample_id}.{ext}
collected_data/{source_type}/{source_name}/records/{sample_id}.json
collected_data/{source_type}/{source_name}/manifest.jsonl

## sample_id Rule
{source_type}_{source_name}_{000001}

## Required Record Fields
| Field | Required | Meaning |
|-------|----------|---------|
| sample_id | yes | 全局样本编号 |
| source_type | yes | simulator / existing_dataset / real_data |
| source_name | yes | 稳定 source 目录名 |
| capability_dimension | yes | Stage 1 能力维度 |
| source_role | yes | primary / supplemental / gt_provider / negative_or_control / needs_stage3_annotation |
| stage1_requirement_ref | yes | 对应 Stage 1 需求、能力维度或评测原型引用 |
| source_card_path | yes | 对应 simulator/dataset/realdata card 路径 |
| source_card_fields_used | yes | 生成和采集时使用过的 card 字段 |
| current_run_only | yes for simulator | simulator 样本是否来自本轮启动/session |
| simulator_start_evidence | yes for simulator | 启动命令、启动时间、进程/session 和 health check |
| image_path | yes | 主图路径 |
| record_json_path | yes | JSON 记录路径 |
| raw_observation_flags | yes | 原始问题标记 |
| provenance | yes | 采集、接入或登记来源 |

## Source-Specific Fields
| Source Type | Field | Meaning |
|-------------|-------|---------|

## Manifest Fields
| Field | Required | Meaning |
|-------|----------|---------|

## Raw-Only Guarantee
Stage 2 scripts preserve raw accessible samples and issue flags only. Filtering, cleaning, rejection and confidence improvement belong to Stage 3.
```

## source_name 注释

`source_name` 可以是一次处理的数据、仿真器的一个场景/地图/任务配置、已有数据集的一个切片或真实数据的一个采集批次。脚本必须把它作为稳定目录名写入所有记录。
