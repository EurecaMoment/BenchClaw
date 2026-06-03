# REVERIE 统一参考卡片

> 本卡片来自用户提供的 `REVERIE.md`，已纳入统一模板系统作为设计依据。它不是原始资料备份，而是用于 Stage1/Stage4 的参考切片。

## 在统一模板包中的作用

| 字段 | 内容 |
|---|---|
| benchmark | REVERIE |
| 场景 | 室内 3D 环境（Matterport3D，90 个房屋场景） |
| 任务范式 | 远程对象定位导航——根据高层语言指令导航并定位目标物体 |
| 主要能力 | C25 任务规划、C16 导航可达性、C27 指代表达理解、C13 区域/房间归属、C6 3D 空间关系 |
| 作答形式 | F18（动作选择题，导航动作序列）；F7（填空题，物体定位） |
| 指标 | SR (Success Rate), RGS (Remote Grounding Score), RGSPL, SPL |
| 自动评分口径 | SR（导航到目标位置）；RGS（正确定位目标物体）；SPL（路径效率） |
| 可迁移用法 | Stage1 用于能力/题型/指标设计依据；Stage4 用于模板实例化和评分口径参考，不直接照搬数据。 |

---

# REVERIE 模板库

**来源**: REVERIE (Remote Embodied Visual rEferring Instructions in Real Environments, CVPR 2020)
**场景**: 室内 3D 环境（Matterport3D，90 个房屋场景）
**任务格式**: 远程对象定位导航——根据高层语言指令导航并定位目标物体
**数据规模**: ~21k 问答对（4150 训练 / 1423 验证 / 515 val_seen）
**评测指标**: SR (Success Rate), RGS (Remote Grounding Score), RGSPL, SPL

---

## 模板元信息

| 字段 | 值 |
|------|-----|
| 作答形式 | F18（动作选择题，导航动作序列）；F7（填空题，物体定位） |
| 考察能力 | C25 任务规划、C16 导航可达性、C27 指代表达理解、C13 区域/房间归属、C6 3D 空间关系 |
| 数据类型 | 多张有时序图像 + GT |
| GT 依赖字段 | 物体列表（object category）、物体绝对坐标（3D coordinates）、三维包围盒（3D bbox）、图本体绝对坐标（camera pose）、导航路径（path） |
| 自动评分方式 | SR（导航到目标位置）；RGS（正确定位目标物体）；SPL（路径效率） |
| 人工检查要点 | 指代表达是否明确（如"the picture above the lamp"是否唯一）；导航指令是否与场景拓扑一致；目标物体是否在导航终点可见 |

---

## 核心特征：两层指令结构

REVERIE 每条样本包含两种互补指令：

- **高层指令 (`instructions`)**：描述导航目标和物体操作任务，不含路径细节，类似人类日常指令
- **低层指令 (`instructions_l`)**：逐步导航指令，包含转向、距离等细节

**数据结构**:
```json
{
  "id": "7172_156",
  "scan": "cV4RVeZvu5T",
  "path_id": 7172,
  "objId": 156,
  "instructions": [
    "Go to the laundryroom on the first level and remove the leopard trinket from the shelf",
    "Go to the laundry room and dust off the trinkets on the first shelf above the sink"
  ],
  "instructions_l": [
    "Exit the bedroom and go up the small set of steps towards the kitchen. Keep going and turn left at the fridge, into the laundry room.",
    "Go up the stairs and straight into the kitchen. Go through the door to the left of the fridge and stop near the sink.",
    "Go into the laundry room and stop next to the sink."
  ],
  "path": ["node_id_1", "node_id_2", ...],
  "heading": 0.32,
  "distance": 10.63
}
```

---

## 问题类型概览

REVERIE 的任务可分为两大类：

1. **导航 + 物体定位** — 根据指令导航到目标位置，并定位指定物体
2. **导航 + 物体操作** — 根据指令导航并执行物体操作（拿起、清洁、放置等）

---

## 类型 1: 导航 + 物体定位（定位类）

