# Skill 17 — 仿真器多模态数据与 GT 采集

全局路径约束：`BENCHCLAW_ROOT` 仅作只读输入；`WORKSPACE_ROOT` 是本次流程唯一总工作目录，所有写操作和流程产物只能落在其下。

## 角色

本节点对应手绘图中的 **仿真器 → 多模态维度数据 + GT** 分支。  
它调用节点 14 注册的仿真器 Skill，根据节点 13 的执行计划采集多模态观测、轨迹、事件日志和 simulator privileged GT。

本节点必须严格受 13 号节点导出的 `execution_plan.md` 与 `stage2_collection_targets.json` 指导，只能实际采集其中 `simulator_targets` 明确选中的仿真器、场景、任务、模态和 GT 字段；不得脱离 13 的采集目标自行扩展、替换、猜测或补充新的仿真器采集任务。

本节点只能实际调用 `BENCHCLAW_ROOT/simulatorCards/**/SKILL.md` 中声明并被 14 号节点登记为可用的仿真器；不得调用 cards 目录之外的仿真器脚本、服务、二进制、临时 wrapper 或未建卡仿真器。

对于通过本地端口提供服务的仿真器，本节点必须直接连接用户已启动的本地 endpoint 执行采集，不得自行启动、重启或替换仿真器服务。

## 依赖

```text
parents = ["13", "14"]
```

## 允许读取

```text
WORKSPACE_ROOT/stage2/13-execution-plan-ingest/**
WORKSPACE_ROOT/stage2/14-simulator-skill-registry/**
WORKSPACE_ROOT/sim_runs/**
WORKSPACE_ROOT/config/stage2_input_paths.json
BENCHCLAW_ROOT/simulatorCards/**
```

## 禁止读取

```text
WORKSPACE_ROOT/stage2/15-real-image-acquisition/**
WORKSPACE_ROOT/stage2/16-existing-benchmark-acquisition/**
```

## 必须输出

```text
WORKSPACE_ROOT/stage2/<node>/manifest.jsonl
WORKSPACE_ROOT/stage2/17-simulator-multimodal-gt-acquisition/
  observations/
  simulator/
    <simulator_id>/
      <scene_or_map_id>/
        rgb/
        depth/
        semantic/
        instance/
        ...other required modalities...
  provenance/
  sim_trace_manifest.jsonl
  gt_manifest.jsonl
  collection_report.md
  USED_INPUTS.json
  DONE.json
```

## observations/ 建议结构

```text
observations/
  carla/
    episode_000001/
      rgb/
      depth/
      semantic/
      instance/
      pose.jsonl
      event_log.jsonl
  habitat/
    episode_000001/
      rgb/
      depth/
      semantic/
      pose.jsonl
      object_state.jsonl
```

## JSONL canonical storage

本节点的规范化记录应写入 `WORKSPACE_ROOT/stage2/<node>/manifest.jsonl` 的 `simulator_trace_records` 与 `simulator_gt_records` 表。`sim_trace_manifest.jsonl` 与 `gt_manifest.jsonl` 仅作为兼容性导出，不再是唯一真相源。

## sim_trace_manifest.jsonl

每行一个 episode 或 sample：

```json
{
  "sample_id": "sim_000001",
  "simulator_id": "carla",
  "episode_id": "episode_000001",
  "scene_id": "",
  "seed": 0,
  "modalities": ["rgb", "depth", "semantic", "pose"],
  "observation_paths": {
    "rgb": "simulator/<simulator_id>/<scene_or_map_id>/episode_000001/rgb/000001.png"
  },
  "target_dimensions": [],
  "task_context": {},
  "provenance_path": "provenance/sim_000001.json"
}
```

## gt_manifest.jsonl

每行一个 GT 字段：

```json
{
  "sample_id": "sim_000001",
  "gt_field": "object_pose",
  "gt_value_path_or_inline": "",
  "gt_source": "simulator_privileged_state",
  "simulator_query": "",
  "confidence": 1.0,
  "timestamp_or_frame_id": ""
}
```

