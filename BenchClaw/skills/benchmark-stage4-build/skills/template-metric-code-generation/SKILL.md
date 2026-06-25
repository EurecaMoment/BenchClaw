---
name: benchclaw-stage4-template-metric-code-generation
description: Use for the specific BenchClaw node skill `stage4-template-metric-code-generation` only when its parent stage explicitly dispatches to it.
---

## Opencode 子 agent 触发契约

本文件是 BenchClaw child skill module。父级 stage、node 或 pipeline 调度到本文件时，必须通过 opencode 命令 `/benchclaw-subskill` 启动隔离子 agent；该命令在 `BENCHCLAW_ROOT/opencode.json` 中配置为 `subtask: true`，并绑定 `mode: "subagent"` 的 `child-skill-module-runner`。禁止父级 manager 直接在自己的对话上下文中内联执行本文件步骤。

调用 `/benchclaw-subskill` 时必须传入：目标 `SKILL.md` 绝对路径、注册 skill 名、冻结的 `PROJECT_ROOT` / `BENCHCLAW_ROOT` / `WORKSPACE_PARENT` / `WORKSPACE_ROOT`、当前 node 或 work_unit id、已满足的输入 artifact 路径、期望输出 artifact 路径、父级 DAG 依赖与完成判据。子 agent 只返回 `status`、artifact 路径、证据摘要和 blockers，不回灌长日志或完整中间内容。

如果当前执行上下文不是 `/benchclaw-subskill` 产生的 `child-skill-module-runner` 子 agent，本文件不得继续执行；应立即返回 `BLOCKED`，说明必须由父级使用 `/benchclaw-subskill` 重新派发。

# Node Skill — 模板 / 指标 / 代码生成

## 目标

生成 `data_20_template_metric_code_bundle`。该 bundle 是下游灰度和全量合成的唯一代码入口，必须包含父类 runtime 副本、运行时生成的薄 `generate_items.py`、deterministic scorer、打包脚本、图像处理产物、manifest、contract 和 self-test。

该节点的最终代码目标是一个类似 `/home/maqiang/uav_spatial_eval_synthesizer.py` 质量的一键评测集合成器：模板少而可证、GT adapter 清晰、答案完全确定、overlay 中性、item validator 严格、模型可见文件与隐藏答案分离。可以调用本地 Qwen 辅助生成 dataset-specific runtime，但必须先生成 `qwen_one_click_synthesizer_prompt.md`，并把 Qwen 输出视为待验证源码而非可信结果。

本节点必须先按 `reference_library/BENCHMARK_QUALITY_CONTRACT.md` 建立通用质量约束：每条题目都要从 Stage3 evidence 经过模型可见锚点、确定性答案规则、隐藏审计和 deterministic scorer，不能用数据集特例、题面缺陷或隐藏 GT 泄漏来“凑” benchmark。

本节点还必须按 `reference_library/UNIVERSAL_EVALSET_FORMAT_CONTRACT.md` 建立统一输出格式：runtime 先生成含答案/证据/quality flags 的 canonical audit items，再由打包脚本派生 Stage5 model-visible rows。LIBERO temporal 只是格式样例，不是所有数据源的任务模板。

## 内部 subskill 顺序

以下每个内部 subskill 都必须通过 `/benchclaw-subskill` 作为新的 `child-skill-module-runner` 子 agent 派发；本 node 只负责编排顺序、传递冻结路径与 artifact 契约、汇总返回摘要，不得直接内联执行 subskill 步骤。

1. `gt-kinship-analysis` -> `benchclaw-stage4-gt-kinship-analysis`
2. `answer-image-processing` -> `benchclaw-stage4-answer-image-processing`
3. `template-compilation` -> `benchclaw-stage4-template-compilation`
4. `metric-compilation` -> `benchclaw-stage4-metric-compilation`
5. `answer-program-generation` -> `benchclaw-stage4-answer-program-generation`
6. `contract-checking` -> `benchclaw-stage4-contract-checking`

这些 subskill 是职责边界，不是允许重复造代码的理由。最终必须收敛到同一个 `data_20_template_metric_code_bundle`。

## 必须读取

```text
WORKSPACE_ROOT/stage4/nodes/stage4-plan-generation/stage4_execution_plan.yaml
contracts/model_agnostic_execution_contract.json
skills/template-metric-code-generation/scripts/build_parent_runtime_bundle.py
skills/template-metric-code-generation/subskills/template-compilation/parent_code/benchclaw_stage4_synthesis_base.py
skills/template-metric-code-generation/subskills/answer-image-processing/scripts/process_answer_images.py
skills/template-metric-code-generation/reference_library/BENCHMARK_QUALITY_CONTRACT.md
skills/template-metric-code-generation/reference_library/ONE_CLICK_SYNTHESIZER_CONTRACT.md
skills/template-metric-code-generation/reference_library/UNIVERSAL_EVALSET_FORMAT_CONTRACT.md
reference_library/*
```

## 输出目录

