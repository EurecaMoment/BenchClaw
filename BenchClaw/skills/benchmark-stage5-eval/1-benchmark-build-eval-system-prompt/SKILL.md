---
name: benchmark-build-eval-system-prompt
description: "Atomic module: stage5 Phase 1 评测 Prompt 构建模块。只负责构建传递给被评测模型的 system prompt、制定运行配置、执行冒烟测试验证API 连通性与输出格式合规性，不负责批量推理、打分或报告生成。Use when user says '构建评测 prompt'build eval prompt'准备评测配置'"
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

# Benchmark Build Eval System Prompt

Execute evaluation prompt construction and smoke test for: **$ARGUMENTS**

This skill is an **atomic single-responsibility skill**.
It must **only** do the work scoped to this module.

---

## Purpose

- 本模块负责构建传递给被评测模型的 system prompt，定义输输出格式规范，确保模型输出可被指标算法解析- 本模块制定完整的批量推理运行配置（模型标识、推理参数、并发、重试、超时等）- 本模块执行冒烟测试验证API 连通性、认证有效性与输出格式合规性- 本模块快照模板API 配置，确保评测结果可追溯到具体模型版本- 本模块位Stage 5 第一环节，直接产物是 `EVAL_SYSTEM_PROMPT.md`、`RUN_CONFIG.json`、`MODEL_API_CONFIG.snapshot.json`- 本模块不负责批量推理、指标打分或异常检查
---

## Inputs

- `$ARGUMENTS`：模型标识、API 端点或其他评测配置补充信息- 必需输入->  - `~/bench_workspace/workspace{i}/stage1/BENCHMARK_DRAFT.md` ->评测目标与能力定义  - `~/bench_workspace/workspace{i}/stage1/EVALSET_PROTOTYPE.md` ->原始指令模板（追溯起点）
  - `~/bench_workspace/workspace{i}/stage4/EVALSET_SCHEMA.md` ->评测样本的输GT 字段定义
  - `~/bench_workspace/workspace{i}/stage4/EVALSET_DATASET/` ->评测集数据（抽样 3-5 个样本用于冒烟测试）
  - `~/bench_workspace/workspace{i}/stage4/VALIDATION_REPORT.md` ->verdict 必须PASS
- 可选输入：
  - `MODEL_API_CONFIG.json`（workspace 根目录或 `~/bench_workspace/workspace{i}/stage5/`）模型 API 配置
  - `model_api/` 目录 ->`LOCAL_MODEL_API_AWARE = true`，可从脚本推API 配置
  - `~/bench_workspace/workspace{i}/stage4/METRIC_LIBRARY/interfaces.py` ->验证输出可解析->  - 父流程Constants：`API_CONCURRENCY`、`API_RETRY_COUNT`
- **`~/bench_workspace/workspace{i}/stage4/VALIDATION_REPORT.md` ->verdict 不是 PASS，应立即停止并提示用户先修复 Stage 4*
- **若其他必需输入缺失，应立即停止并报告缺失文件*
- **若模板API 配置既无 `MODEL_API_CONFIG.json` 也无 `model_api/` 可推导，应立即停止并提示用户提供模型 API 配置*

---

## Procedure

### Step 1: 构建评测 system prompt

1. 读取 `BENCHMARK_DRAFT.md` 中的评测目标和能力定义2. 读取 `EVALSET_PROTOTYPE.md` 中的原始指令模板作为基准3. 读取 `EVALSET_SCHEMA.md` 获取输入字段格式GT 字段格式4. 构建 system prompt，包含：
   - **任务描述**：模型需要完成什么任->   - **输入格式说明**：模型将接收到的数据格式
   - **输出格式约束**：模型必须遵守的输出格式（确保可选`METRIC_LIBRARY/` 解析->   - **约束条件**：不得使用的信息、时间限制等（若适用5. 定义 **Output Parsing Rules**：如何从模型原始输出中提取可评分的结构化结果6. 对照 `EVALSET_PROTOTYPE.md` 中的原始指令模板，记录所有偏差与调整理由
### Step 2: 制定运行配置

7. 确定模型标识API endpoint（从 `MODEL_API_CONFIG.json` ->`model_api/` 推导）8. 定义推理参数（temperature、max_tokens、top_p、seed 等）9. 配置并发控制（`API_CONCURRENCY`）、重试策略（`API_RETRY_COUNT`、退避方式）、超时设置10. 快照完整的模板API 配置，附时间戳11. 输出 `RUN_CONFIG.json` ->`MODEL_API_CONFIG.snapshot.json`
### Step 3: Prompt 冒烟测试

