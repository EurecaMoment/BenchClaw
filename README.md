# BenchClaw

BenchClaw is a comprehensive collection of Codex/OpenCode skill workflows designed for benchmark construction, evaluation, and maintenance. It divides the process into six stages: draft design, data collection, data cleaning, test set construction, model evaluation, and diagnostic maintenance. For each stage, it defines input/output specifications, quality gates, directory contracts, lineage tracking, and rollback strategies. Its goal is to enable agents to start from a rough benchmark idea and systematically generate evaluation plans, data, metrics, results, and reports in a standardized, reproducible, and auditable manner. When failures occur, it identifies the minimal rollback point and forms a closed loop for process diagnostics and skill revision.

## Project Overview

This project is not a traditional software application but rather a set of workflow rules designed for agents. Each SKILL.md describes how to execute a specific stage or task, including what inputs to read, what outputs to generate, how to assess quality, and how to roll back and recover from failures.

The project's core goals are to make the benchmark construction process more:

- Standardized
- Reproducible
- Auditable
- Maintainable
- Rollbackable

## Process Overview

The complete workflow is orchestrated by the top-level enchmark-pipeline and includes six main stages:

1. **Draft Design**  
   Starting from a benchmark idea, clarify the evaluation objectives, capability dimensions, data sources, and overall execution plan.

2. **Data Collection**  
   Collect or integrate required data according to the design plan, including simulated data, existing datasets, and real-world data.

3. **Data Cleaning**  
   Clean, filter, and organize the collected data while maintaining records of data sources and processing steps.

4. **Test Set Construction**  
   Generate formal test samples, test schema, and metric code, and complete basic validation.

5. **Model Evaluation**  
   First conduct small-scale canary evaluation, then execute full-scale evaluation and generate result reports once the process is confirmed reliable.

6. **Diagnosis and Maintenance**  
   Review the entire workflow, identify problem sources, revise skills as needed, and perform regression testing.

## Directory Structure

\\\	ext
.
+-- benchmark-pipeline/
+-- benchmark-stage1-draft/
+-- benchmark-stage2-data-collect/
+-- benchmark-stage3-data-clean/
+-- benchmark-stage4-build/
+-- benchmark-stage5-eval/
\-- benchmark-stage6-diagnosis-maintenance/
\\\

The \SKILL.md\ file in each directory is the main documentation for the corresponding stage.

## Usage

Recommended usage starts with the top-level pipeline:

\\\	ext
/benchmark-pipeline "your benchmark idea"
\\\

You can also invoke individual stages:

\\\	ext
/benchmark-stage1-draft "your benchmark idea"
/benchmark-stage2-data-collect "\"
/benchmark-stage3-data-clean "\"
/benchmark-stage4-build "\"
/benchmark-stage5-eval "\"
/benchmark-stage6-diagnosis-maintenance "\"
\\\

## Workspace Convention

Each execution uses an independent workspace to prevent cross-contamination between different benchmark tasks:

\\\	ext
~/bench_workspace/workspace{i}/
\\\

Typical outputs include stage results, quality reports, evaluation reports, and the final pipeline report.

## Quality Control

The project emphasizes "check first, then proceed." Each stage must produce verifiable results, and the next stage can only be entered after passing quality gates.

Common statuses include:

\\\	ext
PASS          Can proceed
NEEDS_REVIEW  Requires human review
FAIL          Must be fixed or rolled back
\\\

If a stage fails, the process should identify the specific stage or artifact for repair rather than defaulting to a full restart from the beginning.

## Key Deliverables

Upon completion, the process typically generates:

* Benchmark draft
* Data schema
* Data quality report
* Cleaned data inventory
* Test set schema
* Metric code
* Canary evaluation report
* Full evaluation report
* Process diagnosis report
* Final pipeline report

## Maintenance Principles

When maintaining this project, prioritize keeping the workflow clear, rules stable, and stage boundaries well-defined. When modifying skills, use minimal changes and ensure upstream and downstream stages remain properly connected.

## Related Documentation

* [Project Description](./DESCRIPTION.md)
* [Top-level Pipeline Skill](./benchmark-pipeline/SKILL.md)
* [Stage 1 Skill](./benchmark-stage1-draft/SKILL.md)
* [Stage 2 Skill](./benchmark-stage2-data-collect/SKILL.md)
* [Stage 3 Skill](./benchmark-stage3-data-clean/SKILL.md)
* [Stage 4 Skill](./benchmark-stage4-build/SKILL.md)
* [Stage 5 Skill](./benchmark-stage5-eval/SKILL.md)
* [Stage 6 Skill](./benchmark-stage6-diagnosis-maintenance/SKILL.md)
