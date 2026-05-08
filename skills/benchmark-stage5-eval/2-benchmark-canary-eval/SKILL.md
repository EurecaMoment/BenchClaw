---
name: benchmark-canary-eval
description: "Atomic module: Stage 5 灰度/金丝雀评测。只负责在全量评测前运行小规模代表性样本，验证 API、prompt、schema、metric、成本和结果稳定性，不负责全量推理、不负责修改评测集或修复上游 stage。Use when user says '灰度评测'canary eval'全量评测前先小跑'."
argument-hint: [stage5-dir-or-run-config]
allowed-tools: Bash(*), Read, Write, Edit, Grep, Glob
metadata:
  openclaw:
    emoji: ""
    requires:
      bins: [python3]
---


## Workspace and File Access Boundary

This skill must operate only inside the current run workspace.

- Before reading or writing any run artifact, resolve and record the active `WORKSPACE_ROOT = ~/bench_workspace/workspace{i}` from the current task, parent stage, or pipeline state.
- Read and write only files under the active `WORKSPACE_ROOT` and the explicitly required global resource roots named by this skill, such as `~/benchclaw/simulator_cards/`, `~/benchclaw/dataset_cards/`, `~/benchclaw/realdata_cards/`, `~/benchclaw/templates/`, `~/benchclaw/model_api/`, `~/benchclaw/data-juicer_card/`, `~/benchclaw/annotation-tool/`, or `~/benchclaw/skills/` when the current skill explicitly requires them.
- Never read, list, grep, summarize, compare, copy, or infer from any other `~/bench_workspace/workspace{j}` where `j != i`, even if the current artifact is missing or another workspace appears newer or more complete.
- Never scan broad server directories such as `~`, `/`, `/home`, `/mnt`, `/data`, `/tmp`, `C:\Users`, `C:\`, or arbitrary project/download folders to discover context. Only inspect the exact current workspace paths and exact allowlisted resource roots needed for this skill.
- If an expected input is missing from the active workspace or an allowlisted resource root, stop and report the missing path. Do not search unrelated folders or borrow replacement artifacts from another workspace.
- Outputs must be written only to the active `WORKSPACE_ROOT` paths declared by this skill. Do not mirror or cache run artifacts into other workspaces or unrelated server folders.
- If the user explicitly provides an external path, use it only when it is directly relevant to this skill, record it as a user-provided exception, and do not expand access to sibling or parent directories.

This boundary overrides convenience behaviors such as auto-discovery, resume from latest workspace, reuse of previous artifacts, broad recursive grep/list, and fallback search.

# Benchmark Canary Evaluation

Run a gray/canary evaluation before full-scale Stage 5 evaluation for: **$ARGUMENTS**

This skill is an **atomic single-responsibility skill**. It must only execute a bounded canary run and produce a clear go/no-go verdict.

---

## Purpose

- 本模块负责在全量评测前对少量代表性样本执行灰度评测，提前发现 prompt、API、schema、metric、GT 泄露、成本和稳定性问题- 本模块位Stage 5 的全量评测之前，直接产物`~/bench_workspace/workspace{i}/stage5/CANARY_EVAL_REPORT.md`- 本模块不负责全量评测、不负责修改 Stage 1-4 产物、不负责根因修复
---

## Inputs

- `$ARGUMENTS`：Stage 5 目录、模板API 配置或运行配置- 必需输入->  - `~/bench_workspace/workspace{i}/stage5/EVAL_SYSTEM_PROMPT.md`
  - `~/bench_workspace/workspace{i}/stage5/RUN_CONFIG.json`
  - `~/bench_workspace/workspace{i}/stage5/MODEL_API_CONFIG.snapshot.json`
  - `~/bench_workspace/workspace{i}/stage4/EVALSET_DATASET/`
  - `~/bench_workspace/workspace{i}/stage4/EVALSET_SCHEMA.md`
  - `~/bench_workspace/workspace{i}/stage4/METRIC_LIBRARY/`
  - `~/bench_workspace/workspace{i}/stage4/METRIC_SPEC.md`
  - `~/bench_workspace/workspace{i}/stage4/SCORING_RULES.md`
  - `~/bench_workspace/workspace{i}/stage4/STAGE4_UNIT_TEST_REPORT.md`，verdict 应为 PASS 或带明确 waiver- 可选输入：
  - `~/bench_workspace/workspace{i}/stage5/CANARY_POLICY.json`
  - `~/bench_workspace/workspace{i}/stage5/CANARY_SAMPLE_MANIFEST.jsonl`

若任一必需输入缺失，立即写入FAIL 报告，不得继续调用模板API
---

## Canary Policy

默认灰度策略
```json
{
  "sample_ratio": 0.02,
  "min_samples": 20,
  "max_samples": 200,
  "stratify_by": ["capability_dimension", "difficulty", "simulator", "task_type"],
  "api_failure_threshold": 0.03,
  "parse_failure_threshold": 0.02,
  "metric_runtime_failure_threshold": 0.00,
  "gt_leakage_threshold": 0.00,
  "cost_budget_ratio": 0.05,
  "repeatability_trials": 2
}
```

若用户或 `CANARY_POLICY.json` 指定其他阈值，以显式指定为准，但必须写入报告
---

## Procedure

1. **加载配置**：读`EVAL_SYSTEM_PROMPT.md`、`RUN_CONFIG.json`、模型快照和 Stage 4 评测集schema2. **抽取灰度样本**：从 `EVALSET_DATASET/manifest.json` 中按能力维度、难度、仿真器、任务类型分层抽样；写入 `~/bench_workspace/workspace{i}/stage5/CANARY_SAMPLE_MANIFEST.jsonl`3. **执行灰度推理**：仅对灰度样本调用模板API；记录请求、响应、延迟、重试、解析结果和错误类型4. **运行灰度指标**：调`METRIC_LIBRARY/` 对灰度输出打分，检查指标运行、聚合结果和异常分布5. **执行泄露与格式检查*：检查输出中是否出现 GT 答案、评分公式、内部路径、不可暴metadata 或模板痕迹6. **评估稳定义*：对代表性小子集重复调用，比较解析成功率和分数波动7. **形成 verdict**->   - `PASS`：可以进入全量评测集   - `FAIL`：不得进入全量评测，必须调用 `/benchmark-canary-localize-rollback`->   - `NEEDS_REVIEW`：需要用户确waiver 或降低风险后才能进入全量评测集8. **写入报告**：生成`CANARY_EVAL_REPORT.md`、`CANARY_METRICS.json`、`CANARY_RAW_OUTPUTS.jsonl`、`CANARY_VERDICT.json`
---

## Expected Outputs

- `~/bench_workspace/workspace{i}/stage5/CANARY_SAMPLE_MANIFEST.jsonl`
- `~/bench_workspace/workspace{i}/stage5/CANARY_RAW_OUTPUTS.jsonl`
- `~/bench_workspace/workspace{i}/stage5/CANARY_METRICS.json`
- `~/bench_workspace/workspace{i}/stage5/CANARY_VERDICT.json`
- `~/bench_workspace/workspace{i}/stage5/CANARY_EVAL_REPORT.md`

`CANARY_EVAL_REPORT.md` 必须包含
```markdown
# Canary Evaluation Report

