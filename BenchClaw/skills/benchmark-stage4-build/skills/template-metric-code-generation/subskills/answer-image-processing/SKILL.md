---
name: benchclaw-stage4-answer-image-processing
description: Use for the specific BenchClaw subskill `stage4-answer-image-processing` only when its parent node explicitly dispatches to it.
---

## Opencode 子 agent 触发契约

本文件是 BenchClaw child skill module。父级 stage、node 或 pipeline 调度到本文件时，必须通过 opencode 命令 `/benchclaw-subskill` 启动隔离子 agent；该命令在 `BENCHCLAW_ROOT/opencode.json` 中配置为 `subtask: true`，并绑定 `mode: "subagent"` 的 `child-skill-module-runner`。禁止父级 manager 直接在自己的对话上下文中内联执行本文件步骤。

调用 `/benchclaw-subskill` 时必须传入：目标 `SKILL.md` 绝对路径、注册 skill 名、冻结的 `PROJECT_ROOT` / `BENCHCLAW_ROOT` / `WORKSPACE_PARENT` / `WORKSPACE_ROOT`、当前 node 或 work_unit id、已满足的输入 artifact 路径、期望输出 artifact 路径、父级 DAG 依赖与完成判据。子 agent 只返回 `status`、artifact 路径、证据摘要和 blockers，不回灌长日志或完整中间内容。

如果当前执行上下文不是 `/benchclaw-subskill` 产生的 `child-skill-module-runner` 子 agent，本文件不得继续执行；应立即返回 `BLOCKED`，说明必须由父级使用 `/benchclaw-subskill` 重新派发。

# Subskill — 作答图像处理

## 目标

把 Stage3 中的原始媒体、RGB 图、候选 overlay、局部裁剪等统一成可被题目引用的作答图像 manifest。该 subskill 不决定答案，不启用模板，只保证“模型看到的图像”真实存在、可读、路径安全、无答案泄漏，并为对象关系题提供 A/B/C/D 标识图的处理入口。

本 subskill 是 `reference_library/BENCHMARK_QUALITY_CONTRACT.md` 中 “model-visible visual anchor” 的执行层：凡后续题目需要指代具体 GT 物体、区域、轨迹、视角、时刻或候选，本 subskill 必须提供可引用的中性作答图像或明确 rejected。

补充说明：

- 本 subskill 只负责“作答图像处理”，不是题目生成器。
- 本 subskill 可以根据父节点显式提供的图像处理需求生成作答图像，但不能自行决定正确答案。
- 本 subskill 允许做程序化图像合成，但所有合成必须基于 Stage3 已有图像、Ground Truth、bbox、mask、depth、camera pose、trajectory 或父节点显式传入的 recipe。
- 本 subskill 禁止让 LLM 根据图片内容猜测 bbox、对象位置、轨迹、深度或答案。
- 本 subskill 的输出必须服务于后续题目生成器引用，例如：
  - 多视角拼图
  - A/B/C/D 候选标识图
  - 局部裁剪图
  - 原图 + 局部放大图
  - RGB-depth 配对图
  - top-down 轨迹图
  - before-after 对照图
  - global-wrist 双视角图
  - 候选答案图像面板

核心边界：

- 可以生成“给模型看的图”。
- 不可以生成“题目的答案”。
- 可以记录 A/B/C/D 与 object_id 的映射。
- 不可以在图像文件名、图中文字、manifest 字段中暴露 correct、answer、target、gt 等答案暗示。
- 可以拒绝不可处理图像。
- 不可以为了凑数量伪造图像证据。

## 输入

- `data_20_template_metric_code_bundle/evidence_index.jsonl`
- Stage3 原始媒体路径或 bundle 内已归一化媒体路径

可选输入：

- `data_20_template_metric_code_bundle/image_requests.jsonl`
- `data_20_template_metric_code_bundle/template_manifest.jsonl`
- Stage3 中已经生成的 bbox、mask、depth、camera pose、trajectory、object metadata、view metadata

其中 `image_requests.jsonl` 用于父节点显式声明需要生成哪类作答图像。示例：

