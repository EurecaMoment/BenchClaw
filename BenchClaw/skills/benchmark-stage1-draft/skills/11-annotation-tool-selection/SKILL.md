# 11 选择的标注工具 Skill

全局路径约束：`BENCHCLAW_ROOT` 仅作只读输入；`WORKSPACE_ROOT` 是本次流程唯一总工作目录，所有写操作和流程产物只能落在其下。

## 节点定位

- 节点 ID：`11`
- 英文名：`annotation-tool-selection`
- 父节点：08, 06
- 作用：基于能力维度和标注能力矩阵选择自动/半自动标注工具组合。

## 必读输入

- 读取父节点 `08` 的 `DONE.json` 和其声明输出。
- 读取父节点 `06` 的 `DONE.json` 和其声明输出。

## 必写输出

- `stage1/11_annotation_tool_selection/selected_annotation_tools.md`
- `stage1/11_annotation_tool_selection/tool_routing.json`

## 中间文件含义

完整字段、消费方和边界统一维护在仓库根目录的 `contracts/intermediate_files.md`；本节点只保留摘要：

- `selected_annotation_tools.md`：说明选中/排除标注工具的理由、用途、置信度用法和失败回退。
- `tool_routing.json`：把证据字段、模板或能力维度路由到具体标注工具和 I/O 合同。

## 具体步骤

1. 读取 `08_capability_decomposition/capability_dimensions.md` 与 `06_annotation_capability/annotation_capability_matrix.md`。
2. 对每个能力维度和证据字段匹配标注工具。
3. 输出工具选择、用途、I/O、置信度利用方式、失败回退和路由表。
4. 写出 `selected_annotation_tools.md` 与 `tool_routing.json`。

## 质量门

通用质量门见 `contracts/quality_gates.md`；本节点专属质量门：

- 选择工具必须说明证据字段覆盖、I/O 合同、置信度用法和失败回退。
- `tool_routing.json` 中每条路由必须能回到 `06` 和 `08` 的依据。
- 不得把工具选择写成泛泛模型推荐清单。
- 不用大模型标注替代小模型/程序化标注，除非用户明确允许。
