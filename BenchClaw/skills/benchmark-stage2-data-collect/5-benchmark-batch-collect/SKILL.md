---
name: benchmark-batch-collect
description: "Stage 2 Phase 5：批量采集、接入与登记。按 COLLECTION_GUIDANCE_PLAN.md 和 Phase 4 生成的逐源脚本，真实执行 simulator、existing_dataset、real_data 的数据采集/接入/登记，严格校验文件夹格式、图片与 JSON 一一对应、manifest 可追溯，并禁止用 placeholder、dummy、mock、空文件或伪造样本冒充真实数据。"
argument-hint: [stage2-context]
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

# 批量采集、接入与登记

面向：*$ARGUMENTS*

本 phase 是 Stage 2 的实际执行阶段。它必须运行 Phase 4 生成的逐源脚本，把真实可访问数据落到 `collected_data/`，并生成 `RAW_DATA_COLLECTION_REPORT.md`。不得只创建目录结构，不得生成 placeholder 数据，不得在明明有数据源可访问时用示例图片、空 JSON、mock 记录或 dummy manifest 糊弄完成。

## 输入

必须读取：

- `stage2/COLLECTION_GUIDANCE_PLAN.md`
- `stage2/DATA_SCHEMA.md`
- `stage2/collect_scripts/`
- `stage2/ingest_scripts/`
- `stage2/register_scripts/`
- `stage1/DATA_SOURCE_MAPPING.md`
- `stage1/CAPABILITY_SCOPE.md`
- `stage1/BENCHMARK_DRAFT.md`
- `stage1/EVALSET_PROTOTYPE.md`
- `~/benchclaw/simulator_cards/`
- `~/benchclaw/dataset_cards/`
- `~/benchclaw/realdata_cards/`

必须逐源读取 Phase 4 生成的配置：

- `collect_scripts/simulator/{source_name}/config.yaml`
- `ingest_scripts/existing_dataset/{source_name}/field_mapping.yaml`
- `register_scripts/real_data/{source_name}/register_config.yaml`

每个配置必须包含可读取的 `source_card_path`。执行前必须复核该路径属于对应 card 根目录，并检查配置中的运行命令、数据路径、字段 schema、登记表和授权/隐私字段是否来自 card 或显式用户 override。

`~/benchclaw/` 是只读资源根。执行脚本时只允许读取其中的 card、模板或工具说明；严禁在 `~/benchclaw/` 下创建、编辑、覆盖、删除、移动、重命名、复制写入、写日志或写缓存。若脚本计划写入 `~/benchclaw/`，必须中止该 source 并标为 `FAIL`。

## 最高优先级规则：真实执行，不准占位

本 phase 必须真实采集、接入或登记数据。以下行为一律禁止：

- 用 `placeholder`、`dummy`、`mock`、`sample`、`example`、`todo`、`fake`、`test image` 等占位文件冒充真实数据。
- 只生成目录、manifest 或 JSON，但没有真实图片或真实可追溯外部图片路径。
- 明明 `field_mapping.yaml`、`register_config.yaml` 或 simulator config 指向了可访问数据/接口，却不执行脚本。
- 对 simulator，不执行 card 中的 `startup_command` 或不创建新的仿真 `run_id/session_id`，却把旧图片、旧 JSON、缓存文件或其它目录文件计入成功。
- 从其它 `workspace{j}`、其它文件夹、历史 `stage2/collected_data/`、下载目录、缓存目录、示例目录复制/搬运/登记图片和 JSON 来冒充本轮采集。
- 对 `~/benchclaw/` 下任何内容做增删改，或把 `~/benchclaw/` 用作采集输出、日志、缓存、临时文件或中间 manifest 目录。
- 用同一张图片复制成多个 sample，除非原始数据源本身如此，且必须在 JSON 中记录 `duplicate_source_evidence`。
- 写入空 JSON、模板 JSON、未填字段 JSON 或只有 schema 没有样本内容的记录。
- 在采集失败时伪造成功数量。

如果 source 可访问但脚本失败，必须记录失败并将该 source 标为 `FAIL` 或 `NEEDS_RETRY`；不得用占位数据替代。

## 可访问样本必须保存

如果样本在法律和技术上可访问，就必须保存。以下情况不能作为 Stage 2 删除理由：

- 图片模糊、过曝、欠曝、分辨率低。
- 样本重复或疑似重复。
- GT 缺失、GT 不完整、标注缺失。
- QA、caption、label 或 metadata 不完整。
- 置信度低、需要人工复核、存在格式瑕疵。

这些问题必须写入 JSON 和报告字段，而不是导致样本被过滤。

## 执行前检查

在运行任何脚本前，必须逐个 source 做 preflight check，并把结果写入 `RAW_DATA_COLLECTION_REPORT.md`。

