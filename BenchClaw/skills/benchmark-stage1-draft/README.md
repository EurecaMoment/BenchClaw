# benchclaw_stage1_dag_skill_pack

这是按手绘 Stage1 流程重做的非串行 Skill 包。核心文件：

- `SKILL.md`：总调度 skill。
- `dag.json` / `dag.yaml`：DAG 依赖与并行层。
- `skills/*/SKILL.md`：每个子流程自己的 skill。
- `contracts/intermediate_files.md`：Stage1 中间文件含义与最低字段的单一契约。
- `contracts/quality_gates.md`：Stage1 通用质量门的单一契约。
- `scripts/validate_dag.py`：检查是否误写成串行链。
- `templates/`：Stage1 关键输出模板。

核心并行点：

- `02 query 改写` 与 `03 意图理解扩写文档` 分支。
- `00 idea 接收`、`05 数据/仿真器能力描述`、`06 标注能力描述` 都可从外部输入启动；`05/06` 不是由 `03` 产出的分支。
- `04 搜索可用文献` 独立于 `05/06`，等 `02` 完成后运行。
- `09 初版模板集与指标集`、`10 选择的模拟器`、`11 选择的标注工具` 并行。
- `12 benchmark 草稿` 先汇总 0–11；`13 执行计划` 只能依赖 `12`。