```text
WORKSPACE_ROOT/stage4/artifacts/data_20_template_metric_code_bundle/
  README.md
  source_inventory.jsonl
  field_catalog.yaml
  evidence_index.jsonl
  gt_kinship/
  image_processing/image_manifest.jsonl
  image_processing/image_processing_report.json
  contrib/gt_adapter/adapter_contract.json
  contrib/asset_builder/asset_builder_contract.json
  contrib/template_registry/template_registry.json
  contrib/metric_registry/metric_registry.json
  contrib/item_validator/item_validator_contract.json
  difficulty_mix_contract.json
  template_manifest.jsonl
  metric_manifest.jsonl
  code_manifest.json
  synthesizer_contract.json
  qwen_one_click_synthesizer_prompt.md
  synthesis_plan.yaml
  traceability.csv
  scripts/generate_items.py
  scripts/score_predictions.py
  scripts/package_evalset.py
  scripts/validate_bundle.py
  scripts/check_difficulty_mix.py
  contracts/benchmark_item.schema.json
  tests/smoke_test.py
  self_test/dry_run_items.jsonl
  self_test/perfect_score_report.json
  self_test/negative_score_report.json
  self_test/difficulty_mix_report.json
  self_test/py_compile.log
  self_test/self_test_report.md
```

## 处理规则

- `gt-kinship-analysis` 建证据图、字段目录、证据亲疏矩阵和难度支持，并写 `contrib/gt_adapter/adapter_contract.json`，但不直接启用模板。
- `answer-image-processing` 必须把候选作答图像归一化到 manifest，检查图像可读、路径安全、overlay/crop/panel 可生成；凡题目需要指代具体 GT 物体、区域、轨迹、视角或候选，都必须产出或确认模型可见视觉锚点，并写 `contrib/asset_builder/asset_builder_contract.json`。
- `template-compilation` 根据 Stage4 plan、GT 支持、父类模板 registry、难度配比目标决定 enabled/disabled 模板；每个 enabled 模板必须声明 `difficulty_level`、`kinship_level`、`requires_overlay`、`visual_marker_policy`（如需视觉锚点）、`answer_type`、`metric_id`、`gt_rule` 和 `implementation_hint`，并同步写 `contrib/template_registry/template_registry.json`。
- `metric-compilation` 只产生 deterministic metric 契约和 scorer；不得依赖 LLM judge 作为主指标；`score_predictions.py` 必须可由灰度和最终包复用，并同步写 `contrib/metric_registry/metric_registry.json`。
- `answer-program-generation` 必须生成薄 `generate_items.py`、打包/验证脚本、`synthesizer_contract.json` 和 `qwen_one_click_synthesizer_prompt.md`。若使用本地 Qwen，必须把 `BENCHMARK_QUALITY_CONTRACT.md`、`ONE_CLICK_SYNTHESIZER_CONTRACT.md`、`UNIVERSAL_EVALSET_FORMAT_CONTRACT.md` 与前序 contributor/manifest 输入给 Qwen，并只接受通过 contract-checking 的源码。
- `contract-checking` 必须实际运行 `py_compile`、`limit>=1` 合成、正负评分 smoke、难度配比 smoke、打包 smoke、审计格式 smoke 和模型可见数据泄漏检查，并写 `contrib/item_validator/item_validator_contract.json`。

## 子 skill 交接契约

```text
gt-kinship-analysis
  -> gt_kinship/*, field_catalog.yaml, difficulty_support*.json*, contrib/gt_adapter/adapter_contract.json
answer-image-processing
  -> image_processing/image_manifest.jsonl with model_input_path, visual_labels, leakage_check; contrib/asset_builder/asset_builder_contract.json
template-compilation
  -> template_manifest.jsonl + synthesis_plan.yaml + contrib/template_registry/template_registry.json with enabled template ids and implementation hints
metric-compilation
  -> metric_manifest.jsonl + scripts/score_predictions.py + contrib/metric_registry/metric_registry.json with deterministic metric ids
answer-program-generation
  -> qwen prompt + generated one-click runtime scripts bound to the contributor manifests above
contract-checking
  -> self_test/* + contrib/item_validator/item_validator_contract.json proving the generated runtime works before grey-batch-validation
```

如果一个 subskill 的输出没有被下游消费，不能把该 subskill 标记为 DONE；必须修正 manifest 字段或 blocked。

## 推荐可执行入口

```bash
python "$BENCHCLAW_ROOT/skills/benchmark-stage4-build/skills/template-metric-code-generation/scripts/build_parent_runtime_bundle.py"   --input "<stage3_annotated_root_or_evidence_jsonl>"   --bundle "$WORKSPACE_ROOT/stage4/artifacts/data_20_template_metric_code_bundle"   --schema "$BENCHCLAW_ROOT/skills/benchmark-stage4-build/templates/benchmark_item.schema.json"
```

图像处理入口必须使用 bundle 内部路径：

```bash
python "$BENCHCLAW_ROOT/skills/benchmark-stage4-build/skills/template-metric-code-generation/subskills/answer-image-processing/scripts/process_answer_images.py" \
  --bundle "$WORKSPACE_ROOT/stage4/artifacts/data_20_template_metric_code_bundle" \
  --evidence-index "$WORKSPACE_ROOT/stage4/artifacts/data_20_template_metric_code_bundle/evidence_index.jsonl" \
  --out "$WORKSPACE_ROOT/stage4/artifacts/data_20_template_metric_code_bundle/image_processing"
```

## 阻塞条件

- `generate_items.py` 不存在、不可编译或不支持 `--bundle --evidence-index --out --limit --seed --template-id --filtered-output`。
- `qwen_one_click_synthesizer_prompt.md` 或 `synthesizer_contract.json` 缺失，导致本地 Qwen/人工生成的 runtime 无法追溯到固定契约。
- `image_processing/image_manifest.jsonl` 为空。
- `self_test/dry_run_items.jsonl` 为空。
- `self_test/difficulty_mix_report.json` 不满足最低难度比例。
- 完美预测不能满分，或负例与完美预测同分。
- bundle 缺少 manifest、schema、evidence index、metric 或 scorer。
