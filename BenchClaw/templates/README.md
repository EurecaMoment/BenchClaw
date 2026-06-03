
# BenchClaw Stage1/Stage4 统一模板包

这个包不是把 Stage1 和 Stage4 分开堆材料，而是把你给的 **12 个 benchmark 模板卡片、100 条具身空间图文评测模板、4 个 AI2-THOR/qa1 episode 题目与证据链** 整合成一套统一模板系统。

统一逻辑是：

```text
benchmark 参考范式 → 能力维度 → 题目模板 → GT/证据字段 → eval item schema → 指标与质量门
```

- Stage1 使用同一套模板系统来回答：评测什么、为什么这些能力合理、需要什么数据/GT、应该采用哪些题型和指标。
- Stage4 使用同一套模板系统来回答：如何把模板实例化成题目、如何绑定证据、如何生成标准答案、如何自动评分和过滤歧义样本。

## 入口文件

- `SKILL.md`：给大模型/agent 调用的总入口。
- `template_system/00_unified_logic.md`：本包的核心设计逻辑。
- `template_system/01_capability_map.md`：能力维度体系。
- `template_library/templates_100_unified.md`：100 条模板的统一版，保留用户资料中的核心表格并增加统一使用约束。
- `schemas/`：Stage1/Stage4 共用的数据结构约束。
- `examples/ai2thor_qa1_reference_items.jsonl`：由用户 qa1 样例转成的统一 eval item 示例。
- `tools/synthesize_static_vlm_benchmark.py`：可运行的静态具身空间图文评测集合成引擎。
- `tools/score_eval_dataset.py`：可运行的评分脚本，支持 exact/set/numeric/ordered/json 结构化评分。
- `INTEGRATION_AUDIT.md`：说明原资料被吸收到哪些正式文件中。

## 内容规模

- Benchmark 参考卡片：12 个，覆盖 ALFRED, CV-Bench, DriveLM, EmbodiedQA, MME, NuScenesQA, OpenEQA, REVERIE, SQA3D, ScanQA, VSI-Bench, ViewSpatial-Bench。
- 模板库：100 条。
- qa1 参考题：111 条。
- qa1 证据图像：29 张。
- qa1 episode：4 个。

## 使用方式

```bash
cd benchclaw_stage1_stage4_unified_template_pack
python tools/validate_package.py
python tools/synthesize_static_vlm_benchmark.py \
  --input examples/uav_static_demo/sample_0001 \
  --output examples/uav_static_demo/generated_eval_dataset.jsonl \
  --asset-dir examples/uav_static_demo/generated_assets \
  --report examples/uav_static_demo/generated_report.json \
  --max-per-template 2 \
  --seed 7
python tools/score_eval_dataset.py   --gold examples/sample_eval_dataset.jsonl   --pred examples/sample_predictions.jsonl   --out examples/sample_score_report.json
```

新增的合成引擎来自你补充的可运行代码，但已被改造成统一模板包的正式 Stage4 执行组件：它输出统一 eval item schema，同时保留原脚本的兼容字段。详见 `template_system/08_executable_synthesis_engine.md`。

本包刻意没有设置 `source_preserved/`、`raw_from_uploaded_zip/` 等原始资料堆放目录。旧资料中可用的信息已经进入正式模板、参考卡片、schema、示例和审计文件。
