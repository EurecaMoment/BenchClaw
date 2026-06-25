# Stage4 Skill Audit and Revision Notes

## Judgment

The Stage4 DAG is structurally sound, but the previous version over-constrained high-depth GT kinship, over-coupled Stage4 to model evaluation, and duplicated responsibilities across template/metric/answer-program subskills. This revision keeps every subskill but tightens each boundary.

## Revised execution rule

Mandatory: parent-runtime bundle build, generated thin child generator, py_compile, real item dry run, invalid item screening, deterministic positive/negative scoring smoke, full package with hidden answers separated.

Optional unless required by plan: high-depth distant-chain templates, external model mini eval, CDM/IRT diagnostics.

## Critical fix

`EVALSET_DATASET/data/test.jsonl` is now model-facing and must not contain answers, metadata, evidence refs, object provenance, bbox, depth, or GT fields. Hidden answers are written to `ground_truth/answers.jsonl`.
