# Node Skill — 全量合成

## 输入

- `data_20_template_metric_code_bundle`
- `data_21_grey_validation_report`
- Stage3 三类已标注数据

## 处理

1. 只使用通过灰度验证的模板与指标。
2. 按执行计划生成全量 benchmark item、媒体副本、GT、评分配置、数据集卡和校验和。
3. 所有媒体引用必须指向 workspace 内稳定存在的文件。
4. 每个 item 必须能追溯到数据源、证据记录、模板、答案程序与能力维度。

## 输出

- `artifacts/data_22_full_benchmark_dataset/dataset.jsonl`
- `artifacts/data_22_full_benchmark_dataset/media/`
- `artifacts/data_22_full_benchmark_dataset/ground_truth/`
- `artifacts/data_22_full_benchmark_dataset/metrics/`
- `artifacts/data_22_full_benchmark_dataset/cards/benchmark_card.md`
- `artifacts/data_22_full_benchmark_dataset/checksums.json`
- 节点执行记录文件
