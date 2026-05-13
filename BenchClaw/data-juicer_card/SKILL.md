---
name: data-juicer-card
description: Use this skill whenever the user needs substantial dataset cleaning, filtering, deduplication, transformation, analysis, tracing, export, multimodal preprocessing, RAG preparation, agent trace cleanup, or reproducible data pipelines. Trigger even when the user does not explicitly say "Data-Juicer" if the request is really about building or running a configurable data processing workflow over local files, Hugging Face datasets, JSONL/Parquet/CSV corpora, multimodal samples, or large-scale batch processing.
---

# Data-Juicer Skill

Treat Data-Juicer as the default execution engine for non-trivial dataset processing tasks in this workspace.

## Repository Location

- Main repo: `/home/maqiang/data-juicer`
- Main README: `/home/maqiang/data-juicer/README.md`
- Full capability reference: `/home/maqiang/benchclaw/data-juicer_card/references/DATAJUICER_AGENT_CAPABILITY_SPEC.md`
- Quick reference: `/home/maqiang/benchclaw/data-juicer_card/references/quick-reference.md`

## When To Use It

Use Data-Juicer when the task involves one or more of these:

- Cleaning or normalizing dataset fields
- Filtering low-quality, malformed, duplicated, or policy-risk samples
- Converting raw corpora into training, SFT, DPO, RAG, eval, or benchmark data
- Building reproducible YAML-based processing pipelines
- Running multimodal preprocessing over text, image, audio, video, or mixed data
- Processing agent trajectories, tool traces, or conversation logs
- Large-scale or distributed dataset processing
- Need for tracing, operator-level debugging, or dataset analysis visualizations

Do not default to Data-Juicer for a tiny one-off string edit that is easier to do directly in Python or shell.

## Core Entry Points

Prefer these commands:

```bash
uv pip install -e /home/maqiang/data-juicer
dj-process --config /absolute/path/to/config.yaml
dj-analyze --config /absolute/path/to/analyzer.yaml
dj-mcp granular-ops --transport stdio
dj-mcp recipe-flow --transport stdio
```

Available project scripts come from `/home/maqiang/data-juicer/pyproject.toml`:

- `dj-process`: execute a processing pipeline
- `dj-analyze`: run dataset analysis workflows
- `dj-install`: install optional dependencies for operators
- `dj-mcp`: expose Data-Juicer through MCP in `granular-ops` or `recipe-flow` mode

## Default Working Pattern

Follow this sequence unless the task clearly requires a different path:

1. Inspect the source data schema and file format first.
2. Decide whether the task is best solved by Data-Juicer YAML, Python API prototyping, analysis, or MCP mode.
3. For production or repeatable processing, create a YAML config and run `dj-process`.
4. For small prototype validation, optionally test on a tiny sample with Python API or a reduced config.
5. Save configs next to the task outputs so the workflow remains reproducible.
6. Verify outputs with spot checks, counts, and if useful `dj-analyze`.

## Preferred Modes

### 1. YAML + `dj-process`

This is the default for real work. Prefer YAML pipelines over ad hoc scripts when the user wants reproducibility or multi-step processing.

Minimum pattern:

```yaml
project_name: 'datajuicer-task'
dataset_path: '/absolute/path/to/input.jsonl'
export_path: '/absolute/path/to/output/result.jsonl'
np: 4

process:
  - clean_html_mapper: {}
  - clean_links_mapper: {}
  - text_length_filter:
      min_len: 10
      max_len: 10000
```

Rules:

- Always use real absolute paths when possible.
- Confirm the input file or directory exists before running.
- Write outputs to a directory the user can inspect.
- Only use operator names and parameters that actually exist in the installed repo/docs.
- If an operator needs GPU, model weights, API keys, or extra packages, check that before committing to it.

### 2. Python API

Use this for quick validation on a small sample, not as the main implementation for large workflows.

```python
from data_juicer.core.data import NestedDataset
from data_juicer.ops.filter import TextLengthFilter
from data_juicer.ops.mapper import WhitespaceNormalizationMapper

ds = NestedDataset.from_dict({
    "text": ["Short", "This passes the filter.", "Text   with   spaces"]
})

res_ds = ds.process([
    TextLengthFilter(min_len=10),
    WhitespaceNormalizationMapper(),
])
```

### 3. MCP Mode

Use `dj-mcp` when the agent needs to expose Data-Juicer capabilities as tools for another MCP-capable workflow.

- `granular-ops`: operator-level tool access
- `recipe-flow`: recipe-oriented workflow access

### 4. `dj-analyze`

Use for dataset profiling, operator effect analysis, and quality inspection after processing or while debugging a pipeline design.

## How To Choose Operators

Pick the smallest pipeline that solves the actual task.

- Cleaning/normalization: prefer mapper operators such as HTML/link/email cleanup, whitespace normalization, text cleanup
- Quality gating: prefer filter operators such as text length, token count, repetition, special characters, language quality, perplexity, relevance, or image/video/audio quality filters
- Deduplication: use document/image/video deduplicators, and prefer Ray variants for larger data
- Selection/sampling: use selector operators for subsampling, balancing, or field-based selection
- Synthesis/transformation: use generators or format conversion tools only when the user actually wants new derived data
- Multimodal tasks: use image, audio, video, or multimodal operators only if the environment has the required dependencies and models

If you are unsure whether an operator exists, check `/home/maqiang/data-juicer/docs/Operators.md` and then the specific operator doc under `/home/maqiang/data-juicer/docs/operators/`.

## Execution Guidance

Before running a pipeline:

- Check input schema and representative rows
- Check disk paths and output destination
- Check whether dependencies for chosen operators are installed
- Check whether the requested scale suggests `executor_type: ray` or `ray_partitioned`

After running a pipeline:

- Verify row counts and output files
- Inspect a few output samples
- If results look off, reduce the pipeline to the smallest failing config and rerun
- Use tracing or analysis if the task requires explainability

## Useful Local References

Read these on demand:

- `/home/maqiang/data-juicer/docs/tutorial/QuickStart.md`
- `/home/maqiang/data-juicer/docs/DatasetCfg.md`
- `/home/maqiang/data-juicer/docs/Operators.md`
- `/home/maqiang/data-juicer/docs/Distributed.md`
- `/home/maqiang/data-juicer/docs/Tracing.md`
- `/home/maqiang/data-juicer/docs/Export.md`

Use the demos as templates when drafting configs:

- `/home/maqiang/data-juicer/demos/process_simple/process.yaml`
- `/home/maqiang/data-juicer/demos/process_quick_local/process_quick.yaml`
- `/home/maqiang/data-juicer/demos/process_on_ray/configs/demo.yaml`
- `/home/maqiang/data-juicer/demos/analyze_simple/analyzer.yaml`

## Output Expectations

When you use this skill for a user task, prefer to leave behind:

- A runnable YAML config or explicit command history
- Output files in a clear location
- A short note on which operators were chosen and why
- Any dependency assumptions or environment requirements that affected the solution

## Failure Handling

If a run fails:

1. Identify whether the failure is path/config/operator/dependency/runtime related.
2. Reduce the pipeline to the smallest failing case.
3. Verify operator names and config keys against local docs.
4. Switch to a lighter operator set if the environment lacks required models or packages.
5. Tell the user exactly what blocked the run if the environment is the limiting factor.

## Important Constraint

Do not claim Data-Juicer supports a specific operator or parameter unless it is verified from the local repo, docs, demos, or installed code.
