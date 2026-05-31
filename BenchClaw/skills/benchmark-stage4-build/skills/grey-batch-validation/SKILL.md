# Node Skill — 小批量合成灰度验证

## 内部层级

```text
subskills/per-template-batch-synthesis/SKILL.md
subskills/invalid-item-screening/SKILL.md
subskills/cdm-irt-analysis/SKILL.md
```

## 输入

- `data_20_template_metric_code_bundle`
- Stage3 三类已标注数据

## 处理

1. 按每个模板的灰度配额进行小批量合成。
2. 检查媒体存在性、GT 可计算性、答案唯一性、选项干扰项合理性、评分函数可执行性。
3. 对通过灰度验证的模板记录保留原因；对失败模板记录失败原因、修复建议和是否剔除。
4. 可执行 CDM/IRT 统计分析时，记录样本量、估计条件、结论适用范围。

## 输出

- `artifacts/data_21_grey_validation_report/report.md`
- `artifacts/data_21_grey_validation_report/template_status.csv`
- `artifacts/data_21_grey_validation_report/item_level_findings.jsonl`
- 节点执行记录文件
