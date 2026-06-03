# 题目作答形式参考表

| ID | 作答形式 | 输出格式 | 推荐主指标 | 适用场景 | 风险 |
|---|---|---|---|---|---|
| F1 | 单选题 | A/B/C/D | Exact Match | 唯一答案、候选可控 | 干扰项过弱会虚高 |
| F2 | 多选题 | A,C,D 或数组 | Set Exact Match / Precision / Recall / F1 | 多对象、多事实集合 | 漏选/多选评分需明确 |
| F3 | 判断题 | yes/no 或 是/否 | Exact Match / Accuracy+ | 存在性、关系真假、状态真假 | 语言先验强，需成对正负题 |
| F5 | 排序题 | 候选序列 | Exact Match / Kendall Tau | 出现顺序、距离顺序、路径顺序 | 并列时不可用 |
| F7 | 填空题 | 短文本 | 归一化 Exact Match | 类别、房间、方向词、属性词 | 同义词表必须固定 |
| F8 | 数值题 | 整数/浮点数 | AE / RE / tolerance accuracy | 计数、距离、尺寸 | 单位和容差必须明确 |
| F9 | 区间选择题 | 区间标签 | Exact Match | 数量/距离粗粒度估计 | 区间边界需互斥 |
| F10 | 对比选择题 | A>B / 更近 / 更多 | Exact Match | 数量、距离、面积、深度比较 | 差值太小会产生歧义 |
| F11 | 图片/帧选择题 | frame_id/image_id | Exact Match | 首次出现、最佳视角、变化帧 | 帧间差异需足够明显 |
| F12 | 图文匹配题 | 描述编号 | Exact Match | 事实一致性、综合描述 | 错误描述需单点变异 |
| F16 | Mask/区域选择题 | mask_id/bbox_id | Exact Match / mIoU | 定位、指代表达、分割区域 | 同类多实例需消歧 |
| F18 | 动作选择/动作序列 | action_id 或 action list | SR / step accuracy | 导航、操作、任务执行 | 依赖环境执行器 |
| F19 | 步骤排序题 | step list | Exact Match / edit distance | 规划、前置条件、后果 | 合法序列可能不唯一 |
| F25 | 开放问答 | 自由文本 | LLM-Match / 归一化 EM | 解释、功能、复杂场景问答 | 不宜作为唯一主指标 |

Stage1 选择题型时，应优先选择 F1/F2/F3/F7/F8/F10/F11 这类可稳定自动评分的形式。F25 可以保留为扩展题型，但需要严格 rubrics 和抽查。


## 题型选择优先级

- 第一优先级：F1 单选、F2 多选、F3 判断、F8 数值、F10 对比、F11 帧选择。它们最适合自动评分和批量构造。
- 第二优先级：F5 排序、F7 短答、F13 区域选择、F16 Mask/区域选择。需要更强解析或候选区域约束。
- 谨慎使用：F18/F19/F25。它们适合 ALFRED/REVERIE/OpenEQA 等参考范式，但若没有执行环境或固定 rubric，不应作为主评测题。