```json
{
  "request_id": "req_001",
  "sample_id": "sample_001",
  "composer": "bbox_label_overlay",
  "source_images": ["Image_F"],
  "candidate_objects": ["obj_001", "obj_002", "obj_003"],
  "layout": {
    "labels": ["A", "B", "C"],
    "allow_semantic_labels": false
  },
  "purpose": "object_relation_question"
}
````

如果没有 `image_requests.jsonl`，本 subskill 只能执行默认安全处理：

* 检查图像路径；
* 检查图像可读性；
* 复制或转换到 bundle 内部安全路径；
* 生成 `image_manifest.jsonl`；
* 若同一 evidence row 有图像且至少两个 GT 对象具备 bbox/中心点，则额外自动生成一张 `bbox_label_overlay` 或等价中性标识图，用 A/B/C/D 作为后续题目可引用的视觉锚点；
* 复杂拼图或轨迹图仍需显式 recipe。

`evidence_index.jsonl` 中若存在以下字段，应优先用于图像处理：

```text
sample_id
scene_id
media / images
image_id
image_path
modality
view_type
step_id
timestamp
bbox_by_image
mask_by_image
depth_path
camera_pose
trajectory
object_id
object_name
category
visible_images
```

字段缺失时只能降级处理或 rejected，不能编造。

## 输出

```text
data_20_template_metric_code_bundle/image_processing/
  image_manifest.jsonl
  image_processing_report.json
  rejected_images.jsonl
data_20_template_metric_code_bundle/contrib/asset_builder/
  asset_builder_contract.json
```

补充输出约定：

```text
data_20_template_metric_code_bundle/image_processing/
  images/
    imgproc_000001.jpg
    imgproc_000002.jpg
  previews/
  logs/
    process_answer_images.log
  image_manifest.jsonl
  image_processing_report.json
  rejected_images.jsonl