12. ->`EVALSET_DATASET/` 中抽3-5 个样本（覆盖不同维度和难度）13. 用构建的 system prompt + 样本输入调用模型 API14. 验证->    - API 连通性与认证有效->    - 模型输出格式是否符合输出格式约束
    - 输出是否可被 Output Parsing Rules 解析为结构化结果
    - 解析后的结果是否可被 `METRIC_LIBRARY/interfaces.py`（若可用）接15. 记录每个测试样本的结果16. 若冒烟测试失败，标注失败原因（API / 格式 / 解析），建议调整方向
### Step 4: 校验

17. 确认 system prompt 不含 GT 信息、评分标准或指标计算方式泄露18. 确认 `RUN_CONFIG.json` 中的 `evalset_path` 指向正确的评测集目录19. 确认 `MODEL_API_CONFIG.snapshot.json` 已生成功
---

## Expected Outputs

- `~/bench_workspace/workspace{i}/stage5/EVAL_SYSTEM_PROMPT.md`
- `~/bench_workspace/workspace{i}/stage5/RUN_CONFIG.json`
- `~/bench_workspace/workspace{i}/stage5/MODEL_API_CONFIG.snapshot.json`

`EVAL_SYSTEM_PROMPT.md` 结构
```markdown
# Evaluation System Prompt

## Lineage
- Source: `~/bench_workspace/workspace{i}/stage1/BENCHMARK_DRAFT.md` § Motivation + § Eval-Set Design
- Instruction template base: `~/bench_workspace/workspace{i}/stage1/EVALSET_PROTOTYPE.md` § Task Prototypes
- Deviations from prototype: [变更列表与理由]

## System Prompt
[完整system prompt 文本]

## Input Format Specification
[传递给模型的输入数据格式说明]

## Output Format Specification
[模型必须遵守的输出格式]

## Output Parsing Rules
[如何从模型原始输出中提取可评分的结构化结果]

## Smoke Test Results
| Sample ID | API Status | Output Format Valid | Parseable by Metric Library |
|-----------|-----------|--------------------|-----------------------------|
| ...       | ...       | ...                | ...                         |
```

`RUN_CONFIG.json` 结构
```json
{
  "model": "{model_identifier}",
  "endpoint": "{api_endpoint}",
  "inference_params": {
    "temperature": 0.0,
    "max_tokens": 4096,
    "top_p": 1.0,
    "seed": 42
  },
  "concurrency": 5,
  "retry": {
    "max_attempts": 3,
    "backoff": "exponential",
    "base_delay_seconds": 2
  },
  "timeout_seconds": 120,
  "evalset_path": "../stage4/EVALSET_DATASET/",
  "output_path": "RAW_MODEL_OUTPUTS.jsonl"
}
```

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

- [ ] `~/bench_workspace/workspace{i}/stage5/EVAL_SYSTEM_PROMPT.md` 存在且包含完整的 System Prompt、Input/Output Format Specification、Output Parsing Rules ->Smoke Test Results- [ ] System prompt 不含 GT 信息、评分标准或指标计算方式- [ ] Lineage 章节记录了与 `EVALSET_PROTOTYPE.md` 的所有偏差及理由- [ ] `~/bench_workspace/workspace{i}/stage5/RUN_CONFIG.json` 存在且所有字段合法- [ ] `~/bench_workspace/workspace{i}/stage5/MODEL_API_CONFIG.snapshot.json` 存在且附时间戳- [ ] 冒烟测试至少3 个样本执行完毕，结果已记录（无论通过与否）- [ ] ->Stage 4 verdict ->PASS 或必需输入缺失，不得标记完成功
---

## Rules

- 不执行批量推理——那Phase 2 的职责。冒烟测试仅3-5 个样本- 不计算指标分数或生成评测报告——那Phase 3 ->Phase 4 的职责- 不擅自改写任Stage 1 ->Stage 4 产出- Prompt 不得泄露 GT——system prompt 中不得包GT 答案、评分标准或指标计算方式，这是硬性安全约束- API 配置必须快照——`MODEL_API_CONFIG.snapshot.json` 是评测可追溯性的关键证据，不可省略- 冒烟测试失败不阻塞产出生成——仍应写入所有文件，但在 Smoke Test Results 中明确标注失败项，由统筹 skill 决定是否回退到- 出错时必须明确指出阻塞原因（API 不可达、认证失效、模型不支持指定参数）- 如果 Write 因文件过大失败，立即 fallback ->Bash 分块写入，不要询问用户许可选
---

## Downstream Handoff

- `benchmark-call-model-api` 读取 `~/bench_workspace/workspace{i}/stage5/EVAL_SYSTEM_PROMPT.md` ->`~/bench_workspace/workspace{i}/stage5/RUN_CONFIG.json` 执行批量推理由- `benchmark-check-scores` 读取 `~/bench_workspace/workspace{i}/stage5/EVAL_SYSTEM_PROMPT.md` 进行污染检查（检查GT 泄露信号）- 本模块只写交接关系，不调度下游模块