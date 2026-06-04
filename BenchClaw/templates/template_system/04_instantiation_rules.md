# 严格模板实例化规则

1. 先读取 `template_library/benchclaw_fixed_template_registry.yaml`。
2. 默认只选择 `template_sets.strict_core`。
3. 只有 manifest 中存在可靠 depth 字段时，才可选择 `strict_depth`。
4. 多帧、姿态、3D 扩展模板必须由 required_fields 解锁。
5. `deprecated_locked` 中的模板永远不可实例化。
6. 所有实例级候选题必须生成 overlay 图，并在题干中使用 A/B/C/D 标注物体。
7. 候选项显示文本重复时，必须改用标注字母作为答案空间，不能只输出类别名。
8. 数量、距离、深度、面积等数值必须先映射到互斥区间。
9. 真实值落在区间边界、排序并列、深度差/面积差/位置差不足阈值时，直接丢弃样本。
10. 题干不得出现 GT、depth_median、object_id、可见物体列表等元数据词。