```

`image_manifest.jsonl` 每行记录一张可被题目引用的作答图像，推荐字段如下：

```json
{
  "manifest_id": "imgproc_000001",
  "sample_id": "sample_001",
  "scene_id": "scene_001",
  "request_id": "req_001",
  "composer": "bbox_label_overlay",
  "model_input_path": "data_20_template_metric_code_bundle/image_processing/images/imgproc_000001.jpg",
  "source_image_ids": ["Image_F"],
  "source_paths": [
    "data_20_template_metric_code_bundle/stage3/images/Image_F.jpg"
  ],
  "width": 1280,
  "height": 720,
  "format": "jpg",
  "sha256": "string",
  "visual_labels": [
    {
      "label": "A",
      "object_id": "obj_001",
      "bbox_xyxy": [100, 120, 180, 240],
      "label_type": "neutral_letter"
    }
  ],
  "layout": {
    "type": "single_overlay",
    "panels": [
      {
        "panel_id": "main",
        "source_image_id": "Image_F"
      }
    ]
  },
  "available_evidence_flags": {
    "has_rgb": true,
    "has_depth": false,
    "has_bbox": true,
    "has_mask": false,
    "has_camera_pose": false,
    "has_trajectory": false
  },
  "leakage_check": {
    "path_safe": true,
    "filename_safe": true,
    "overlay_text_safe": true,
    "contains_answer_hint": false
  },
  "quality_check": {
    "decode_ok": true,
    "not_blank": true,
    "not_near_empty": true,
    "size_bytes": 12345,
    "luma_stddev": 35.0
  },
  "answerability_support": {
    "anchor_type": "safe_rgb|rgb_depth_pair|bbox_label_overlay|pose_map_overlay|trajectory_panel|candidate_panel",
    "supports_private_gt_fields": ["depth", "pose", "trajectory"],
    "sufficient_for_template_ids": ["..."]
  },
  "status": "accepted"
}
```

`rejected_images.jsonl` 每行记录一个被拒绝的图像或处理请求，推荐字段如下：

```json
{
  "sample_id": "sample_001",
  "request_id": "req_001",
  "image_id": "Image_F",
  "path": "original/path.jpg",
  "composer": "bbox_label_overlay",
  "reason_code": "MISSING_BBOX",
  "reason": "bbox_label_overlay requires bbox, but bbox is missing for candidate object obj_001 in Image_F",
  "recoverable": false
}
```

`image_processing_report.json` 推荐字段如下：

```json
{
  "total_samples": 100,
  "total_requests": 120,
  "accepted_images": 110,
  "rejected_images": 10,
  "composer_counts": {
    "safe_copy": 50,
    "bbox_label_overlay": 20,
    "multi_view_grid": 15
  },
  "rejection_counts": {
    "MISSING_BBOX": 4,
    "UNREADABLE_IMAGE": 3,
    "ANSWER_LEAKAGE_RISK": 3,
    "BLANK_OR_NEAR_EMPTY_IMAGE": 2,
    "MISSING_REQUIRED_VISIBLE_ANCHOR": 1
  },
  "blocking": false,
  "blocking_reasons": [],
  "warnings": []
}
```

`contrib/asset_builder/asset_builder_contract.json` 是给合成器装配使用的机器可读 asset builder 契约，必须说明：

```json
{
  "schema_version": "benchclaw.stage4.asset_builder.v1",
  "manifest": "image_processing/image_manifest.jsonl",
  "asset_root": "image_processing/images",
  "supported_composers": ["safe_copy", "bbox_label_overlay", "multi_view_grid", "candidate_panel"],
  "model_visible_path_policy": "bundle_relative_then_packaged_as ./images/...",
  "neutral_label_policy": ["A", "B", "C", "D", "View 1", "Step 1"],
  "composer_inputs": {
    "bbox_label_overlay": ["source_image", "bbox_xyxy", "neutral_labels"],
    "trajectory_topdown": ["trajectory", "pose", "coordinate_frame"]
  },
  "rejection_reason_codes": ["MISSING_BBOX", "UNREADABLE_IMAGE"],
  "forbidden_filename_tokens": ["answer", "correct", "gt", "target", "gold"]
}
```

本文件不记录正确答案；只记录可见资产如何生成、哪些 composer 可被 `generate_items.py` 调用、以及哪些失败必须 filtered。

## 规则

* 只处理作答图像，不写答案、不写评分逻辑。
* 所有输出路径必须在 bundle 或工作区内部，不得使用 URL、symlink、目录外路径作为最终模型输入。
* 对象题所需 overlay/crop 可以由父类 runtime 在出题时生成，但必须基于 manifest 中通过检查的原始图像。
* 图像不可读、尺寸为 0、路径不存在、文件过小、文件格式异常时必须记录 rejected。
* 全黑、全白、近空、极低方差、明显无纹理/无内容的图像必须记录 rejected 或 `quality_status: low_information` 并默认不得进入 valid item；除非 Stage4 plan 明确声明该任务就是检测空白/遮挡，否则不能用低信息图像凑数量。
* 若后续模板答案依赖 depth、pose、simulator coordinate、trajectory、地图、bbox/mask 或 metric scale，本 subskill 必须生成或确认相应的模型可见处理图，例如 `rgb_depth_pair`、`pose_map_overlay`、`trajectory_panel`、`bbox_label_overlay`、`candidate_panel`。只登记 raw RGB 不足以支持这类模板。
* `image_manifest.jsonl` 每条 accepted 记录必须包含 `quality_check` 与 `answerability_support` 字段，至少记录：是否可解码、尺寸、sha256、是否 blank/near_blank、是否有 required visual anchor、适用的 anchor type。

补充规则：

### 1. 支持的作答图像处理类型

本 subskill 至少支持以下 composer 名称。父节点可以通过 `image_requests.jsonl` 显式请求。

#### safe_copy

用途：把原始可读图像复制或转换到 bundle 内部安全路径。

要求：

* 输入图像必须存在且可读。
* 输出路径必须统一重命名为 `imgproc_xxxxxx.jpg/png`。
* 不得保留可能泄漏答案的原始文件名。

#### bbox_label_overlay

用途：为对象关系题、定位题、匹配题生成 A/B/C/D 标识图。

要求：

* bbox 必须来自 Stage3 / Ground Truth / evidence_index。
* 默认只允许画 A/B/C/D 或数字编号。
* 默认不允许把对象名称直接画到图上。
* A/B/C/D 与 object_id 的映射只能写入 manifest。
* 不得用特殊颜色、粗细、大小、位置暗示正确答案。
* 如果候选对象缺少 bbox，应 rejected，不能靠猜测补框。

#### point_label_overlay

用途：当 bbox 不稳定或目标较小时，用点标记候选对象中心。

要求：

* 点必须来自 bbox 中心、mask 中心或 GT 坐标投影。
* 若 request 只给 object id 而未给点，脚本必须优先使用显式 centroid/point，其次用 bbox 中心推导。
* 禁止 LLM 猜测点位。
* 点标签只能是 A/B/C/D 或数字编号。

#### single_crop

用途：根据 bbox 或父节点给定 crop box 生成局部裁剪图。

要求：

* crop 坐标必须在原图范围内。
* 允许 padding，但 padding 后不得越界。
* 不得裁出空图。
* 不得裁出带有答案或 GT 字样的文件名区域、标注区域。

#### inset_zoom

用途：生成“原图 + 局部放大”的作答图像。

要求：

* 放大区域必须来自原图真实裁剪。
* 主图必须保留。
* 必须用中性线框标出放大区域来源。
* 禁止生成式补全细节。

#### multi_view_grid

用途：生成多视角拼图，例如 Image A-H、T1-T4、Global/Wrist。

要求：

* 输入图像数量至少为 2。
* 每个 panel 必须有稳定编号。
* 不得拉伸图像。
* 允许 padding 保持比例。
* 如果父节点提供顺序，必须按父节点顺序排列。
* 如果父节点没有提供时序顺序，不得自行推断。

#### candidate_panel

用途：生成选择题候选图像面板。

要求：

* 每个候选 panel 样式一致。
* 候选标签使用 A/B/C/D。
* 不能让正确候选更清晰、更大、更居中。
* 不判断哪个候选正确。
* 候选顺序若需要随机，应使用固定 seed，并记录在 manifest 中。

#### rgb_depth_pair

用途：生成 RGB + metric depth 并列图。

要求：

* RGB 与 depth 必须来自同一 frame，或父节点明确声明可配对。
* depth 必须有 Near/Far 标尺。
* 必须说明 near/far 方向，例如 Near 0m / Far 10m。
* depth 尺寸无法对齐时必须 rejected。

#### trajectory_topdown

用途：根据 camera pose / agent pose / trajectory 生成俯视轨迹图。

要求：

* trajectory 必须来自 GT。
* 如果画方向箭头，方向必须来自 yaw / pose。
* 必须标出 N 或坐标轴方向。
* 如有 grid spacing，应写入图中。
* 坐标系未知时，不得生成方向题所需的轨迹图，只能生成无方向路径图并在 manifest 中标记。

#### before_after_pair

用途：生成操作前后、状态前后、时间前后的对照图。

要求：

* before / after 顺序必须来自 step_id、timestamp 或父节点显式指定。
* 不得把 success、correct、answer 写入图中。
* 顺序不明确时必须 rejected。

#### global_wrist_pair

用途：生成机器人操作中的 Global / Wrist 双视角图。

要求：

* Global 和 Wrist 必须来自同一时间步，或在 manifest 中记录 temporal_offset。
* panel header 可以写 Global / Wrist。
* 不得额外标出正确抓取点，除非父节点显式请求，并且所有候选点都来自 GT。

### 2. 答案泄漏控制

最终模型输入路径、文件名、图中文字、候选样式都不能泄漏答案。

禁止最终 `model_input_path` 或输出文件名包含：

```text
answer
correct
gt
groundtruth
label
target
positive
negative
true
false
gold
left
right
near
far
success
failure
```

默认禁止 overlay 文本包含：

```text
correct
answer
target
ground truth
success
failure
```

默认允许 overlay 文本：

```text
A B C D
Image A Image B Image C
T1 T2 T3 T4
Global Wrist
RGB Metric depth
Near Far
N E S W
```

默认不允许把对象真实名称画到图上，除非父节点显式设置：

```json
{
  "allow_semantic_labels": true
}
```

### 3. 路径安全

所有输入路径必须检查：

* 不允许 URL。
* 不允许 symlink 作为最终模型输入。
* 不允许 `..` 逃逸。
* 不允许目录外路径作为最终模型输入。
* 最终图像必须位于 `data_20_template_metric_code_bundle/image_processing/images/` 下。
* manifest 中的 `model_input_path` 必须是 bundle 内部相对路径。

### 4. 图像可读性检查

每张图像至少检查：

* 文件存在。
* 文件大小大于 1KB。
* PIL 或 OpenCV 可解码。
* width > 0。
* height > 0。
* 格式属于 jpg、jpeg、png、webp、bmp。
* 输出图像可再次被 PIL 或 OpenCV 打开。
* EXIF orientation 应正确处理。

### 5. 处理流程

脚本应按以下流程执行：

```text
1. 读取 evidence_index.jsonl。
2. 建立 sample_id、image_id、object_id 索引。
3. 读取可选 image_requests.jsonl。
4. 如果没有 image_requests.jsonl：
   4.1 对所有可读 RGB 图执行 safe_copy。
   4.2 写 image_manifest.jsonl。
   4.3 写 rejected_images.jsonl。
   4.4 写 image_processing_report.json。
