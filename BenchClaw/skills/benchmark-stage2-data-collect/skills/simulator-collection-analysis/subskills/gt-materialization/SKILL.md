---
name: benchclaw-stage2-simulator-gt-materialization
description: Use for the specific BenchClaw subskill `stage2-simulator-gt-materialization` only when its parent node explicitly dispatches to it.
---

# Subskill — 仿真器 GT 物化

## 作用域

本 subskill 只物化一个仿真器任务族 work unit 的 GT。不要写入其他仿真器或任务族目录，也不要直接追加写 bundle 根目录下的汇总文件。

## 输入

- `simulator_id`
- `simulator_card_skill`
- `task_family`
- `data-acquisition` 本次真实运行产生的观测、状态日志、动作记录、场景配置、随机种子和运行日志

## tmux 采集监控硬约束

本 subskill 执行 privileged state 读取、官方状态接口调用、GT 导出、GT 校验或仿真器卡声明的外部命令时，必须使用父节点传入的 `tmux_session_name`、`log_path`、`monitoring_log_path` 后台执行。

- 启动命令必须形如：`tmux new-session -d -s <tmux_session_name> "<command> > <log_path> 2>&1; printf '\nEXIT_CODE:%s\n' \$? >> <log_path>"`。
- 启动后立即检查一次 `tmux has-session -t <tmux_session_name>`、`tmux capture-pane -pt <tmux_session_name>` 和 `tail -n 100 <log_path>`。
- 只要会话仍在运行，必须每 15 秒检查一次 GT 物化状态并追加写 `monitoring_log_path`；检查必须持续到 tmux 会话结束。
- `scenario_manifest.json` 与 `SIMULATOR_REPORT.md` 必须记录 tmux session、日志路径、每 15 秒监控摘要、最终退出状态、GT 记录计数和缺失/失败计数；缺少这些证据时不得向父节点报告完成。

## GT 来源硬规则

GT 必须来自当前 work unit 本次真实运行产生的 privileged state、仿真器官方状态接口、确定性场景配置，或可验证计算。不得手写 GT、使用未执行产生的样例 GT、从非本次运行缓存复制 GT，或用模型预测结果冒充 GT。

如果 data-acquisition 尚未成功落盘任何真实图像或渲染帧，本 subskill 不得进入完成态，也不得写成最终阻塞结果；应继续等待父 work unit 重新采集，直到至少一个真实图像存在后再进行 GT 物化。零图像情况下，不能把空 GT、模板 GT 或历史缓存 GT 当成本次运行结果。

若无法证明 GT 与本次运行的 `run_id`、`scenario_id`、`seed` 和状态日志对应，必须向父节点报告阻塞原因，由父节点写 `BLOCKED.json` 与 `BLOCKED.md`。

## 处理

1. 按当前 `simulator_card_skill` 识别 privileged state、传感器状态、对象状态、碰撞/接触、位姿、可见性、任务成功条件等可用 GT 来源。
2. 按 `templates/collection_bundle_contract.md` 规整 GT。标准字段统一写入 envelope，仿真器特有 GT 字段完整保留到 `gt_fields`、`source_fields`、`raw_record` 或 `extra_metadata`。
3. 从本次运行的状态日志或仿真器官方接口导出 GT，并为每个字段记录来源。
4. 将 GT 写入当前 work unit 的 `privileged_gt.jsonl`。
5. 校验每条 GT 记录能关联到对应 `simulator_id`、`task_family`、`run_id`、`scenario_id`、`seed` 和观测帧。
6. 若对应 work unit 的观测媒体计数为 0，不得输出 `DONE.json`；必须把该 work unit 视为仍在采集重试中，直到真实图像出现为止。

## 规整字段

`privileged_gt.jsonl` 每条记录必须包含：

- `record_id`
- `data_source_type = simulator`
- `simulator_id`
- `task_family`
- `source_card_skill`
- `run_id`
- `scenario_id`
- `seed`
- `step_index` 或时间戳
- `gt_fields`
- `gt_source`
- `linked_state_record_id`
- `linked_media_ids`
- `source_fields`
- `raw_record`
- `extra_metadata`
- `validation`

如果 GT 包含对象级、关系级、轨迹级、可见性、接触/碰撞、成功条件、几何量或语义图字段，必须全部保留；不能只保留单个 success 或 reward 字段。

## 反糊弄质量门

写入完成前必须检查：

- `privileged_gt.jsonl` 非空，除非执行计划明确允许该任务族无 GT。
- 每条 GT 都能关联到本次运行的 `run_id`、`scenario_id`、`seed`、状态记录和观测帧。
- `gt_source` 说明字段来自 privileged state、官方接口、确定性配置或可验证计算。
- 不存在手写 GT、模型预测冒充 GT、未执行样例 GT、非本次运行缓存 GT。
- GT 字段覆盖情况、失败/缺失字段和阻塞原因写入 `scenario_manifest.json` 与 `SIMULATOR_REPORT.md`。

## 输出

只写入当前 work unit 的隔离目录：

```text
artifacts/data_16_simulator_collection_bundle/simulators/<simulator_id>/<task_family>/
  run_logs/
  privileged_gt.jsonl
  scenario_manifest.json
  SIMULATOR_REPORT.md
```

每条 `privileged_gt.jsonl` 记录必须包含：

- `simulator_id`
- `task_family`
- `source_card_skill`
- `run_id`
- `scenario_id`
- `seed`
- `gt_fields`
- `gt_source`
- 对应观测或状态日志路径
