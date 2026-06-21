---
name: benchclaw-stage2-simulator-collection-analysis
description: Use for the specific BenchClaw node skill `stage2-simulator-collection-analysis` only when its parent stage explicitly dispatches to it.
---

# Node Skill — 仿真器采集与分析

## 内部层级

本节点包含两个 subskill，按每个仿真器和任务族独立运行。运行时必须优先按已注册 skill 名调度，下面的路径仅用于源码定位：

```text
subskills/data-acquisition/SKILL.md
subskills/gt-materialization/SKILL.md
```

## Registered Subskill Names

本节点的内部 DAG 在 opencode 中必须显式调用以下 skill 名：

- `data-acquisition` -> `benchclaw-stage2-simulator-data-acquisition`
- `gt-materialization` -> `benchclaw-stage2-simulator-gt-materialization`

## Work Unit Context Return Protocol

每个仿真器 work unit 只返回：`simulator_id`、`task_family`、`status`、per-work-unit 输出目录、观测/状态/GT 计数、重试次数、阻塞原因和一句摘要。不要回灌长运行日志、长状态序列或大批 privileged GT 正文。

## 动态仿真器发现

1. 使用冻结的 `BENCHCLAW_ROOT`，定位仿真器卡根目录：

```text
BENCHCLAW_ROOT/simulatorCards
```

2. 运行时枚举该目录的直接子文件夹；不要硬编码任何仿真器名称，也不要修改该目录下的任何文件。
3. 每个直接子文件夹代表一个候选仿真器。该文件夹必须包含：

```text
<simulator_folder>/SKILL.md
```

4. 若计划要求执行的仿真器文件夹缺少 `SKILL.md`，不可静默跳过；必须在本节点写入 `BLOCKED.json` 与 `BLOCKED.md`，说明缺失的仿真器文件夹和期望的 skill 路径。
5. 若没有发现任何仿真器文件夹，只有在 `stage2_execution_plan.yaml` 明确说明本项目不需要仿真器数据时，才可写入空 bundle；否则必须阻塞。

## 输入

- `stage2_execution_plan.yaml`
- `BENCHCLAW_ROOT/simulatorCards/*/SKILL.md` 动态发现到的仿真器卡
- 每个仿真器卡中声明的环境配置、启动方式、任务接口、输出格式和限制

## tmux 后台采集监控硬约束

本节点内所有仿真器启动、任务运行、replay、观测采集、状态日志采集和 GT 物化命令，都必须按 `stage2_execution_plan.yaml` 中对应 DAG 节点的 `tmux_required: true` 执行。

1. 每个可执行 DAG 节点必须用 `tmux new-session -d -s <tmux_session_name> "<command> > <log_path> 2>&1; printf '\nEXIT_CODE:%s\n' \$? >> <log_path>"` 后台启动，不得在前台长时间运行仿真器或 replay。
2. 启动后立即用 `tmux has-session -t <tmux_session_name>`、`tmux capture-pane -pt <tmux_session_name>` 和 `tail -n 100 <log_path>` 检查一次。
3. 只要 tmux 会话仍存在，就必须每 15 秒检查一次采集状态；任一活跃会话两次检查间隔不得超过 15 秒。检查内容至少包括会话是否存活、最近 pane 输出、最近 100 行日志、场景/step/观测媒体/状态/动作/GT 已落盘计数。
4. 每次检查必须追加写入 `monitoring_log_path`，记录 `timestamp`、`tmux_session_name`、`dag_node_id`、`status`、`log_tail_summary`、`artifact_counts`；直到 `tmux has-session` 显示会话结束为止。
5. 会话结束后必须读取最终日志和 `EXIT_CODE`，校验 per-simulator 输出目录、观测媒体、state/action logs、privileged GT、manifest 和样本计数；缺少 15 秒监控记录、最终日志或真实运行产物时，不得写 `DONE.json`。
6. 任何一次采集如果没有真实图像或渲染帧落盘，都只能算 transient failure，必须立即回到采集循环重新尝试；不得把零图像结果当作完成、阻塞终局或可接受空结果，也不得写 `DONE.json`、`BLOCKED.json` 作为这次零图像尝试的终局。

## 每仿真器并行 work unit

先从 `stage2_execution_plan.yaml` 解析本阶段需要执行的仿真器和任务族。若计划没有显式列出子集，但要求产出 `data_16_simulator_collection_bundle`，则将动态发现到的所有合法仿真器卡视为待执行对象。

对每个待执行仿真器和任务族创建独立 work unit：

```text
simulator_id = 文件夹名
simulator_card_skill = BENCHCLAW_ROOT/simulatorCards/<simulator_id>/SKILL.md
task_family = stage2_execution_plan.yaml 中对该仿真器要求执行的任务族
```

每个 work unit 必须先读取自己的 `simulator_card_skill`，再在该仿真器卡的指导下依次运行：

1. `benchclaw-stage2-simulator-data-acquisition`
2. `benchclaw-stage2-simulator-gt-materialization`

执行时必须优先读取 `stage2_execution_plan.yaml` 的 `parallel_dag.nodes[]`，只选择 `category: simulator` 且 `parent_category_node: simulator-collection-analysis` 的节点作为本节点内部 DAG。每个仿真器与任务族 work unit 必须在计划中存在以下两个具体 DAG 节点：

```text
simulator::<simulator_id>::<task_family>::data-acquisition
simulator::<simulator_id>::<task_family>::gt-materialization
```