5. 如果存在 image_requests.jsonl：
   5.1 对每个 request 检查 composer 是否支持。
   5.2 检查所需图像、bbox、mask、depth、trajectory 是否存在。
   5.3 执行对应 composer。
   5.4 检查输出路径安全和答案泄漏风险。
   5.5 成功则写 image_manifest.jsonl。
   5.6 失败则写 rejected_images.jsonl。
6. 如果没有任何 accepted 作答图像，则触发阻塞。
```

### 6. 推荐 reason_code

```text
PATH_NOT_FOUND
PATH_ESCAPE
SYMLINK_NOT_ALLOWED
URL_NOT_ALLOWED
UNREADABLE_IMAGE
ZERO_SIZE_IMAGE
TOO_SMALL_FILE
UNSUPPORTED_FORMAT
INVALID_DIMENSION
EMPTY_OR_BLANK_IMAGE
MISSING_RGB
MISSING_DEPTH
MISSING_BBOX
MISSING_MASK
MISSING_CAMERA_POSE
MISSING_TRAJECTORY
MISSING_CANDIDATE_OBJECTS
INVALID_RECIPE
ANSWER_LEAKAGE_RISK
OUTPUT_WRITE_FAILED
ALL_SOURCES_REJECTED
```

## 可执行脚本

```text
scripts/process_answer_images.py
```

推荐命令：

```bash
python scripts/process_answer_images.py \
  --bundle data_20_template_metric_code_bundle \
  --evidence-index data_20_template_metric_code_bundle/evidence_index.jsonl \
  --out data_20_template_metric_code_bundle/image_processing
