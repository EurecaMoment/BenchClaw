
# 模板实例化规则

## 1. 输入要求

每次实例化至少需要：

- 图像或帧序列路径；
- 与图像对齐的 GT/tracker；
- 可见物体、bbox/mask、depth、3D 坐标、receptacle、state、timestep 中至少一种可用字段；
- 明确的 template_id、capability_id、answer_format 和 scoring_metric。

## 2. 实例化流程

```text
选择模板 T
→ 检查 GT 字段是否满足 required_gt_fields
→ 从样本中筛选可唯一作答的实体/关系
→ 生成 question/options/gold_answer
→ 绑定 evidence_ref 和 derivation 说明
→ 运行质量门
→ 写入 eval_item.jsonl
```

## 3. 候选项构造

- 单选题：必须只有一个正确选项，干扰项来自同场景、同类别层级或相近数值，不要使用明显无关项。
- 多选题：必须允许多个正确答案，gold answer 用集合表示，预测解析也按集合处理。
- 判断题：建议成对构造正负题，或使用 Accuracy+ 降低 yes/no 语言先验。
- 数值题：必须指定单位和容差；计数题一般用精确匹配。
- 帧选择题：候选帧必须来自同一 episode，正确帧唯一，若并列则过滤。

## 4. 证据绑定

每道题必须包含：

```json
{
  "evidence_ref": ["image path", "tracker path", "field path or computation note"],
  "evidence_fields": ["objects[*].objectType", "receptacleObjectIds", "timestep"],
  "answer_derivation": "用一句话说明答案如何由证据得到"
}
```

## 5. 过滤规则

过滤以下样本：

- GT 缺少模板要求字段；
- 候选答案并列或不唯一；
- 目标物体不可见但题目要求视觉判断；
- 物体太小、遮挡严重、同类实例无法区分；
- 需要 navmesh、动作标签、affordance 或语义地图，但当前数据没有这些字段；
- 题面依赖常识，而非给定证据。

## 7. 可运行合成引擎接入规则

当样本满足 `schemas/entity_annotations.schema.json` 的输入契约时，Stage4 应优先使用 `tools/synthesize_static_vlm_benchmark.py` 生成候选 eval items，而不是只让大模型手写题目。该引擎已经把模板实例化中的关键约束固化为代码：对象置信度过滤、面积过滤、中心点 margin、深度差阈值、排序唯一性、bbox overlay 证据图、不可答边界和结构化答案 schema。

使用顺序为：

```text
entity_annotations.json → synthesize_static_vlm_benchmark.py → generated_eval_dataset.jsonl → schema/quality gate → score_eval_dataset.py
```

若某条模板需要时序、容器、agent pose、动作状态或 navmesh，而输入 GT 不包含这些字段，不允许通过常识补题；应记录为“当前数据条件不可执行模板”。
