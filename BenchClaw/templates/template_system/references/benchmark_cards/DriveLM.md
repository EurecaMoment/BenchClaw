# DriveLM 统一参考卡片

> 本卡片来自用户提供的 `DriveLM.md`，已纳入统一模板系统作为设计依据。它不是原始资料备份，而是用于 Stage1/Stage4 的参考切片。

## 在统一模板包中的作用

| 字段 | 内容 |
|---|---|
| benchmark | DriveLM |
| 场景 | 自动驾驶场景（nuScenes 数据集，多摄像头环视） |
| 任务范式 | 图文对话式 VQA，覆盖感知→预测→规划完整链路 |
| 主要能力 | C1 物体识别、C4 物体状态理解、C20 时间变化理解、C23 操作后果预测、C25 任务规划、C9 方位/朝向理解 |
| 作答形式 | F25（开放问答）、F3（判断题，是否类）、F1（单选题，概率/动作类） |
| 指标 | GPT-Score, Accuracy, BLEU, CIDEr |
| 自动评分口径 | 感知/状态类：Exact Match；预测/规划类：LLM-as-judge（GPT-Score）；行为类：BLEU/CIDEr |
| 可迁移用法 | Stage1 用于能力/题型/指标设计依据；Stage4 用于模板实例化和评分口径参考，不直接照搬数据。 |

---

# DriveLM 模板库

**来源**: DriveLM (OpenDriveLab, 2024)
**场景**: 自动驾驶场景（nuScenes 数据集，多摄像头环视）
**任务格式**: 图文对话式 VQA，覆盖感知→预测→规划完整链路
**数据规模**: ~4k 关键帧，~16k QA 对
**评测指标**: GPT-Score, Accuracy, BLEU, CIDEr

---

## 模板元信息

| 字段 | 值 |
|------|-----|
| 作答形式 | F25（开放问答）、F3（判断题，是否类）、F1（单选题，概率/动作类） |
| 考察能力 | C1 物体识别、C4 物体状态理解、C20 时间变化理解、C23 操作后果预测、C25 任务规划、C9 方位/朝向理解 |
| 数据类型 | 多张有时序图像 + GT |
| GT 依赖字段 | 物体列表（object category）、物体绝对坐标（3D coordinates）、图本体绝对坐标（camera pose）、物体状态（object state：moving/parked/stopped） |
| 自动评分方式 | 感知/状态类：Exact Match；预测/规划类：LLM-as-judge（GPT-Score）；行为类：BLEU/CIDEr |
| 人工检查要点 | 物体引用坐标是否与 GT 对应；预测答案是否与实际轨迹一致；规划动作是否符合交通规则 |

---

## 核心特征：驾驶场景图文链式推理

DriveLM 的独特之处在于将驾驶决策链路分解为感知→预测→规划三个层次，每个关键帧包含多个层次的 QA 对，形成推理链。

**物体引用格式**: `<c{id},{camera},{x},{y}>` 表示特定摄像头画面中坐标 (x,y) 处的物体。

---

## 类型 1: perception（感知）

**作答形式**: F25（开放问答）
**考察能力**: C1 物体识别、C4 物体状态理解、C9 方位/朝向理解
**GT 依赖**: object category、3D coordinates、object state、camera pose

### 模板

```
What are objects to the {direction} of the ego car?
What is the status of the {object_type} that is to the {direction} of the ego car?
```

### 真实示例

| 问题 | 答案 |
|------|------|
| What are objects to the front right of the ego car? | There are many barriers and one construction vehicle to the front right of the ego car. |
| What are objects to the front left of the ego car? | There is one truck and one barrier to the front left of the ego car. |
| What is the status of the truck that is to the front left of the ego car? | One truck is moving. |
| What are objects to the back left of the ego car? | There are two barriers, many trucks, two trailers, and one car to the back left of the ego car. |
| What is the status of the trucks that are to the back left of the ego car? | Many trucks are parked. |
| What is the status of the construction vehicle that is to the front right of the ego car? | The construction vehicle to the front right of the ego car is parked. |
| What are objects to the front of the ego car? | There are many obstacles in front of the ego car. |
| What is the status of the trailers that are to the back left of the ego car? | Two trailers are parked. |

---

## 类型 2: prediction（预测）

**作答形式**: F3（判断题）、F25（开放问答）
**考察能力**: C20 时间变化理解、C23 操作后果预测、C12 遮挡关系理解
**GT 依赖**: 3D coordinates（时序帧）、object state、camera pose

### 模板

```
Is <c{id},{camera},{x},{y}> a traffic sign or a road barrier?
Would <c{id},{camera},{x},{y}> be in the moving direction of the ego vehicle?
What is the future state of <c{id},{camera},{x},{y}>?
Which object is most likely to be occluded by <c{id},{camera},{x},{y}>? Would this object affect the ego vehicle? Based on this object, what action of the ego vehicle is dangerous?
```

