# ALFRED 统一参考卡片

> 本卡片来自用户提供的 `ALFRED.md`，已纳入统一模板系统作为设计依据。它不是原始资料备份，而是用于 Stage1/Stage4 的参考切片。

## 在统一模板包中的作用

| 字段 | 内容 |
|---|---|
| benchmark | ALFRED |
| 场景 | 室内 3D 模拟环境（AI2-THOR） |
| 任务范式 | 语言指令 → 具身操作序列（导航 + 物体交互） |
| 主要能力 | C25 任务规划、C16 导航可达性、C21 动作可供性、C22 操作前置条件、C23 操作后果预测、C13 区域/房间归属 |
| 作答形式 | F18（动作选择题，操作动作序列）；子步骤为 F19（步骤排序题） |
| 指标 | Task Success Rate (SR), Goal Condition Success Rate (GC) |
| 自动评分口径 | SR（所有 goal condition 满足）；GC（满足 goal condition 的比例） |
| 可迁移用法 | Stage1 用于能力/题型/指标设计依据；Stage4 用于模板实例化和评分口径参考，不直接照搬数据。 |

---

# ALFRED 模板库

**来源**: ALFRED (Allen Institute for AI, CVPR 2020)
**场景**: 室内 3D 模拟环境（AI2-THOR）
**任务格式**: 语言指令 → 具身操作序列（导航 + 物体交互）
**数据规模**: ~25k 专家演示，~8k 任务
**评测指标**: Task Success Rate (SR), Goal Condition Success Rate (GC)

---

## 模板元信息

| 字段 | 值 |
|------|-----|
| 作答形式 | F18（动作选择题，操作动作序列）；子步骤为 F19（步骤排序题） |
| 考察能力 | C25 任务规划、C16 导航可达性、C21 动作可供性、C22 操作前置条件、C23 操作后果预测、C13 区域/房间归属 |
| 数据类型 | 多张有时序图像 + GT |
| GT 依赖字段 | 物体列表（object category）、物体绝对坐标（3D coordinates）、三维包围盒（3D bbox）、图本体绝对坐标（camera pose）、物体状态（object state） |
| 自动评分方式 | SR（所有 goal condition 满足）；GC（满足 goal condition 的比例） |
| 人工检查要点 | 任务描述是否存在歧义（如"one desk"是否唯一）；高层步骤与底层动作是否对齐；物体操作前置条件是否在 GT 场景中可满足 |

---

## 核心特征：语言指令驱动的具身操作

ALFRED 不是 QA 任务，而是**指令跟随**任务。给定自然语言任务描述，agent 需要在 3D 环境中完成一系列导航和物体操作动作。

**数据结构**:
```json
{
  "task_desc": "Put a clean mug in the cabinet.",
  "high_descs": [
    "Go to the kitchen sink.",
    "Pick up the mug.",
    "Clean the mug.",
    "Go to the cabinet.",
    "Put the mug in the cabinet."
  ],
  "high_pddl": [
    {"discrete_action": {"action": "GotoLocation"}},
    {"discrete_action": {"action": "PickupObject"}},
    {"discrete_action": {"action": "CleanObject"}},
    {"discrete_action": {"action": "GotoLocation"}},
    {"discrete_action": {"action": "PutObject"}}
  ]
}
```

---

## 问题类型概览

ALFRED 包含 7 种主要任务类型：

1. **pick_and_place_simple** — 拿起物体并放到指定位置
2. **pick_two_obj_and_place** — 拿起两个物体并分别放置
3. **pick_and_place_with_movable_recep** — 拿起物体放入可移动容器
4. **pick_clean_then_place_in_recep** — 清洁物体后放入容器
5. **pick_heat_then_place_in_recep** — 加热物体后放入容器
6. **pick_cool_then_place_in_recep** — 冷却物体后放入容器
7. **look_at_obj_in_light** — 在特定光线条件下观察物体

---

## 类型 1: pick_and_place_simple（简单拿取放置）

**作答形式**: F18（动作序列选择）
**考察能力**: C25 任务规划、C16 导航可达性、C21 动作可供性
**GT 依赖**: object category、3D coordinates、object state
**数据类型**: 多张有时序图像 + GT

### 模板

```
{task_desc}
Navigate to the {location}, pick up the {object}, and place it in/on the {target_location}.
Find the {object} and move it to the {target_location}.
```

### 真实示例

| 任务描述 | 高层步骤 | 动作序列 |
|---------|---------|---------|
| Put a clean mug in the cabinet. | 1. Go to sink 2. Pick up mug 3. Clean mug 4. Go to cabinet 5. Put mug in cabinet | GotoLocation → PickupObject → CleanObject → GotoLocation → PutObject |
| Put a mug in the cabinet. | 1. Go to mug location 2. Pick up mug 3. Go to cabinet 4. Put mug in cabinet | GotoLocation → PickupObject → GotoLocation → PutObject |
| Put the apple on the table. | 1. Find apple 2. Pick it up 3. Go to table 4. Place on table | GotoLocation → PickupObject → GotoLocation → PutObject |

