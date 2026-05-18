# BenchClaw

BenchClaw is an Agent Skill workflow library for benchmark design, dataset construction, evaluation, and maintenance. It is not a traditional application or Python package. Instead, it provides a structured set of Skill contracts, task templates, capability cards, and quality gates that can be used by Codex/OpenCode-style agents to manufacture benchmark assets in a reproducible and auditable way.

The goal is to turn a rough benchmark idea into a traceable evaluation pipeline: target definition, data collection, evidence compilation, eval-set construction, and model evaluation are organized as fixed stages with fixed artifacts and explicit review gates.

## Core Capabilities

- Five-stage benchmark manufacturing workflow: draft design, raw data collection, evidence compilation, eval-set construction, and model evaluation.
- Layered Skill system: each stage has an orchestrator `SKILL.md`, and each stage is decomposed into smaller atomic sub-skills.
- 48 reference task templates for embodied, spatial, navigation, dynamics, active perception, autonomous driving, and quality-audit tasks.
- Capability cards for simulators, datasets, real-world data sources, Data-Juicer, and annotation tools.
- Quality gates across the full process: each stage produces summaries, reports, and a gate verdict before the next stage can proceed.
- Workspace isolation and lineage tracking: generated artifacts live in an active workspace, while this repository acts as a read-only resource library.

## Repository Layout

```text
.
|-- skills/
|   |-- benchmark-pipeline/
|   |-- benchmark-stage1-draft/
|   |-- benchmark-stage2-data-collect/
|   |-- benchmark-stage3-evidence-compiler/
|   |-- benchmark-stage4-build/
|   `-- benchmark-stage5-eval/
|-- templates/
|-- simulatorCards/
|-- dataset_cards/
|-- realdata_cards/
|-- data-juicer_card/
|-- annotation-tool/
`-- LICENSE
```

## Skills

The `skills/` directory is the core of BenchClaw. It contains one top-level pipeline orchestrator and five stage orchestrators.

| Skill | Purpose |
|---|---|
| `benchmark-pipeline` | Coordinates the Stage1→Stage5 serial workflow, creates or inherits the workspace, passes stage inputs, and enforces stage handoff checks. |
| `benchmark-stage1-draft` | Turns a benchmark idea into target definition, literature review, capability scope, data-source mapping, eval-set prototype, benchmark draft, and execution plan. |
| `benchmark-stage2-data-collect` | Collects, ingests, or registers raw data based on Stage 1 artifacts. It must not clean, filter, reject, or quality-screen accessible samples. |
| `benchmark-stage3-evidence-compiler` | Normalizes Stage 2 sources, runs cleaning and semi-supervised evidence compilation, and preserves source-aware GT provenance. |
| `benchmark-stage4-build` | Builds the formal eval set, metric library, scoring rules, ground-truth references, and validation reports. |
| `benchmark-stage5-eval` | Runs evaluation and produces model-level and dimension-level reports from the Stage 4 benchmark artifact pack. |

Each stage directory also contains numbered sub-skills. For example, Stage 1 includes `00-idea-intake`, `09-initial-template-metric-set`, and `13-execution-plan`; Stage 5 includes `38-evaluation-run` and `39-evaluation-report`.

## Reference Templates

The `templates/` directory contains a lightweight library of 48 JSON task templates:

- `templates/_index.json`: template inventory, version, family list, and file list.
- `templates/_README.md`: field definitions and usage notes.
- `01_*.json` through `48_*.json`: reference templates across families such as `egocentric_spatial`, `counterfactual_egomotion`, `navigation_topology`, `spatial_memory`, `dynamics`, `semantic_affordance`, `active_perception`, `carla_driving`, and `quality_audit`.

These templates are references for designing benchmark-specific task types. They are not the final eval-set schema. Ground truth should be derived from simulator state, geometry, navigation state, rendering outputs, trajectory data, or verified annotations, not generated directly by an LLM.

## Capability Cards

Capability cards are read-only evidence sources used by the Skills when choosing data sources, planning collection, or generating tool calls.

### Simulators

`simulatorCards/` currently includes:

- `CARLA/`
- `HABITAT/`
- `LIBERO/`

These cards document simulator paths, environments, supported observation modalities, action spaces, task types, APIs, startup commands, data collection methods, and common failure modes.

### Datasets And Real Data

`dataset_cards/` currently includes:

- `ERQA.md`

The ERQA card describes a multimodal QA dataset for real-world scenes, with emphasis on multi-image visual understanding, spatial reasoning, short-answer QA, and embodied perspective reasoning.

`realdata_cards/` is reserved for future real-data source cards. It should be used to document collection batches, authorization status, privacy constraints, metadata schemas, and annotation gaps.

### Data-Juicer

`data-juicer_card/DATAJUICER_AGENT_CAPABILITY_SPEC.md` explains how an Agent should decide when to use Data-Juicer, generate YAML configs, choose operators, run small canary jobs, inspect traces and stats, and produce cleaning reports. It mainly supports Stage 3.

### Annotation Tools

`annotation-tool/` contains tool-entry placeholders and smoke-test scripts:

