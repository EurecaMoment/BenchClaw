# 09 初版模板集与指标集 Skill

全局路径约束：`BENCHCLAW_ROOT` 仅作只读输入；`WORKSPACE_ROOT` 是本次流程唯一总工作目录，所有写操作和流程产物只能落在其下。

## 节点定位

- 节点 ID：`09`
- 英文名：`initial-template-metric-set`
- 父节点：08, 07
- 作用：从能力维度和细分能力考点推出初版评测模板、证据需求、指标模板和模板-考点 Q-matrix。

## 必读输入

- 读取父节点 `08` 的 `DONE.json` 和其声明输出。
- 读取父节点 `07` 的 `DONE.json` 和其声明输出。

## 必写输出

- `stage1/09_templates_metrics/template_set.yaml`
- `stage1/09_templates_metrics/metric_set.yaml`
- `stage1/09_templates_metrics/evidence_contracts.yaml`
- `stage1/09_templates_metrics/q_matrix.csv`

## 中间文件含义

完整字段、消费方和边界统一维护在仓库根目录的 `contracts/intermediate_files.md`；本节点只保留摘要：

- `template_set.yaml`：初版评测 item/template 集合，描述任务形态、所需证据和反捷径约束。
- `metric_set.yaml`：可计算指标或待淘汰指标候选集合，描述输入字段、计算方式和失败情形。
- `evidence_contracts.yaml`：模板和指标运行时需要哪些 GT、标注输出、校验和来源证明。
- `q_matrix.csv`：模板-考点 Q-matrix；行是出题模板，列是细分能力考点，值为 0/1，用于后续教育学分析。

## 具体步骤

1. 读取 `08_capability_decomposition/capability_dimensions.md`、`08_capability_decomposition/capability_checkpoints.yaml` 和 `07_literature_analysis/benchmark_design_evidence.md`。
2. 针对已经分析得到的能力维度和细分能力考点设计初版 item template、evidence contract 和 metric template。
3. 每个出题模板必须且只能属于一个能力维度，并声明 `capability_dimension`。
4. 每个出题模板可以覆盖多个细分能力考点，并在 `checkpoint_refs` 中列出；同一个考点可以被多个模板复用。
5. 每个模板必须声明所需 GT 字段、标注输出、可计算指标、失败判定、反捷径约束。
6. 生成 `q_matrix.csv`：第一列为 `template_id`，第二列为 `capability_dimension`，后续每列为一个 `checkpoint_id`；若模板覆盖该考点则填 `1`，否则填 `0`。
7. 输出 `template_set.yaml`、`metric_set.yaml`、`evidence_contracts.yaml`、`q_matrix.csv`。

## 质量门

通用质量门见 `contracts/quality_gates.md`；本节点专属质量门：

- 每个模板必须声明唯一能力维度、覆盖的细分能力考点、所需 GT/标注输出、反捷径约束和可用指标。
- Q-matrix 的模板行必须与 `template_set.yaml` 的 `template_id` 一致；考点列必须与 `capability_checkpoints.yaml` 的 `checkpoint_id` 一致。
- Q-matrix 中模板不得跨维度覆盖考点；若一个模板需要跨维度，应拆成多个模板。
- 指标必须可计算；主观评分只能作为待淘汰或需审计候选。
- `evidence_contracts.yaml` 只声明证据需求，不选择具体仿真器或标注工具。
- 不把模板和指标绑定到单一仿真器，除非能力本身只能由该仿真器支持。
