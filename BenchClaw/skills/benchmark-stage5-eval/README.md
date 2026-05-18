# benchclaw_stage5_opencode_ready_skill_pack

This is an Opencode-ready Stage5 skill pack for BenchClaw.

Stage5 is exactly:

```text
38 评测 -> 39 评测报告
```

The pack contains:

```text
SKILL.md
OPENCODE_RUN.md
dag.json
dag.yaml
contracts/node_io_contracts.json
skills/38-evaluation-run/SKILL.md
skills/39-evaluation-report/SKILL.md
scripts/validate_dag.py
scripts/ready_set_runner.py
scripts/check_stage5_outputs.py
scripts/run_evaluation.py
scripts/generate_report.py
```

Run the validator:

```bash
python scripts/validate_dag.py
```
