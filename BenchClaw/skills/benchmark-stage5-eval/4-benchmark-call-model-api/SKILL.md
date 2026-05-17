---
name: benchmark-call-model-api
description: "Atomic module: stage5 Phase 2 批量模型推理模块。只负责按运行配置遍历评测集、调用模板API、解析原始输出、记录推理日志并支持断点续跑，不负责 prompt 构建、指标打分或异常检查。Use when user says '批量推理'call model API'跑模板执行推理'"
argument-hint: [model-api-config]
allowed-tools: Bash(*), Read, Write, Edit, Grep, Glob
metadata:
  openclaw:
    emoji: ""
    requires:
      bins: [python3]
---

## `BENCHCLAW_ROOT` 只读约束

- **BENCHCLAW_READONLY = true**：`BENCHCLAW_ROOT/` 只能作为 BenchClaw 仓库内共享只读资源根，必须从当前 skill 所在的 BenchClaw 仓库位置解析，不能依赖固定 home 路径或机器绝对路径。
- 严禁在 `BENCHCLAW_ROOT/` 下创建、编辑、覆盖、删除、移动、重命名、复制写入、初始化 git、提交、打 tag、写日志、写缓存或写临时文件。
- 所有派生产物、补丁、快照、报告、脚本、配置、日志和测试输出必须写入 active `WORKSPACE_ROOT`。
- 如必须修改 `BENCHCLAW_ROOT/` 中的资源，只能在 workspace 中生成 patch 或修改建议，等待用户在外部处理；当前 skill 不得直接应用。


## Workspace and File Access Boundary

This skill must operate only inside the current run workspace.

