# VSI-Bench 统一参考卡片

> 本卡片来自用户提供的 `VSI-Bench.md`，已纳入统一模板系统作为设计依据。它不是原始资料备份，而是用于 Stage1/Stage4 的参考切片。

## 在统一模板包中的作用

| 字段 | 内容 |
|---|---|
| benchmark | VSI-Bench |
| 场景 | 室内视频序列（多视角帧，基于 ScanNet 场景） |
| 任务范式 | 选择题（MCQ）+ 数值估计题 |
| 主要能力 | C2 物体计数、C8 尺寸/尺度理解、C7 定量距离理解、C6 3D 空间关系、C9 方位/朝向理解、C18 轨迹理解 |
| 作答形式 | F1（单选题）、F8（数值题）、F5（排序题，出现顺序类） |
| 指标 | 选择题准确率；数值题相对误差 |
| 自动评分口径 | 选择题：Exact Match；数值题：相对误差（ |
| 可迁移用法 | Stage1 用于能力/题型/指标设计依据；Stage4 用于模板实例化和评分口径参考，不直接照搬数据。 |

---

# VSI-Bench 模板库

**来源**: VSI-Bench (NYU VisionX, 2024)
**场景**: 室内视频序列（多视角帧，基于 ScanNet 场景）
**任务格式**: 选择题（MCQ）+ 数值估计题
**数据规模**: ~5000 问题，9 类
**评测指标**: 选择题准确率；数值题相对误差

---

## 模板元信息

| 字段 | 值 |
|------|-----|
| 作答形式 | F1（单选题）、F8（数值题）、F5（排序题，出现顺序类） |
| 考察能力 | C2 物体计数、C8 尺寸/尺度理解、C7 定量距离理解、C6 3D 空间关系、C9 方位/朝向理解、C18 轨迹理解 |
| 数据类型 | 多张有时序图像 + GT |
| GT 依赖字段 | 物体列表（object category）、物体绝对坐标（3D coordinates）、三维包围盒（3D bbox）、图本体绝对坐标（camera pose）、instance id |
| 自动评分方式 | 选择题：Exact Match；数值题：相对误差（|pred-gt|/gt）；排序题：Exact Match 或 Kendall Tau |
| 人工检查要点 | 数值 GT 是否来自精确测量；距离题中两物体是否在同一场景帧中可见；排序题中物体首次出现帧是否标注正确 |

---

## 类别 1: object_counting（物体计数）

**作答形式**: F8（数值题）
**考察能力**: C2 物体计数
**GT 依赖**: instance id、object category

### 模板

```
How many {object_category}(s) are in this room?
```

### 真实示例

| 问题 | 答案类型 |
|------|--------|
| How many table(s) are in this room? | 整数 |
| How many chair(s) are in this room? | 整数 |
| How many door(s) are in this room? | 整数 |

---

## 类别 2: object_size_estimation（物体尺寸估计）

**作答形式**: F8（数值题）
**考察能力**: C8 尺寸/尺度理解
**GT 依赖**: 3D bbox（从包围盒三轴取最大值）

### 模板

```
What is the length of the longest dimension (length, width, or height) of the {object}, measured in centimeters?
```

### 真实示例

| 问题 | 答案类型 |
|------|--------|
| What is the length of the longest dimension (length, width, or height) of the table, measured in centimeters? | 数值（cm） |
| What is the length of the longest dimension (length, width, or height) of the sofa, measured in centimeters? | 数值（cm） |
| What is the length of the longest dimension (length, width, or height) of the door, measured in centimeters? | 数值（cm） |

---

## 类别 3: room_size_estimation（房间面积估计）

**作答形式**: F8（数值题）
**考察能力**: C8 尺寸/尺度理解
**GT 依赖**: 3D coordinates（场景边界框推算面积）

### 模板

```
What is the size of this room (in square meters)?
```

### 真实示例

| 问题 | 答案类型 |
|------|--------|
| What is the size of this room (in square meters)? | 数值（m²） |

---

## 类别 4: object_abs_distance（物体绝对距离）

**作答形式**: F8（数值题）
**考察能力**: C7 定量距离理解
**GT 依赖**: 3D coordinates、3D bbox（取最近点距离）

### 模板

```
Measuring from the closest point of each object, what is the distance between the {object_A} and the {object_B} (in meters)?
```

### 真实示例

| 问题 | 答案类型 |
|------|--------|
| Measuring from the closest point of each object, what is the distance between the table and the bathtub (in meters)? | 数值（m） |
| Measuring from the closest point of each object, what is the distance between the sofa and the door (in meters)? | 数值（m） |

---

## 类别 5: object_rel_distance（相对最近物体）

**作答形式**: F1（单选题）
**考察能力**: C7 定量距离理解
**GT 依赖**: 3D coordinates、3D bbox

### 模板