### 通用检查

- `source_type`、`source_name` 必须出现在 `DATA_SOURCE_MAPPING.md` 和 `COLLECTION_GUIDANCE_PLAN.md`。
- 对应脚本、配置和 README 必须存在。
- 配置、README 和脚本必须记录 `source_card_path`，且 card 文件可读取。
- 脚本、配置和运行命令不得把任何输出、日志、缓存、状态文件或临时文件写入 `~/benchclaw/`。
- 配置中的关键运行/访问/schema/授权字段必须能在 card 中找到，或在报告中标为用户 override。
- 配置中的输入路径、数据集根目录、真实数据目录、manifest/sheet 或 simulator endpoint 必须可解析。
- 输出目录不得预先含有旧的、无法追溯的样本；如存在旧样本，必须先记录 `pre_existing_files`，本轮统计必须排除这些文件，不能混入未说明的数据。

### simulator 检查

- simulator SDK、服务地址、场景/地图/任务配置、传感器配置、seed 或采样计划必须可读取。
- 启动命令、SDK/API、endpoint、scene/map/task、sensor 和 GT 字段必须与 simulator card 一致。
- 如果 simulator card 缺少运行方式或采集接口，记录 `NEEDS_CARD_DETAIL`，不得猜测启动命令。
- 必须执行 simulator card 中的启动命令或启动流程，并记录 `simulator_started_at`、`simulator_start_command`、process/session、endpoint、health check 和新 `run_id/session_id`。
- 如果 simulator 服务未启动、启动失败或 SDK 不可用，记录 `access_error`，不得生成伪造图片，不得复用旧数据。
- 如果只能生成脚本但无法启动真实仿真器或创建新 session，当前 source 必须标为 `NEEDS_RUNTIME`，不能标为成功采集。

### existing_dataset 检查

- `field_mapping.yaml` 中的 `dataset_root`、图像字段、原始样本 ID 字段必须存在或有明确外部路径策略。
- `dataset_root`、访问方式、split、字段 schema、license 必须与 dataset card 一致。
- 如果原始数据集可访问，必须运行 ingest；不得只写 manifest。
- 如果原始图像无法复制但允许外链登记，必须保存真实外部路径、文件大小、哈希或其它可追溯证据。

### real_data 检查

- `register_config.yaml` 中的 `image_root`、`manifest_or_sheet` 或登记清单必须存在。
- `image_root`、`manifest_or_sheet`、registration sheet、metadata 字段、授权/隐私字段必须与 realdata card 一致。
- 授权/隐私状态不完整时，样本仍可登记，但必须写入 `license_and_privacy` 和 `needs_human_review`。
- 如果真实数据目录为空，必须报告空目录，不能造样本。

## 执行顺序与并行要求

必须按照 `COLLECTION_GUIDANCE_PLAN.md` 中三类数据源的 source 列表执行：

```text
simulator -> collect_scripts/simulator/{source_name}/collect.py
existing_dataset -> ingest_scripts/existing_dataset/{source_name}/ingest.py
real_data -> register_scripts/real_data/{source_name}/register.py
```

如执行环境支持并行，可以并行运行不同 source；如不支持并行，也必须在同一 Phase 5 中逐个完成，不得拆成其它阶段。无论并行还是串行，报告必须保留每个 source 的独立执行日志、开始时间、结束时间、命令、退出码和产物计数。

对 simulator，执行顺序必须是：

```text
1. read simulator card
2. record pre_existing_files under collected_data/simulator/{source_name}/
3. run startup_command or card-defined launch procedure
4. perform runtime health check
5. create new run_id/session_id
6. run collect.py against that live runtime/session
7. count only samples with the current run_id/session_id
```

## 统一输出格式

每个实际启用的 source 必须输出：

```text
stage2/collected_data/{source_type}/{source_name}/
  images/{sample_id}.{ext}
  records/{sample_id}.json
  manifest.jsonl
```

图片必须显式编号并平铺在 `images/` 下。每张图片必须有一个同编号 JSON 记录。例如：

```text
images/simulator_CARLA_Town05_000001.png
records/simulator_CARLA_Town05_000001.json
```

不得使用以下结构替代固定格式：

```text
images/town05/frame001.png
images/scene_a/camera_front/image.png
records/all_records.json
metadata.csv
manifest_only_no_images.jsonl
```

如果需要记录 town、scene、camera、frame、shard、split 等信息，必须写入 JSON 字段和 manifest 字段，而不是打散固定目录结构。

## manifest.jsonl 必备字段

`manifest.jsonl` 每行必须至少包含：

