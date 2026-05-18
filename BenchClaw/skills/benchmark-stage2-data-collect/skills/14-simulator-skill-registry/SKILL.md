# Skill 14 — 各个仿真器 Skill 注册与适配

## 角色

本节点对应手绘图中的 **14 各个仿真器的 skill**。  
它负责发现、登记、规范化可用仿真器 Skill，为节点 17 提供可调用的 simulator adapter registry。

## 依赖

```text
parents = []
```

本节点可与 13 并行启动。  
它不依赖真实图片分支，不依赖已有 benchmark 分支。

## 路径解析

`BENCHCLAW_ROOT` 必须解析为当前 skill 所在的 BenchClaw 根目录，也就是包含本 `skills/` 目录的父级项目根。  
仿真器 skill/card 只从 `BENCHCLAW_ROOT/simulatorCards` 读取，不使用机器绝对路径，也不扫描其他候选根。

## 允许读取

```text
BENCHCLAW_ROOT/simulatorCards/**
```

## 禁止读取

```text
WORKSPACE_ROOT/stage2/15-real-image-acquisition/**
WORKSPACE_ROOT/stage2/16-existing-benchmark-acquisition/**
WORKSPACE_ROOT/stage2/17-simulator-multimodal-gt-acquisition/**
```

## 必须输出

```text
WORKSPACE_ROOT/stage2/14-simulator-skill-registry/
  simulator_skill_registry.json
  simulator_io_contracts.json
  adapter_plan.md
  USED_INPUTS.json
  DONE.json
```

## simulator_skill_registry.json

建议格式：

```json
[
  {
    "simulator_id": "CARLA",
    "skill_path": "BENCHCLAW_ROOT/simulatorCards/CARLA/SKILL.md",
    "status": "available",
    "supported_modalities": ["rgb", "depth", "semantic", "pose", "bbox"],
    "supported_gt": ["object_pose", "agent_pose", "depth", "segmentation", "map"],
    "launch_command_template": "",
    "collect_command_template": "",
    "known_limits": []
  }
]
```

## simulator_io_contracts.json

必须说明每个仿真器 Skill 的输入输出：

```json
{
  "carla": {
    "inputs": ["scene_config", "route_config", "sensor_config", "seed"],
    "outputs": ["rgb", "depth", "pose", "object_state", "map_state", "event_log"],
    "gt_provenance": "simulator_privileged_state"
  }
}
```

## 执行步骤

1. 扫描 `BENCHCLAW_ROOT/simulatorCards` 下的可用 simulator skill 子目录。
2. 对每个 simulator 读取其 `SKILL.md` 或接口说明。
3. 标准化为统一 registry。
4. 标注缺失能力，不伪造可用能力。
5. 写 `USED_INPUTS.json` 与 `DONE.json`。

## DONE.json 格式

```json
{
  "node_id": "14",
  "status": "done",
  "outputs": [
    "simulator_skill_registry.json",
    "simulator_io_contracts.json",
    "adapter_plan.md"
  ],
  "next_ready_hint": ["17"],
  "notes": ""
}
```