```
Measuring from the closest point of each object, which of these objects ({object_A}, {object_B}, {object_C}, {object_D}) is the closest to the {target_object}?
```

### 真实示例

| 问题 | 选项格式 |
|------|--------|
| Measuring from the closest point of each object, which of these objects (table, chair, stool, bathtub) is the closest to the tv? | 从列举物体中选一 |
| Measuring from the closest point of each object, which of these objects (sofa, door, window, cabinet) is the closest to the bed? | 从列举物体中选一 |

---

## 类别 6: object_rel_direction_easy（相对方向-简单）

**作答形式**: F1（单选题，2 选 1）
**考察能力**: C6 3D 空间关系、C9 方位/朝向理解
**GT 依赖**: 3D coordinates、camera pose

### 模板

```
If I am standing by the {anchor_object} and facing the {facing_object}, is the {query_object} to the left or the right of the {facing_object}?
```

### 真实示例

| 问题 | 选项 |
|------|------|
| If I am standing by the stove and facing the tv, is the sofa to the left or the right of the tv? | left / right |
| If I am standing by the bed and facing the door, is the window to the left or the right of the door? | left / right |

---

## 类别 7: object_rel_direction_medium（相对方向-中等）

**作答形式**: F1（单选题，3 选 1）
**考察能力**: C6 3D 空间关系、C9 方位/朝向理解
**GT 依赖**: 3D coordinates、camera pose

### 模板

```
If I am standing by the {anchor_object} and facing the {facing_object}, is the {query_object} to my left, right, or back?
```

### 真实示例

| 问题 | 选项 |
|------|------|
| If I am standing by the table and facing the sofa, is the fireplace to my left, right, or back? | left / right / back |
| If I am standing by the chair and facing the window, is the desk to my left, right, or back? | left / right / back |

---

## 类别 8: object_rel_direction_hard（相对方向-困难）

**作答形式**: F1（单选题，4 选 1）
**考察能力**: C6 3D 空间关系、C9 方位/朝向理解
**GT 依赖**: 3D coordinates、camera pose

### 模板

```
If I am standing by the {anchor_object} and facing the {facing_object}, is the {query_object} to my front-left, front-right, back-left, or back-right?
```

### 真实示例

| 问题 | 选项 |
|------|------|
| If I am standing by the stool and facing the sofa, is the stove to my front-left, front-right, back-left, or back-right? | front-left / front-right / back-left / back-right |
| If I am standing by the bed and facing the closet, is the lamp to my front-left, front-right, back-left, or back-right? | front-left / front-right / back-left / back-right |

---

## 类别 9: obj_appearance_order（物体首次出现顺序）

**作答形式**: F5（排序题）
**考察能力**: C18 轨迹理解
**GT 依赖**: 图本体绝对坐标（camera pose）、instance id、时序帧序列

### 模板

```
What will be the first-time appearance order of the following categories in the video: {category_A}, {category_B}, {category_C}, {category_D}?
```

### 真实示例

| 问题 | 答案格式 |
|------|--------|
| What will be the first-time appearance order of the following categories in the video: ceiling light, cup, heater, door? | 排列顺序（如 door, ceiling light, heater, cup） |
| What will be the first-time appearance order of the following categories in the video: sofa, table, lamp, window? | 排列顺序 |

---

## 占位符说明

| 占位符 | 含义 | 示例值 |
|--------|------|--------|
| `{object_category}` | 物体类别 | table, chair, door, window |
| `{object}` | 目标物体 | table, sofa, door |
| `{object_A}` / `{object_B}` | 距离计算的两个物体 | table, bathtub |
| `{target_object}` | 距离参照物 | tv, bed |
| `{anchor_object}` | 站立参照点 | stove, stool |
| `{facing_object}` | 面朝的物体 | tv, sofa |
| `{query_object}` | 被询问方位的物体 | sofa, fireplace |
| `{category_A..D}` | 视频出现顺序候选类别 | ceiling light, cup, heater, door |

---

## 难度梯度说明

| 类别 | 选项数 | 认知需求 |
|------|--------|---------|
| object_rel_direction_easy | 2（左/右） | 单轴方向判断 |
| object_rel_direction_medium | 3（左/右/后） | 含后方判断 |
| object_rel_direction_hard | 4（斜向四方位） | 完整三维方位 |
| object_rel_distance | N（列举中选一） | 相对距离比较 |
| object_abs_distance | 数值估计 | 绝对度量 |
| object_size_estimation | 数值估计（cm） | 物体尺度感 |
| room_size_estimation | 数值估计（m²） | 空间整体感 |

## 可自动化检查

- 选择题：Exact Match
- 数值题：相对误差 ≤ 20% 视为正确（可调阈值）
- 排序题：Exact Match 或 Kendall Tau ≥ 0.8
- 检查 GT 3D bbox 是否覆盖所有候选物体实例
