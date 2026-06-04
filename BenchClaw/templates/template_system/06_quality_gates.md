# 严格质量门

| Gate | 通过条件 | 失败处理 |
|---|---|---|
| Template Lock Gate | 模板不在 deprecated_locked | reject |
| Question Type Gate | 题型属于 QT1–QT6 且不是不可答三选 | reject |
| Numeric Interval Gate | 数值答案已区间化 | rewrite/reject |
| GT Leakage Gate | 题干无 GT/depth_median/object_id/可见物体列表 | reject |
| Visual Evidence Gate | 问题可由图像/overlay 支撑 | reject/flag |
| Candidate Uniqueness Gate | 候选项不歧义；同类实例有 A/B/C/D | reject |
| Answer Uniqueness Gate | 单选/二选唯一，排序无并列，区间远离边界 | reject |
| Area Filter Gate | sky/road/ground/floor/wall/ceiling 和过大区域默认过滤 | reject object |
| Distribution Gate | 答案分布不过度集中 | rebalance |

运行前执行：

```bash
python tools/validate_strict_template_library.py
```