### 真实示例

| 问题 | 答案 |
|------|------|
| Is `<c1,CAM_BACK,1088.3,497.5>` a traffic sign or a road barrier? | No. |
| Would `<c1,CAM_BACK,1088.3,497.5>` be in the moving direction of the ego vehicle? | No. |
| What is the future state of `<c1,CAM_BACK,1088.3,497.5>`? | Turn left. |
| Which object is most likely to be occluded by `<c2,CAM_BACK,864.2,468.3>`? Would this object affect the ego vehicle? Based on this object, what action of the ego vehicle is dangerous? | None, no, none. |

---

## 类型 3: planning（规划）

**作答形式**: F3（判断题）、F1（单选题，概率级别）、F25（开放问答）
**考察能力**: C25 任务规划、C23 操作后果预测
**GT 依赖**: 3D coordinates（时序帧）、object state、camera pose

### 模板

```
Is <c{id},{camera},{x},{y}> an object that the ego vehicle should consider in the current scene?
What actions could the ego vehicle take based on <c{id},{camera},{x},{y}>? Why take this action and what's the probability?
What is the probability of colliding with <c{id},{camera},{x},{y}> after the ego vehicle {action}?
What actions taken by the ego vehicle can lead to a collision with <c{id},{camera},{x},{y}>?
```

### 真实示例

| 问题 | 答案 |
|------|------|
| Is `<c1,CAM_BACK,1088.3,497.5>` an object that the ego vehicle should consider in the current scene? | No. |
| What actions could the ego vehicle take based on `<c1,CAM_BACK,1088.3,497.5>`? Why take this action and what's the probability? | The action is to keep going at the same speed. The reason is to follow the traffic rules, which has a high probability. |
| What is the probability of colliding with `<c1,CAM_BACK,1088.3,497.5>` after the ego vehicle goes straight and keeps the same speed? | Low. |
| What actions taken by the ego vehicle can lead to a collision with `<c2,CAM_BACK,864.2,468.3>`? | Back up. |

---

## 类型 4: behavior（行为预测）

**作答形式**: F25（开放问答）
**考察能力**: C20 时间变化理解、C9 方位/朝向理解
**GT 依赖**: 图本体绝对坐标（camera pose，时序帧间位移推算方向和速度）

### 模板

```
Predict the behavior of the ego vehicle.
```

### 真实示例

| 问题 | 答案 |
|------|------|
| Predict the behavior of the ego vehicle. | The ego vehicle is going straight. The ego vehicle is driving fast. |
| Predict the behavior of the ego vehicle. | The ego vehicle is going straight. The ego vehicle is driving slowly. |
| Predict the behavior of the ego vehicle. | The ego vehicle is going straight. The ego vehicle is not moving. |
| Predict the behavior of the ego vehicle. | The ego vehicle is turning left. The ego vehicle is driving slowly. |

---

## 占位符说明

| 占位符 | 含义 | 示例值 |
|--------|------|--------|
| `{direction}` | 自车相对方向 | front, front right, front left, back, back left, back right |
| `{object_type}` | 物体类型 | truck, car, pedestrian, barrier, construction vehicle |
| `<c{id},{camera},{x},{y}>` | 物体引用（摄像头+坐标） | `<c1,CAM_BACK,1088.3,497.5>` |
| `{camera}` | 摄像头名称 | CAM_FRONT, CAM_BACK, CAM_FRONT_LEFT, CAM_FRONT_RIGHT, CAM_BACK_LEFT, CAM_BACK_RIGHT |
| `{action}` | 自车动作 | goes straight and keeps the same speed, accelerates and goes straight, turns left |

---

## 答案格式特征

| 类型 | 答案格式 |
|------|---------|
| perception-存在 | "There are {count} {objects} to the {direction} of the ego car." |
| perception-状态 | "{Count} {objects} are {moving/parked/stopped}." |
| prediction-是否 | "Yes." / "No." |
| prediction-未来状态 | "Turn left." / "Go straight." / "Stop." |
| planning-概率 | "Low." / "Medium." / "High." |
| planning-动作 | "The action is to {action}. The reason is {reason}, which has a {probability} probability." |
| behavior | "The ego vehicle is {direction}. The ego vehicle is {speed_state}." |

## 可自动化检查

- 感知-状态类：与 GT object state 对比，Exact Match
- 预测-是否类：Exact Match（Yes/No）
- 规划-概率类：Exact Match（Low/Medium/High）
- 行为类：从 camera pose 时序差分自动验证方向和速度状态
- 开放问答类：LLM-judge，需人工抽查推理链合理性
