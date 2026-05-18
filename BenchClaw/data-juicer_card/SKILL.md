---
name: data-juicer-card
description: Use this skill whenever the task is dataset cleaning, filtering, normalization, deduplication, dataset quality control, or reproducible data processing with Data-Juicer. This skill is self-contained: reading this file alone is enough to inspect local data, draft a runnable YAML, orchestrate Data-Juicer cleaning, execute the run, and verify outputs.
---

# Data-Juicer Skill

This skill is the only document that needs to be read inside `data-juicer_card`.

Do not rely on any other file in this skill directory. The `references/` directory is intentionally removed.

## Hard Requirement

The conda environment for this skill is already standardized as `data_juicer`.

Always execute Data-Juicer commands through that environment. Preferred form:

```bash
conda run -n data_juicer <command>
```

Use this rule for all package checks, CLI invocation, and smoke runs. Do not assume the current shell is already activated.

## Repository And Runtime

- Data-Juicer repo: `/home/maqiang/data-juicer`
- Skill directory: `BENCHCLAW_ROOT/data-juicer_card`
- Standard conda env: `data_juicer`

If `dj-process` is unavailable inside `data_juicer`, bootstrap it with:

```bash
conda run -n data_juicer pip install -e /home/maqiang/data-juicer
```

Then verify with one of these:

```bash
conda run -n data_juicer dj-process --help
conda run -n data_juicer python -c "import data_juicer; print(data_juicer.__file__)"
```

## What This Skill Must Accomplish

When used, this skill should be sufficient to:

1. Inspect the input dataset path and sample schema.
2. Choose a minimal set of valid Data-Juicer operators.
3. Write a runnable YAML config with absolute paths.
4. Run dataset cleaning through Data-Juicer in `data_juicer`.
5. Verify that outputs were produced and inspect sample rows.
6. Leave behind reproducible artifacts: config, input sample, output path, and command history.

## When To Use This Skill

Use it when the task is any of the following:

- Text cleaning or normalization
- Quality filtering
- Dataset deduplication
- Reproducible YAML-based data processing
- Preprocessing JSONL, JSON, CSV, TSV, TXT, or Parquet datasets
- Preparing cleaned outputs for later benchmark, training, or analysis stages

Do not default to this skill for a trivial one-line string edit that does not need a data pipeline.

## Mandatory Workflow

Follow this order unless the user explicitly asks for something else:

1. Confirm the input path exists.
2. Read a small sample of the dataset and identify the text-bearing fields.
3. Pick the smallest operator list that solves the requested cleaning task.
4. Write a YAML config with absolute `dataset_path` and `export_path`.
5. Run the config with `conda run -n data_juicer dj-process --config <config>`.
6. Read the output file and compare a few rows before and after cleaning.
7. Report what changed, where the config lives, and where the cleaned data was written.

## Minimal Operator Set You Can Use Safely

These operators are confirmed in the local Data-Juicer docs and are stable CPU text operators suitable for default cleaning:

### `clean_html_mapper`

- Purpose: strip HTML tags and convert HTML text to plain text.
- Parameters: none required.

### `clean_links_mapper`

- Purpose: remove URLs from text.
- Parameters:
  - `pattern`: optional
  - `repl`: optional, default empty string

### `text_length_filter`

- Purpose: keep rows whose text length is within a character range.
- Parameters:
  - `min_len`
  - `max_len`

### `words_num_filter`

- Purpose: keep rows whose word count is within a range.
- Parameters:
  - `lang`
  - `tokenization`
  - `min_num`
  - `max_num`

## Default Config Pattern

Prefer this template for local text cleaning:

```yaml
project_name: 'data-juicer-cleaning'
dataset_path: '/absolute/path/to/input.jsonl'
export_path: '/absolute/path/to/output/cleaned.jsonl'
np: 1

process:
  - clean_html_mapper: {}
  - clean_links_mapper: {}
  - text_length_filter:
      min_len: 10
      max_len: 10000
  - words_num_filter:
      lang: en
      tokenization: false
      min_num: 3
      max_num: 2000
```

Rules:

- Always use absolute paths in configs written by this skill.
- Do not overwrite raw input files.
- Keep the pipeline minimal.
- Prefer `np: 1` for smoke runs and small local verification.
- Only add heavier operators if the task actually needs them.

## Execution Commands

### Inspect runtime

```bash
conda run -n data_juicer python -c "import data_juicer; print('ok')"
```

### Run a cleaning config

```bash
conda run -n data_juicer dj-process --config /absolute/path/to/process.yaml
```

### Alternative source-run path

If the CLI script is missing but the repo exists, run:

```bash
conda run -n data_juicer python /home/maqiang/data-juicer/tools/process_data.py --config /absolute/path/to/process.yaml
```

## Output Verification Checklist

After each run, verify all of the following:

1. The export file exists.
2. The export file is non-empty.
3. At least two rows were spot-checked.
4. The observed changes match the intended operators.

If the run fails, classify the failure as one of:

- environment not bootstrapped
- wrong input path
- invalid YAML
- invalid operator name
- operator parameter mismatch
- runtime dependency issue

Then fix the smallest blocking issue and rerun.

## Self-Contained Example In This Directory

This directory is expected to contain an executable local example so the skill can be validated without external skill docs.

Example input:

- `BENCHCLAW_ROOT/data-juicer_card/examples/minimal_input.jsonl`

Example config:

- `BENCHCLAW_ROOT/data-juicer_card/examples/minimal_process.yaml`

Expected run command:

```bash
conda run -n data_juicer dj-process --config BENCHCLAW_ROOT/data-juicer_card/examples/minimal_process.yaml
```

Expected output path:

- `BENCHCLAW_ROOT/data-juicer_card/examples/output/minimal_cleaned.jsonl`

## Example Validation Standard

The local example is considered valid when:

- HTML tags are removed from the first sample.
- Links are removed from samples that contain URLs.
- Very short text is filtered out.
- The cleaned output file exists under `examples/output/`.

## Reporting Format

When this skill is used, leave a concise report that includes:

- input dataset path
- output dataset path
- config path
- exact command executed through `conda run -n data_juicer`
- operators used and why
- result summary from spot checks

## Important Constraint

Do not claim a Data-Juicer operator or parameter is supported unless it is verified from the local repo or local docs under `/home/maqiang/data-juicer`.
