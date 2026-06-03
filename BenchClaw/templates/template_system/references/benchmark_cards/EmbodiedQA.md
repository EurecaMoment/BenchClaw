# EmbodiedQA 统一参考卡片

> 本卡片来自用户提供的 `EmbodiedQA.md`，已纳入统一模板系统作为设计依据。它不是原始资料备份，而是用于 Stage1/Stage4 的参考切片。

## 在统一模板包中的作用

| 字段 | 内容 |
|---|---|
| benchmark | EmbodiedQA |
| 场景 | 室内 3D 环境（House3D，基于 SUNCG 数据集） |
| 任务范式 | 具身视觉问答——agent 在 3D 环境中导航并回答关于场景的问题 |
| 主要能力 | C1 物体识别、C2 物体计数、C13 区域/房间归属、C16 导航可达性、C25 任务规划 |
| 作答形式 | F7（填空题，物体/房间名称）；F3（判断题，存在性）；F2（多选题，物体列表） |
| 指标 | Accuracy (exact match) |
| 自动评分口径 | 归一化后 Exact Match（物体/房间名称）；Accuracy（判断题） |
| 可迁移用法 | Stage1 用于能力/题型/指标设计依据；Stage4 用于模板实例化和评分口径参考，不直接照搬数据。 |

---

# EmbodiedQA 模板库

**来源**: EmbodiedQA (Facebook AI Research, CVPR 2018)
**场景**: 室内 3D 环境（House3D，基于 SUNCG 数据集）
**任务格式**: 具身视觉问答——agent 在 3D 环境中导航并回答关于场景的问题
**数据规模**: ~150k 问答对（训练集）
**评测指标**: Accuracy (exact match)

---

## 模板元信息

| 字段 | 值 |
|------|-----|
| 作答形式 | F7（填空题，物体/房间名称）；F3（判断题，存在性）；F2（多选题，物体列表） |
| 考察能力 | C1 物体识别、C2 物体计数、C13 区域/房间归属、C16 导航可达性、C25 任务规划 |
| 数据类型 | 多张有时序图像 + GT |
| GT 依赖字段 | 物体列表（object category）、房间列表（room type）、物体绝对坐标（3D coordinates）、图本体绝对坐标（camera pose） |
| 自动评分方式 | 归一化后 Exact Match（物体/房间名称）；Accuracy（判断题） |
| 人工检查要点 | 问题是否存在歧义（如"the chair"是否唯一）；答案是否与 agent 当前位置的可见范围一致；计数答案是否准确 |

---

## 核心特征：程序化生成 + 导航依赖

EmbodiedQA 的问题由程序化模板生成，每道题都要求 agent 在 3D 环境中导航到特定位置才能回答。问题类型包括：

- **位置查询** — "Where is the {object}?"
- **计数查询** — "How many {objects} are in the {room}?"
- **存在性查询** — "Is there a {object} in the {room}?"
- **房间查询** — "What room is the {object} in?"

**数据结构**:
```json
{
  "question": "Where is the sofa?",
  "answer": "living room",
  "question_type": "location",
  "object": "sofa",
  "room": "living room",
  "template": "Where is <ARTICLE> <OBJ>?",
  "navigation_required": true
}
```

---

## 问题类型概览

EmbodiedQA 包含 6 种主要问题类型：

1. **location** — 物体位置查询
2. **count** — 物体计数查询
3. **room_count** — 房间内物体计数
4. **global_object_count** — 全局物体计数
5. **room_object_count** — 特定房间物体计数
6. **exist** — 存在性判断

---

## 类型 1: location（物体位置查询）

**作答形式**: F7（填空题，房间名称）
**考察能力**: C1 物体识别、C13 区域/房间归属、C16 导航可达性
**GT 依赖**: object category、room type、3D coordinates
**数据类型**: 多张有时序图像 + GT

### 模板

```
Where is <ARTICLE> <OBJ>?
In which room can you find <ARTICLE> <OBJ>?
What room is <ARTICLE> <OBJ> in?
```

### 真实示例

| 问题 | 答案 | 物体 | 房间 |
|------|------|------|------|
| Where is the sofa? | living room | sofa | living room |
| Where is the bed? | bedroom | bed | bedroom |
| In which room can you find the dining table? | dining room | dining table | dining room |
| What room is the kitchen counter in? | kitchen | kitchen counter | kitchen |
| Where is the toilet? | bathroom | toilet | bathroom |

---

## 类型 2: count（物体计数查询）

**作答形式**: F7（填空题，整数）
**考察能力**: C2 物体计数、C13 区域/房间归属
**GT 依赖**: object category、room type、instance count
**数据类型**: 多张有时序图像 + GT