## 执行步骤

1. 读取 13 的采集目标，确定目标维度、场景、模态和 GT 字段。
2. 读取 14 的 simulator registry，并将 13 中声明的 `simulator_targets` 逐项绑定到 `BENCHCLAW_ROOT/simulatorCards/**/SKILL.md` 中实际存在且被 14 登记为可用的仿真器；若目标无法映射到 card+registry，节点必须阻塞。
3. 仅为这些已映射且被 13 选中的仿真器目标逐项生成 attach config；若该仿真器通过本地端口提供服务，则在 config 中写明实际使用的本地 `host:port`。每个选中场景都必须继承 `simulator_scene_min_timepoints` 约束，且当前最低允许值为 50。
4. 调用这些已登记 simulatorCards 仿真器 skill，连接已启动的本地仿真器服务并执行真实采集；不得只做连通性检查、空跑、计划生成或样例输出。
5. 对每个选中场景，至少采集 `simulator_scene_min_timepoints` 个时刻帧的数据；一个时刻可对应多张图像或多模态观测。按 `simulator/<simulator_id>/<scene_or_map_id>/...` 目录树保存 RGB/depth/semantic/instance/pose/event/state 等原始输出；同一 execution-plan target 要求的图像型观测必须全量落盘，不得只保留抽样帧或导出视频。
6. 记录 simulator seed、版本、地图、对象状态、传感器配置。
7. 输出 trace manifest、GT manifest 和 provenance。
8. 对每条 GT 写明 provenance，不允许 LLM 代填。

## 强制约束

- `observations/` 与 `provenance/` 中必须存在后续 Stage3/Stage4 可实际读取的多模态观测和 GT 证据文件，不能只写 summary、统计数字或空目录。
- 图像型观测文件必须优先落在 `WORKSPACE_ROOT/stage2/17-simulator-multimodal-gt-acquisition/simulator/<simulator_id>/<scene_or_map_id>/` 下，并按 execution-plan 中的 scene/map/task context 分层；不得把不同场景或不同仿真器的图像混写。
- `sim_trace_manifest.jsonl` 与 `gt_manifest.jsonl` 中的路径必须解析到本节点输出目录下的真实文件或内联 GT 值。
- `sim_trace_manifest.jsonl` 中每条记录都必须能追溯到：`13` 中被选中的 `simulator_targets` 之一，以及 `BENCHCLAW_ROOT/simulatorCards/**/SKILL.md` 中被 14 登记为可用的某个仿真器；不得出现无法回溯到这两者的采集记录。
- 对 execution-plan 要求采集的 RGB/depth/semantic/instance 等图像型观测，必须全量保存对应帧文件；不得仅保留压缩视频、抽样截图、统计表、缩略图或“可按需重采”的说明来替代完整落盘。
- 对每个被 13 选中的仿真器场景，实际采集的时刻帧数不得低于 `stage2_collection_targets.json` 中的 `simulator_scene_min_timepoints`，且当前最低允许值为 `50`；低于该值即视为数量不足，节点必须阻塞。
- 若仿真器通过本地端口提供服务，采集前必须先做 endpoint 健康检查；若本地 endpoint 未启动、端口不可达或健康检查失败，本节点必须阻塞，而不是尝试重新启动仿真器。
- 若 13 未选择任何 simulator target，或目标无法映射到 `BENCHCLAW_ROOT/simulatorCards/**` 中已登记的仿真器，本节点必须阻塞，不得自行改写采集范围或写 `DONE.json`。
- 若仿真器采集失败或数量不足，必须阻塞并记录失败原因，不得以空 observations、简化摘要或占位 manifest 冒充完成。

## DONE.json 格式

```json
{
  "node_id": "17",
  "status": "done",
  "outputs": [
    "observations/",
    "provenance/",
    "sim_trace_manifest.jsonl",
    "gt_manifest.jsonl",
    "collection_report.md"
  ],
  "terminal": true,
  "notes": ""
}
```
