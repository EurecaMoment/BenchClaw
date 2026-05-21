# BenchClaw

BenchClaw is a Skill-first benchmark manufacturing repository for Agent environments such as OpenCode. It is not a single executable app or a traditional Python package. Instead, it provides staged `SKILL.md` contracts, DAG and ready-set execution rules, capability cards, validation scripts, and fixed workspace artifact layouts for data collection, evidence compilation, benchmark packaging, and evaluation.

The repository is designed to turn a rough benchmark idea into a reproducible Stage1 to Stage5 pipeline with explicit artifacts, path isolation, and auditability.

## Current Scope

BenchClaw currently implements a five-stage pipeline:

1. Stage1: benchmark draft and execution plan
2. Stage2: raw data collection
3. Stage3: evidence compilation, cleaning, and semi-supervised GT generation
4. Stage4: benchmark build and artifact packing
5. Stage5: multi-model evaluation and reporting

The pipeline is orchestrated by `BenchClaw/skills/benchmark-pipeline/SKILL.md`, while each stage keeps its own internal DAG and numbered sub-skills.

## Repository Layout

```text
BenchClaw/
├── skills/
│   ├── benchmark-pipeline/
│   ├── benchmark-stage1-draft/
│   ├── benchmark-stage2-data-collect/
│   ├── benchmark-stage3-evidence-compiler/
│   ├── benchmark-stage4-build/
│   └── benchmark-stage5-eval/
├── templates/
├── simulatorCards/
├── benchmarkDatasetCards/
├── realDataCards/
├── annotation-tool/
├── data-juicer_card/
├── modelNeedMeasured/
└── LICENSE
```

Important naming notes:

- simulator cards live under `simulatorCards/`
- existing benchmark dataset cards live under `benchmarkDatasetCards/`
- real-data source cards live under `realDataCards/`
- annotation tool contracts live under `annotation-tool/`
- the fixed Stage5 model roster and multimodal API client live under `modelNeedMeasured/`

## Core Skills

| Skill | Role |
|---|---|
| `benchmark-pipeline` | Top-level Stage1 to Stage5 serial orchestrator. Freezes `BENCHCLAW_ROOT` and `WORKSPACE_ROOT`, manages stage handoff, and enforces stage-level completion checks. |
| `benchmark-stage1-draft` | Converts a benchmark idea into capability decomposition, template/metric draft, simulator selection, annotation-tool selection, benchmark draft, and execution plan. |
| `benchmark-stage2-data-collect` | Executes Stage1 collection targets against three source branches: real data, existing benchmark datasets, and simulators. |
| `benchmark-stage3-evidence-compiler` | Converts Stage2 raw assets into normalized evidence, cleaned GT, and semi-supervised image annotations. |
| `benchmark-stage4-build` | Builds the final benchmark package and evaluation-facing artifact tree. |
| `benchmark-stage5-eval` | Runs required model evaluation and writes report artifacts from the Stage4 package. |

Each stage directory contains numbered sub-skills. Examples:

- Stage1: `00-idea-intake`, `10-simulator-selection`, `12-benchmark-draft`, `13-execution-plan`
- Stage2: `13-stage1-execution-plan-ingest`, `15-real-image-acquisition`, `16-existing-benchmark-acquisition`, `17-simulator-multimodal-gt-acquisition`
- Stage3: `18-real-image-semi-supervised-gt`, `19-benchmark-image-semi-supervised-gt`, `20-simulator-clean-gt-pack`, `27-semi-supervised-tool-registry`
- Stage4: `36-full-scale-synthesis`, `37-benchmark-artifact-pack`
- Stage5: `38-evaluation-run`, `39-evaluation-report`

## Capability Resources

### Simulators

`simulatorCards/` currently includes:

- `CARLA/`
- `HABITAT/`
- `LIBERO/`

These cards document what each simulator can provide, how it should be attached during Stage2, what GT and multimodal observations exist, and how collection should be executed.

BenchClaw now treats service-style simulators conservatively:

- if a simulator exposes a localhost service or endpoint, Stage2 should attach to an already running local endpoint,
- Stage2 should not relaunch a simulator service during normal collection.

### Existing Benchmark Datasets And Real Data

`benchmarkDatasetCards/` currently includes benchmark dataset cards such as:

- `ERQA/`

