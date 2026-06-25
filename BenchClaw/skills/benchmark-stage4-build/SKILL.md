---
name: benchclaw-stage4-build
description: Use for the BenchClaw skill `stage4-build` when the workflow is explicitly entering this stage or manager.
---

# Benchmark Stage4 Build Skill — 评测集合成与指标构建

## 角色

读取 Stage1 的能力/模板/指标意图、Stage3 的已标注证据和冻结路径，生成可执行模板代码、指标代码、作答图像处理产物、灰度验证报告，并最终输出 Stage5 可直接消费的离线 benchmark 包。

## 一键生成器目标

Stage4 的 `data_20_template_metric_code_bundle` 必须把模板、指标、图像处理和答案程序收敛成一个本地可执行的一键评测集合成器，而不是只写 manifest。参考质量目标是 `/home/maqiang/uav_spatial_eval_synthesizer.py` 的严格生成器模式：小而准的模板 registry、规范化 GT adapter、确定性答案函数、中性 A/B/C/D overlay、强 item validator、正负评分 smoke、模型可见数据与隐藏答案分离。

该合成器必须是 **由子 skill 贡献模块后装配出来的工程**：`gt-kinship-analysis` 贡献 GT adapter/字段目录，`answer-image-processing` 贡献 asset builder/image manifest，`template-compilation` 贡献 template registry，`metric-compilation` 贡献 metric registry/scorer，`answer-program-generation` 只负责把这些 contributor 装配为 `generate_items.py`、`package_evalset.py` 和 validator。禁止让 `answer-program-generation` 绕开前序 contributor 重新扫描 Stage3 私有目录、重新发明模板或独立决定可见锚点。

最终必须同时产出两层格式：

```text
stage4/artifacts/data_22_full_benchmark_dataset/audit_format/
  benchmark_items.jsonl
  template_registry.json
  generation_report.json
  benchmark_assets/

WORKSPACE_ROOT/EVALSET_DATASET/
  data/test.jsonl
  images/
  ground_truth/
  metrics/
```

第一层是类似 `/home/maqiang/libero_temporal_benchmark_final` 的审计/复现格式，允许保留答案、provenance、quality_flags 和 GT rule；第二层是 Stage5 模型可见安全交付包，必须剥离答案和隐藏 GT。两层必须由同一批 audit items 派生，不能各自生成一套题。

可以使用本地 Qwen 模型生成数据集专用 runtime 代码，但 Qwen 只作为代码作者，不作为判题者或质量门。提示必须包含通用质量契约 `reference_library/BENCHMARK_QUALITY_CONTRACT.md`、一键生成器契约 `reference_library/ONE_CLICK_SYNTHESIZER_CONTRACT.md`、Stage4 plan、GT kinship 摘要、image manifest schema、template manifest 和 metric manifest；生成代码必须通过同一套 deterministic contract-checking 后才能进入灰度。

## 统一执行原则

所有执行者使用同一个 skill 包、同一条 DAG、同一套父类 runtime 和同一组质量门。不得根据模型大小、供应商或 agent 能力切换流程、阈值、schema 或输出契约。

Stage4 只允许写入：

```text
WORKSPACE_ROOT/stage4/
WORKSPACE_ROOT/EVALSET_DATASET/
```

## 输入

- `data_11_template_metric_initial_draft`
- `data_13_execution_plan`
- `data_17_annotated_real_image_bundle`
- `data_18_annotated_existing_benchmark_bundle`
- `data_19_annotated_simulator_bundle`

缺少全部可用 Stage3 GT、真实媒体、标注结果或 Stage1 能力目标时，必须写 `BLOCKED.json` 与 `BLOCKED.md`。

## DAG 节点

| Node ID | Skill | Parents | 输出 |
|---|---|---|---|
| `stage4-plan-generation` | `benchclaw-stage4-plan-generation` | 无 | `stage4_execution_plan` |
| `template-metric-code-generation` | `benchclaw-stage4-template-metric-code-generation` | `stage4-plan-generation` | `data_20_template_metric_code_bundle` |
| `grey-batch-validation` | `benchclaw-stage4-grey-batch-validation` | `template-metric-code-generation` | `data_21_grey_validation_report` |
| `full-synthesis` | `benchclaw-stage4-full-synthesis` | `grey-batch-validation` | `data_22_full_benchmark_dataset` |