```json
{
  "sample_id": "simulator_CARLA_Town05_000001",
  "source_type": "simulator",
  "source_name": "CARLA_Town05",
  "source_role": "primary",
  "stage1_requirement_ref": "CAPABILITY_SCOPE.md#...",
  "source_card_path": "~/benchclaw/simulator_cards/CARLA_Town05.md",
  "source_card_fields_used": ["startup_command", "scenes", "sensors", "gt_fields"],
  "capability_dimension": "...",
  "image_path": "collected_data/simulator/CARLA_Town05/images/simulator_CARLA_Town05_000001.png",
  "record_json_path": "collected_data/simulator/CARLA_Town05/records/simulator_CARLA_Town05_000001.json",
  "gt_availability": "full_gt",
  "annotation_status": "complete",
  "raw_observation_flags": [],
  "provenance": {
    "script": "collect_scripts/simulator/CARLA_Town05/collect.py",
    "config": "collect_scripts/simulator/CARLA_Town05/config.yaml",
    "simulator_start_command": "...",
    "simulator_started_at": "...",
    "simulator_health_check": "pass",
    "run_id": "...",
    "current_run_only": true,
    "old_data_reuse": false
  }
}
```

## records/{sample_id}.json 必备字段

每个 JSON 必须至少包含：

- `sample_id`
- `source_type`
- `source_name`
- `source_role`
- `stage1_requirement_ref`
- `source_card_path`
- `source_card_fields_used`
- `capability_dimension`
- `current_run_only`（simulator 必须为 `true`）
- `old_data_reuse`（simulator 必须为 `false`）
- `image_path`
- `record_json_path`
- `original_source_ref`
- `gt_availability`
- `annotation_status`
- `raw_observation_flags`
- `integrity_notes`
- `annotation_gap`
- `access_error`
- `needs_human_review`
- `provenance`
- `metadata`

`original_source_ref` 必须能证明样本来自真实源，例如 simulator run/frame、已有数据集 original_sample_id、真实数据原始路径或登记表行号。

## 反 placeholder 校验

每个 source 执行后必须做 anti-placeholder validation：

- 图片文件必须存在且大小大于 0。
- 图片扩展名必须与实际文件类型基本一致；能读取时应验证图片头或尺寸。
- JSON 不能只包含空字段、模板字段或 `TODO`。
- `sample_id`、`source_name`、`capability_dimension`、`image_path`、`record_json_path`、`original_source_ref` 必须非空。
- `source_card_path` 必须非空且指向对应 card 根目录下的真实文件。
- 文件名、路径、JSON 字段和 manifest 中不得出现占位词：`placeholder`、`dummy`、`mock`、`fake`、`todo`、`example_only`、`replace_me`。
- 对已有数据集和真实数据，必须有真实原始路径、原始 ID、文件哈希、文件大小或登记行号中的至少一种追溯证据。
- 对仿真器数据，必须有 `simulator_start_command`、`simulator_started_at`、health check、新 `run_id/session_id`、frame_id、scene/map/task、sensor config 或 seed 中的至少四类追溯证据，其中 `run_id/session_id` 和 frame_id 必须存在。
- 对仿真器数据，`image_path`、`record_json_path` 和 `original_source_ref` 不得指向其它 workspace、下载目录、缓存目录、历史 `collected_data/` 或 card 未声明的外部输出目录。
- 对仿真器数据，文件时间或脚本记录的采集时间必须晚于 `simulator_started_at`；无法读取文件时间时，必须用 runtime event log 或 frame timestamp 证明来自当前 session。

发现 placeholder 或不可追溯样本时，不得把它计入 `Collected Samples`。该 source 必须标为 `FAIL` 或 `NEEDS_REVIEW`，并在报告中列出问题路径。

## 三类执行细则

### simulator

执行：

```text
python collect_scripts/simulator/{source_name}/collect.py --config collect_scripts/simulator/{source_name}/config.yaml
```

必须保存：

- 本轮启动/本轮 session 中仿真器生成的真实图片或可验证传感器输出。
- 仿真器启动命令、启动时间、process/session、endpoint、health check、新 `run_id/session_id`。
- 场景、地图、任务、seed、run、frame、timestamp、sensor config。
- 原始 GT 引用或 GT 不可用原因。
- 采集命令、退出码、日志路径。

如果仿真器不可运行，必须报告 `NEEDS_RUNTIME` 或 `FAIL`，不能生成示例图片，不能复用旧图片或旧 JSON。

### existing_dataset

执行：

```text
python ingest_scripts/existing_dataset/{source_name}/ingest.py --mapping ingest_scripts/existing_dataset/{source_name}/field_mapping.yaml
```

必须保存：

- 已有 benchmark 数据集的真实图片或真实外部路径。
- `original_sample_id`、原始数据集路径、字段映射、QA/caption/label/metadata。
- 授权信息、缺失字段、接入错误。