`realDataCards/` currently includes real-data cards such as:

- `Uav_photos/`

Stage2 is intentionally strict:

- selected real-data cards must flow through the full Stage2 to Stage4 pipeline,
- selected existing benchmark datasets must also flow through the full Stage2 to Stage4 pipeline,
- both must be physically materialized inside `WORKSPACE_ROOT`, not referenced only by external paths.

### Annotation Tools

`annotation-tool/` currently includes local tool skills such as:

- `sam3/`
- `yoloe/`
- `depthanything3/`
- `llm-local/`

These tools are used in Stage3 for semi-supervised image annotation. The shared chain is:

```text
input image
  -> YOLOE + LLM
  -> SAM3
  -> Depth Anything 3
  -> semantic/depth-aware entity segmentation candidates
```

For normal workflow, these service-style tools are expected to attach to already-running localhost endpoints instead of repeatedly starting new services.

### Data-Juicer

`data-juicer_card/` contains the Data-Juicer capability card used by Stage3 cleaning nodes.

### Models To Be Measured

`modelNeedMeasured/` defines the Stage5 model roster and multimodal API contract.

Current required Stage5 evaluation roster:

- `qwen3-vl-235b-a22b-instruct`
- `kimi-k2.5`
- `llama-4-maverick-17b-128e-instruct`
- `grok-4-fast`
- `gpt-5.4-mini-2026-03-17`
- `glm-4.5v`
- `gemini-3-flash-preview`
- `claude-haiku-4-5-20251001-thinking`
- `claude-sonnet-4-5-20250929`

The current local client is:

- `modelNeedMeasured/yeysai_multimodal_client.py`

and the current API target is:

- `https://yeysai.com/v1/chat/completions`

## Reference Templates

`templates/` contains 48 reference JSON templates covering embodied perception, navigation, memory, dynamics, active inspection, semantic reasoning, CARLA driving, and QA or audit tasks.

These are template references, not final benchmark items. Final GT must come from simulator privileged state, official labels, verified or tool-generated Stage3 evidence, or executable scoring or evaluation logic, not directly from free-form LLM fabrication.

## End-to-End Pipeline

```text
Stage1 draft
  -> Stage2 data collect
  -> Stage3 evidence compiler
  -> Stage4 benchmark build
  -> Stage5 evaluation
```

| Stage | Main Role | Key Outputs |
|---|---|---|
| Stage1 | benchmark definition, capability decomposition, source selection, execution planning | `benchmark_draft.md`, `design_traceability_table.csv`, `execution_plan.md`, `stage2_handoff.yaml` |
| Stage2 | source-aware raw data materialization from real data, existing benchmarks, and simulators | `15-real-image-acquisition/`, `16-existing-benchmark-acquisition/`, `17-simulator-multimodal-gt-acquisition/` |
| Stage3 | normalized evidence, semi-supervised image GT, simulator clean GT | `realdata/`, `benchmarkdataset/`, `simulator/`, plus terminal node outputs 18, 19, 20 |
| Stage4 | final benchmark packaging | `37-benchmark-artifact-pack/EVALSET_DATASET/`, `FINAL_BENCHMARK_CARD.md`, `STAGE4_REPORT.md` |
| Stage5 | required model evaluation and reporting | `38-evaluation-run/`, `39-evaluation-report/` |

## Stage-Specific Conventions

### Stage1

Stage1 is a DAG, not a linear script. It now carries explicit quantity constraints downstream:

- if a real-data source is selected, its image and text data must flow through the later pipeline in full,
- if an existing benchmark dataset is selected, its image and text data must also flow through in full,
- if a simulator scene is selected, Stage2 must later collect at least 50 timepoints per scene.

### Stage2

Stage2 writes all image-bearing data into `WORKSPACE_ROOT/stage2/` and requires materialized outputs, not just manifests.

Current directory convention:

```text
stage2/
├── 15-real-image-acquisition/
│   └── realdata/
│       └── <real_scene_or_source>/
├── 16-existing-benchmark-acquisition/
│   └── benchmarkdataset/
│       └── <dataset_name>/
│           └── <existing_dataset_split_or_category>/
└── 17-simulator-multimodal-gt-acquisition/
    └── simulator/
        └── <simulator_id>/
            └── <scene_or_map_id>/
```

Additional rules:

- selected real-data and existing benchmark data must be fully materialized rather than sampled down,
- simulator observations must be fully saved for the required modalities,
- every selected simulator scene must contain at least 50 timepoints.

### Stage3

Stage3 writes image-bearing evidence into `WORKSPACE_ROOT/stage3/` and requires three image classes plus GT for retained samples:

```text
stage3/
├── realdata/
│   └── <real_scene_or_source>/
│       ├── original/
│       ├── semantic_entity_segmentation/
│       ├── depth/
│       └── gt/
├── benchmarkdataset/
│   └── <dataset_name>/
│       └── <existing_dataset_split_or_category>/
│           ├── original/
│           ├── semantic_entity_segmentation/
│           ├── depth/
│           └── gt/
└── simulator/
    └── <simulator_id>/
        └── <scene_or_map_id>/
            ├── original/
            ├── semantic_entity_segmentation/
            ├── depth/
            └── gt/
```

For real-data and existing benchmark branches, semantic entity segmentation comes from the `YOLOE + LLM -> SAM3` chain and depth comes from Depth Anything 3. For simulator branches, semantic entity segmentation and depth come from simulator-native or equivalent privileged render outputs.

### Stage4

The final benchmark package is now a single required structure under:

```text
WORKSPACE_ROOT/stage4/37-benchmark-artifact-pack/EVALSET_DATASET/
├── README.md
├── data/
│   └── test.jsonl
├── images/
└── metrics/
    └── evaluate.py
```

This is the only final benchmark folder format that Stage5 is expected to consume.

### Stage5

Stage5 reads the Stage4 `EVALSET_DATASET/` package and runs evaluation over the fixed required model roster from `modelNeedMeasured/`.

It uses:

- `EVALSET_DATASET/data/test.jsonl`
- `EVALSET_DATASET/images/`
- `EVALSET_DATASET/metrics/evaluate.py`
- `modelNeedMeasured/model_roster.yaml`
- `modelNeedMeasured/yeysai_multimodal_client.py`

Stage5 must not silently subset the required models and must not fabricate predictions.

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

Using `benchmark-pipeline` is recommended because it creates and passes a consistent `WORKSPACE_ROOT`, then stops at each major stage boundary to show the summary, gate verdict, key artifacts, and blocking issues.

## Workspace Convention

BenchClaw treats this repository as a shared read-only resource root during benchmark runs. Generated run artifacts should be written to an isolated workspace:

```text
WORKSPACE_ROOT/
├── stage1/
├── stage2/
├── stage3/
├── stage4/
├── stage5/
├── path_resolution.json
├── pipeline_state.json
├── PIPELINE_DONE.json
└── PIPELINE_REPORT.md
```

Key rules:

- a new pipeline run creates or receives one unique workspace,
- downstream stages must inherit the exact same `WORKSPACE_ROOT` from upstream stages,
- a stage must not auto-discover or borrow artifacts from another workspace unless the user explicitly provides that path and reuse scope,
- `BENCHCLAW_ROOT` should be used as read-only reference material,
- reports, generated scripts, temporary files, logs, model outputs, and evaluation results belong in the active workspace.

## Quality Gates

Common gate verdicts:

```text
PASS          The stage is eligible to proceed, but the user still chooses the next step.
NEEDS_REVIEW  The stage has explainable gaps and needs a waiver or revision.
FAIL          The next stage must not start; fix the reported phase or artifact first.
BLOCKED       A required input, permission, runtime, or external resource is missing.
WARNING       A non-blocking risk was found and should be tracked.
```

BenchClaw follows a check-before-proceeding policy. A `PASS` verdict means the next stage is allowed, not that the pipeline should automatically continue.

## Maintenance Principles

- Keep stage boundaries clear: Stage2 collects, Stage3 cleans and annotates, Stage4 packages the benchmark, and Stage5 evaluates models without rewriting Stage4 assets.
- Preserve fixed artifact contracts: file names, directory layouts, schemas, report fields, and verdict semantics should remain stable.
- Prefer minimal Skill revisions with explicit rationale and impact scope.
- Treat templates, cards, and tool docs as shared reference resources.
- Add or update source cards before expecting Stage1 or Stage2 to select and collect from a new simulator, dataset, or real-data source.

## License

BenchClaw is licensed under the Apache License 2.0. See `LICENSE` for details.
