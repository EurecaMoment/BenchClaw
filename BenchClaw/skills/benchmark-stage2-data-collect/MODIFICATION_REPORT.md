# 修改说明：Stage 2 skill 库精简与并行化重构

## 核心修改

1. 将顶层 `benchmark-stage2-data-collect` 改成真正的 phase orchestrator：只负责编排，不替代子 skill 自己发挥。
2. 将 Phase 5 改成 `dispatcher + worker`：
   - `benchmark-batch-collect` 只生成 `source_jobs/*.json`、启动 worker subagent、聚合结果；
   - 新增 `benchmark-source-collect-worker`，每个 subagent 只处理一个 source。
3. 增加机器可读中间契约：
   - `source_inventory.jsonl`
   - `source_plan.jsonl`
   - `template_index.jsonl`
   - `source_jobs/*.json`
   - `source_results/*.json`
   - `status/*.json`
4. 明确并行执行证据：`RAW_DATA_COLLECTION_REPORT.md` 必须写 `Dispatch Summary`、`parallel_mode` 和 `worker_skill`。
5. 精简重复约束，把公共硬约束放在顶层和关键 phase，只在子 skill 保留必要执行契约。
6. 保留原有功能边界：三类数据源、source card 追溯、仿真器新 session、图片/JSON/manifest 一一对应、禁止 placeholder、禁止 Stage 2 清洗过滤。

## 新目录结构

```text
benchmark-stage2-data-collect/
├── SKILL.md
├── 1-benchmark-data-capability-survey/SKILL.md
├── 2-benchmark-collection-guidance/SKILL.md
├── 3-benchmark-template-refinement/SKILL.md
├── 4-benchmark-collect-codegen/SKILL.md
├── 5-benchmark-batch-collect/SKILL.md
├── 5a-benchmark-source-collect-worker/SKILL.md
└── 6-benchmark-unit-test-stage2/SKILL.md
```

## 关键运行路径

```text
Stage 1 artifacts
  ↓
Phase 1 source_inventory.jsonl
  ↓
Phase 2 source_plan.jsonl
  ↓
Phase 3 templates + template_index.jsonl
  ↓
Phase 4 per-source scripts/configs
  ↓
Phase 5 dispatcher creates source_jobs/*.json
  ↓
Phase 5 launches one benchmark-source-collect-worker subagent per source
  ↓
source_results/*.json + collected_data/*
  ↓
Phase 6 contract unit test
  ↓
STAGE2_SUMMARY.md
```