### 模板

```
How many <OBJ-plural> are in the <ROOM>?
How many <OBJ-plural> <AUX> there?
Count the number of <OBJ-plural> in the <ROOM>.
```

### 真实示例

| 问题 | 答案 | 物体 | 房间 |
|------|------|------|------|
| How many chairs are in the living room? | 3 | chairs | living room |
| How many beds are in the bedroom? | 1 | beds | bedroom |
| How many tables are there? | 2 | tables | (全局) |
| Count the number of lamps in the kitchen. | 2 | lamps | kitchen |
| How many doors are in the hallway? | 4 | doors | hallway |

---

## 类型 3: room_count（房间内物体计数）

**作答形式**: F7（填空题，整数）
**考察能力**: C2 物体计数、C13 区域/房间归属
**GT 依赖**: room type、object category、instance count
**数据类型**: 多张有时序图像 + GT

### 模板

```
How many objects are in the <ROOM>?
What is the total number of items in the <ROOM>?
Count all the objects in the <ROOM>.
```

### 真实示例

| 问题 | 答案 | 房间 |
|------|------|------|
| How many objects are in the living room? | 12 | living room |
| What is the total number of items in the bedroom? | 8 | bedroom |
| Count all the objects in the kitchen. | 15 | kitchen |

---

## 类型 4: global_object_count（全局物体计数）

**作答形式**: F7（填空题，整数）
**考察能力**: C2 物体计数、C16 导航可达性
**GT 依赖**: object category、global instance count
**数据类型**: 多张有时序图像 + GT

### 模板

```
How many <OBJ-plural> are there in total?
What is the total count of <OBJ-plural>?
Count all the <OBJ-plural> in the house.
```

### 真实示例

| 问题 | 答案 | 物体 |
|------|------|------|
| How many chairs are there in total? | 8 | chairs |
| What is the total count of lamps? | 5 | lamps |
| Count all the doors in the house. | 12 | doors |

---

## 类型 5: exist（存在性判断）

**作答形式**: F3（判断题，yes/no）
**考察能力**: C1 物体识别、C13 区域/房间归属
**GT 依赖**: object category、room type、existence flag
**数据类型**: 多张有时序图像 + GT

### 模板

```
Is there <ARTICLE> <OBJ> in the <ROOM>?
<AUX> there <ARTICLE> <OBJ> in the <ROOM>?
Can you find <ARTICLE> <OBJ> in the <ROOM>?
```

### 真实示例

| 问题 | 答案 | 物体 | 房间 |
|------|------|------|------|
| Is there a sofa in the living room? | yes | sofa | living room |
| Are there any beds in the kitchen? | no | beds | kitchen |
| Can you find a toilet in the bathroom? | yes | toilet | bathroom |
| Is there a dining table in the bedroom? | no | dining table | bedroom |

---

## 类型 6: room_object_count（特定房间物体计数）

**作答形式**: F7（填空题，整数）
**考察能力**: C2 物体计数、C13 区域/房间归属
**GT 依赖**: room type、object category、instance count
**数据类型**: 多张有时序图像 + GT

### 模板

```
How many <OBJ-plural> are in the <ROOM>?
What is the number of <OBJ-plural> in the <ROOM>?
```

### 真实示例

| 问题 | 答案 | 物体 | 房间 |
|------|------|------|------|
| How many chairs are in the living room? | 3 | chairs | living room |
| What is the number of lamps in the bedroom? | 2 | lamps | bedroom |
| How many cabinets are in the kitchen? | 4 | cabinets | kitchen |

---

## 占位符说明

| 占位符 | 含义 | 示例值 |
|--------|------|--------|
| `<OBJ>` | 单数物体名称 | sofa, bed, chair, table, lamp |
| `<OBJ-plural>` | 复数物体名称 | sofas, beds, chairs, tables, lamps |
| `<ARTICLE>` | 冠词（自动根据单复数调整） | a, an, (复数时省略) |
| `<AUX>` | 助动词（自动根据单复数调整） | is, are |
| `<ROOM>` | 房间名称 | living room, bedroom, kitchen, bathroom, hallway |

---

## 答案特征

- **location / room_object_count**：房间名称（living room, bedroom, kitchen 等）
- **count / global_object_count / room_count**：非负整数（0, 1, 2, ...）
- **exist**：yes / no
- 所有答案均为短文本，exact match 即可评测

## 可自动化检查

- 所有类型：归一化后 Exact Match
- location 类：从 GT 3D coordinates 验证物体是否在指定房间
- count 类：从 GT instance count 直接验证
- exist 类：从 GT 检查物体是否存在于指定房间
- 导航可达性：检查 agent 是否能到达问题涉及的所有房间