如果原始数据集存在但部分样本损坏，损坏样本应记录到 `raw_observation_flags` 或 `access_error`，不得整体伪造成成功。

### real_data

执行：

```text
python register_scripts/real_data/{source_name}/register.py --config register_scripts/real_data/{source_name}/register_config.yaml
```

必须保存：

- 真实图片或真实外部登记路径。
- 采集批次、设备、时间、地点或可公开 metadata。
- 授权/隐私状态、标注缺口、人工复核需求。

如果真实数据源没有图片或登记清单为空，报告为空源，不得造样本。

## 产物一致性校验

每个 source 执行后必须检查：

- `images/` 数量等于 `records/` 数量。
- `manifest.jsonl` 行数等于图片数量。
- 每个 manifest 行都能定位到唯一图片和唯一 JSON。
- 每个 JSON 中的 `image_path` 和 `record_json_path` 与实际文件一致。
- `sample_id` 在当前 source 下唯一，且符合 `{source_type}_{source_name}_{000001}` 递增编号。
- `capability_dimension` 必须来自 Stage 1 的 `CAPABILITY_SCOPE.md` 或 `DATA_SOURCE_MAPPING.md`。
- `source_role` 必须来自 Phase 2 的 `Capability-To-Source Routing`。

任何一项失败，都必须在 `RAW_DATA_COLLECTION_REPORT.md` 中标为 `FAIL` 或 `NEEDS_REVIEW`。

## RAW_DATA_COLLECTION_REPORT.md 固定结构

```markdown
# Raw Data Collection Report

## Raw-Only Guarantee
Stage 2 preserved accessible raw samples only. No cleaning, filtering, dedup deletion or quality rejection was executed.

## Execution Summary
| Source Type | Source Name | Command | Exit Code | Start Time | End Time | Status |
|-------------|-------------|---------|-----------|------------|----------|--------|

## Preflight Checks
| Source Type | Source Name | Script Exists | Config Exists | Card Path | Card Readable | Card Match | Input Accessible | Runtime Accessible | Status | Notes |
|-------------|-------------|---------------|---------------|-----------|---------------|------------|------------------|--------------------|--------|-------|

## Simulator Runtime Evidence
| Source Name | Startup Command | Started At | Process / Session | Health Check | Run ID / Session ID | Current Run Samples | Status |
|-------------|-----------------|------------|-------------------|--------------|---------------------|---------------------|--------|

## Old Data Reuse Check
| Source Type | Source Name | Pre-Existing Files | External / Old Paths Found | Samples Excluded | Current Run Only | Result |
|-------------|-------------|--------------------|----------------------------|------------------|------------------|--------|

## Source Summary
| Source Type | Source Name | Expected Units | Real Input Evidence | Collected Samples | Access Failures | Status |
|-------------|-------------|----------------|---------------------|-------------------|-----------------|--------|

## Image-Record Contract
| Source Type | Source Name | Image Count | Record Count | Manifest Rows | One-to-One Status |
|-------------|-------------|-------------|--------------|---------------|-------------------|

## Anti-Placeholder Validation
| Source Type | Source Name | Check | Result | Evidence |
|-------------|-------------|-------|--------|----------|

## Benchclaw Read-Only Check
| Source Type | Source Name | Command | Attempted Write Under ~/benchclaw | Result | Evidence |
|-------------|-------------|---------|------------------------------------|--------|----------|

## Raw Observation Flags
| Source Type | Source Name | Flag | Count | Notes |
|-------------|-------------|------|-------|-------|

## Access Errors And Skipped Units
| Source Type | Source Name | Unit | Reason | Recoverable |
|-------------|-------------|------|--------|-------------|

## Capability Coverage
| Capability Dimension | Source Type | Source Name | Raw Samples | Notes |
|----------------------|-------------|-------------|-------------|-------|

## Failed Or Incomplete Sources
| Source Type | Source Name | Failure Mode | Why Placeholder Was Not Used | Required Next Action |
|-------------|-------------|--------------|------------------------------|----------------------|

## Handoff To Stage 3
| Path | Meaning |
|------|---------|
```

## 阶段判定

- `PASS`：所有启用 source 均真实执行，文件格式正确，图片/JSON/manifest 一一对应，反 placeholder 校验通过；启用的 simulator 均有本轮启动/session 证据且未复用旧数据。
- `NEEDS_REVIEW`：有 source 因运行环境、授权、外部路径或部分损坏需要人工确认，但未使用占位数据冒充成功。
- `FAIL`：任一启用 source 使用 placeholder/fake/mock/dummy 数据、明明有可访问数据却未执行、文件格式无法追溯，或 simulator 未启动/未创建新 session 却复用旧数据。

即使判定为 `FAIL`，也不得删除已采集的真实原始数据；只在报告中标记问题，交给用户或后续重试处理。
