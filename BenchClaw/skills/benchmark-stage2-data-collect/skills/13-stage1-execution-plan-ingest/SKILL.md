# Skill 13 — Stage1 执行计划入口校验与导入

## 角色

本节点对应手绘图中的 **13 执行计划**。  
它是 Stage2 的入口节点，只负责读取 Stage1 末端执行计划，抽取 Stage2 所需的数据采集约束。  
它不重新生成 Stage1，不修改 Stage1 产物。

## 依赖

```text
parents = []
```

## 允许读取

```text
WORKSPACE_ROOT/stage1/13-execution-plan/**
WORKSPACE_ROOT/stage1/**/execution_plan.*
WORKSPACE_ROOT/stage1/**/benchmark_draft.*
WORKSPACE_ROOT/stage1/**/traceability.*
WORKSPACE_ROOT/config/stage2_input_paths.json
```

## 禁止读取

```text
WORKSPACE_ROOT/stage2/15-real-image-acquisition/**
WORKSPACE_ROOT/stage2/16-existing-benchmark-acquisition/**
WORKSPACE_ROOT/stage2/17-simulator-multimodal-gt-acquisition/**
```

## 必须输出

```text
WORKSPACE_ROOT/stage2/13-execution-plan-ingest/
  execution_plan.md
  stage2_collection_targets.json
  input_manifest.json
  USED_INPUTS.json
  DONE.json
```

## 输出语义

### execution_plan.md

对 Stage1 执行计划的只读副本或压缩版，至少保留：

```text
1. benchmark 目标；
2. 能力维度；
3. 数据源偏好；
4. 需要的仿真器；
5. 需要的场景/任务/环境/对象/行为等细节；
6. 需要采集的仿真器数据数量（应该对应到每个场景）；
7. 需要的图像/视频/轨迹/传感器字段；
8. 期望 GT 类型；
9. 质量门限。
```

### stage2_collection_targets.json

必须包含：

```json
{
  "target_dimensions": [],
  "real_image_targets": [],
  "existing_benchmark_targets": [],
  "simulator_targets": [],
  "required_modalities": [],
  "required_gt_fields": [],
  "quality_constraints": []
}
```

## 执行步骤

1. 定位 Stage1 node-13 目录。
2. 读取执行计划、benchmark 草稿、追踪表。
3. 抽取 Stage2 三条数据分支的采集目标：
   - 真实图片；
   - 已有 benchmark；
   - 仿真器多模态数据 + GT。
4. 写 `stage2_collection_targets.json`。
5. 写 `USED_INPUTS.json`，记录实际读取路径。
6. 写 `DONE.json`。

## DONE.json 格式

```json
{
  "node_id": "13",
  "status": "done",
  "outputs": [
    "execution_plan.md",
    "stage2_collection_targets.json",
    "input_manifest.json"
  ],
  "next_ready_hint": ["15", "16"],
  "notes": ""
}
```
