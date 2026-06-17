# PATCH_SUMMARY

本次修改面向 `template-metric-code-generation` skill，新增 BenchClaw 图像/视频模板-指标外挂参考库，并以最小侵入方式修改原 skill 说明。

## 新增文件

- `reference_library/README.md`
- `reference_library/BENCHCLAW_IMAGE_VIDEO_TEMPLATE_METRIC_LIBRARY.md`
- `reference_library/template_family_registry.yaml`
- `reference_library/answer_type_metric_registry.json`
- `reference_library/schema_patch_notes.md`

## 修改文件

- `SKILL.md`
  - 增加外挂参考库读取/登记要求。
  - 明确外挂参考库是适配过滤层，不替代统一模板包。
  - 增加 references 输出与 runtime_contract 引用。
  - 收紧主指标：不得以 LLM-as-judge、captioning metric、主观 rating 作为主指标。

- `subskills/template-compilation/SKILL.md`
  - 增加读取参考库的要求。
  - 在模板选择阶段加入 10 类保留模板族、保留 answer type、deterministic metric 和可审计 GT 的过滤。
  - 增加 `reference_template_family`、`reference_answer_type`、`reference_metric_id` 等追溯字段。

- `subskills/metric-compilation/SKILL.md`
  - 替换推荐指标映射为 BenchClaw 图像/视频适配指标集。
  - 要求主指标来自 `answer_type_metric_registry.json`。

- `subskills/answer-program-generation/SKILL.md`
  - 要求答案程序只生成保留 answer type。
  - 增加 provenance 和隐藏 GT 字段题面约束。
  - 要求 bundle 复制 references。

- `subskills/contract-checking/SKILL.md`
  - 增加 references 目录完整性、映射一致性和隐藏 GT 字段检查。

## 未改动原则

- 未移除原 stage schema、DONE/BLOCKED、统一模板包、Stage3 evidence 和 self-test 契约。
- 未改变原产物主目录和后续 grey-batch-validation handoff 主入口。
- 未把外挂参考库作为统一模板包的替代品。