- Before reading or writing any run artifact, resolve and record the active `WORKSPACE_ROOT = ~/bench_workspace/workspace{i}` from the current task, parent stage, or pipeline state.
- Read and write only files under the active `WORKSPACE_ROOT` and the explicitly required global resource roots named by this skill, such as `BENCHCLAW_ROOT/simulatorCards/`, `BENCHCLAW_ROOT/benchmarkDatasetCards/`, `BENCHCLAW_ROOT/realdata_cards/`, `BENCHCLAW_ROOT/templates/`, `BENCHCLAW_ROOT/model_api/`, `BENCHCLAW_ROOT/data-juicer_card/`, `BENCHCLAW_ROOT/annotation-tool/`, or `BENCHCLAW_ROOT/skills/` when the current skill explicitly requires them.
- Never read, list, grep, summarize, compare, copy, or infer from any other `~/bench_workspace/workspace{j}` where `j != i`, even if the current artifact is missing or another workspace appears newer or more complete.
- Never scan broad server directories such as `~`, `/`, `/home`, `/mnt`, `/data`, `/tmp`, `C:\Users`, `C:\`, or arbitrary project/download folders to discover context. Only inspect the exact current workspace paths and exact allowlisted resource roots needed for this skill.
- If an expected input is missing from the active workspace or an allowlisted resource root, stop and report the missing path. Do not search unrelated folders or borrow replacement artifacts from another workspace.
- Outputs must be written only to the active `WORKSPACE_ROOT` paths declared by this skill. Do not mirror or cache run artifacts into other workspaces or unrelated server folders.
- If the user explicitly provides an external path, use it only when it is directly relevant to this skill, record it as a user-provided exception, and do not expand access to sibling or parent directories.

This boundary overrides convenience behaviors such as auto-discovery, resume from latest workspace, reuse of previous artifacts, broad recursive grep/list, and fallback search.

# Benchmark Call Model API

Execute batch model inference for: **$ARGUMENTS**

This skill is an **atomic single-responsibility skill**.
It must **only** do the work scoped to this module.

---

## Purpose

- 本模块负责遍历评测集全部样本，按运行配置调用模型 API，获取并解析模型输出- 本模块实现并发控制、失败重试、断点续跑、实时进度监控与推理结果汇总- 本模块位Stage 5 第二环节，直接产物是 `RAW_MODEL_OUTPUTS.jsonl`- 本模块不负责 prompt 构建、指标打分、异常检查或报告生成功
---

## Inputs

- `$ARGUMENTS`：推理执行的补充要求（如指定仅推理特定维度、限制样本范围）- 必需输入->  - `~/bench_workspace/workspace{i}/stage5/EVAL_SYSTEM_PROMPT.md` ->system prompt、输输出格式规范、Output Parsing Rules
  - `~/bench_workspace/workspace{i}/stage5/RUN_CONFIG.json` ->运行配置（模型、endpoint、推理参数、并发、重试、超时）
  - `~/bench_workspace/workspace{i}/stage4/EVALSET_DATASET/` ->评测集数据- 可选输入：
  - `~/bench_workspace/workspace{i}/stage5/MODEL_API_CONFIG.snapshot.json` ->API 配置快照（用于验证一致性）
  - `~/bench_workspace/workspace{i}/stage5/resume_state.json` ->断点续跑状态文件（若存在则从上次进度恢复）
  - 父流程Constants：`API_FAILURE_THRESHOLD`、`API_CONCURRENCY`、`API_RETRY_COUNT`
- **若任一必需输入缺失，应立即停止并报告缺失文件*

---

## Procedure

### Step 1: 初始化推理环境
1. 读取 `RUN_CONFIG.json` 获取模型标识、endpoint、推理参数、并发设置、重试策略2. 读取 `EVAL_SYSTEM_PROMPT.md` 获取 system prompt 文本、输入格式规范、Output Parsing Rules3. 扫描 `EVALSET_DATASET/manifest.json` 获取全部样本 ID 列表4. ->`resume_state.json` 存在，从中恢复已完成的样本列表，跳过已成功的样本
### Step 2: 批量推理执行

5. 遍历所有待推理样本，对每个样本->   - ->`Input Format Specification` 组装 API 请求（system prompt + 样本输入数据->   - 调用模型 API
   - 记录 API 状态码和延->   - ->`Output Parsing Rules` 将原始输出解析为结构化结构   - 标记解析成功/失败
6. 并发控制：按 `API_CONCURRENCY` 限制同时请求数据7. 失败处理由   - API 调用失败 ->`API_RETRY_COUNT` 和退避策略重跑   - 重试耗尽 ->标记`api_failed`，记录错误信息   - 输出解析失败 ->标记`parse_failed`，保留原始输8. 断点续跑：每完成一批样本（或定期），将进度写入 `resume_state.json`
### Step 3: 推理过程监控

9. 实时统计（可周期性输出到日志）：
   - 完成率：已完成/ 总样本数
   - 成功率：API 成功 / 已完成   - 输出格式合规率：解析成功 / API 成功
   - 平均延迟
10. 若失败率超过 `API_FAILURE_THRESHOLD`，暂停推理并在产出中标记 `[PAUSED: failure rate exceeded]`
### Step 4: 推理结果汇
11. 将所有样本的推理结果写入 `RAW_MODEL_OUTPUTS.jsonl`（每行一个样本）12. 在文件末尾或单独统计段记录推理摘要：总样本数、成功数、失败数、格式错误数、平均延迟、总耗时
### Step 5: 校验

13. 确认 `RAW_MODEL_OUTPUTS.jsonl` 中的样本= `manifest.json` 中的总样本数（含失败样本）14. 确认每条记录包含完整的必需字段
---

## Expected Outputs

- `~/bench_workspace/workspace{i}/stage5/RAW_MODEL_OUTPUTS.jsonl`

每行一个样本：

```json
{
  "sample_id": "dim1_sample_001",
  "dimension": "dimension_1",
  "difficulty": "medium",
  "api_status": 200,
  "latency_ms": 1523,
  "retry_count": 0,
  "raw_output": "...",
  "parsed_output": { "..." },
  "parse_success": true,
  "eval_status": "success",
  "error_message": null,
  "timestamp": "2026-04-23T10:30:00Z"
}
```

`eval_status` 取值：`success`（API 成功 + 解析成功）、`parse_failed`（API 成功但解析失败）、`api_failed`（API 调用最终失败）
---

---

## Fixed Artifact Format Contract

All artifacts produced by this skill have fixed file formats. The format block under `Expected Outputs`, `Output`, `Output Structure`, `Unified Output`, or the nearest equivalent output section is normative, not illustrative.

Mandatory rules:

- Produce every declared artifact at the exact declared path and with the exact declared extension. Do not rename, relocate, split, merge, or substitute artifacts unless this skill explicitly permits it.
- Markdown artifacts (`.md`) must keep the declared top-level title and section heading order exactly. Required tables must keep the declared column names and column order exactly. If a value is unknown, write `UNKNOWN`; if it is not applicable, write `N/A`; do not omit the row, section, or column.
- JSON artifacts (`.json`) must be valid UTF-8 JSON with a single top-level object unless this skill explicitly declares a top-level array. Required keys must always be present. Use `null`, `[]`, or `{}` for empty values instead of deleting keys.
- JSONL artifacts (`.jsonl`) must contain exactly one valid JSON object per non-empty line. Every line must share the same required key set declared by this skill or by the upstream schema.
- CSV/TSV artifacts must include a header row. Header names and order are fixed. Quote fields when needed and keep one logical record per row.
- YAML artifacts must be parseable YAML and must preserve the declared top-level keys. Generated config YAML must include enough comments or companion fields to trace each operator, field, or rule back to the source artifact named by this skill.
- Directory artifacts must contain the declared files plus a `MANIFEST.json` or `manifest.jsonl` when the skill declares one. The manifest must enumerate relative paths, artifact type, source_type/source_name when applicable, producer skill name, and creation timestamp.
- Validation or gate reports must include a fixed `verdict` value from `PASS`, `FAIL`, `WARNING`, `BLOCKED`, or `NEEDS_REVIEW`, plus `checked_artifacts`, `blocking_issues`, and `next_action` sections or keys.
- Handoff artifacts consumed by downstream skills must be backward-compatible: add optional fields only under an `extras` section/key, never by changing or deleting required fields.
- Before marking the skill complete, perform a format check against this contract and mention any deviation explicitly in the completion or gate report.

## Completion Criteria

- [ ] `~/bench_workspace/workspace{i}/stage5/RAW_MODEL_OUTPUTS.jsonl` 存在且非空- [ ] 文件中的样本数等`EVALSET_DATASET/manifest.json` 中的总样本数据- [ ] 每条记录包含 sample_id、dimension、difficulty、api_status、latency_ms、raw_output、parsed_output、parse_success、eval_status、timestamp 字段- [ ] 失败率（`api_failed` 占比）已记录，若超过 `API_FAILURE_THRESHOLD` 则文件中`[PAUSED]` 标记- [ ] 若存在断点续跑，`resume_state.json` 已更新- [ ] 若必需输入缺失，不得标记完成功
---

## Rules

- 不构建或修改 system prompt——那Phase 1 的职责- 不计算指标分数——那Phase 3 的职责- 不生成评测报告或执行异常检查——那Phase 4 的职责- 不擅自改`EVAL_SYSTEM_PROMPT.md`、`RUN_CONFIG.json` 或任何上游产出- 推理必须可断点续跑——中断后可从 `resume_state.json` 恢复，不可要求从头重跑- 不可丢弃失败样本——`api_failed` ->`parse_failed` 的样本必须保留在输出文件中，由下phase 处理由- 原始输出必须完整保留——`raw_output` 字段存储模型原始返回，不可在本阶段裁剪或后处理由- 失败率超阈值时暂停而非终止——标`[PAUSED]` 并保留已完成的结果，由统skill 决定后续操作- 出错时必须明确指出阻塞原因（API 不可达、认证过期、模型端限流、磁盘空间不足）- 如果 Write 因文件过大失败，立即 fallback ->Bash 分块写入，不要询问用户许可选
---

## Downstream Handoff

- `benchmark-run-metrics` 读取 `~/bench_workspace/workspace{i}/stage5/RAW_MODEL_OUTPUTS.jsonl` ->`parse_success = true` 的样本进行打分- `benchmark-check-scores` 读取 `~/bench_workspace/workspace{i}/stage5/RAW_MODEL_OUTPUTS.jsonl` 进行异常响应检查与污染检查- 本模块只写交接关系，不调度下游模块