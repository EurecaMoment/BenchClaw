# reference_library

本目录是 `template-metric-code-generation` skill 的外挂参考库，用于将统一模板包中的候选模板过滤/适配到 BenchClaw 的图像/视频 + 仿真器或半监督 GT 制造范式。

文件：

- `BENCHCLAW_IMAGE_VIDEO_TEMPLATE_METRIC_LIBRARY.md`：完整人类可读参考，包含 10 类保留模板、schema、GT 规则、指标和准入规则。
- `template_family_registry.yaml`：机器可读的保留模板族、允许媒体、GT 来源、answer type 和主指标映射。
- `answer_type_metric_registry.json`：机器可读的 answer type 与 deterministic evaluator registry。
- `schema_patch_notes.md`：对 stage item schema 的适配说明和 provenance/题面约束。

使用原则：

1. 本目录不替代 `BENCHCLAW_ROOT/templates/` 统一模板包。
2. 本目录用于过滤和适配：只有能映射到保留模板族、保留 answer type、deterministic metric 和可审计 GT 的模板，才允许 enabled。
3. 与 stage schema 或统一模板包硬契约冲突时，不能擅自绕过硬契约；应 blocked/disabled 并记录原因。