---

## 类型 2: pick_two_obj_and_place（双物体拿取放置）

**作答形式**: F18（动作序列选择）
**考察能力**: C25 任务规划、C2 物体计数、C16 导航可达性
**GT 依赖**: object category、3D coordinates、object state
**数据类型**: 多张有时序图像 + GT

### 模板

```
Pick up the {object1} and the {object2}, then place them in/on the {target_location}.
Move both {object_type}s to the {target_location}.
```

### 真实示例

| 任务描述 | 高层步骤 |
|---------|---------|
| Put two mugs in the cabinet. | 1. Find first mug 2. Pick up 3. Go to cabinet 4. Put down 5. Find second mug 6. Pick up 7. Go to cabinet 8. Put down |
| Move the apple and the orange to the table. | 1. Pick up apple 2. Go to table 3. Put down 4. Pick up orange 5. Go to table 6. Put down |

---

## 类型 3: pick_clean_then_place_in_recep（清洁后放置）

**作答形式**: F18（动作序列选择）
**考察能力**: C25 任务规划、C22 操作前置条件、C23 操作后果预测
**GT 依赖**: object category、object state、receptacle type
**数据类型**: 多张有时序图像 + GT

### 模板

```
Clean the {object} and put it in the {receptacle}.
Wash the {object} and place it in/on the {target_location}.
```

### 真实示例

| 任务描述 | 高层步骤 |
|---------|---------|
| Put a clean mug in the cabinet. | 1. Go to sink 2. Pick up mug 3. Clean mug 4. Go to cabinet 5. Put in cabinet |
| Clean the plate and put it on the shelf. | 1. Go to sink 2. Pick up plate 3. Clean plate 4. Go to shelf 5. Put on shelf |

---

## 类型 4: pick_heat_then_place_in_recep（加热后放置）

**作答形式**: F18（动作序列选择）
**考察能力**: C25 任务规划、C22 操作前置条件、C23 操作后果预测
**GT 依赖**: object category、object state、appliance type
**数据类型**: 多张有时序图像 + GT

### 模板

```
Heat the {object} and put it in the {receptacle}.
Warm up the {object} and place it in/on the {target_location}.
```

### 真实示例

| 任务描述 | 高层步骤 |
|---------|---------|
| Heat the mug and put it in the cabinet. | 1. Pick up mug 2. Go to microwave 3. Heat mug 4. Go to cabinet 5. Put in cabinet |

---

## 类型 5: pick_cool_then_place_in_recep（冷却后放置）

**作答形式**: F18（动作序列选择）
**考察能力**: C25 任务规划、C22 操作前置条件、C23 操作后果预测
**GT 依赖**: object category、object state、appliance type
**数据类型**: 多张有时序图像 + GT

### 模板

```
Cool the {object} and put it in the {receptacle}.
Chill the {object} and place it in/on the {target_location}.
```

### 真实示例

| 任务描述 | 高层步骤 |
|---------|---------|
| Cool the mug and put it in the cabinet. | 1. Pick up mug 2. Go to fridge 3. Cool mug 4. Go to cabinet 5. Put in cabinet |

---

## 类型 6: look_at_obj_in_light（特定光线下观察）

**作答形式**: F18（动作序列选择）
**考察能力**: C25 任务规划、C11 可见性理解、C9 方位/朝向理解
**GT 依赖**: object category、3D coordinates、lighting state
**数据类型**: 多张有时序图像 + GT

### 模板

```
Look at the {object} under the {light_source}.
Examine the {object} in the {location} with the {light_source} on.
```

### 真实示例

| 任务描述 | 高层步骤 |
|---------|---------|
| Look at the picture in the light. | 1. Go to picture location 2. Turn on light 3. Look at picture |

---

## 占位符说明

| 占位符 | 含义 | 示例值 |
|--------|------|--------|
| `{object}` | 目标物体 | mug, plate, apple, orange, picture |
| `{object_type}` | 物体类别 | mug, plate, apple, book |
| `{location}` | 房间或位置 | kitchen, bedroom, living room, sink |
| `{target_location}` | 目标放置位置 | cabinet, shelf, table, counter |
| `{receptacle}` | 容器类型 | cabinet, drawer, shelf, fridge |
| `{light_source}` | 光源 | lamp, light, window |

---

## 答案特征

- **动作序列**：GotoLocation、PickupObject、PutObject、CleanObject、HeatObject、CoolObject、ToggleObject、LookObject 等
- **评分方式**：SR（任务完全成功）、GC（目标条件满足比例）
- 所有答案均为动作序列，可通过执行模拟器验证

## 可自动化检查

- 动作序列是否符合 PDDL 规范
- 物体操作前置条件是否满足（如清洁前需要在水槽）
- 导航路径是否可达（基于 navmesh）
- 最终物体位置是否符合 goal condition