Ready-set 调度只能通过 `/benchclaw-subskill` 使用上表注册 skill 名。Stage4 manager 禁止在自身上下文中直接内联执行 node skill 或 nested subskill；每次派发必须传入目标 `SKILL.md` 绝对路径、注册 skill 名、冻结路径、输入/输出 artifact、父依赖和完成判据。每个节点完成后必须写：

```text
WORKSPACE_ROOT/stage4/nodes/<node-id>/USED_INPUTS.json
WORKSPACE_ROOT/stage4/nodes/<node-id>/DONE.json
WORKSPACE_ROOT/stage4/nodes/<node-id>/NODE_REPORT.md
```

长任务必须按 pipeline tmux 协议运行，写入 `run_logs/`，记录命令、日志、退出码和监控摘要。短任务可以前台执行，但必须在 `NODE_REPORT.md` 写明实际耗时和短任务依据。

## Opencode 子 agent 调度契约

`stage4-plan-generation`、`template-metric-code-generation`、`grey-batch-validation` 和 `full-synthesis` 必须分别由 `/benchclaw-subskill` 派发到 `child-skill-module-runner` 子 agent。`template-metric-code-generation` 与 `grey-batch-validation` 内部列出的所有 `subskills/<subskill-id>/SKILL.md` 也必须继续用 `/benchclaw-subskill` 派发，不能由父 node 直接内联执行。无法创建子 agent 时必须写 `BLOCKED`，不得继续灰度或全量合成。

## 父类 runtime 边界

必须读取：

```text
STAGE4_ARCHITECTURE.md
contracts/model_agnostic_execution_contract.json
skills/template-metric-code-generation/reference_library/ONE_CLICK_SYNTHESIZER_CONTRACT.md
skills/template-metric-code-generation/reference_library/BENCHMARK_QUALITY_CONTRACT.md
skills/template-metric-code-generation/reference_library/UNIVERSAL_EVALSET_FORMAT_CONTRACT.md
skills/template-metric-code-generation/scripts/build_parent_runtime_bundle.py
skills/template-metric-code-generation/subskills/template-compilation/parent_code/benchclaw_stage4_synthesis_base.py
```

skill 包只沉淀数据集无关父类代码。当前数据集专用生成器必须在 `data_20_template_metric_code_bundle/scripts/generate_items.py` 运行时生成，且只能作为薄子类绑定字段映射、图像处理产物与 enabled template。

`generate_items.py` 是 canonical one-click item generator，必须支持 `--bundle --evidence-index --out --limit --seed --template-id --filtered-output`。如另写 `scripts/one_click_generate_evalset.py`，它只能编排 `generate_items.py`、`score_predictions.py`、`package_evalset.py` 和 `check_difficulty_mix.py`，不得另起一套生成/评分逻辑。

## 子 skill contributor 装配契约

`data_20_template_metric_code_bundle` 必须显式保存每个子 skill 可被合成器消费的贡献：

```text
contrib/
  gt_adapter/adapter_contract.json
  asset_builder/asset_builder_contract.json
  template_registry/template_registry.json
  metric_registry/metric_registry.json
  item_validator/item_validator_contract.json
```

`generate_items.py` 可以是单文件，但必须在 `synthesizer_contract.json` 中声明它消费了上述 contributor；若某 contributor 缺失、未被读取或输出字段没有进入 item/provenance/quality_flags，contract-checking 必须 FAIL。贡献边界如下：

- GT adapter：只做字段归一化和证据 profile，不写题目。
- Asset builder：只生成/登记模型可见资产和中性 label mapping，不决定答案。
- Template registry：只声明 enabled/disabled 模板、GT rule、required visible transform、invalid 条件和 generator hook。
- Metric registry：只声明 prediction parser、score function 和 scorer CLI。
- Item validator：集中执行 answerability、leakage、option shortcut、media integrity、difficulty 和 provenance 检查。
- Orchestrator：调用 contributor 生成 audit items，再派生 LIBERO 风格审计包和 Stage5 安全包。

## 必达质量门

