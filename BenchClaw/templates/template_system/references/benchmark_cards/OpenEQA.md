# OpenEQA 统一参考卡片

> 本卡片来自用户提供的 `OpenEQA.md`，已纳入统一模板系统作为设计依据。它不是原始资料备份，而是用于 Stage1/Stage4 的参考切片。

## 在统一模板包中的作用

| 字段 | 内容 |
|---|---|
| benchmark | OpenEQA |
| 场景 | 室内 RGB-D 视频扫描（HM3D + ScanNet） |
| 任务范式 | 开放式 VQA，自由文本回答 |
| 主要能力 | C1 物体识别、C3 属性识别、C5 2D 空间关系、C4 物体状态理解、C21 动作可供性、C13 区域/房间归属 |
| 作答形式 | F25（开放问答题） |
| 指标 | LLM-Match (GPT-4 打分) |
| 自动评分口径 | LLM-as-judge（GPT-4 打分，0–1 分）；部分类别可用归一化 Exact Match |
| 可迁移用法 | Stage1 用于能力/题型/指标设计依据；Stage4 用于模板实例化和评分口径参考，不直接照搬数据。 |

---

# OpenEQA 模板库

**来源**: OpenEQA (Facebook Research, 2024)
**场景**: 室内 RGB-D 视频扫描（HM3D + ScanNet）
**任务格式**: 开放式 VQA，自由文本回答
**数据规模**: ~1600 问题，7 类
**评测指标**: LLM-Match (GPT-4 打分)

---

## 模板元信息

| 字段 | 值 |
|------|-----|
| 作答形式 | F25（开放问答题） |
| 考察能力 | C1 物体识别、C3 属性识别、C5 2D 空间关系、C4 物体状态理解、C21 动作可供性、C13 区域/房间归属 |
| 数据类型 | 多张有时序图像 + GT |
| GT 依赖字段 | 物体列表（object category）、物体绝对坐标（3D coordinates）、物体状态（object state）、房间 id（room id） |
| 自动评分方式 | LLM-as-judge（GPT-4 打分，0–1 分）；部分类别可用归一化 Exact Match |
| 人工检查要点 | 答案是否语义正确但措辞不同；功能推理答案是否合理；状态判断是否与 GT 一致 |

---

## 类别 1: object_recognition（物体识别）

**作答形式**: F25（开放问答）
**考察能力**: C1 物体识别
**GT 依赖**: object category、3D bbox

### 模板

```
What is the {location_desc} object {spatial_relation} the {reference_object}?
What is the {color/size} object on the {surface}?
What is the object to the {direction} of the {reference_object}?
```

### 真实示例

| 问题 | 答案 |
|------|------|
| What is the white object on the wall above the TV? | Air conditioning unit |
| What is the large, round, and black object on the wall? | A clock |
| What is the green object in the left of the garage? | A hose |
| What is the bin with the yellow lid? | A recycling bin |
| What is the object to the left of the bed? | A radiator |

---

## 类别 2: attribute_recognition（属性识别）

**作答形式**: F25（开放问答）
**考察能力**: C3 属性识别
**GT 依赖**: color、material、state 属性字段

### 模板

```
What material is the {object} in the {room}?
What color is the {object}?
What shape are the {object}?
What type of {object} does this {space} feature?
```

### 真实示例

| 问题 | 答案 |
|------|------|
| What material is the ceiling in the living room? | Wood panel |
| What color is the staircase railing? | Brown |
| What shape are the door knobs? | Round or spherical |
| What type of flooring does this house feature? | Wood panels |
| What color is the car? | Blue |

---

## 类别 3: spatial_understanding（空间理解）

**作答形式**: F25（开放问答）或 F3（判断题，Is there room…）
**考察能力**: C5 2D 空间关系、C6 3D 空间关系
**GT 依赖**: 3D bbox、3D coordinates

### 模板

```
What is in between the {object_A} and the {object_B}?
What is to the {direction} of the {reference_object}?
What is on the {position} shelf to the {direction} side of the {room}?
Is there room on the {surface} to {action}?
```

