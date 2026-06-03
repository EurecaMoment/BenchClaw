# NuScenesQA 统一参考卡片

> 本卡片来自用户提供的 `NuScenesQA.md`，已纳入统一模板系统作为设计依据。它不是原始资料备份，而是用于 Stage1/Stage4 的参考切片。

## 在统一模板包中的作用

| 字段 | 内容 |
|---|---|
| benchmark | NuScenesQA |
| 场景 | 自动驾驶场景（nuScenes 数据集，室外多摄像头） |
| 任务范式 | 封闭式 VQA，答案为短文本（yes/no、数字、物体类别、状态词） |
| 主要能力 | C1 物体识别、C2 物体计数、C4 物体状态理解、C9 方位/朝向理解、C6 3D 空间关系 |
| 作答形式 | F3（判断题）、F7（填空题）、F1（单选题） |
| 指标 | Accuracy (exact match) |
| 自动评分口径 | 归一化后 Exact Match（yes/no、整数、物体类别名、状态词均可归一化） |
| 可迁移用法 | Stage1 用于能力/题型/指标设计依据；Stage4 用于模板实例化和评分口径参考，不直接照搬数据。 |

---

# NuScenesQA 模板库

**来源**: NuScenes-QA (Qian et al., AAAI 2024)
**场景**: 自动驾驶场景（nuScenes 数据集，室外多摄像头）
**任务格式**: 封闭式 VQA，答案为短文本（yes/no、数字、物体类别、状态词）
**数据规模**: ~83k 问答对（test split）
**评测指标**: Accuracy (exact match)

---

## 模板元信息

| 字段 | 值 |
|------|-----|
| 作答形式 | F3（判断题）、F7（填空题）、F1（单选题） |
| 考察能力 | C1 物体识别、C2 物体计数、C4 物体状态理解、C9 方位/朝向理解、C6 3D 空间关系 |
| 数据类型 | 多张有时序图像 + GT |
| GT 依赖字段 | 物体列表（object category）、物体绝对坐标（3D coordinates）、图本体绝对坐标（camera pose）、物体状态（object state：moving/parked/stopped） |
| 自动评分方式 | 归一化后 Exact Match（yes/no、整数、物体类别名、状态词均可归一化） |
| 人工检查要点 | 方向类 GT 是否依据 camera pose 正确计算；多跳问题（hop=1）中间实体是否唯一确定；状态词是否与 GT 一致 |

---

## 核心特征：程序化生成 + 多跳推理

NuScenes-QA 的问题由程序化模板生成，每道题附带 `num_hop`（0 或 1），表示回答该问题需要的推理跳数：

- **hop=0**：直接查询，无需中间推理步骤
- **hop=1**：需先定位/识别中间实体，再回答目标问题

**数据结构**:
```json
{
  "id": "...",
  "image_paths": ["..."],
  "question": "Are any moving bicycles visible?",
  "answer": "no",
  "type": "exist",
  "num_hop": 0
}
```

---

## 问题类型概览

| 类型 | 说明 | 答案形式 |
|------|------|----------|
| `exist` | 询问某类物体是否存在 | yes / no |
| `count` | 统计某类物体数量 | 整数 |
| `object` | 询问某位置/条件下的物体类别 | 物体名称 |
| `status` | 询问某物体的运动状态 | moving / parked / stopped |
| `comparison` | 比较两个物体的状态是否相同 | yes / no |

---

## 类型 1: exist（存在性判断）

**作答形式**: F3（判断题）
**考察能力**: C1 物体识别、C9 方位/朝向理解（hop=1 时）
**GT 依赖**: object category、3D coordinates、camera pose

### 模板

```
Are any {status} {object_type}s visible?
Are there any {object_type}s?
Are there any {status} {object_type}s to the {direction} of me?
Are any {object_type}s visible?
```

### 真实示例

| 问题 | 答案 | hop |
|------|------|-----|
| Are any moving bicycles visible? | no | 0 |
| Are any moving pedestrians visible? | yes | 0 |
| Are there any things? | yes | 0 |
| Are any moving things visible? | yes | 0 |
| Are there any parked cars? | yes | 0 |
| Are there any traffic cones to the back of me? | no | 1 |
| Are there any moving cars to the back of me? | yes | 1 |
| Are there any without rider bicycles to the front of me? | yes | 1 |
| Are there any moving cars to the front left of me? | no | 1 |
| Are any cars visible? | yes | 0 |

---

## 类型 2: count（数量统计）

**作答形式**: F7（填空题）
**考察能力**: C2 物体计数、C9 方位/朝向理解（hop=1 时）
**GT 依赖**: instance id、object category、3D coordinates、camera pose

### 模板

```
What number of {object_type}s are there?
How many {status} {object_type}s are there?
How many {object_type}s are to the {direction} of me?
What number of {status} {object_type}s are to the {direction} of me?
How many {attribute} {object_type}s are there?
```

