---
name: benchclaw-stage4-answer-program-generation
description: Use for the specific BenchClaw subskill `stage4-answer-program-generation` only when its parent node explicitly dispatches to it.
---

## Opencode 子 agent 触发契约

本文件是 BenchClaw child skill module。父级 stage、node 或 pipeline 调度到本文件时，必须通过 opencode 命令 `/benchclaw-subskill` 启动隔离子 agent；该命令在 `BENCHCLAW_ROOT/opencode.json` 中配置为 `subtask: true`，并绑定 `mode: "subagent"` 的 `child-skill-module-runner`。禁止父级 manager 直接在自己的对话上下文中内联执行本文件步骤。

调用 `/benchclaw-subskill` 时必须传入：目标 `SKILL.md` 绝对路径、注册 skill 名、冻结的 `PROJECT_ROOT` / `BENCHCLAW_ROOT` / `WORKSPACE_PARENT` / `WORKSPACE_ROOT`、当前 node 或 work_unit id、已满足的输入 artifact 路径、期望输出 artifact 路径、父级 DAG 依赖与完成判据。子 agent 只返回 `status`、artifact 路径、证据摘要和 blockers，不回灌长日志或完整中间内容。

如果当前执行上下文不是 `/benchclaw-subskill` 产生的 `child-skill-module-runner` 子 agent，本文件不得继续执行；应立即返回 `BLOCKED`，说明必须由父级使用 `/benchclaw-subskill` 重新派发。

# Subskill — 答案程序与运行时子类生成

## 目标

生成当前数据集专用但足够薄的 `scripts/generate_items.py`。答案计算应复用父类模板的 `instantiate/finalize_item/validate_item` 逻辑，只在必要时覆写 GT 字段映射、读取作答图像 manifest 和绑定 enabled templates。

该 subskill 是本地 Qwen 代码生成的唯一入口。目标是产出类似 `/home/maqiang/uav_spatial_eval_synthesizer.py` 的严格一键 synthesizer，但结构上仍服从 Stage4 bundle：`generate_items.py` 负责真实 item 生成，`score_predictions.py` 负责 deterministic scoring，`package_evalset.py` 负责模型可见/隐藏答案分离。

本 subskill 是装配器，不是独裁生成器。它必须消费并记录以下 contributor：

```text
contrib/gt_adapter/adapter_contract.json
contrib/asset_builder/asset_builder_contract.json
contrib/template_registry/template_registry.json
contrib/metric_registry/metric_registry.json
```

生成器可以把这些 contributor 内联成单文件实现，但 `synthesizer_contract.json` 必须声明 consumed_contributors，`generate_items.py` 的模板函数必须对应 `template_registry.json` 的 `implementation_hint`，媒体解析必须对应 `asset_builder_contract.json`，字段读取必须对应 `adapter_contract.json`。若 contributor 缺失或没有被实际使用，必须阻塞。

## 必须生成

```text
data_20_template_metric_code_bundle/scripts/generate_items.py
data_20_template_metric_code_bundle/scripts/package_evalset.py
data_20_template_metric_code_bundle/scripts/validate_bundle.py
data_20_template_metric_code_bundle/scripts/check_difficulty_mix.py
data_20_template_metric_code_bundle/qwen_one_click_synthesizer_prompt.md
data_20_template_metric_code_bundle/synthesizer_contract.json
data_20_template_metric_code_bundle/contrib/item_validator/item_validator_contract.json
```

本 subskill 自带一个默认可执行运行时写入器：

```bash
python subskills/answer-program-generation/scripts/write_one_click_runtime.py --bundle data_20_template_metric_code_bundle
```

`build_parent_runtime_bundle.py` 会自动调用它，初始化一个能直接 smoke test 的严格 baseline。本地 Qwen 的任务是在此基础上按数据集增强 adapter/template 函数，而不是从空白文件开始。

允许额外生成：

```text
data_20_template_metric_code_bundle/scripts/one_click_generate_evalset.py
```

该 wrapper 只能调用上述 canonical scripts，不得重写独立生成/评分/打包逻辑。

## 本地 Qwen 使用方式

如果使用本地 Qwen 生成 runtime 源码，必须先写 `qwen_one_click_synthesizer_prompt.md`。提示必须小模型友好：短、结构化、只包含通用契约和 compact manifest，不用坏样例特例教模型。至少包含：

