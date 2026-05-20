# ERQA Skill

## Core Path

- BenchClaw root: resolve `BENCHCLAW_ROOT` as the BenchClaw directory that contains `skills/`, `benchmarkDatasetCards/`, and related card directories.
- Skill directory: `BENCHCLAW_ROOT/benchmarkDatasetCards/ERQA`
- Local dataset root: `/home/maqiang/benchmarkData/ERQA`

## Goal

This skill describes the ERQA benchmark dataset as a reusable benchmark-dataset card in BenchClaw.

If a model only reads this file and follows it exactly, it should be able to:

1. Locate the local ERQA dataset.
2. Understand the benchmark task format.
3. Recognize the key capabilities ERQA evaluates.
4. Use ERQA as a benchmark/evaluation dataset card.

## Dataset Overview

ERQA is a multimodal question-answering benchmark for real-world scenes. It mainly evaluates spatial reasoning, world-knowledge understanding, and embodied or robotics-related visual grounding. The current local directory corresponds to an accessible version converted from the original TFRecord release from [embodiedreasoning/ERQA](https://github.com/embodiedreasoning/ERQA).

- Local data path: `/home/maqiang/benchmarkData/ERQA`
- Split: `test`
- Sample count: `400`
- Dataset size: about `91 MB`
- Download size: about `78 MB`
- Task form: predict a short answer from a question plus a group of related images

## Input And Output Format

### Input

- `question_id`: unique question identifier
- `question`: question text
- `question_type`: question category
- `visual_indices`: indices of the visual inputs associated with the question
- `images`: a group of images used for multi-image reasoning

### Output

- `answer`: reference answer, usually short text

## Primary Capability Requirements

ERQA mainly tests the following capabilities:

1. multi-image visual understanding: locate relevant information across multiple visual clues
2. spatial reasoning: judge direction, distance, relative position, reachability, and similar relations
3. commonsense and world knowledge: combine real-world semantics with visual evidence
4. embodied or robot-view understanding: reason about movement, viewpoint changes, and visibility
5. fine-grained question answering: extract directly verifiable answers from visual content

## Suitable Task Characteristics

1. Inputs are usually not a single image but a set of images related to the question.
2. Questions often depend on spatial relations rather than simple classification.
3. Answers are usually short text, making exact-match style evaluation practical.
4. `question_type` can be used for per-subtask analysis.

## Evaluation Suggestions

1. Check whether the model actually uses all relevant images instead of relying only on language priors.
2. Report separate accuracy for question types involving direction, front/back, left/right, distance, occlusion, and visibility.
3. For multi-image questions, inspect cross-image consistency instead of accepting answers based on partial evidence.
4. Normalize case, spaces, and punctuation before evaluating short answers.

## Limitations

1. The current local version only includes the `test` split, so it is not directly suitable for training-set analysis.
2. Answers are often very short, so scores can be sensitive to wording variation.
3. Models without strong multi-image reasoning will usually degrade substantially.
4. Spatial-reasoning failures often come from viewpoint confusion or ignored visual indices.

## Suitable Model Profile

ERQA is especially useful for describing whether a model can:

1. understand multi-image questions
2. perform stable spatial relation reasoning
3. apply commonsense reasoning in real scenes
4. align visual clues with question constraints

## Notes

This card is adapted from the original local ERQA dataset description and rewritten into BenchClaw's folder-plus-skill structure. It is a good initial benchmark dataset card and can be extended later with sample statistics, question-type distributions, or representative examples.

## Source Of Truth

The execution source of truth for this benchmark dataset card is:

```text
BENCHCLAW_ROOT/benchmarkDatasetCards/ERQA/SKILL.md
```
