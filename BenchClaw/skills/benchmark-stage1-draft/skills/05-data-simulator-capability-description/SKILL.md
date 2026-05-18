# 05 数据/仿真器能力描述 Skill

## 节点定位

- 节点 ID：`05`
- 英文名：`data-simulator-capability-description`
- 父节点：无，外部能力文档输入节点
- 作用：读取外部数据/仿真器能力文档，描述可用数据源、仿真器、GT 字段、可观测变量和物理/交互能力，为能力维度划分提供客观约束。

## 必读输入

- 直接读取外部描述 skill/card 目录：
  - `BENCHCLAW_ROOT/simulatorCards`：仿真器能力描述。
  - `BENCHCLAW_ROOT/benchmarkDatasetCards`：已有 benchmark 数据集描述。
  - `BENCHCLAW_ROOT/realDatasetCards`：真实数据源描述。
- 若外部能力文档缺失，仍要产出空矩阵和缺失说明，不得从 `03` 推断能力。

## 必写输出

- `stage1/05_data_capability/simulator_capability_matrix.md`
- `stage1/05_data_capability/observable_gt_fields.json`

## 中间文件含义

完整字段、消费方和边界统一维护在仓库根目录的 `contracts/intermediate_files.md`；本节点只保留摘要：

- `simulator_capability_matrix.md`：描述可用数据源/仿真器能提供哪些场景、对象、动作、关系和 GT。
- `observable_gt_fields.json`：把可观测变量和 GT 字段整理成后续节点可解析的字段清单。

## 具体步骤

1. 读取 `BENCHCLAW_ROOT/simulatorCards`，抽取每个仿真器客观支持的场景、对象、动作、关系、GT 字段、可观测变量、可复现实验变量、可执行限制。
2. 读取 `BENCHCLAW_ROOT/benchmarkDatasetCards`，抽取已有 benchmark 数据集的任务类型、数据模态、标注/GT、评测指标、许可和复用限制。
3. 读取 `BENCHCLAW_ROOT/realDatasetCards`，抽取真实数据源的采集条件、数据模态、标注/GT、覆盖范围、质量风险和许可限制。
4. 建立数据/仿真器能力矩阵，并为每条能力保留外部来源引用。
5. 输出 `observable_gt_fields.json`，为后续模板证据合同提供字段基础。

## 质量门

通用质量门见 `contracts/quality_gates.md`；本节点专属质量门：

- 能力矩阵只能描述可用数据源和仿真器能力，不得选择最终仿真器。
- `observable_gt_fields.json` 中每个字段必须声明来源、可用性和限制。
- 没有外部能力文档依据的 GT/变量必须标为未知或缺失。
- 不得读取或依赖 `03` 来补全数据/仿真器能力。
- 三个外部 card 目录中的信息优先级高于本地镜像；若两者冲突，记录冲突和来源，不得擅自合并成确定结论。
