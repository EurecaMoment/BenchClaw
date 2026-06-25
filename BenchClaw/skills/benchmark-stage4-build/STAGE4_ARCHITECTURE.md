# Stage4 Architecture Contract — Difficulty-balanced, image-aware, mandatory-grey pipeline

## 结论

Stage4 的职责不是只“生成一些题”，而是把 Stage1 能力意图和 Stage3 GT 证据编译为可执行、可评分、可灰度验证、可全量交付的 benchmark。修订后采用一条统一执行轨道：所有模型/agent 都使用同一个 skill 包、同一父类 runtime、同一灰度门；不得因模型能力强弱改变流程或放宽质量门。

## 修订后的关键原则

1. **GT kinship 不再只服务高难远血缘题**：它必须给每个候选模板标注证据亲疏、推理跳数和难度等级，并约束 easy/medium/hard 多难度题目在灰度和全量集中都有最低比例。
2. **作答图像处理是独立 subskill**：所有用于作答的 RGB、overlay、局部裁剪、候选标签图都必须进入 `image_processing/image_manifest.jsonl`，模板只能引用经过处理和审计的图像。
3. **可见可答证明是逐 item 硬门**：每个 item 必须在 hidden audit 中记录 `answerability_proof`，说明模型可见的哪张图、哪个 overlay/panel/文本锚点足以确定答案。任何只由 simulator pose、深度图、坐标、object id、bbox/mask、trajectory 或私有状态决定、但模型只看到 raw RGB 的题目必须被过滤或阻塞。
4. **交付包边界必须干净**：`WORKSPACE_ROOT/EVALSET_DATASET` 只交付 model-visible `data/test.jsonl`、本地 `images/`、hidden `ground_truth/`、metrics、manifest/card/checksums；根目录不得混入带答案的 `dataset.jsonl` 或 `items.jsonl`。答案版审计数据只在 `ground_truth/`，或留在 `stage4/artifacts/data_22_full_benchmark_dataset/`。
5. **图像质量是 answerability 的一部分**：全黑、全白、近空、极小、不可解码、symlink、路径/文件名泄漏答案的媒体不能进入 valid items。低信息图像必须记录 rejected reason。
6. **small-batch-result-evaluation 是全量前置门**：必须产生小批量 score matrix。若外部模型不可用，必须运行内置 deterministic/proxy responders，用于验证 scorer、题型解析和灰度矩阵形态；报告必须清楚标记 proxy，不得冒充真实模型排行。
7. **CDM/IRT 是全量前置门**：必须基于 small-batch score matrix 产出题目难度、区分度和能力覆盖诊断。小样本可以是 `limited_matrix` 诊断，但不能 N/A 直接放行。
8. **全量生成代码必须丰富但不臃肿**：父类 runtime 提供多能力、多题型、多难度模板族；运行时 `generate_items.py` 只做 adapter 绑定和模板选择，不复制大型生成器。
9. **合成器是 contributor 装配结果**：每个子 skill 产出一个可消费模块，而不是只写报告。GT kinship 产出 `contrib/gt_adapter/adapter_contract.json`，answer-image-processing 产出 `contrib/asset_builder/asset_builder_contract.json`，template-compilation 产出 `contrib/template_registry/template_registry.json`，metric-compilation 产出 `contrib/metric_registry/metric_registry.json`，contract-checking 产出 `contrib/item_validator/item_validator_contract.json`。`answer-program-generation` 只能装配这些 contributor，不得绕过它们重扫私有 GT 或另造题型。
10. **全量输出分为审计格式和 Stage5 格式**：`data_22_full_benchmark_dataset/audit_format/` 必须包含类似 `libero_temporal_benchmark_final` 的 `benchmark_items.jsonl`、`template_registry.json`、`generation_report.json` 和 `benchmark_assets/`；`WORKSPACE_ROOT/EVALSET_DATASET/` 是安全交付格式。两个格式必须由同一批 accepted audit items 派生。

## 子 skill 职责边界

