# 10 选择的模拟器 Skill

全局路径约束：`BENCHCLAW_ROOT` 仅作只读输入；`WORKSPACE_ROOT` 是本次流程唯一总工作目录，所有写操作和流程产物只能落在其下。

## 节点定位

- 节点 ID：`10`
- 英文名：`simulator-selection`
- 父节点：08, 05
- 作用：基于能力维度和仿真器能力矩阵选择可执行的仿真器组合。

## 必读输入

- 读取父节点 `08` 的 `DONE.json` 和其声明输出。
- 读取父节点 `05` 的 `DONE.json` 和其声明输出。

## 必写输出

- `stage1/10_simulator_selection/selected_simulators.md`
- `stage1/10_simulator_selection/simulator_routing.json`

## 中间文件含义

完整字段、消费方和边界统一维护在仓库根目录的 `contracts/intermediate_files.md`；本节点只保留摘要：

- `selected_simulators.md`：说明选中/排除仿真器的理由、覆盖率、缺口和回退方案。
- `simulator_routing.json`：把能力维度或模板路由到具体仿真器及其可提供的 GT/变量。

## 具体步骤

1. 读取 `08_capability_decomposition/capability_dimensions.md` 与 `05_data_capability/simulator_capability_matrix.md`。
2. 对每个能力维度匹配可用仿真器。
3. 对每个被选中的仿真器，明确列出可执行场景/地图/任务上下文，并把“每个选中场景至少采集 50 个时刻帧的数据”写入选择理由和路由约束。
4. 输出选择理由、覆盖率、缺口、回退方案和路由表。
5. 写出 `selected_simulators.md` 与 `simulator_routing.json`。

## 质量门

通用质量门见 `contracts/quality_gates.md`；本节点专属质量门：

- 选择仿真器必须说明能力覆盖、必要 GT/变量、缺口和回退方案。
- `simulator_routing.json` 中每条路由必须能回到 `05` 和 `08` 的依据。
- 不得因知名度或便利性选择无法支撑证据需求的仿真器。
- 对被选中的仿真器场景，不得把采集规模写成“少量样例”“若干帧”“视情况抽样”；最低约束必须是每个场景至少 50 个时刻帧的数据。
