---
name: benchmark-evalset-plan-route
description: "Atomic module: stage4 Phase 1 评测蓝图与数据路由。负责先整理能力维度对应的评测集模板、评测指标接口，并将 Stage3 清理后的样本路由到合适的模板和指标；不批量合成评测集，不实现指标代码。Use when user says '规划评测集路由', 'evalset blueprint', 'route stage3 data to eval templates'."
argument-hint: [stage3-dir]
allowed-tools: Bash(*), Read, Write, Edit, Grep, Glob
metadata:
  openclaw:
    emoji: ""
    requires:
      bins: [python3]
---

## `~/benchclaw` 只读约束

- **BENCHCLAW_READONLY = true**：`~/benchclaw/` 只能作为共享只读资源根。
- 严禁在 `~/benchclaw/` 下创建、编辑、覆盖、删除、移动、重命名、复制写入、初始化 git、提交、打 tag、写日志、写缓存或写临时文件。
- 所有派生产物、补丁、快照、报告、脚本、配置、日志和测试输出必须写入 active `WORKSPACE_ROOT`。
- 如必须修改 `~/benchclaw/` 中的资源，只能在 workspace 中生成 patch 或修改建议，等待用户在外部处理；当前 skill 不得直接应用。

## Workspace and File Access Boundary

This skill must operate only inside the current run workspace.

- Before reading or writing any run artifact, resolve and record the active `WORKSPACE_ROOT = ~/bench_workspace/workspace{i}` from the current task, parent stage, or pipeline state.
- Read and write only files under the active `WORKSPACE_ROOT` and the explicitly required global resource roots named by this skill, such as `~/benchclaw/templates/`, `~/benchclaw/model_api/`, or `~/benchclaw/skills/` when explicitly required.
- Never read, list, grep, summarize, compare, copy, or infer from any other `~/bench_workspace/workspace{j}` where `j != i`.
- Outputs must be written only to `~/bench_workspace/workspace{i}/stage4/`.

# Evalset Blueprint And Stage3 Routing

Execute evalset blueprinting and Stage3 sample routing for: **$ARGUMENTS**

This skill is an atomic planning/routing skill. It must not synthesize evalset samples and must not implement metric code.

## Purpose

Stage4 must not begin by blindly generating evalset samples. This skill is the required first step:

- Determine which benchmark capability dimensions exist and what each dimension needs to evaluate.
- Determine which evalset template candidates correspond to each capability dimension.
- Determine which metric interfaces or `metric_id`s are needed for each capability/template pair.
- Self-review every template candidate before publishing it as usable: verify that it matches the user intent, has enough discrimination power, resists shortcut solutions, and maps to the intended capability dimension.
- Route Stage3 cleaned samples to the appropriate `{capability_dimension, template_id, metric_ids}` target.
- Exclude or mark as `needs_review` any Stage3 sample that lacks required fields, confidence evidence, GT/annotation, observation files, or grounding safety.

This skill only declares metric interface requirements. Executable metric implementation belongs to `/benchmark-metric-establish`.

## Inputs

Required:

- `~/bench_workspace/workspace{i}/stage1/CAPABILITY_SCOPE.md`
- `~/bench_workspace/workspace{i}/stage1/EVALSET_PROTOTYPE.md`
- `~/bench_workspace/workspace{i}/stage1/BENCHMARK_DRAFT.md`
- `~/bench_workspace/workspace{i}/stage2/templates/*.yaml`
- `~/bench_workspace/workspace{i}/stage3/final/CLEANED_DATA_SCHEMA.md`
- `~/bench_workspace/workspace{i}/stage3/final/STAGE4_INPUT_MANIFEST.jsonl`
- `~/bench_workspace/workspace{i}/stage3/final/cleaned_data/`

Optional:

- `~/bench_workspace/workspace{i}/stage2/TEMPLATE_REFINEMENT_REPORT.md`
- `~/bench_workspace/workspace{i}/stage3/CLEANING_QUALITY_REPORT.md`

If any required input is missing, stop and report the missing path.

## Procedure

1. Read capability dimensions from `CAPABILITY_SCOPE.md`, including sub-dimensions, operational definitions, coverage requirements, and any required modalities.
2. Read template candidates from `EVALSET_PROTOTYPE.md`, `TEMPLATE_REFINEMENT_REPORT.md`, and `stage2/templates/*.yaml`.
3. For each capability dimension, select compatible template candidates and define:
   - `template_id`
   - required input fields
   - required observation files
   - required GT/annotation fields
   - quality constraints
   - leakage/grounding constraints
   - template self-review result
4. For each template candidate, perform a mandatory template fitness review before it can be routed:
   - User-intent fit: the template evaluates the benchmark goal and user-requested behavior, not a convenient proxy.
   - Discrimination power: the template can separate stronger and weaker models through non-trivial evidence, difficulty variation, and scoring sensitivity.
   - Shortcut resistance: the task cannot be solved by ignoring the image/observation, exploiting answer options, filenames, metadata, scene IDs, template wording, or common priors.
   - Capability alignment: the template's required inputs, expected reasoning, GT fields, and metric interface all correspond to the declared capability dimension.
   - Publish decision: only templates with `template_review.verdict=PASS` may be used for `routing_status=ready`; `FAIL` or `NEEDS_REVIEW` templates must be blocked with explicit reasons.
