# Stage1 通用质量门

本文件是所有 Stage1 子 skill 共享质量门的单一维护点。子 skill 只保留节点专属质量门；如有冲突，以本文件和 `contracts/intermediate_files.md` 为准。

## 全局质量门

- Traceability：每个业务结论必须标注来源，来源可以是用户 idea、父节点产物、检索文献、仿真器能力卡或工具能力卡。
- Contract alignment：业务产物必须符合 `contracts/intermediate_files.md` 中对应文件的含义、最低字段和边界。
- No hallucinated capability：不得声称某个仿真器、数据源或工具支持某能力，除非输入材料或父节点产物明确支持。
- Local output only：每个节点只写自己的输出目录，不覆盖其他节点产物。
- Parent-only inputs：每个节点只读取 DAG 声明的父节点输出和允许的输入目录；`13` 只能读取 `12`。
- Explicit uncertainty：缺失信息、歧义和低置信判断必须显式标记，不能用猜测补齐。
- DONE marker：节点结束时必须写 `DONE.json`，且 `outputs_written` 与实际产物一致。

## 节点专属质量门

节点专属质量门写在各自的 `skills/<id>-*/SKILL.md` 中，只描述该节点额外需要防止的失败模式。