**Verdict**: PASS | FAIL | NEEDS_REVIEW
**Sample policy**: [ratio/min/max/strata]
**Model**: [model identifier + snapshot]

## Summary
- Samples tested: [N]
- API success rate: [...]
- Parse success rate: [...]
- Metric runtime pass rate: [...]
- GT leakage findings: [...]
- Estimated full-eval cost/time: [...]

## Failure Table
| Failure Type | Count | Rate | Example Sample IDs | Likely Owner |
|--------------|-------|------|--------------------|--------------|
| API/auth | ... | ... | ... | Stage 5 prompt/API |
| output_parse | ... | ... | ... | Stage 5 prompt or Stage 4 schema |
| metric_runtime | ... | ... | ... | Stage 4 metric |
| schema_mismatch | ... | ... | ... | Stage 4 evalset/schema |
| bad_gt | ... | ... | ... | Stage 2/3 data |
| task_mismatch | ... | ... | ... | Stage 1/4 design |

## Go/No-Go Decision
- Full-scale evaluation allowed: yes/no
- Required next skill if no: `/benchmark-canary-localize-rollback`
```

---

## Completion Criteria

- [ ] Canary sample manifest exists and is stratified.
- [ ] Canary raw outputs and metrics are written.
- [ ] `CANARY_VERDICT.json` is valid JSON and contains `verdict`, `blocking_failures`, and `recommended_next_skill`.
- [ ] No full-scale model inference is launched by this skill.
- [ ] FAIL verdict explicitly blocks `/benchmark-call-model-api` full-run execution.

---

## Rules

- 严禁在灰度失败时继续全量评测集- 严禁修改 Stage 1-4 产物来“绕过”灰度失败- 灰度样本必须覆盖每个核心能力维度；覆盖不到的维度必须列为 blocking risk ->waiver- 如果 Write 因文件过大失败，立即 fallback ->Bash 分块写入
---

## Downstream Handoff

- `benchmark-stage5-eval` 读取 `CANARY_VERDICT.json` 判断是否进入 `/benchmark-call-model-api`- `/benchmark-canary-localize-rollback` 读取 `CANARY_EVAL_REPORT.md` ->`CANARY_METRICS.json` 定位回退目标- Stage 6 读取灰度报告评估流程前置质量门是否有效