- `reference_library/BENCHMARK_QUALITY_CONTRACT.md` 的通用质量生命周期：evidence -> model-visible anchor -> deterministic answer -> hidden audit -> deterministic scorer -> audit gate。
- `reference_library/ONE_CLICK_SYNTHESIZER_CONTRACT.md` 的硬约束。
- `reference_library/UNIVERSAL_EVALSET_FORMAT_CONTRACT.md` 的 canonical audit item 与 Stage5 package 投影规则。
- `stage4_execution_plan.yaml` 中的能力、难度和图像策略。
- `contrib/*/*_contract.json` 的 contributor 摘要。
- `template_manifest.jsonl` 中 enabled 模板的 `template_id`、`answer_type`、`metric_id`、`difficulty_level`、`requires_overlay`、`visual_marker_policy`、`required_evidence_fields`、`gt_rule`、`implementation_hint`。
- `metric_manifest.jsonl` 中 parser 和 score function。
- `gt_kinship_report.md` / `difficulty_support_by_template.jsonl` 的摘要，尤其是每个模板的 evidence kinship 和可验证字段族。
- `image_processing/image_manifest.jsonl` 的字段 schema 和 3-5 条脱敏样例。
- `/home/maqiang/uav_spatial_eval_synthesizer.py` 的设计摘要：curated registry、dataclasses、adapter、overlay、strict validator、report writers、CLI。
- `/home/maqiang/libero_temporal_benchmark_final` 的格式摘要：`benchmark_items.jsonl`、`template_registry.json`、`generation_report.json`、`benchmark_assets/`，但不得复制 LIBERO 的 temporal 模板作为通用默认任务。

不得把完整 Stage3 私有 GT、大量原图路径、答案泄漏字段或“正确答案示例”直接塞进提示。Qwen 输出必须保存为源码后接受 contract-checking；若失败，修代码或重新生成，不能放宽契约。

## 代码边界

允许：

```python
class GeneratedDatasetAdapter(GenericGTAdapter):
    CATEGORY_KEYS = (...)
    BBOX_KEYS = (...)
```

禁止：

- 把父类 runtime 整体复制粘贴到 `generate_items.py`。
- 绕过 `validate_item()`。
- 在题干中暴露 object id、bbox、mask、depth 字段名。
- 对需要对象、区域、轨迹、视角或候选指代的题，直接在题干中写 GT 对象名称或隐藏字段来代替视觉锚点；必须使用处理后图像上的 A/B/C/D、P1/P2、View 1/2、Step 1/2 等中性标记，并让题干或选项引用这些标记。
- 生成不可回答、三分类不可确定、裸数字答案。
- 只写 manifest，不真实生成 item。
- 只生成单一难度模板，导致全量无法满足难度配比。

## `generate_items.py` 推荐结构

```text
constants: CAPABILITIES, QUESTION_TYPES, ENABLED_TEMPLATE_REGISTRY
dataclasses: EvidenceRecord, CandidateObject, GeneratedItem
adapter: GeneratedDatasetAdapter
asset access: GeneratedAssetBuilder / image manifest resolver
validators: validate_item_contract(), validate_no_leakage(), validate_media()
visuals: resolve_answer_image(), optional neutral overlay/panel helpers
template funcs: one deterministic gen_* function per enabled template
scoring hints: metric_id copied from metric_manifest
writers: audit item JSONL, filtered/rejected JSONL, generation report, optional audit_format
main(): parse CLI, load bundle manifests, generate, validate, write
```

每个 `gen_*` 函数必须只消费 `required_evidence_fields` 和 image manifest 中已通过检查的图像。不能在函数内部重新扫描私有 Stage3 目录寻找额外 GT。

每个 `gen_*` 函数还必须显式执行通用质量检查：

- 题目引用的 GT 实体是否有模型可见锚点。
- 答案是否只由模板声明的 deterministic rule 得到。
- 选项是否无重复、无格式唯一缺陷、无不完整文本、无逃避项。
- model-visible row 是否不含 hidden GT、audit metadata 或原始 annotation path。
- hidden audit row 是否能复现答案和视觉标记映射。

## 输出格式装配

`generate_items.py` 输出的是含答案 audit items，字段必须尽量贴近 `UNIVERSAL_EVALSET_FORMAT_CONTRACT.md`：

```text
id/sample_id/scene_id/split/image/images/source_image_count/input_modalities/
sequence_semantics/template_id/capability_id/capability_name/question_type/
question_type_name/question/options/answer/answer_type/scoring/provenance/
answerability_proof/quality_flags
```

`package_evalset.py` 必须能从同一批 audit items 派生：

- Stage5 model-visible package：`data/test.jsonl`、`images/`、`ground_truth/`、`metrics/`。
- 可选审计格式：通过 `--audit-format-out <dir>` 写 `benchmark_items.jsonl`、`template_registry.json`、`generation_report.json`、`benchmark_assets/`。

这两个输出不得分别采样或重新生成题目。只允许投影、复制媒体、脱敏和写报告。

## CLI 契约

`generate_items.py` 必须支持：

```bash
--bundle --evidence-index --out --limit --seed --template-id --filtered-output
```

## 阻塞条件

- 代码不可 `py_compile`。
- `--limit 1` 不能生成真实 item。
- 生成 item 缺媒体、答案、metric、template_id、difficulty_level 或追溯信息。
- 初始化后仍是 guard/placeholder runtime，没有真实 `gen_*` 模板函数。