1. `data_20_template_metric_code_bundle` 中 `scripts/generate_items.py`、`scripts/score_predictions.py`、`scripts/package_evalset.py`、`scripts/check_difficulty_mix.py` 和父类 runtime 均可 `py_compile`。
2. `image_processing/image_manifest.jsonl` 必须存在且至少包含一张可作答图像；需要标注题时必须有 overlay 或候选框处理产物。
3. 每个 enabled template 和每条生成 item 必须有 **model-visible answerability proof**：说明答案由哪些模型可见图像/面板/overlay/文本锚点决定、隐藏 GT 只用于审计和判分；若答案来自 simulator pose、深度、坐标、轨迹、object id、bbox/mask 或多视角状态，则必须先生成对应的可见 depth panel、pose/map overlay、trajectory panel、candidate panel 或中性标识图，不能只把 raw RGB 当作可见证据。
4. `self_test/dry_run_items.jsonl` 至少真实产出 1 条 benchmark item，且 dry-run item 通过 answerability proof、图像质量、选项 shortcut、hidden-answer separation 检查。
5. 完美预测评分满分；错误预测低于满分；漏答、重复 id、未知 id 必须被 scorer 拒绝或得到严格低于满分，分母必须是全量 gold item。
6. `qwen_one_click_synthesizer_prompt.md` 和 `synthesizer_contract.json` 必须记录本地 Qwen 生成 runtime 时使用的输入摘要、硬约束和验收命令；若没有使用 Qwen，也必须说明由 agent 手写同等契约代码。
7. 灰度阶段必须真实调用 `generate_items.py`，并让 `invalid-item-screening/valid_items.jsonl` 非空。
8. `small-batch-result-evaluation` 必须执行并输出 score matrix；没有外部模型时必须用内置 deterministic/proxy responders 跑通，不得跳过。
9. `cdm-irt-analysis` 必须执行并输出 item difficulty/discrimination/capability diagnostics；小样本可以标记 `diagnostic_proxy` 或 `limited_matrix`，但不能写 N/A 后放行。
10. 灰度和全量 items 必须包含难度标签，且 easy/medium/hard 多难度题目均需达到 Stage4 plan 中的最低比例；默认比例：easy ≥ 0.20，medium ≥ 0.25，hard ≥ 0.20。若 GT 不支持某难度，必须在 `difficulty_mix_report.json` 记录可证伪原因并阻塞，除非 Stage1/Stage4 plan 明确降低该能力要求。
11. 全量合成必须输出 LIBERO 风格审计格式 `audit_format/benchmark_items.jsonl`、`audit_format/template_registry.json`、`audit_format/generation_report.json`、`audit_format/benchmark_assets/`，并输出 Stage5 安全格式 `data/test.jsonl`、`images/`、`ground_truth/`、`metrics/`、`cards/benchmark_card.md`、`checksums.json`。兼容旧审计文件 `dataset.jsonl`/`media/` 可以保留在 `data_22_full_benchmark_dataset` 内，但不得作为唯一全量产物。
12. `WORKSPACE_ROOT/EVALSET_DATASET/data/test.jsonl` 必须是模型可见版：media 路径为 `./images/...`，且不得含 `answer`、`metadata`、`evidence_refs`、object provenance、bbox/depth/area 等隐藏 GT。
13. `WORKSPACE_ROOT/EVALSET_DATASET/` 是 Stage5 交付包，根目录不得保留带答案/审计字段的 `dataset.jsonl`、`items.jsonl` 或其它答案版 sidecar；答案版只能在 `ground_truth/answers.jsonl` 与 `ground_truth/audit_items_with_answers.jsonl`。`stage4/artifacts/data_22_full_benchmark_dataset/dataset.jsonl` 可作为审计 artifact 存在，但不得复制到 `EVALSET_DATASET` 根目录作为模型可见交付物。
14. `WORKSPACE_ROOT/EVALSET_DATASET/ground_truth/answers.jsonl` 必须含答案与审计证据，供 scorer 使用。
15. 图像质量必须进入硬门：模型可见图像不得是全黑/全白/近空图、不可解码图、极小文件、symlink 或答案泄漏文件名；低信息图像必须进入 rejected/filtered，不得凑数进入全量。
16. `cards/benchmark_card.md` 必须说明数据源、采集/合成配置、task families、可见输入、hidden GT 边界、scorer CLI、已知限制、license/usage boundary 和样本/难度分布；一句话 card 不能通过全量合成。

## Stage gate

写 `stage4/_STAGE_DONE.json` 或返回 PASS 前必须运行：

```bash
python3 "$BENCHCLAW_ROOT/skills/validate_stage_gate.py"   --workspace-root "$WORKSPACE_ROOT"   --stage stage4   --report "$WORKSPACE_ROOT/stage4/stage4_gate_report.json"
```

只有退出码为 0 且报告 `status: PASS` 才能完成 Stage4；失败时写 `BLOCKED.json` 与 `BLOCKED.md`。
