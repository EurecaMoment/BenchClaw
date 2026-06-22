# BenchClaw

## Paper

BenchClaw is described in our paper:

- [Embodied-BenchClaw: An Autonomous Multi-Agent System for Embodied Spatial Intelligence Benchmark Construction](https://arxiv.org/abs/2606.11909)

## Awesome Benchmark Index

For a year-organized list of existing embodied AI, robotics, navigation, simulation, and multimodal-agent benchmarks tracked from `benchmarks.xlsx`, see [Awesome BenchClaw Benchmarks](AWESOME.md).

BenchClaw is a Skill-first benchmark manufacturing repository for Agent environments such as OpenCode. It is not a single executable app or a traditional Python package. Instead, it provides staged `SKILL.md` contracts, DAG and ready-set execution rules, capability cards, validation scripts, and fixed workspace artifact layouts for data collection, evidence compilation, benchmark packaging, and evaluation.

The repository is designed to turn a rough benchmark idea into a reproducible Stage1 to Stage5 pipeline with explicit artifacts, path isolation, and auditability.

## What BenchClaw Provides

BenchClaw focuses on benchmark construction rather than only benchmark execution. In practice, the repository provides:

- stage-wise `SKILL.md` contracts for planning, collection, evidence compilation, benchmark synthesis, and evaluation
- fixed workspace layouts so every run can be audited and reproduced
- source cards for simulators, datasets, and real-image collections
- annotation-tool contracts for semi-supervised GT generation
- template, metric, and evaluation packaging logic for turning evidence into executable benchmarks

BenchClaw is intentionally not packaged as a single monolithic CLI. The main unit of reuse is the Skill plus its artifact contract.

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

## Typical Workflow

At a high level, a normal BenchClaw run looks like this:

1. Stage1 converts an evaluation idea into a benchmark draft, capability decomposition, source selection, and execution plan.
2. Stage2 materializes raw assets from real data, existing benchmarks, and simulators into a dedicated workspace.
3. Stage3 converts those assets into normalized evidence, cleaned GT, segmentation or depth byproducts, and audit-ready records.
4. Stage4 synthesizes benchmark items, media, GT-linked evidence, metrics, and final benchmark packages.
5. Stage5 evaluates the required model roster on the Stage4 package and writes reports.

The important design choice is that every stage reads shared reference resources from the repository, but writes run-specific outputs only into `WORKSPACE_ROOT`.

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

## What A Final Benchmark Looks Like

By the time a run reaches the Stage4 terminal package, the benchmark should be executable rather than only descriptive. In the current contract, Stage5 consumes a package shaped like:

```text
EVALSET_DATASET/
├── README.md
├── data/
│   └── test.jsonl
├── images/
└── metrics/
    └── evaluate.py
```

Depending on the benchmark family, Stage4 may also retain richer intermediate artifacts in the workspace, such as generated answer programs, template manifests, GT-linked evidence tables, or dual-image benchmark items where the original image and the answer-facing processed image are both preserved for auditability.

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

## Start From Scratch

If you are using BenchClaw for the first time, the safest way to start is to treat the repository as a reusable definition layer and create one fresh workspace for one fresh benchmark run.

### 1. Prepare The Repository And Workspace

1. Clone the repository and enter the project root:

```bash
git clone <your-benchclaw-repo-url>
cd BenchClaw
```

2. Pick or create a new workspace directory. A typical choice is under `workspaces/`:

```bash
mkdir -p workspaces/workspace001
```

3. Make sure you know the two important roots:
   - `BENCHCLAW_ROOT`: the reusable repository root, for example `/path/to/BenchClaw/BenchClaw`
   - `WORKSPACE_ROOT`: the run-specific artifact root, for example `/path/to/BenchClaw/workspaces/workspace001`

4. Confirm the workspace is writable and is not being reused by another unfinished run.

### 2. Check The Minimum Runtime Assumptions

Before launching a pipeline, confirm:

- your Agent environment can invoke repository Skills
- any required localhost simulator service is already running if its card says attach-only
- any required annotation tool service is already running if its card says attach-only
- any external or private source data you intend to use can be legally and practically materialized into `WORKSPACE_ROOT`

If you are just exploring the repository structure, you do not need every service up front. But if you want a real end-to-end run, Stage2 and Stage3 usually depend on these local capabilities being ready.

### 3. Start With The Top-Level Pipeline

For a normal first run, use the top-level pipeline instead of jumping directly into a later stage:

```text
/benchmark-pipeline "Build an embodied spatial benchmark for <your task idea>"
```

This is the recommended entrypoint because it:

- creates or locks in one consistent `WORKSPACE_ROOT`
- handles stage handoff in order
- keeps path resolution stable across stages
- exposes stage summaries and gate verdicts before you continue

### 4. What To Expect Stage By Stage

When the pipeline runs normally, you can think of the stages like this:

1. Stage1 defines the benchmark: capability scope, source selection, template direction, and execution plan.
2. Stage2 collects or materializes raw data from selected sources into the workspace.
3. Stage3 turns raw assets into evidence, GT, and annotation-ready records.
4. Stage4 turns evidence into benchmark items, media, metrics, and final packages.
5. Stage5 evaluates the required model roster on the Stage4 package.

After each stage, check the generated report and gate result before moving on.

### 5. Where To Look For Outputs

During a run, the most important files and folders are usually:

- `WORKSPACE_ROOT/stage1/` through `WORKSPACE_ROOT/stage5/`
- `WORKSPACE_ROOT/path_resolution.json`
- `WORKSPACE_ROOT/pipeline_state.json`
- `WORKSPACE_ROOT/PIPELINE_REPORT.md`
- stage-specific reports, filtered items, manifests, logs, and final dataset packages inside each stage directory

If a benchmark build succeeds, the Stage4 final package is typically the artifact you will inspect first, and Stage5 reports are the place to look for model-level outcomes.

### 6. If You Only Want To Run One Stage

You can run stages individually, but this is better after you already understand the workspace layout:

```text
/benchmark-stage1-draft "your benchmark idea"
/benchmark-stage2-data-collect "$WORKSPACE_ROOT/stage1"
/benchmark-stage3-evidence-compiler "$WORKSPACE_ROOT/stage2"
/benchmark-stage4-build "$WORKSPACE_ROOT/stage3"
/benchmark-stage5-eval "$WORKSPACE_ROOT/stage4"
```

As a first-time user, prefer the full pipeline unless you are explicitly debugging one stage.

### 7. Common First-Run Pitfalls

The most common mistakes when starting from scratch are:

- writing artifacts back into the repository tree instead of the workspace
- reusing an old workspace with partially stale outputs
- trying to skip Stage1 and Stage2 before source assumptions are clear
- forgetting that some simulators or annotation tools are expected to be pre-running local services
- assuming the repository is a single install-and-run app rather than a Skill-driven pipeline

## Minimal Local Expectations

BenchClaw assumes you already have an environment that can invoke repository Skills and, when needed, connect to local tools or simulator endpoints. Before running a full pipeline, it helps to confirm:

- you have a writable `WORKSPACE_ROOT`
- required local services for selected annotation tools are already running if the card marks them as service-style
- selected simulator endpoints are already attached and reachable when Stage2 expects attach-only behavior
- any private or external data sources referenced by a run have already been approved and materialized into the workspace

For ordinary development, you usually edit the repository under `BenchClaw/` and inspect generated artifacts under `workspaces/`.

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

The repository root already includes example long-lived directories such as:

- `BenchClaw/` for the reusable Skill and card library
- `workspaces/` for isolated benchmark runs
- `path_resolution.json` for repository-level path anchoring used by some flows

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

## How To Add A New Data Source Or Simulator Card

BenchClaw is easiest to extend by adding or updating a source card first, then letting Stage1 and Stage2 select it through the normal pipeline rather than hard-coding special cases into a run.

### Add A New Real-Data Or Benchmark-Dataset Source

1. Create or update a card under `realDataCards/` or `benchmarkDatasetCards/`.
2. Document what the source contains:
   - modalities such as RGB, depth, text, trajectory, metadata, or labels
   - license or usage constraints
   - expected acquisition method
   - how the source should be materialized into `WORKSPACE_ROOT/stage2/`
3. Make sure the card states whether the source is fully local, externally mounted, or requires a preprocessing step before Stage2 can ingest it.
4. Keep the downstream contract in mind:
   - Stage2 must materialize the source into the active workspace
   - Stage3 must be able to derive evidence, GT, or annotation-ready records from it
   - Stage4 must be able to trace benchmark items back to source evidence
5. If the source needs custom cleaning or annotation assumptions, add or update the corresponding Stage3 documentation or helper logic instead of burying those assumptions in Stage2 prompts alone.

### Add A New Simulator Card

1. Create a new directory under `simulatorCards/`.
2. Describe the simulator’s observation channels and privileged signals as concretely as possible:
   - RGB or multi-view images
   - segmentation, depth, normals, occupancy, or maps
   - object IDs, poses, trajectories, relations, or action logs
   - scene reset, stepping, and collection semantics
3. State whether BenchClaw should:
   - attach to an already running localhost endpoint, or
   - run a local executable or script as part of collection
4. Define what Stage2 is expected to save per scene or episode and where it should land under `WORKSPACE_ROOT/stage2/`.
5. Define what Stage3 can trust as privileged GT versus what still needs cleaning, normalization, or derived annotations.
6. If the simulator introduces a new artifact pattern, update the relevant stage skill or contract documentation so the change is explicit and reusable.

### Extension Checklist

Before considering a new source integrated, it is worth checking:

- Stage1 can discover and justify selecting the source
- Stage2 can materialize it into the workspace without hidden manual steps
- Stage3 can produce usable evidence or GT from it
- Stage4 can build benchmark items whose answers remain traceable to source evidence
- Stage5 can consume the resulting benchmark package without special-case evaluation hacks

## FAQ

### Is BenchClaw a Python package or a standalone app?

No. BenchClaw is primarily a repository of Skills, contracts, cards, and artifact conventions. Some stages generate scripts or runnable outputs inside a workspace, but the repository itself is not organized as a single installable app.

### Where should generated data go?

Generated data should go into the active `WORKSPACE_ROOT`, not back into the repository source tree. The repository is the reusable definition layer; the workspace is the run-specific artifact layer.

### Can I run only one stage?

Yes. Individual stages can be invoked directly, but the recommended entrypoint is still `benchmark-pipeline` because it keeps `WORKSPACE_ROOT`, stage handoff, and gate semantics consistent.

### When should I edit a Skill versus a source card?

Edit a source card when the capability, acquisition method, or source contract changes. Edit a Skill when the stage logic, artifact rules, or execution procedure changes.

### Can I point BenchClaw to data that already exists elsewhere on disk?

You can reference existing data during planning, but the normal pipeline still expects selected data to be materialized into the active workspace so later stages remain reproducible and auditable.

### What if a simulator or annotation tool already runs as a service?

The current project generally prefers attach-only behavior for service-style tools. If a card says the tool should attach to an existing localhost endpoint, the pipeline should not repeatedly relaunch it during ordinary collection.

### What is the most common reason a stage gets blocked?

Usually one of four things:

- the selected source was never fully materialized into the workspace
- a required local tool or simulator endpoint is unavailable
- a downstream artifact contract is underspecified
- the evidence or GT is not strong enough to support an auditable benchmark item

## Current Project Direction

The repository is currently oriented toward embodied spatial intelligence benchmark manufacturing across mixed carriers and sources, including:

- indoor embodied reasoning
- outdoor and aerial spatial reasoning
- simulator-native privileged GT construction
- semi-supervised enhancement of existing benchmark images
- evaluation packages that remain executable, traceable, and maintainable after synthesis

Recent Stage3 and Stage4 work in this repository emphasizes stronger GT traceability, benchmark-item auditability, workspace-local path stability, and benchmark packages that can be regenerated or repaired instead of being treated as static one-off datasets.

## Maintenance Principles

- Keep stage boundaries clear: Stage2 collects, Stage3 cleans and annotates, Stage4 packages the benchmark, and Stage5 evaluates models without rewriting Stage4 assets.
- Preserve fixed artifact contracts: file names, directory layouts, schemas, report fields, and verdict semantics should remain stable.
- Prefer minimal Skill revisions with explicit rationale and impact scope.
- Treat templates, cards, and tool docs as shared reference resources.
- Add or update source cards before expecting Stage1 or Stage2 to select and collect from a new simulator, dataset, or real-data source.

## License

BenchClaw is licensed under the Apache License 2.0. See `LICENSE` for details.

## Citation

If BenchClaw helps your work, please cite:

```bibtex
@article{jiang2026embodiedbenchclaw,
  title={Embodied-BenchClaw: An Autonomous Multi-Agent System for Embodied Spatial Intelligence Benchmark Construction},
  author={Jiang, Baoyang and Zhang, Fengchun and Wang, Leyuan and Li, Haotian and Wang, Yida and Ji, Zhe and Lai, Jinshan and Ren, Xi and Hu, Jianwei and Ma, Qiang},
  journal={arXiv preprint arXiv:2606.11909},
  year={2026}
}
```