5. Extract metric interface candidates from Stage1/Stage4 metric drafts, prototype notes, or template declarations. Record `metric_id`, metric family, input fields, GT fields, and scoring object. Do not implement metric code.
6. Read `stage3/final/STAGE4_INPUT_MANIFEST.jsonl` and per-sample metadata from `metadata_json_path`.
7. Route each Stage3 sample to zero, one, or multiple `{capability_dimension, template_id, metric_ids}` targets.
8. A route may be `ready` only if:
   - `stage4_ready_status=ready`
   - `template_review.verdict=PASS`
   - `confidence_status` is acceptable for the target template
   - `confidence_evidence` exists
   - `metadata_json_path`, `final_image_path`, and `record_json_path` exist
   - required input fields and GT/annotation fields exist
   - required observation files exist
   - the route can satisfy grounding and leakage constraints
9. If a sample cannot be routed, write a routing record with `routing_status=excluded` or `routing_status=needs_review` and an explicit `routing_reason`.

## Expected Outputs

- `~/bench_workspace/workspace{i}/stage4/EVALSET_BLUEPRINT.md`
- `~/bench_workspace/workspace{i}/stage4/CAPABILITY_TEMPLATE_METRIC_MAP.json`
- `~/bench_workspace/workspace{i}/stage4/STAGE3_TO_EVALSET_ROUTING.jsonl`

`EVALSET_BLUEPRINT.md` must use this structure:

```markdown
# Evalset Blueprint

## Capability Dimensions
| Capability Dimension | Operational Definition | Required Modalities | Coverage Target |

## Template Candidates
| Template ID | Capability Dimension | Source Template | Required Input Fields | Required GT Fields | Quality Constraints |

## Template Fitness Review
| Template ID | User Intent Fit | Discrimination Power | Shortcut Resistance | Capability Alignment | Verdict | Blocking Issues |

## Metric Interface Candidates
| Metric ID | Capability Dimension | Metric Family | Required Input Fields | Required GT Fields | Scoring Object |

## Stage3 Data Availability
| Source Type | Source Name | Ready Samples | Needs Review | Excluded | Main Blocking Reason |

## Routing Summary
| Capability Dimension | Template ID | Metric IDs | Ready Routes | Needs Review Routes | Excluded Routes |

## Blocking Gaps
| Gap Type | Affected Dimension | Affected Source | Blocking Reason | Suggested Fix |
```

`CAPABILITY_TEMPLATE_METRIC_MAP.json` must be valid JSON:

```json
{
  "capability_dimensions": [
    {
      "capability_dimension": "string",
      "template_ids": ["string"],
      "metric_ids": ["string"],
      "required_input_fields": ["string"],
      "required_gt_fields": ["string"],
      "eligible_source_types": ["simulator", "existing_dataset", "real_data"],
      "quality_constraints": {},
      "template_review": {
        "user_intent_fit": "PASS | FAIL | NEEDS_REVIEW",
        "discrimination_power": "PASS | FAIL | NEEDS_REVIEW",
        "shortcut_resistance": "PASS | FAIL | NEEDS_REVIEW",
        "capability_alignment": "PASS | FAIL | NEEDS_REVIEW",
        "verdict": "PASS | FAIL | NEEDS_REVIEW",
        "blocking_issues": ["string"]
      }
    }
  ]
}
```

`STAGE3_TO_EVALSET_ROUTING.jsonl` must contain one JSON object per non-empty line. Required keys:

- `routing_id`
- `sample_id`
- `source_type`
- `source_name`
- `capability_dimension`
- `template_id`
- `metric_ids`
- `metadata_json_path`
- `final_image_path`
- `record_json_path`
- `confidence_status`
- `confidence_evidence`
- `routing_status`
- `routing_reason`

`routing_status` must be one of `ready`, `needs_review`, or `excluded`.

## Completion Criteria

- [ ] Every capability dimension is mapped to at least one template candidate and metric interface candidate, or has an explicit blocking gap.
- [ ] Every published template candidate has `template_review.verdict=PASS`.
- [ ] Every template was checked for user-intent fit, discrimination power, shortcut resistance, and capability alignment before routing.
- [ ] `CAPABILITY_TEMPLATE_METRIC_MAP.json` is valid JSON and contains required input/GT fields for every mapping.
- [ ] `STAGE3_TO_EVALSET_ROUTING.jsonl` is valid JSONL.
- [ ] Every `ready` route has required paths, confidence evidence, template_id, metric_ids, and required fields.
- [ ] No unroutable sample is silently dropped.

## Rules

- Do not synthesize `EVALSET_DATASET/`.
- Do not implement metric code.
- Do not publish or route with a template unless its template fitness review passes.
- Do not route samples that lack confidence evidence, GT/annotation fields, required observation files, or grounding safety.
- Do not mark a route `ready` solely because a sample exists in Stage3.
- Downstream `/benchmark-evalset-generate` may consume only `routing_status=ready` records.

---

## Fixed Artifact Format Contract

All artifacts produced by this skill have fixed file formats. The format block under `Expected Outputs`, `Output`, `Output Structure`, `Unified Output`, or the nearest equivalent output section is normative, not illustrative.

Mandatory rules:

- Produce every declared artifact at the exact declared path and with the exact declared extension. Do not rename, relocate, split, merge, or substitute artifacts unless this skill explicitly permits it.
- Markdown artifacts (`.md`) must keep the declared top-level title and section heading order exactly. Required tables must keep the declared column names and column order exactly.
- JSON artifacts (`.json`) must be valid UTF-8 JSON with a single top-level object unless this skill explicitly declares a top-level array. Required keys must always be present.
- JSONL artifacts (`.jsonl`) must contain exactly one valid JSON object per non-empty line.
- Before marking the skill complete, perform a format check against this contract and mention any deviation explicitly.