### 真实示例

| 问题 | 答案 |
|------|------|
| What is in between the two picture frames on the blue wall in the living room? | The TV |
| Is there room on the dining table to eat? | Yes |
| What is to the left of the mirror? | A plant in a tall vase |
| What is to the left of the staircase? | A storage closet |
| What is on the top shelf to the right side of the garage? | An ice cooler |

---

## 类别 4: object_state_recognition（物体状态识别）

**作答形式**: F3（判断题）或 F25（开放问答）
**考察能力**: C4 物体状态理解
**GT 依赖**: object state（open/closed/set 等）

### 模板

```
Is the {object} open?
Is the {object} set with {items}?
Are the {objects} closed?
Is the {object} {state}?
```

### 真实示例

| 问题 | 答案 |
|------|------|
| Is the dining table set with table mats? | Yes |
| Is the front door open? | No |
| Are the cabinets below the mirror closed? | Yes |
| Is the bedroom door open? | Yes |
| Is the garbage bin open? | Yes |

---

## 类别 5: functional_reasoning（功能推理）

**作答形式**: F25（开放问答）
**考察能力**: C21 动作可供性
**GT 依赖**: affordance labels、object category

### 模板

```
What should I do to {goal}?
What can I do to {action_goal}?
What can I use to {task}?
Where can I {activity}?
```

### 真实示例

| 问题 | 答案 |
|------|------|
| What should I do to cool down? | Turn on the AC unit |
| What can I do to increase the speed of the ceiling fan? | Turn the dial on the switch panel next to the front door |
| What can I use to water my plants? | The green hose |
| What can I use to keep drinks cold at a picnic? | The blue cooler |
| Where can I take a nap? | On the bed in the bedroom |

---

## 类别 6: world_knowledge（世界知识）

**作答形式**: F25（开放问答）
**考察能力**: C1 物体识别、C13 区域/房间归属
**GT 依赖**: object category、room id、semantic map

### 模板

```
What type of {object/space} is {description}?
Which {container} should I put {item} in?
What style of {items} are {location}?
Is this {space} in the {location_type}?
```

### 真实示例

| 问题 | 答案 |
|------|------|
| What type of ceiling is in the living room? | A vaulted ceiling |
| What type of car is in the garage? | A sedan |
| Which bin should I put paper in? | The bin with the yellow lid |
| What style of paintings are put up in the bedroom? | Abstract |
| Is this home in the suburbs? | No |

---

## 类别 7: object_localization（物体定位）

**作答形式**: F25（开放问答）
**考察能力**: C13 区域/房间归属、C5 2D 空间关系
**GT 依赖**: 3D coordinates、room id

### 模板

```
Where is the {object}?
Where is the {object} located?
```

### 真实示例

| 问题 | 答案 |
|------|------|
| Where is the mirror? | Next to the staircase above the dark brown cabinet |
| Where is the garage opener? | To the left of the house doorway |
| Where is the broom? | Below the garage door opener |
| Where is the cartoon cat? | It's drawn on the pink photo frame |
| Where is the orange painting? | Above the bed |

---

## 占位符说明

| 占位符 | 含义 | 示例值 |
|--------|------|--------|
| `{object}` | 目标物体 | mirror, door, bin |
| `{reference_object}` | 参照物体 | TV, staircase, bed |
| `{room}` | 房间类型 | living room, garage, bedroom |
| `{direction}` | 方向 | left, right, above, below |
| `{location_desc}` | 位置描述 | white, large round black |
| `{surface}` | 表面 | dining table, top shelf |
| `{state}` | 状态 | open, closed, set |
| `{task}` | 任务 | water my plants, keep drinks cold |
| `{activity}` | 活动 | take a nap, sit down |
| `{space}` | 空间 | house, home |

## 可自动化检查

- 状态类（is open/closed）：与 GT object state 对比，exact match
- 物体识别类：归一化物体名后 exact match，或 LLM-judge 语义匹配
- 功能推理类：仅 LLM-judge，需人工抽查合理性
