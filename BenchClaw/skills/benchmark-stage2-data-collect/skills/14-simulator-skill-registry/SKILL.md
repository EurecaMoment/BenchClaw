# Skill 14 — 各个仿真器 Skill 注册与适配

全局路径约束：`BENCHCLAW_ROOT` 仅作只读输入；`WORKSPACE_ROOT` 是本次流程唯一总工作目录，所有写操作和流程产物只能落在其下。

## 角色

本节点对应手绘图中的 **14 各个仿真器的 skill**。  
它负责发现、登记、规范化可用仿真器 Skill，为节点 17 提供可调用的 simulator adapter registry。

对于通过本地端口提供服务的仿真器，14 号节点只登记“如何连接已启动服务”，不登记也不生成新的启动流程。

## 依赖

```text
parents = []
```

本节点可与 13 并行启动。  
它不依赖真实图片分支，不依赖已有 benchmark 分支。

## 路径解析

`BENCHCLAW_ROOT` 必须解析为当前 skill 所在的 BenchClaw 根目录，也就是包含本 `skills/` 目录的父级项目根。  
仿真器 skill/card 只从 `BENCHCLAW_ROOT/simulatorCards` 读取，不使用机器绝对路径，也不扫描其他候选根。

Node 14 的输入边界进一步收紧为：**以明确列出的 simulator `SKILL.md` 为主输入，以其中显式点名的关键脚本/健康检查文件为可选补充输入**；不得为了“看看目录里还有什么”而对 simulator 目录做大范围通配扫描。

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
    "connection_mode": "attach_existing_local_endpoint",
    "default_endpoint": "127.0.0.1:2000",
    "healthcheck_command_template": "python BENCHCLAW_ROOT/simulatorCards/CARLA/test_connect.py --host {host} --port {port}",
    "collect_command_template": "",
    "known_limits": []
  },
  {
    "simulator_id": "HABITAT",
    "skill_path": "BENCHCLAW_ROOT/simulatorCards/HABITAT/SKILL.md",
    "status": "available",
    "connection_mode": "attach_existing_local_endpoint",
    "default_endpoint": "http://127.0.0.1:8401",
    "healthcheck_command_template": "python -c \"import json,urllib.request;print(json.load(urllib.request.urlopen('http://{host}:{port}/health', timeout=10)))\"",
    "collect_command_template": "",
    "known_limits": []
  },
  {
    "simulator_id": "LIBERO",
    "skill_path": "BENCHCLAW_ROOT/simulatorCards/LIBERO/SKILL.md",
    "status": "available",
    "connection_mode": "attach_existing_local_endpoint",
    "default_endpoint": "http://127.0.0.1:8402",
    "healthcheck_command_template": "python -c \"import json,urllib.request;print(json.load(urllib.request.urlopen('http://{host}:{port}/health', timeout=10)))\"",
    "collect_command_template": "",
    "known_limits": []
  }
]
```

其中：

- `launch_command_template` 对于此类仿真器应保持为空，表示 Stage2 不负责启动服务；
- `default_endpoint` 仅表示默认连接目标，若用户或上游配置提供了其他本地 endpoint，应优先使用显式提供的值。

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

1. 只读取本节点明确要求登记的 simulator `SKILL.md`，默认就是 `CARLA`、`HABITAT`、`LIBERO` 三个 skill 文件；不额外扩展到其他目录扫描，除非上游执行计划明确要求新增 simulator。
2. 从这些 `SKILL.md` 中提取 registry 所需字段：`simulator_id`、`skill_path`、`status`、`supported_modalities`、`supported_gt`、`connection_mode`、`default_endpoint`、`healthcheck_command_template`、`known_limits`。
3. 只有当 `SKILL.md` 中对某个关键脚本路径有明确引用且该路径会直接写入 registry 或 adapter 合同字段时，才允许核对该**具体文件路径**是否存在；禁止为“探测脚本是否存在”而对 `BENCHCLAW_ROOT/simulatorCards/*` 目录执行通配 glob、目录普扫或无边界文件枚举。
4. 对通过本地端口提供服务的仿真器，标准化记录其连接方式、默认 endpoint 和健康检查方式，而不是启动命令。
5. 标注缺失能力，不伪造可用能力；若某个关键脚本路径在 `SKILL.md` 中被明确声明但实际不存在，应在 `adapter_plan.md` 中记为缺失能力或阻塞项，而不是继续做目录级探测。
6. 写 `USED_INPUTS.json` 与 `DONE.json`。

## 最小执行约束

- 能直接从 `SKILL.md` 文本中得到的字段，不得再通过额外 glob/目录扫描去“验证还有没有别的脚本”。
- 若必须做文件存在性校验，只允许针对 `SKILL.md` 中已明确点名的单个文件路径做最小数量的读取或查找。
- 不允许并发发起多个仅用于目录探测的 glob 调用；尤其禁止对 `CARLA/*.py`、`HABITAT/*.py`、`LIBERO/*.py`、`*.sh` 这类通配模式做无差别枚举。
- 目录探测失败不得让节点悬空等待；若最小必要的具体文件校验失败，应立即降级为“按 `SKILL.md` 已知字段生成 registry，并在 `adapter_plan.md` 中记录未校验项”或显式阻塞。

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
