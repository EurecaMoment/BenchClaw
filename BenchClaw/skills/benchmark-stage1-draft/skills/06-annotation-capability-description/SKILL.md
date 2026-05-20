# 06 标注能力描述 Skill

全局路径约束：`BENCHCLAW_ROOT` 仅作只读输入；`WORKSPACE_ROOT` 是本次流程唯一总工作目录，所有写操作和流程产物只能落在其下。

## 节点定位

- 节点 ID：`06`
- 英文名：`annotation-capability-description`
- 父节点：无，外部能力文档输入节点
- 作用：读取外部标注工具能力文档，描述可自动/半自动标注工具的输入、输出、置信度、局限和可调用约束。

## 必读输入

- 优先读取外部标注工具 skill 文档目录：
  - `BENCHCLAW_ROOT/annotation-tool`：标注工具能力、I/O、部署和限制说明。
- 若外部能力文档缺失，仍要产出空矩阵和缺失说明，不得从 `03` 推断工具能力。

## 必写输出

- `stage1/06_annotation_capability/annotation_capability_matrix.md`
- `stage1/06_annotation_capability/tool_io_contracts.md`

## 中间文件含义

完整字段、消费方和边界统一维护在仓库根目录的 `contracts/intermediate_files.md`；本节点只保留摘要：

- `annotation_capability_matrix.md`：描述自动/半自动标注工具支持的任务、输入输出、置信度和限制。
- `tool_io_contracts.md`：定义每个工具可调用时的输入、输出、置信度语义和失败模式。

## 具体步骤

1. 读取 `BENCHCLAW_ROOT/annotation-tool` 下的标注工具 skill 文档。
2. 抽取每个工具客观支持的标注能力：检测、分割、深度、姿态、跟踪、OCR、几何校准、质量评分等。
3. 建立标注能力矩阵，并为每条能力保留外部来源引用。
4. 为每个工具记录输入、输出、置信度、批处理方式、失败条件、是否可服务器部署。

## 质量门

通用质量门见 `contracts/quality_gates.md`；本节点专属质量门：

- 能力矩阵只能描述标注工具能力，不得选择最终工具组合。
- `tool_io_contracts.md` 必须区分工具客观输出和主观判断。
- 不得用大模型主观标注替代客观标注能力，除非用户明确允许。
- 不得读取或依赖 `03` 来补全标注工具能力。
- `BENCHCLAW_ROOT/annotation-tool` 中的信息优先级高于本地镜像；若两者冲突，记录冲突和来源，不得擅自合并成确定结论。
