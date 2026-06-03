# 08 可运行合成引擎：静态具身空间图文评测集生成

## 1. 定位

`tools/synthesize_static_vlm_benchmark.py` 是本模板包中的 Stage4 可运行合成引擎。它不是独立于模板体系之外的脚本，而是把 `template_library/templates_100_unified.md` 中可由单张图像、实例标注、bbox/mask、depth 和粗 3D 信息支持的模板子集落成可执行生成流程。

它承接统一链条：

```text
能力维度 C → 作答形式 F → 模板 T → GT 字段 G → eval item E → 指标 M → 质量门 Q
```

其中：

- `TEMPLATE_META` 将可执行模板绑定到题型、能力维度和评分口径。
- `entity_annotations.json` 提供 GT 字段与证据来源。
- `ItemSink.add(...)` 统一生成题目、标准答案、证据字段、质量标记和 scoring 配置。
- bbox overlay 图保证实例级 A/B/C/D 候选在图像上可见，而不是只藏在元数据里。

## 2. 可运行输入契约

目录或 zip 样本至少应满足：

```text
sample/
  img_0001.jpg
  entity_annotations.json
  instance_masks/*.png                可选
  depth_map.png / semantic_*.png      可选
```

核心字段：

| 字段 | 用途 | 支持模板 |
|---|---|---|
| `objects[*].object_id` | 实例唯一 ID | 计数、筛选、JSON 输出 |
| `objects[*].category` | 物体类别 | T001-T020, T082/T084/T090 |
| `objects[*].mask.area_px` | 可见面积 | 主体类别、面积最大、复杂筛选 |
| `objects[*].bbox_2d.xyxy` | 2D 外接框 | 左右上下、重叠、相邻、overlay |
| `objects[*].bbox_2d.centroid_xy` | 像素中心 | 2D 关系、排序、九宫格 |
| `objects[*].bbox_2d.centroid_normalized_xy` | 归一化中心 | 左/右半区、九宫格 |
| `objects[*].depth_median` | 深度层次 | 远近、前后、深度区间 |
| `objects[*].centroid_3d.xyz` | 相机坐标 3D 质心 | 三维距离、三点比较 |
| `objects[*].rough_3d_bbox.size_xyz` | 可见 3D 包围盒尺寸 | 体积、尺寸排序 |
| `objects[*].confidence.value` | 标注置信度过滤 | 质量门 |
| `objects[*].valid_for_question_generation` | 题目生成准入 | 质量门 |

## 3. 已接入模板范围

该引擎目前可执行 51 个模板，覆盖静态图文评测中最稳定的部分：

- 可见类别与存在判断：`T001-T008`
- 计数与类别频次：`T011-T015`, `T020`
- 2D 空间关系：`T021-T035`
- 深度/前后/远近：`T036-T045`, `T091`, `T095`
- 3D 距离与可见 3D 包围盒：`T056`, `T057`, `T060`, `T061`, `T063`
- 证据边界与不可答判断：`T082`, `T084`, `T090`
- 复杂约束筛选和结构化输出：`T096`, `T097`, `T099`, `T100`

完整列表见：`template_library/executable_template_coverage.csv`。

没有被接入的模板并不是无效，而是通常需要额外 GT，例如时序轨迹、agent pose、容器关系、动作状态、navmesh、交通规则或多帧历史。Stage1 可以继续把这些模板纳入 benchmark 规划，但 Stage4 只有在对应 GT 字段可得时才能执行。

## 4. 输出格式

生成的 JSONL 同时保留两类字段：

1. 统一模板包字段：`item_id`, `source_sample_id`, `question_text`, `answer_format`, `capability_ids`, `gold_answer`, `scoring`, `evidence_ref`, `evidence_fields`, `quality_gate`。
2. 兼容原脚本字段：`id`, `sample_id`, `image`, `question`, `answer`, `answer_type`, `provenance`。

这样既能被本包的 `tools/score_eval_dataset.py` 直接评分，也能兼容原始合成代码的使用习惯。

## 5. 推荐运行命令

```bash
cd benchclaw_stage1_stage4_unified_template_pack
python tools/synthesize_static_vlm_benchmark.py \
  --input examples/uav_static_demo/sample_0001 \
  --output examples/uav_static_demo/generated_eval_dataset.jsonl \
  --asset-dir examples/uav_static_demo/generated_assets \
  --report examples/uav_static_demo/generated_report.json \
  --max-per-template 2 \
  --seed 7
```

然后可以直接评分：

```bash
python tools/score_eval_dataset.py \
  --gold examples/uav_static_demo/generated_eval_dataset.jsonl \
  --pred examples/uav_static_demo/generated_predictions.perfect.jsonl \
  --out examples/uav_static_demo/generated_score_report.json
```

## 6. 质量门

引擎内置了几类过滤：

- `min_conf`：过滤低置信实例。
- `min_area`：过滤面积过小、难以视觉辨认的实例。
- `require_valid`：尊重 `valid_for_question_generation`。
- `xy_margin_frac`：左右/上下/排序题要求中心点距离足够大。
- 深度题要求 `depth_median` 有效且差距超过阈值。
- 3D 题要求 `centroid_3d.xyz` 或 `rough_3d_bbox.size_xyz` 完整。
- 排序题要求候选之间没有近似并列。
- 不可答题显式记录不可答原因，防止模型凭常识臆测。

## 7. Stage1 与 Stage4 的使用方式

Stage1 使用该引擎时，不应直接写“我们能生成所有 100 类题”。更准确的说法是：模板库中 51 类已经有静态 GT 可执行实现，其余模板需要额外数据条件。Stage1 应把这些条件写进 benchmark 设计和数据采集需求。

Stage4 使用该引擎时，应把它作为题目生成主入口：先用该脚本批量生成候选题，再用 `generated_report.json`、schema check、质量门统计和抽样可视化审查过滤结果。
