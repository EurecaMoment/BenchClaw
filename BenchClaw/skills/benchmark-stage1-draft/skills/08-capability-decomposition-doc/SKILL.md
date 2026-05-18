# 08 能力拆解文档 Skill

## 节点定位

- 节点 ID：`08`
- 英文名：`capability-decomposition-doc`
- 父节点：03, 05, 06, 07
- 作用：综合意图、文献、仿真器/数据能力、标注能力，划分可测能力维度，并进一步拆出可出题、可测量的细粒度能力考点。

## 必读输入

- 读取父节点 `03` 的 `DONE.json` 和其声明输出。
- 读取父节点 `05` 的 `DONE.json` 和其声明输出。
- 读取父节点 `06` 的 `DONE.json` 和其声明输出。
- 读取父节点 `07` 的 `DONE.json` 和其声明输出。

## 必写输出

- `stage1/08_capability_decomposition/capability_dimensions.md`
- `stage1/08_capability_decomposition/capability_checkpoints.yaml`
- `stage1/08_capability_decomposition/capability_dependency_graph.json`

## 中间文件含义

完整字段、消费方和边界统一维护在仓库根目录的 `contracts/intermediate_files.md`；本节点只保留摘要：

- `capability_dimensions.md`：确认可测能力维度，并说明 construct、证据、GT/标注支撑、测量风险和下属考点。
- `capability_checkpoints.yaml`：列出每个维度下更细粒度的能力考点，供 `09` 生成模板-考点 Q-matrix。
- `capability_dependency_graph.json`：用机器可读图表达能力维度和细粒度考点之间的依赖关系。

## 具体步骤

1. 读取 `03` 的意图文档、`05` 的外部数据/仿真器能力整理、`06` 的外部标注工具能力整理、`07` 的文献分析。
2. 划分能力维度，每个维度必须同时满足：意图相关、文献可解释、数据/仿真器可观测、标注/GT 可支撑。
3. 在每个能力维度下拆出细粒度能力考点；每个考点必须是可被题目模板覆盖、可被证据字段或标注输出观测、可被指标或判定规则评分的最小测量单元。
4. 为每个维度写出：dimension_id、construct definition、observable evidence、candidate task family、measurement risk、dependency、checkpoint_refs。
5. 为每个考点写出：checkpoint_id、dimension_id、checkpoint_name、measurable_behavior、required_evidence、candidate_template_affordances、scoring_observation、measurement_risk、source_refs。
6. 输出 `capability_dimensions.md`、`capability_checkpoints.yaml` 与 `capability_dependency_graph.json`。

## 质量门

通用质量门见 `contracts/quality_gates.md`；本节点专属质量门：

- 每个能力维度必须同时有意图相关性、文献解释、数据/仿真器可观测性和标注/GT 支撑。
- 每个细粒度能力考点必须隶属于且只隶属于一个能力维度，并使用稳定 `checkpoint_id`。
- 考点必须足够细，能被一个或多个出题模板显式覆盖；不能只是维度名称的同义改写。
- `capability_dependency_graph.json` 只能表达能力依赖，不得混入执行排期。
- 不得产生没有 GT 或标注支撑的能力维度或细粒度考点。
- 不只按文献分类划分能力维度。
