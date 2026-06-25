---
name: benchclaw-stage4-contract-checking
description: Use for the specific BenchClaw subskill `stage4-contract-checking` only when its parent node explicitly dispatches to it.
---

## Opencode 子 agent 触发契约

本文件是 BenchClaw child skill module。父级 stage、node 或 pipeline 调度到本文件时，必须通过 opencode 命令 `/benchclaw-subskill` 启动隔离子 agent；该命令在 `BENCHCLAW_ROOT/opencode.json` 中配置为 `subtask: true`，并绑定 `mode: "subagent"` 的 `child-skill-module-runner`。禁止父级 manager 直接在自己的对话上下文中内联执行本文件步骤。

调用 `/benchclaw-subskill` 时必须传入：目标 `SKILL.md` 绝对路径、注册 skill 名、冻结的 `PROJECT_ROOT` / `BENCHCLAW_ROOT` / `WORKSPACE_PARENT` / `WORKSPACE_ROOT`、当前 node 或 work_unit id、已满足的输入 artifact 路径、期望输出 artifact 路径、父级 DAG 依赖与完成判据。子 agent 只返回 `status`、artifact 路径、证据摘要和 blockers，不回灌长日志或完整中间内容。

如果当前执行上下文不是 `/benchclaw-subskill` 产生的 `child-skill-module-runner` 子 agent，本文件不得继续执行；应立即返回 `BLOCKED`，说明必须由父级使用 `/benchclaw-subskill` 重新派发。

# Subskill — 契约检查

## 目标

在进入灰度前检查 `data_20_template_metric_code_bundle` 是否真的可运行。该 subskill 是硬门，不做模型推理。

## 必做检查

1. `py_compile`：父类 runtime、`generate_items.py`、`score_predictions.py`、`package_evalset.py`、`audit_evalset_quality.py`、`check_difficulty_mix.py`、`validate_bundle.py`、`tests/smoke_test.py`。
2. 作答图像：`image_processing/image_manifest.jsonl` 非空，且至少一张图像可读。
3. dry run：调用 `generate_items.py --limit 1`，`self_test/dry_run_items.jsonl` 至少 1 行。
4. schema：每条 dry-run item 必须有 `item_id/media/question/options/answer/answer_type/template_id/metric_id/evidence_refs/difficulty_level`。
5. 难度：`check_difficulty_mix.py` 可运行；灰度/全量阶段必须检查 easy/medium/hard 比例。
6. 正例评分：用 gold answer 作为 prediction，summary 必须满分。
7. 负例评分：至少一条错误 prediction，分数必须低于正例。
8. 漏答评分：只提交 1 条正确 prediction 必须被 scorer 拒绝，或不能得到满分；scorer 必须要求完整预测集、拒绝重复/未知 item id，分母必须是全量 item。
9. 打包 smoke：`package_evalset.py` 输出的 `data/test.jsonl` 不得含 `answer`、`metadata`、`evidence_refs`、`gold_*`、`gt_*`、bbox/depth/area provenance，并且必须写出 `manifest.json`、`checksums.json`、`ground_truth/audit_items_with_answers.jsonl`、`cards/benchmark_card.md`。
10. 可见可答证明：dry-run 和 package smoke 中每条 audit item 必须含 `answerability_proof`，并指向模型可见 media/anchor；答案依赖 private GT 的题目必须证明 private GT 已被可见 transform 暴露，不能只有 raw RGB。
11. Evalset 质量审计：运行 `scripts/audit_evalset_quality.py --evalset <package>`，必须 PASS；该审计必须能阻塞残缺选项 shortcut、正确答案表面异常、normalized duplicate options、answers 缺 audit/evidence、同一图片哈希跨多个 scene 身份复用、根目录答案版 JSONL、空白/近空图像、缺少 answerability proof。
12. Qwen/一键生成器追溯：`qwen_one_click_synthesizer_prompt.md` 和 `synthesizer_contract.json` 必须存在；`generate_items.py` 必须支持 canonical CLI，且源码中不能出现 placeholder、TODO-only、random answer、LLM judge、hardcoded answer rows、重新扫描隐藏 GT 找补等模式。
13. 子 skill 消费链：enabled `template_manifest.jsonl` 的每个模板必须能在 `metric_manifest.jsonl` 找到 metric，在 `generate_items.py` 找到对应 `implementation_hint` 或 template id 绑定；requires_overlay 模板必须能引用 `image_manifest.jsonl` 中 accepted 图像；private-GT-consuming 模板必须引用 `answerability_support` 足够的 processed image。
14. Contributor 装配链：`contrib/gt_adapter/adapter_contract.json`、`contrib/asset_builder/asset_builder_contract.json`、`contrib/template_registry/template_registry.json`、`contrib/metric_registry/metric_registry.json` 必须存在且被 `synthesizer_contract.json.consumed_contributors` 声明；`generate_items.py` 的字段读取、媒体解析、模板函数和 metric id 必须能追溯到对应 contributor。
15. Universal audit format smoke：调用 `package_evalset.py --audit-format-out self_test/audit_format_smoke`，必须写出 `benchmark_items.jsonl`、`template_registry.json`、`generation_report.json`、`benchmark_assets/`；`benchmark_items.jsonl` 每行必须保留 `answer`、`provenance`、`quality_flags` 和 `answerability_proof`，并且资产路径必须落在 `benchmark_assets/`。

## 输出

```text
data_20_template_metric_code_bundle/self_test/py_compile.log
data_20_template_metric_code_bundle/self_test/dry_run_items.jsonl
data_20_template_metric_code_bundle/self_test/difficulty_mix_report.json
data_20_template_metric_code_bundle/self_test/perfect_score_report.json
data_20_template_metric_code_bundle/self_test/negative_score_report.json
data_20_template_metric_code_bundle/self_test/evalset_quality_audit_report.json
data_20_template_metric_code_bundle/self_test/audit_format_smoke/benchmark_items.jsonl
data_20_template_metric_code_bundle/self_test/audit_format_smoke/template_registry.json
data_20_template_metric_code_bundle/self_test/audit_format_smoke/generation_report.json
data_20_template_metric_code_bundle/self_test/self_test_report.md
data_20_template_metric_code_bundle/contrib/item_validator/item_validator_contract.json
```

`self_test_report.md` 必须单独列出“一键生成器验收”小节，说明：

- 是否使用本地 Qwen 生成源码。
- Qwen prompt 文件路径和输入摘要。
- `generate_items.py --limit 1` 命令、退出码和输出行数。
- scorer 正负例分数。
- 漏答 prediction 是否被拒绝。
- 打包 smoke 的 `data/test.jsonl` 泄漏检查结果。
- 审计格式 smoke 的 `benchmark_items.jsonl/template_registry.json/generation_report.json/benchmark_assets` 是否齐全。
- contributor 消费链检查结果。
- `audit_evalset_quality.py` 的 PASS/FAIL 和关键 findings。
- answerability proof 覆盖率、private-GT-only 题目筛除数量、低信息图像筛除数量。

## 阻塞条件

任一必做检查失败即阻塞 `template-metric-code-generation`，不得进入 grey-batch-validation。
