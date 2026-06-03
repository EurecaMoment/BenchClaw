# Subskill — 仿真器数据采集

## 作用域

本 subskill 只处理一个仿真器任务族 work unit。work unit 由父节点动态创建：

```text
simulator_id = simulatorCards 下的直接子文件夹名
simulator_card_skill = BENCHCLAW_ROOT/simulatorCards/<simulator_id>/SKILL.md
task_family = stage2_execution_plan.yaml 中对该仿真器要求执行的任务族
```

不要假设固定仿真器名单；必须以传入的 `simulator_card_skill` 为该仿真器的执行来源。

## 输入

- `stage2_execution_plan.yaml`
- `simulator_id`
- `simulator_card_skill`
- `task_family`
- 仿真器卡中声明的环境配置、启动方式、任务接口、输出格式和限制

## tmux 采集监控硬约束

本 subskill 执行仿真器启动、任务运行、replay、观测渲染、状态/动作日志采集或仿真器卡声明的外部命令时，必须使用父节点传入的 `tmux_session_name`、`log_path`、`monitoring_log_path` 后台执行。

- 启动命令必须形如：`tmux new-session -d -s <tmux_session_name> "<command> > <log_path> 2>&1; printf '\nEXIT_CODE:%s\n' \$? >> <log_path>"`。
- 启动后立即检查一次 `tmux has-session -t <tmux_session_name>`、`tmux capture-pane -pt <tmux_session_name>` 和 `tail -n 100 <log_path>`。
- 只要会话仍在运行，必须每 15 秒检查一次采集状态并追加写 `monitoring_log_path`；检查必须持续到 tmux 会话结束。
- `scenario_manifest.json` 与 `SIMULATOR_REPORT.md` 必须记录 tmux session、日志路径、每 15 秒监控摘要、最终退出状态、场景计数、step 计数、观测媒体计数、状态/动作计数；缺少这些证据时不得向父节点报告完成。

## 真实采集硬规则

必须真实运行当前仿真器和任务族，采集本次运行产生的数据。不能只读取卡片、登记外部路径、生成占位 JSON、复述计划、手写状态日志或使用未执行产生的样例数据。

若仿真器启动失败、任务配置缺失、依赖不可用或无权限运行，必须向父节点报告阻塞原因；不可降级为伪造采集结果。

## 处理

1. 读取且仅按当前 `simulator_card_skill` 准备仿真器环境和任务。
2. 按 `stage2_execution_plan.yaml` 的任务族、场景数量、种子和采样要求运行仿真器。
3. 按 `templates/collection_bundle_contract.md` 规整本次运行的观测和状态。标准字段统一写入 envelope，仿真器特有状态、传感器字段、任务参数和环境字段完整保留到 `source_fields`、`raw_record` 或 `extra_metadata`。
4. 采集观测媒体、状态日志、动作记录、场景配置、随机种子、环境版本和运行日志。
5. 为每个观测媒体写 `media_manifest.jsonl`。图片或渲染帧必须真实落盘，存在、非空、sha256 已记录、可解码，并记录宽高、通道或色彩模式。
6. 记录实际执行命令或 API 调用入口、退出状态、运行时长和复现参数。
7. 不修改 `simulatorCards` 中的任何文件；仿真器卡、安装目录和基础资源均视为只读。

## 规整字段

`state_logs.jsonl`、`actions.jsonl` 和 `media_manifest.jsonl` 必须能共同还原每个观测步：

- `record_id`
- `data_source_type = simulator`
- `simulator_id`
- `task_family`
- `source_card_skill`
- `run_id`
- `scenario_id`
- `seed`
- `step_index` 或时间戳
- `workspace_media` 与 `media_ids`
- `state`
- `action`
- `scenario_config`
- `source_fields`
- `raw_record`
- `extra_metadata`
- `provenance`
- `validation`

如果某个仿真器提供 RGB、深度、分割、mask、语义图、点云或多视角图像，必须保留各自的 `role` 和时间/帧对应关系，不能只留一种默认图像。

## 反糊弄质量门

写入完成前必须检查：

- `state_logs.jsonl`、`actions.jsonl`、`scenario_manifest.json` 和 `media_manifest.jsonl` 非空，除非执行计划明确允许某类输出为空。
- 每个计划要求的场景或任务族都有真实执行记录、运行日志、退出状态和 run_id。
- 每个观测媒体路径都在 workspace 内真实存在且非空。
- 图片或渲染帧可解码，manifest 中尺寸与实际尺寸一致。
- 不存在 placeholder、dummy、fake、TODO、手写状态日志或未执行样例数据被当作有效采集结果。
- 采集计数、失败计数、种子、环境版本、执行命令和产物校验写入 `scenario_manifest.json`。

## 输出给本 work unit

只写入父节点为该 work unit 分配的隔离目录：

```text
artifacts/data_16_simulator_collection_bundle/simulators/<simulator_id>/<task_family>/
  observations/
  media_manifest.jsonl
  state_logs.jsonl
  actions.jsonl
  scenario_manifest.json
  run_logs/
```

每条记录必须包含：

- `simulator_id`
- `task_family`
- `source_card_skill`
- `scenario_id`
- `seed`
- `run_id`
- workspace 内媒体、状态或动作路径
- `raw_record` 或 `source_fields` 中的仿真器原始关键字段
