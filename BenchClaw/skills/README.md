# BenchClaw Production Skill Engineering Bundle

这是一个面向生产流程的 BenchClaw skill 工程骨架。根目录 `SKILL.md` 是启动入口；`benchmark-pipeline/SKILL.md` 是 Stage1 到 Stage5 的总控；各 stage 目录中的 `SKILL.md`、`dag.json`、`contracts/`、`skills/` 和 `templates/` 定义了可由大模型执行的最小完整流程。

## 目录

```text
SKILL.md
benchmark-pipeline/
benchmark-stage1-draft/
benchmark-stage2-data-collect/
benchmark-stage3-evidence-compiler/
benchmark-stage4-build/
benchmark-stage5-eval/
```

## 使用方式

把本目录放到：

```text
BENCHCLAW_ROOT/skills/
```

或将其中各 skill 目录合并到已有 `BENCHCLAW_ROOT/skills/`。启动时让模型读取最外层 `SKILL.md`，之后由 `benchmark-pipeline/SKILL.md` 接管。

本工程不提供脚本总驱动；调度由 skill 文档和 DAG 契约完成。
