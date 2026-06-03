# ScanQA 统一参考卡片

> 本卡片来自用户提供的 `ScanQA.md`，已纳入统一模板系统作为设计依据。它不是原始资料备份，而是用于 Stage1/Stage4 的参考切片。

## 在统一模板包中的作用

| 字段 | 内容 |
|---|---|
| benchmark | ScanQA |
| 场景 | 室内 3D 点云扫描（ScanNet，800 个场景） |
| 任务范式 | 开放式 VQA，自由文本回答 |
| 主要能力 | C1 物体识别、C3 属性识别、C5 2D 空间关系、C2 物体计数、C4 物体状态理解、C13 区域/房间归属 |
| 作答形式 | F25（开放问答题） |
| 指标 | BLEU-1/4, ROUGE-L, METEOR, CIDEr, EM |
| 自动评分口径 | BLEU-1/4、ROUGE-L、METEOR、CIDEr；归一化后 Exact Match |
| 可迁移用法 | Stage1 用于能力/题型/指标设计依据；Stage4 用于模板实例化和评分口径参考，不直接照搬数据。 |

---

# ScanQA 模板库

**来源**: ScanQA (ATR-DBI, CVPR 2022)
**场景**: 室内 3D 点云扫描（ScanNet，800 个场景）
**任务格式**: 开放式 VQA，自由文本回答
**数据规模**: ~41k 问答对
**评测指标**: BLEU-1/4, ROUGE-L, METEOR, CIDEr, EM

---

## 模板元信息

| 字段 | 值 |
|------|-----|
| 作答形式 | F25（开放问答题） |
| 考察能力 | C1 物体识别、C3 属性识别、C5 2D 空间关系、C2 物体计数、C4 物体状态理解、C13 区域/房间归属 |
| 数据类型 | 多张有时序图像 + GT |
| GT 依赖字段 | 物体列表（object category）、物体绝对坐标（3D coordinates）、三维包围盒（3D bbox） |
| 自动评分方式 | BLEU-1/4、ROUGE-L、METEOR、CIDEr；归一化后 Exact Match |
| 人工检查要点 | 答案是否语义等价但表述不同（如 "dark gray" vs "grey"）；位置描述是否合理；数量答案是否唯一确定 |

---

## 问题类型概览

ScanQA 为人工标注的自由形式问题，覆盖以下主要类型：

1. 物体识别与定位
2. 空间关系描述
3. 颜色/材质/外观属性
4. 数量统计
5. 物体功能与用途
6. 比较与对比

---

## 类型 1: 物体识别与定位

**作答形式**: F25（开放问答）
**考察能力**: C1 物体识别、C13 区域/房间归属
**GT 依赖**: object category、3D bbox、room id

### 模板

```
What is {spatial_relation} the {reference_object}?
What is in {location_description}?
Where is the {object}?
What {object_type} is {location_description}?
```

### 真实示例

| 问题 | 答案 |
|------|------|
| What is in the right corner of room by curtains? | brown cabinet with tv sitting in it |
| What is on the left of the tv? | bicycle on floor |
| What is in front of the radiator? | small table |
| What is next to the chair? | small table |
| What is in the corner of the bath? | shower |
| What is found in one corner of the room? | cabinet |
| What can be seen near the refrigerator? | cabinet |
| What is in front of a window? | white tv stand |

---

## 类型 2: 空间关系描述

**作答形式**: F25（开放问答）
**考察能力**: C5 2D 空间关系、C6 3D 空间关系
**GT 依赖**: 3D bbox、3D coordinates

### 模板

```
Where is the {object} located?
Where is the {object} placed?
What is the {object} in front of / behind / next to?
The {object} is sitting to the {direction} of what?
```

### 真实示例

| 问题 | 答案 |
|------|------|
| Where is the beige wooden working table placed? | right of tall cabinet |
| Where is the brown door located? | between 2 tall cabinets |
| Where is the triangular shape table located? | in front of radiator |
| Where is the tv stand sitting? | under 2 windows |
| The tv stand is sitting to the right of what? | window |
| What does the rectangular window with brown molding sit behind? | tv stand |
| Where do the bottoms of the windows sit? | floor level |

---

## 类型 3: 颜色与外观属性

**作答形式**: F25（开放问答）
**考察能力**: C3 属性识别
**GT 依赖**: object category、color/material 属性字段

### 模板

```
What color is the {object}?
What color {object} is {location_description}?
What color {object} is {relation} the {reference_object}?
What does the {description} {object} have in its {part}?
```

### 真实示例

| 问题 | 答案 |
|------|------|
| What color is the couch? | dark gray |
| What color is the throw pillow? | blue |
| What color is the trash can? | blue |
| What color storage bin is next to the orange one? | teal |
| What color storage bin is on top of a white cabinet? | orange |
| What color couch is the pillow sitting on? | grey |
| What does the dark grey upholstered couch have in its middle? | blue pillow |

---

## 类型 4: 数量统计

**作答形式**: F7（填空题）或 F25（开放问答）
**考察能力**: C2 物体计数
**GT 依赖**: instance id、object category

### 模板

```
How many {objects} are in the {room/area}?
How many {objects} does the {container} have?
```

### 真实示例

| 问题 | 答案 |
|------|------|
| How many drawers are in the storage cabinet? | 3 |

---

## 类型 5: 物体属性与状态

**作答形式**: F25（开放问答）
**考察能力**: C4 物体状态理解、C8 尺寸/尺度理解
**GT 依赖**: object state、object size

### 模板

```
What is the {attribute} of the {object}?
What is {kept/placed} on the {object}?
What is the {object} on top of?
```

### 真实示例

| 问题 | 答案 |
|------|------|
| What is the height of the storage cabinet? | short |
| What is kept on the chair left of the windows? | pillow |
| What is the black microwave on top of? | mini fridge |
| What is the orange storage bin on top of? | white cabinet |
| What is under the couch's front feet? | orange rug |

---

## 占位符说明

| 占位符 | 含义 | 示例值 |
|--------|------|--------|
| `{object}` | 目标物体 | couch, cabinet, tv stand |
| `{reference_object}` | 参照物体 | radiator, window, chair |
| `{spatial_relation}` | 空间关系词 | in front of, next to, on the left of |
| `{location_description}` | 位置描述短语 | in the right corner of room by curtains |
| `{direction}` | 方向 | right, left, above, below |
| `{attribute}` | 属性类型 | height, color, size |
| `{container}` | 容器物体 | storage cabinet, drawer |

---

## 答案特征

- 答案为自由文本，通常 1–10 词
- 颜色答案：单词（dark gray, teal, blue）
- 位置答案：介词短语（right of tall cabinet, under 2 windows）
- 物体答案：名词短语（brown cabinet with tv, bicycle on floor）
- 数量答案：数字（3）
- 属性答案：形容词（short）

## 可自动化检查

- 数量类答案：与 GT instance count 对比，exact match
- 颜色类答案：归一化颜色词后 exact match
- 位置类答案：BLEU/ROUGE 辅助，人工抽查语义等价性