**作答形式**: F18（导航动作序列）+ F7（物体定位）
**考察能力**: C25 任务规划、C16 导航可达性、C27 指代表达理解、C13 区域/房间归属
**GT 依赖**: object category、3D coordinates、path、camera pose
**数据类型**: 多张有时序图像 + GT

### 模板

```
{high_level_instruction}
Navigate to the {location} and locate the {object_description}.
Go to the {room} and find the {object_with_attributes}.
```

### 真实示例

| 高层指令 | 低层指令 | 目标物体 | 导航距离 |
|---------|---------|---------|---------|
| Go to the laundryroom on the first level and remove the leopard trinket from the shelf | Exit bedroom → go up steps → turn left at fridge → enter laundry room | leopard trinket on shelf | 10.63m |
| Go to the lounge room and pick up the top picture above the lamp | Walk out of bathroom → turn left → wait by fireplace | top picture above lamp | 5.73m |
| Go to the bedroom with the fireplace and bring me the lowest hanging small picture on the right wall across from the bedside table with the lamp on it | Exit bedroom → turn left at double doors → wait in bathroom | lowest hanging small picture on right wall | 6.06m |
| Go to the bathroom on level 3 at the end of the hallway and water plant on top of the sink | Leave bedroom → take left → down hallway → enter bathroom | plant on sink | 9.29m |
| Go to the sitting room and straighten the picture on the fireplace mantel | Walk away from stairs → turn right → turn left at double doors → stop in front of fireplace | picture on fireplace mantel | 6.37m |

---

## 类型 2: 导航 + 物体操作（操作类）

**作答形式**: F18（导航动作序列）+ F18（操作动作）
**考察能力**: C25 任务规划、C21 动作可供性、C22 操作前置条件、C23 操作后果预测
**GT 依赖**: object category、3D coordinates、object state、operation type
**数据类型**: 多张有时序图像 + GT

### 模板

```
{high_level_instruction}
Navigate to the {location}, find the {object}, and {action} it.
Go to the {room} and {action} the {object_description}.
```

### 真实示例

| 高层指令 | 操作类型 | 目标物体 |
|---------|---------|---------|
| Go to the laundryroom on the first level and remove the leopard trinket from the shelf | remove | leopard trinket |
| Go to the laundry room and dust off the trinkets on the first shelf above the sink | dust off | trinkets on shelf |
| Go to the lounge room and pick up the top picture above the lamp | pick up | top picture |
| Go to the lounge area and clean the top picture above the lamp | clean | top picture |
| Go to the master bedroom and straighten the crooked picture on the right wall | straighten | crooked picture |
| Go to the bathroom on level 3 and water the plant on the sink | water | plant |

---

## 占位符说明

| 占位符 | 含义 | 示例值 |
|--------|------|--------|
| `{high_level_instruction}` | 高层自然语言指令 | "Go to the laundry room and remove the trinket from the shelf" |
| `{location}` | 目标房间或位置 | laundry room, bedroom, bathroom, kitchen, lounge |
| `{room}` | 房间名称 | bedroom, bathroom, kitchen, living room |
| `{object_description}` | 物体描述（含属性和位置） | "the leopard trinket on the shelf", "the top picture above the lamp" |
| `{object_with_attributes}` | 带属性的物体 | "the crooked picture", "the small plant" |
| `{action}` | 操作动作 | remove, pick up, clean, dust off, straighten, water |

---

## 答案特征

- **导航动作**：GotoLocation、TurnLeft、TurnRight、MoveForward 等
- **操作动作**：PickupObject、RemoveObject、CleanObject、DustObject、StraightenObject、WaterObject 等
- **物体定位**：3D 坐标或 bbox
- 所有答案均可通过模拟器验证

## 可自动化检查

- 导航路径是否连通（基于 Matterport3D 拓扑）
- 最终位置是否能看到目标物体（基于可见性）
- 指代表达是否唯一确定（检查是否有多个物体匹配描述）
- 操作前置条件是否满足（如清洁前物体必须可达）