```

如果存在父节点显式图像处理请求：

```bash
python scripts/process_answer_images.py \
  --bundle data_20_template_metric_code_bundle \
  --evidence-index data_20_template_metric_code_bundle/evidence_index.jsonl \
  --image-requests data_20_template_metric_code_bundle/image_requests.jsonl \
  --out data_20_template_metric_code_bundle/image_processing
```

脚本也必须兼容旧参数名 `--out-dir`，但 manifest 中一律写新的字段：`manifest_id`、`model_input_path`、`source_image_ids`、`visual_labels`、`available_evidence_flags`、`leakage_check`、`status`。`answer-program-generation` 和本地 Qwen 只能消费 accepted rows。

脚本建议至少包含以下函数：

```python
load_jsonl()
write_jsonl()
safe_resolve_path()
validate_image()
sanitize_output_filename()
check_answer_leakage()
compose_safe_copy()
compose_bbox_label_overlay()
compose_point_label_overlay()
compose_single_crop()
compose_inset_zoom()
compose_multi_view_grid()
compose_candidate_panel()
compose_rgb_depth_pair()
compose_trajectory_topdown()
compose_before_after_pair()
compose_global_wrist_pair()
build_manifest_record()
write_report()
```

最小可用实现顺序：

```text
P0 必须实现：
  safe_copy
  bbox_label_overlay
  multi_view_grid
  candidate_panel

P1 建议实现：
  single_crop
  inset_zoom
  before_after_pair
  global_wrist_pair

P2 可延后实现：
  point_label_overlay
  rgb_depth_pair
  trajectory_topdown
  mask_overlay
```

P0 未完成时，不能声称本 subskill 完成。

## 阻塞条件

* 没有任何可读作答图像。
* 模板 manifest 中启用了 requires_overlay 的模板，但没有可处理的 bbox/图像对。
* 图像路径逃逸工作区或包含答案/GT 文件名暗示。

补充阻塞条件：

* `image_manifest.jsonl` 为空。
* `image_manifest.jsonl` 不是合法 JSONL。
* 任意 accepted 记录的 `model_input_path` 不存在。
* 任意 accepted 记录的 `model_input_path` 指向 bundle 或工作区外部。
* 所有 `image_requests.jsonl` 请求全部失败。
* 父节点请求 `rgb_depth_pair`，但没有任何可配对 depth。
* 父节点请求 `trajectory_topdown`，但没有 trajectory 或 camera pose。
* 检测到明显答案泄漏且无法自动修复。
* 输出目录无法写入。
* `image_processing_report.json` 中 `blocking=true`。
