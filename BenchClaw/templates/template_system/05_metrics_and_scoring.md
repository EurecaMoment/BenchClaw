# 统一指标与评分规则

## 1. Exact Match / Accuracy

适用于单选题、判断题、短答案题。预测归一化后与标准答案完全一致计 1，否则计 0。

归一化建议：大小写统一、去标点、去多余空格、同义词映射、中文/英文 yes-no 映射。

## 2. Set Exact Match

适用于多选题。预测集合与标准答案集合完全一致计 1，否则计 0。

```text
set_exact = 1[pred_set == gold_set]
```

## 3. Precision / Recall / F1

适用于多选题、可见物体集合、检索式答案。

```text
precision = |pred ∩ gold| / |pred|
recall    = |pred ∩ gold| / |gold|
f1        = 2 * precision * recall / (precision + recall)
```

空集处理：如果 `pred` 和 `gold` 都为空，F1 记为 1；如果只有一方为空，F1 记为 0。

## 4. 数值误差

适用于计数、距离、尺寸、时间步。

```text
absolute_error = |pred - gold|
relative_error = |pred - gold| / max(|gold|, epsilon)
tolerance_accuracy = 1[|pred - gold| <= tolerance]
```

计数题建议 exact match；距离/尺寸题建议同时报告相对误差和容差准确率。

## 5. 排序指标

适用于距离顺序、出现顺序、路径顺序。

- 完全排序：Exact Match。
- 部分排序或容忍相邻错误：Kendall Tau 或 pairwise accuracy。
- 存在并列答案时，应过滤或显式允许 tie。

## 6. 区域/Mask 指标

适用于区域选择、指代表达定位、分割题。

```text
IoU = area(pred_mask ∩ gold_mask) / area(pred_mask ∪ gold_mask)
```

常用 mIoU 或 `IoU >= threshold` accuracy。若只让模型选择候选 mask，则可用 Exact Match。

## 7. Accuracy+

适用于 MME 风格同图正负成对判断。只有同一图像的一对或一组题全部答对才计 1。

用途：降低 yes/no 题的语言先验风险。

## 8. SR / GC / SPL / RGS

适用于导航、操作或具身执行任务。

- SR：任务整体成功率。
- GC：goal condition 满足比例。
- SPL：成功且路径效率较高时得分更高。
- RGS：远程对象定位正确率。

如果当前 stage4 只生成静态图文 QA，通常不要使用这些执行型指标。

## 9. LLM-as-judge / LLM-Match

适用于开放问答或解释题。必须满足：

- 有标准答案或参考要点；
- 有固定 rubrics；
- 有模型版本、prompt、temperature 记录；
- 作为辅助指标或开放子集指标，不作为唯一主指标。

## 推荐主指标映射

| answer_format | 推荐指标 | 适用 |
|---|---|---|
| F1 单选 | Accuracy / Exact Match | 主评测 |
| F2 多选 | Set Exact + macro F1 | 主评测 |
| F3 判断 | Accuracy + Accuracy+ | 主评测 |
| F7 短答 | Normalized EM | 主评测或辅助 |
| F8 数值 | AE / RE / tolerance accuracy | 主评测 |
| F10 对比 | Exact Match | 主评测 |
| F11 帧选择 | Exact Match | 主评测 |
| F16 区域选择 | Exact Match / mIoU | 主评测 |
| F25 开放问答 | LLM-Match + 人工抽查 | 辅助评测 |


## Stage1/Stage4 统一指标口径

Stage1 中只允许提出 Stage4 能落地实现的指标。Stage4 中必须把指标绑定到 `scoring.metric` 字段，并在评分脚本中有明确实现或可解释的外部评估过程。

推荐的最小主指标集合：

| 指标族 | 用途 | 是否主指标 |
|---|---|---|
| Accuracy / EM | 单选、判断、短答案 | 是 |
| Set Exact + F1 | 多选、集合题 | 是 |
| AE / tolerance accuracy | 计数、距离、尺寸 | 是 |
| Pairwise / Kendall | 排序题 | 可选主指标 |
| IoU / mIoU | 区域、mask、定位 | 条件主指标 |
| LLM-Match | 开放题/解释题 | 辅助 |
| SR/GC/SPL | 执行任务 | 仅当有执行环境 |

## 6. 可运行评分脚本增强

`tools/score_eval_dataset.py` 现支持合成引擎输出的主要题型：

| metric | 适用题型 | 说明 |
|---|---|---|
| `exact_match` | 单选、判断、三选判断 | 归一化后精确匹配 |
| `set_exact_match + macro_f1` | 多选题 | 同时报告集合精确匹配和 F1 |
| `numeric_exact` | 整数/数值题 | 默认绝对误差为 0 才算正确，可扩展 tolerance |
| `ordered_list_pairwise_accuracy` | 排序题 | 按成对顺序一致性评分 |
| `json_field_accuracy` | JSON 对象、JSON 数组 | 对象按字段准确率，数组按集合 F1 |

这使 Stage4 可以从模板实例化直接进入自动评分，而不是只生成不可执行样例。
