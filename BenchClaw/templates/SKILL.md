# BenchClaw Fixed Template Library Skill

Use this package as the Stage4 question-template library for BenchClaw.

Agent selection entrypoint:

1. Read `template_library/benchclaw_fixed_template_registry.yaml`.
2. Use `template_sets.strict_core` by default.
3. Unlock `strict_depth` only when reliable depth/depth-derived fields exist.
4. Unlock temporal/pose/3D extended templates only when the manifest contains the declared required fields.
5. Never select any template in `deprecated_locked`.

Hard constraints:

- No three-way unanswerable questions.
- All numeric answers must be interval choices.
- No hidden metadata output such as object_id or depth_median.
- No GT field names in model-facing question text.
- All instance-level choices must be grounded by overlay labels.
- Answer uniqueness is required before generation.

Run validation before use:

```bash
python tools/validate_strict_template_library.py
```