- `depthanything3/start_backend.sh`
- `sam3/test.sh`
- `yoloe/test.sh`

Generated outputs from these tools should be written to the active workspace, not back into this repository.

## Five-Stage Workflow

```text
/benchmark-stage1-draft
-> /benchmark-stage2-data-collect
-> /benchmark-stage3-evidence-compiler
-> /benchmark-stage4-build
-> /benchmark-stage5-eval
-> BENCHMARK_PIPELINE_REPORT.md
```

| Stage | Input | Main Outputs | Gate Focus |
|---|---|---|---|
| Stage 1: Draft | Benchmark idea | `IDEA_TARGET.md`, `LITERATURE_REVIEW.md`, `CAPABILITY_SCOPE.md`, `DATA_SOURCE_MAPPING.md`, `EVALSET_PROTOTYPE.md`, `BENCHMARK_DRAFT.md`, `EXECUTION_PLAN.md` | Target, capability scope, data-source mapping, and eval prototype are coherent. |
| Stage 2: Collect | Stage 1 artifacts | `SOURCE_CAPABILITY_SURVEY.md`, `COLLECTION_GUIDANCE_PLAN.md`, `DATA_SCHEMA.md`, `collected_data/`, `RAW_DATA_COLLECTION_REPORT.md` | Raw-only collection, no placeholder data, no old-data reuse, one image to one JSON record. |
| Stage 3: Evidence | Stage 2 raw data | `18-real-image-semi-supervised-gt/`, `19-benchmark-image-semi-supervised-gt/`, `20-simulator-clean-gt-pack/` | Source-aware cleaning, semi-supervised candidates, official labels, and simulator GT remain traceable. |
| Stage 4: Build | Stage 3 evidence and Stage 1 templates | `37-benchmark-artifact-pack/EVALSET_DATASET/`, `FINAL_BENCHMARK_CARD.md`, `STAGE4_REPORT.md` | Dataset structure, GT references, metric execution, and scoring rules are reproducible. |
| Stage 5: Evaluate | Stage 4 benchmark artifact pack | `38-evaluation-run/`, `39-evaluation-report/` | No fabricated predictions, raw outputs retained, only Stage 4 metrics and logged predictions are used. |

## Quick Start

In an Agent environment that supports Skill invocation, start with the top-level pipeline:

```text
/benchmark-pipeline "your benchmark idea"
```

You can also run a single stage directly:

```text
/benchmark-stage1-draft "your benchmark idea"
/benchmark-stage2-data-collect "$WORKSPACE_ROOT/stage1"
/benchmark-stage3-evidence-compiler "$WORKSPACE_ROOT/stage2"
/benchmark-stage4-build "$WORKSPACE_ROOT/stage3"
/benchmark-stage5-eval "$WORKSPACE_ROOT/stage4"
```

Using `benchmark-pipeline` is recommended because it creates and passes a consistent `WORKSPACE_ROOT`, then stops at each major stage boundary to show the summary, gate verdict, key artifacts, blocking issues, and next-step options.

## Workspace Convention

BenchClaw treats this repository as a shared read-only resource root during benchmark runs. Generated run artifacts should be written to an isolated workspace:

```text
WORKSPACE_ROOT/
|-- stage1/
|-- stage2/
|-- stage3/
|-- stage4/
`-- stage5/
```

Key rules:

- A new pipeline run creates a new incrementing workspace by default.
- Downstream stages must inherit the exact same `WORKSPACE_ROOT` from upstream stages.
- A stage must not auto-discover, copy, or borrow artifacts from another `workspace{j}` unless the user explicitly provides that path and reuse scope.
- `BENCHCLAW_ROOT` should be used as read-only reference material.
- Reports, generated scripts, temporary files, patches, logs, caches, model outputs, and evaluation results belong in the active workspace.

## Quality Gates

Common gate verdicts:

```text
PASS          The stage is eligible to proceed, but the user still chooses the next step.
NEEDS_REVIEW  The stage has explainable gaps and needs a waiver or revision.
FAIL          The next stage must not start; fix the reported phase or artifact first.
BLOCKED       A required input, permission, runtime, or external resource is missing.
WARNING       A non-blocking risk was found and should be tracked.
```

BenchClaw follows a "check before proceeding" policy. A `PASS` verdict means the next stage is allowed, not that the pipeline should automatically continue.

## Maintenance Principles

- Keep stage boundaries clear: Stage 2 collects raw data, Stage 3 cleans it, Stage 4 builds the eval set, and Stage 5 evaluates models without modifying Stage 4 assets.
- Preserve fixed artifact contracts: file names, directory layouts, schemas, report fields, and verdict semantics should remain stable.
- Prefer minimal Skill revisions with explicit rationale, impact scope, and regression evidence.
- Treat templates, cards, and tool docs as shared reference resources.
- Add or update source cards before expecting Stage 1 or Stage 2 to select and collect from a new simulator, dataset, or real-data source.

## License

BenchClaw is licensed under the Apache License 2.0. See `LICENSE` for details.