### 真实示例

| 问题 | 答案 | hop |
|------|------|-----|
| What number of traffic cones are there? | 3 | 0 |
| What number of moving cars are there? | 5 | 0 |
| How many with rider motorcycles are there? | 0 | 0 |
| How many without rider bicycles are there? | 4 | 0 |
| How many cars are to the back right of me? | 10 | 1 |
| How many parked cars are to the front right of me? | 0 | 1 |
| What number of things are to the front of me? | 9 | 1 |
| What number of moving pedestrians are to the front right of me? | 0 | 1 |
| What number of moving things are to the back right of the stopped thing? | 3 | 1 |

---

## 类型 3: object（物体识别）

**作答形式**: F7（填空题）
**考察能力**: C1 物体识别、C9 方位/朝向理解
**GT 依赖**: object category、3D coordinates、camera pose

### 模板

```
There is a {status} thing to the {direction} of me; what is it?
What is the {status} thing?
There is a thing that is both to the {direction1} of the {reference} and the {direction2} of me; what is it?
The {status} thing to the {direction} of me is what?
What is the {status} thing to the {direction} of me?
```

### 真实示例

| 问题 | 答案 | hop |
|------|------|-----|
| There is a parked thing to the front of me; what is it? | car | 1 |
| What is the stopped thing? | car | 0 |
| The parked thing to the front of me is what? | car | 1 |
| What is the parked thing to the front left of me? | car | 1 |
| There is a parked thing; what is it? | car | 0 |
| There is a thing that is both to the back right of the stopped car and the back of me; what is it? | car | 1 |
| There is a thing that is both to the front left of the stopped thing and the front left of me; what is it? | pedestrian | 1 |
| There is a moving thing that is to the front left of me and the front of the stopped car; what is it? | pedestrian | 1 |

---

## 类型 4: status（状态查询）

**作答形式**: F7（填空题）
**考察能力**: C4 物体状态理解、C9 方位/朝向理解
**GT 依赖**: object state、3D coordinates、camera pose

### 模板

```
There is a {object_type} that is to the {direction} of me; what is its status?
The {object_type} that is to the {direction} of me is in what status?
There is a {object_type} to the {direction} of me; what status is it?
What is the status of the {object_type} to the {direction} of me?
```

### 真实示例

| 问题 | 答案 | hop |
|------|------|-----|
| There is a pedestrian to the back of me; what is its status? | moving | 1 |
| There is a car that is to the front of me; what is its status? | parked | 1 |
| The car that is to the front of me is in what status? | parked | 1 |
| There is a car to the front left of me; what status is it? | moving | 1 |
| What is the status of the car to the front of me? | parked | 1 |
| What is the status of the car to the front left of me? | moving | 1 |
| There is a car that is to the front left of me; what is its status? | moving | 1 |

---

## 类型 5: comparison（状态比较）

**作答形式**: F3（判断题）
**考察能力**: C4 物体状态理解
**GT 依赖**: object state、3D coordinates

### 模板

```
Is the {object_type1} the same status as the {object_type2}?
There is a {object_type} that is to the {direction} of the {reference}; is its status the same as the {object_type2} that is to the {direction2} of the {reference2}?
```

### 真实示例

| 问题 | 答案 | hop |
|------|------|-----|
| Is the pedestrian the same status as the car? | no | 0 |
| There is a car that is to the front left of the standing pedestrian; is its status the same as the car that is to the front of the standing pedestrian? | yes | 1 |
| There is a car that is to the front left of the standing pedestrian; is its status the same as the thing to the front of the standing pedestrian? | yes | 1 |

---

## 占位符说明

| 占位符 | 含义 | 示例值 |
|--------|------|--------|
| `{object_type}` | 物体类别 | car, pedestrian, bicycle, motorcycle, traffic cone, truck |
| `{status}` | 运动状态修饰词 | moving, parked, stopped, standing, with rider, without rider |
| `{direction}` | 相对方向 | front, back, front left, front right, back left, back right |
| `{reference}` | 参照物体（带状态描述） | stopped car, standing pedestrian, parked thing |
| `{attribute}` | 属性修饰词 | with rider, without rider |

---

## 答案特征

- **exist / comparison**：`yes` 或 `no`
- **count**：非负整数（0、1、2、…）
- **object**：物体类别名（car, pedestrian, bicycle, motorcycle, truck, traffic cone）
- **status**：`moving`、`parked`、`stopped`
- 所有答案均为短文本，exact match 即可评测

## 可自动化检查

- 所有类型：归一化后 Exact Match
- exist/count/object/status 类：从 GT 3D coordinates + camera pose 自动验证方向和物体
- comparison 类：从 GT object state 直接比较
- hop=1 问题：检查中间实体是否唯一（若不唯一需过滤）