| Skill | 必要性 | 职责 | 关键输出 |
|---|---:|---|---|
| stage4-plan-generation | 必达 | 冻结输入、能力目标、难度配比、灰度评测要求、CDM/IRT 阈值、打包契约 | `stage4_execution_plan.yaml` |
| gt-kinship-analysis | 必达 | 归一化 GT 证据图，给模板候选标注 kinship/difficulty 支持 | `gt_kinship/*`, `difficulty_support.json` |
| answer-image-processing | 必达 | 处理作答图像、overlay、裁剪、尺寸/路径/泄漏检查 | `image_processing/image_manifest.jsonl`, `contrib/asset_builder/asset_builder_contract.json` |
| template-compilation | 必达 | 从父类 registry 选择多能力、多题型、多难度模板，满足配比目标 | `template_manifest.jsonl`, `contrib/template_registry/template_registry.json` |
| metric-compilation | 必达 | 生成 deterministic scorer 与 metric manifest | `metric_manifest.jsonl`, `contrib/metric_registry/metric_registry.json` |
| answer-program-generation | 必达 | 生成薄 `generate_items.py`、adapter 和 synthesis plan | `scripts/generate_items.py` |
| contract-checking | 必达 | py_compile、dry-run、正负评分、图像/答案/GT 泄漏检查 | `self_test/*` |
| per-template-batch-synthesis | 必达 | 逐模板真实生成灰度 items，记录失败原因 | `per_template_batch/*` |
| invalid-item-screening | 必达 | 删除无媒体、无答案、重复选项、题干泄漏、近似平局等无效题 | `invalid_item_screening/*` |
| small-batch-result-evaluation | 必达 | 必须产生 score matrix；外部模型不可用时运行 proxy responders | `small_model_eval/*`, `scorer_smoke/*` |
| cdm-irt-analysis | 必达 | 必须输出难度/区分度/能力覆盖诊断 | `cdm_irt/*` |
| full-synthesis | 必达 | 只使用灰度通过且满足难度配比的模板全量合成并打包 | `data_22_full_benchmark_dataset`, `EVALSET_DATASET` |

## 推荐内部顺序

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

## 难度配比 contract

默认最低比例：

```json
{"easy": 0.20, "medium": 0.25, "hard": 0.20}
```

每个 item 必须在 `metadata.difficulty_level` 或顶层 `difficulty_level` 中标注难度；每个模板必须在 `template_manifest.jsonl` 中声明 `difficulty_level`、`kinship_level`、`required_evidence_fields`。全量前必须运行 `scripts/check_difficulty_mix.py`，失败则不得执行 `full-synthesis`。

## Hard gates

- 至少一条真实 item 由运行时生成的 `generate_items.py` 产出。
- 所有生成脚本 `py_compile` 通过。
- 作答图像处理 manifest 非空。
- 每条 item hidden audit 都包含 `answerability_proof`，并且 proof 指向 model-visible media/anchor；private-GT-only 题目不得通过。
- 答案依赖 depth/pose/trajectory/map/simulator coordinate 的题目，必须提供对应的 RGB-depth pair、pose/map overlay、trajectory panel 或 multi-view/candidate panel；raw RGB-only 不足以作为 proof。
- 全量 valid items 不得引用全黑/全白/近空/极小/不可解码图像。
- 完美预测满分；错误预测低于满分。
- 漏答、重复 id、未知 id 必须被 scorer 拒绝或严格低于满分。
- `small-batch-result-evaluation` 产出 score matrix。
- `cdm-irt-analysis` 产出非空诊断文件。
- `invalid-item-screening/valid_items.jsonl` 非空。
- `data/test.jsonl` 所有 media 路径为 `./images/...`，且不含答案/隐藏 GT 字段。
- `EVALSET_DATASET` 根目录不得含 answer-bearing `dataset.jsonl`、`items.jsonl` 或其它可被误当成模型输入的答案版 sidecar。
- `images/`、`ground_truth/`、`metrics/` 非空。
- `cards/benchmark_card.md` 不得只有一句话；必须记录数据源、采集参数、任务类型、输入/隐藏边界、metric CLI、限制与分布。
- `data_22_full_benchmark_dataset/audit_format/benchmark_items.jsonl` 非空，且每行包含 `id`、`image/images`、`template_id`、`capability_id`、`question_type`、`answer`、`provenance` 和 `quality_flags`。
- `audit_format/template_registry.json` 与 `template_manifest.jsonl` 同源，不能只复制 LIBERO 的模板名；`audit_format/generation_report.json` 必须记录真实 rejected/filtered/quality checks 和生成配置。
