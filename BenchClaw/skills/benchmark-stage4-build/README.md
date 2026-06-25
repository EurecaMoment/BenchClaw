# benchmark-stage4-build

Stage4 把 Stage1 的能力/模板/指标意图与 Stage3 的已标注证据，编译成可离线评测的 benchmark 包。当前版本采用统一模型无关架构：同一个 skill 包、同一条 DAG、同一套父类 runtime、同一组灰度质量门适用于所有执行模型或 agent。

## Canonical flow

```text
stage4-plan-generation
-> template-metric-code-generation
   -> gt-kinship-analysis
   -> answer-image-processing
   -> template-compilation
   -> metric-compilation
   -> answer-program-generation
   -> contract-checking
-> grey-batch-validation
   -> per-template-batch-synthesis
   -> invalid-item-screening
   -> small-batch-result-evaluation
   -> cdm-irt-analysis
-> full-synthesis
-> WORKSPACE_ROOT/EVALSET_DATASET
```

`template-metric-code-generation` 的核心产物不是静态 manifest，而是一套可运行的一键 synthesizer contract：`scripts/generate_items.py`、`scripts/score_predictions.py`、`scripts/package_evalset.py`、`synthesizer_contract.json` 和 `qwen_one_click_synthesizer_prompt.md`。本地 Qwen 3.6 可以参与生成这些 dataset-specific 薄 runtime 文件，但所有输出必须通过同一套 deterministic gate。

这套 synthesizer 必须由子 skill 的 contributor 装配而成：GT adapter、asset builder、template registry、metric registry 和 item validator 分别由对应 subskill 产出，`answer-program-generation` 只把它们绑定成一键合成器。目标质量参考 `/home/maqiang/uav_spatial_eval_synthesizer.py`，但不能把 UAV 或 LIBERO 的任务集合硬编码成所有数据源的模板。

## 设计边界

- skill 包只沉淀数据集无关父类 runtime、工具脚本、schema、contract 和操作规约。
- 当前数据集专用逻辑只能在运行时生成的 `data_20_template_metric_code_bundle/scripts/generate_items.py` 中体现，且应保持薄子类形式。
- Stage4 的必达目标不是只产出 JSONL，而是产出经过作答图像处理、灰度生成、无效题筛查、小批量结果评测、CDM/IRT 诊断后可进入全量合成的 benchmark。
- 全量输出必须同时包含审计/复现格式和 Stage5 安全格式。审计格式参考 `/home/maqiang/libero_temporal_benchmark_final` 的 `benchmark_items.jsonl + template_registry.json + generation_report.json + benchmark_assets/`；Stage5 安全格式是 `EVALSET_DATASET/data/test.jsonl + images/ + ground_truth/ + metrics/`。
- `small-batch-result-evaluation` 和 `cdm-irt-analysis` 是全量合成前置门。没有外部模型配置时，必须使用内置 deterministic/proxy responders 生成 score matrix 并跑通诊断；报告必须标清 proxy，不得冒充真实模型排行榜。
- GT kinship 不再只是“远血缘高难题”开关，而是用于生成 easy/medium/hard 多难度题目配比。默认最低比例：easy ≥ 0.20，medium ≥ 0.25，hard ≥ 0.20。
- model-facing `EVALSET_DATASET/data/test.jsonl` 必须去除答案、GT provenance、metadata；隐藏答案写入 `EVALSET_DATASET/ground_truth/`。
- 每条 item 必须有 model-visible answerability proof。答案若来自 simulator pose、坐标、深度、trajectory、bbox/mask、object id 等 private GT，必须先被可见化为 depth panel、pose/map overlay、trajectory panel、candidate panel 或中性标识图；只给 raw RGB 不允许通过。
- `EVALSET_DATASET` 是交付包，根目录不得放带答案的 `dataset.jsonl` 或 `items.jsonl`；答案和审计只在 `ground_truth/`，内部审计版数据留在 Stage4 artifact。
- 空白/近空/低信息图像、固定 fallback distractor、从不为正确答案的选项、太薄的 benchmark card 都属于阻塞级质量问题。

## 必达产物

```text
WORKSPACE_ROOT/stage4/artifacts/data_20_template_metric_code_bundle/
  scripts/generate_items.py
  scripts/score_predictions.py
  scripts/package_evalset.py
  scripts/check_difficulty_mix.py
  synthesizer_contract.json
  qwen_one_click_synthesizer_prompt.md
  image_processing/image_manifest.jsonl
  contrib/gt_adapter/adapter_contract.json
  contrib/asset_builder/asset_builder_contract.json
  contrib/template_registry/template_registry.json
  contrib/metric_registry/metric_registry.json
  contrib/item_validator/item_validator_contract.json
  gt_kinship/difficulty_support.json
  difficulty_mix_contract.json
  evidence_index.jsonl
  template_manifest.jsonl
  metric_manifest.jsonl
  self_test/dry_run_items.jsonl

WORKSPACE_ROOT/stage4/artifacts/data_21_grey_validation_report/
  per_template_batch/generated_items.jsonl
  invalid_item_screening/valid_items.jsonl
  difficulty_mix_report.json
  small_model_eval/score_matrix.jsonl
  small_model_eval/status.json
  cdm_irt/cdm_irt_summary.json
  cdm_irt/status.json
  report.md

WORKSPACE_ROOT/stage4/artifacts/data_22_full_benchmark_dataset/
  audit_format/benchmark_items.jsonl
  audit_format/template_registry.json
  audit_format/generation_report.json
  audit_format/benchmark_assets/
  dataset.jsonl
  media/
  ground_truth/
  metrics/
  cards/benchmark_card.md
  checksums.json

WORKSPACE_ROOT/EVALSET_DATASET/
  data/test.jsonl
  images/
  ground_truth/answers.jsonl
  metrics/score_predictions.py
  README.md
```

## 不允许的完成方式

- 用 manifest、空 JSONL、URL、symlink 或外部路径冒充真实 benchmark。
- `data/test.jsonl` 泄漏 `answer`、`metadata`、`evidence_refs`、object id、bbox、depth、area 等隐藏 GT。
- 让问题答案只依赖 hidden simulator state、坐标、深度图、bbox/mask、trajectory 或文件/scene id，而没有模型可见锚点。
- 把带答案的 audit JSONL 放在 `EVALSET_DATASET` 根目录，导致下游误把答案版文件当作模型输入。
- 用全黑/全白/近空/低信息图像凑数，或保留明显不可能为正确答案的 fallback 选项。
- 根据执行模型身份切换流程、阈值、schema 或 skill 包。
- 绕过作答图像处理、`py_compile`、真实 `limit=1` 合成、无效题筛查、难度配比检查、小批量结果评测、CDM/IRT 诊断或正负评分 smoke。

## 当前父类模板规模

父类 runtime 默认可编译出 17 类静态 VLM 严格模板，覆盖 D1–D5：类别可见性、单选/多选类别、计数区间、平面关系、九宫格、中心距离、左右排序、面积比较/排序、深度区间、近远比较/排序。具体启用集合由运行时 GT profile 与 Stage4 plan 决定。
