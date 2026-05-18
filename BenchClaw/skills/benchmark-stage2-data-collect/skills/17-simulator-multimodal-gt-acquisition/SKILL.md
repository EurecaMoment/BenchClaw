# Skill 17 — 仿真器多模态数据与 GT 采集

## 角色

本节点对应手绘图中的 **仿真器 → 多模态维度数据 + GT** 分支。  
它调用节点 14 注册的仿真器 Skill，根据节点 13 的执行计划采集多模态观测、轨迹、事件日志和 simulator privileged GT。

## 依赖

```text
parents = ["13", "14"]
```

## 允许读取

```text
WORKSPACE_ROOT/stage2/13-execution-plan-ingest/**
WORKSPACE_ROOT/stage2/14-simulator-skill-registry/**
simulator_outputs/**
WORKSPACE_ROOT/sim_runs/**
```

## 禁止读取

```text
WORKSPACE_ROOT/stage2/15-real-image-acquisition/**
WORKSPACE_ROOT/stage2/16-existing-benchmark-acquisition/**
```

## 必须输出

```text
WORKSPACE_ROOT/stage2/17-simulator-multimodal-gt-acquisition/
  observations/
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
  "observation_paths": {},
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
2. 读取 14 的 simulator registry，选择可执行 simulator skill。
3. 逐仿真器生成 run config。
4. 调用 simulator skill 执行采集。
5. 保存 RGB/depth/semantic/instance/pose/event/state 等原始输出。
6. 记录 simulator seed、版本、地图、对象状态、传感器配置。
7. 输出 trace manifest、GT manifest 和 provenance。
8. 对每条 GT 写明 provenance，不允许 LLM 代填。

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