这两个节点必须分别精确调用对应的已注册 skill 名；文件路径只作为源码定位：

```text
benchclaw-stage2-simulator-data-acquisition
benchclaw-stage2-simulator-gt-materialization
```

如果 `stage2_execution_plan.yaml` 没有显式列出某个仿真器任务族的上述 DAG 节点、节点缺少 `subskill_path`、`subskill_path` 指向其他类别，或不同仿真器/任务族之间被错误建立依赖，必须 BLOCKED，不得自行补一个隐式串行流程。

不同仿真器或任务族 work unit 之间可以并行处理。并行时必须遵守：

- `stage2_execution_plan.yaml`、仿真器卡、仿真器安装目录和基础资源只读。
- 每个 work unit 只能写入自己的 per-simulator 输出目录。
- 不允许多个 work unit 同时追加写 bundle 根目录下的汇总 JSONL/YAML。
- 所有 per-simulator work unit 完成后，再进行一次串行汇总。

## 真实采集要求

每个待执行 work unit 必须真实运行对应仿真器采集数据，不能只读取仿真器卡、写占位文件、登记外部路径、复述计划或使用未执行产生的样例数据。

如果某次执行后观测图像、渲染帧或可解码媒体计数为 0，这不是成功结果，也不是可以退出的阻塞结果；必须继续保持 work unit 身份，更新 retry 计数、时间戳和 run 记录，再次启动采集，直到至少一个真实图像写入 `observations/` 和 `media_manifest.jsonl`。在出现真实图像之前，不得进入完成态。

每个 work unit 必须记录并物化：

- 实际执行命令或 API 调用入口
- 环境版本、依赖版本、场景配置和随机种子
- 运行日志、退出状态和失败堆栈，如有
- 本次运行生成的观测媒体、状态日志、动作记录和 privileged GT
- 从运行产物到 workspace 文件的映射
- 零图像重试历史、每次尝试的媒体计数、最终成功运行号和累计重试次数

若仿真器卡缺失、计划无效或没有可调用入口，必须阻塞；但只要已经进入运行采集流程，启动失败、任务失败或本轮无图像都不得作为零图像终局退出，必须记录失败并继续重试采集。不可改用未授权数据、历史缓存、手写 GT 或模拟输出替代。只有当 `stage2_execution_plan.yaml` 和仿真器卡都明确允许使用某个既有 replay/recording 作为执行输入时，才可读取 replay，但仍必须实际运行 replay 采集流程并记录命令与日志。

## Per-simulator 输出目录

每个 work unit 先写入隔离目录：

```text
artifacts/data_16_simulator_collection_bundle/simulators/<simulator_id>/<task_family>/
  observations/
  media_manifest.jsonl
  state_logs.jsonl
  actions.jsonl
  privileged_gt.jsonl
  scenario_manifest.json
  run_logs/
  SIMULATOR_REPORT.md
```

每条 `state_logs.jsonl`、`actions.jsonl` 与 `privileged_gt.jsonl` 记录必须遵守 `templates/collection_bundle_contract.md` 的统一样本 envelope 或可追溯运行记录结构，并至少带有：

- `simulator_id`
- `task_family`
- `source_card_skill`
- `scenario_id`
- `seed`
- `run_id`
- workspace 内稳定可访问的媒体、状态或 GT 路径

## 处理

1. 动态发现 `simulatorCards` 下的所有仿真器文件夹和对应 `SKILL.md`。
2. 根据 `stage2_execution_plan.yaml` 确定需要真实执行的仿真器和任务族。
3. 对每个待执行仿真器和任务族真实运行仿真器，采集观测、状态、动作、场景配置和 privileged GT。
4. 在各自 per-simulator 目录中物化观测媒体、媒体 manifest、状态日志、GT、随机种子、环境版本、执行命令和运行日志。
5. 如果采集结果中没有真实图像或渲染帧，不能结束当前 work unit；必须记录本次失败尝试并立刻重试。采集失败必须记录失败原因与复现命令，不可改用未授权数据、历史缓存或占位产物替代。
6. 所有 work unit 完成后，串行汇总 per-simulator 结果到 bundle 根目录。

## 汇总输出

- `artifacts/data_16_simulator_collection_bundle/observations/`
- `artifacts/data_16_simulator_collection_bundle/simulators/<simulator_id>/<task_family>/...`
- `artifacts/data_16_simulator_collection_bundle/media_manifest.jsonl`
- `artifacts/data_16_simulator_collection_bundle/state_logs.jsonl`
- `artifacts/data_16_simulator_collection_bundle/actions.jsonl`
- `artifacts/data_16_simulator_collection_bundle/privileged_gt.jsonl`
- `artifacts/data_16_simulator_collection_bundle/scenario_manifest.json`
- 节点执行记录文件

`scenario_manifest.json` 必须记录：

- `simulator_cards_root`
- 动态发现到的所有仿真器文件夹
- 每个待执行仿真器的 `simulator_card_skill`
- 每个 work unit 的 `simulator_id`、`task_family`、`run_id`、执行命令、随机种子、环境版本和 per-simulator 输出目录
- 每个 work unit 的 `tmux_session_name`、`log_path`、`monitoring_log_path`、15 秒监控记录摘要和最终退出状态
- 真实采集产物清单和校验信息
- 被阻塞的仿真器、任务族及原因，如有
