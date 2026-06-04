# BenchClaw 严格修正版题型图谱

题型被收束为 6 类。F1–F24 仅作为历史字段保留，不再作为 agent 选择依据。

| 题型 ID | 名称 | 允许性 |
|---|---|---|
| QT1_SINGLE_CHOICE | 单选候选选择 | 允许 |
| QT2_MULTI_SELECT | 多选集合选择 | 允许 |
| QT3_BINARY_OR_COMPARISON | 是/否、正确/错误、A/B 二选比较 | 允许 |
| QT4_INTERVAL_CHOICE | 区间选择题 | 所有数量、距离、深度、面积数值必须使用 |
| QT5_ORDERING | 排序题 | 允许，但必须过滤并列 |
| QT6_STRUCTURED_MATCH | 受限结构化匹配 | 默认不开数字 JSON；只允许字段固定且视觉可验证 |

## 禁止题型

- 三选不可答；
- 无法判断 / 信息不足 / 是否可回答；
- 裸整数、裸浮点；
- 输出隐藏 object_id、depth_median 或内部 GT 字段；
- 依赖文件名、帧号泄漏而非视觉证据的排序题。
