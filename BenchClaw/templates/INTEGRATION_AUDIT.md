
# 整合审计说明

本文件说明用户上传资料中的有用内容如何进入统一模板包。此处只做可追溯说明，不设置原始资料备份目录。

## 1. 12 个 benchmark 模板卡片

来源目录：用户压缩包中的 `templates/*.md`。

整合结果：

- 结构化索引：`template_system/references/benchmark_cards.index.json`
- 人工矩阵：`template_system/references/benchmark_cards.matrix.csv`
- 统一参考卡片：`template_system/references/benchmark_cards/*.md`
- 综合设计依据：`template_system/03_benchmark_reference_synthesis.md`

保留内容包括：benchmark 名称、来源、场景、任务格式、数据规模、作答形式、能力维度、GT 依赖、自动评分方式、人工检查要点、模板示例。

## 2. 100 条具身空间图文模板

来源文件：用户资料中的《具身空间智能图文评测模板库（100条）》。

整合结果：

- 正式模板库：`template_library/templates_100_unified.md`
- 结构化索引：`template_library/templates_100_unified.index.json`
- 审阅矩阵：`template_library/templates_100_unified.matrix.csv`
- 模板族目录：`template_library/template_family_catalog.md`
- schema：`schemas/question_template.schema.json`

保留内容包括：100 条 ID、模板问题、使用数据类型、题目作答形式、考察能力方向、GT 依赖字段、自动评分方式、人工检查要点。

## 3. qa1 episode 题目和证据链

来源目录：用户压缩包中的 `qa1/episode_1` 到 `qa1/episode_4`。

整合结果：

- 统一 eval item 示例：`examples/ai2thor_qa1_reference_items.jsonl`
- 样例数据集：`examples/sample_eval_dataset.jsonl`
- 题族统计：`examples/ai2thor_qa1_family_summary.md`
- 证据包：`examples/ai2thor_qa1_evidence/episode_*/`
- 评分脚本：`tools/score_eval_dataset.py`

保留内容包括：111 道问题、29 张图像、4 个 tracker、选项、标准答案、metadata、evidence 字段。

## 4. 我新增的统一逻辑

新增内容不是替代用户资料，而是把旧资料串成可执行模板系统：

- `template_system/00_unified_logic.md`：能力-题型-模板-GT-指标-质量门的统一链条。
- `template_system/04_instantiation_rules.md`：模板实例化流程。
- `template_system/05_metrics_and_scoring.md`：统一评分口径。
- `template_system/06_quality_gates.md`：把旧模板中的人工检查要点转成可执行质量门。
- `schemas/`：Stage1/Stage4 共用 schema。
- `output_templates/`：Stage1 设计输出与 Stage4 实例化输出模板。

## 5. 明确未做的事情

- 没有设置 `source_preserved/`。
- 没有设置 `raw_from_uploaded_zip/`。
- 没有把用户资料作为杂散原始文件夹堆进去。
- 没有虚构新的 benchmark 数据或指标结果。


## 新增可运行合成代码的整合说明

用户补充的 `Pasted code.py` 是一个可以从 `entity_annotations.json` 生成静态具身空间图文评测集的合成器。新版没有把它作为原始代码备份目录保存，而是改造成正式工具：

- 代码主体进入 `tools/synthesize_static_vlm_benchmark.py`；
- 输入契约进入 `schemas/entity_annotations.schema.json`；
- 模板覆盖矩阵进入 `template_library/executable_template_coverage.csv/json`；
- 设计解释进入 `template_system/08_executable_synthesis_engine.md`；
- 可运行样例进入 `examples/uav_static_demo/`；
- 评分脚本同步增强，支持 ordered list 与 JSON field accuracy。

该整合保留了原代码中的核心生成逻辑：对象过滤、类别/计数/2D 关系/depth/3D/不可答/复杂筛选模板、bbox overlay、generation report、negative category distractor pool、margin-based 去歧义规则。新增部分主要是统一 schema 字段、评分 metric 映射、文档化输入契约和可复现实例。
