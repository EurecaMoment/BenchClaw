# CV-Bench 统一参考卡片

> 本卡片来自用户提供的 `CV-Bench.md`，已纳入统一模板系统作为设计依据。它不是原始资料备份，而是用于 Stage1/Stage4 的参考切片。

## 在统一模板包中的作用

| 字段 | 内容 |
|---|---|
| benchmark | CV-Bench |
| 场景 | 室内/室外通用场景（ADE20K、COCO、ScanNet、nuScenes 等多数据源） |
| 任务范式 | 多选题 VQA（2–6 选 1），测试视觉空间理解能力 |
| 主要能力 | C2 物体计数、C5 2D 空间关系、C6 3D 空间关系、C7 定量距离理解 |
| 作答形式 | F1（单选题）、F9（区间选择题，Count 类） |
| 指标 | Accuracy (exact match on choice label) |
| 自动评分口径 | Exact Match（选项字母标签） |
| 可迁移用法 | Stage1 用于能力/题型/指标设计依据；Stage4 用于模板实例化和评分口径参考，不直接照搬数据。 |

---

# CV-Bench 模板库

**来源**: CV-Bench (NYU Vision X Lab, 2024)
**场景**: 室内/室外通用场景（ADE20K、COCO、ScanNet、nuScenes 等多数据源）
**任务格式**: 多选题 VQA（2–6 选 1），测试视觉空间理解能力
**数据规模**: ~2.6k 问答对（2D: 1438 / 3D: 1200）
**评测指标**: Accuracy (exact match on choice label)

---

## 模板元信息

| 字段 | 值 |
|------|-----|
| 作答形式 | F1（单选题）、F9（区间选择题，Count 类） |
| 考察能力 | C2 物体计数、C5 2D 空间关系、C6 3D 空间关系、C7 定量距离理解 |
| 数据类型 | 单张图像 + GT |
| GT 依赖字段 | 可见物体列表（object category）、可见物体分割结果（mask）、可见物体深度信息（depth） |
| 自动评分方式 | Exact Match（选项字母标签） |
| 人工检查要点 | 干扰选项是否合理（Count 类干扰数字是否接近真实值）；Depth/Distance 类 GT 是否来自精确深度图；Relation 类左右/上下判断是否存在边界歧义 |

---

## 核心特征：2D 与 3D 双维度空间理解

CV-Bench 将视觉空间理解分为两个维度：

- **2D**：基于图像平面的空间关系（左右、上下）和物体计数
- **3D**：基于真实世界深度的距离判断（哪个物体离相机/参照物更近）

---

## 问题类型概览

| 维度 | 任务 | 说明 | 答案形式 |
|------|------|------|----------|
| 2D | Count | 统计图中特定物体数量 | 数字（多选） |
| 2D | Relation | 判断两物体的左右/上下关系 | left/right 或 above/below（2选1） |
| 3D | Depth | 判断哪个物体离相机更近 | 物体名称（2选1） |
| 3D | Distance | 判断哪个物体离参照物更近 | 物体名称（2选1） |

---

## 类型 1: 2D Count（物体计数）

**作答形式**: F1（单选题）
**考察能力**: C2 物体计数
**GT 依赖**: 可见物体列表（instance id、object category）

### 模板

```
How many {object_type}s are in the image?
```

### 真实示例

| 问题 | 答案 | 选项 |
|------|------|------|
| How many organs are in the image? | (C) 1 | 3 / 2 / 1 / 0 |
| How many cushions are in the image? | (E) 6 | 4 / 5 / 8 / 0 / 6 / 7 |
| How many table lamps are in the image? | (C) 1 | 0 / 2 / 1 / 3 |
| How many curtains are in the image? | (D) 1 | 2 / 0 / 3 / 1 |
| How many pictures are in the image? | (D) 1 | 3 / 2 / 0 / 1 |

---

## 类型 2: 2D Relation（空间关系判断）

**作答形式**: F1（单选题，2 选 1）
**考察能力**: C5 2D 空间关系
**GT 依赖**: mask（从分割结果计算质心坐标，判断相对位置）

### 模板

```
Considering the relative positions of the {object_A} and the {object_B} in the image provided, where is the {object_A} located with respect to the {object_B}?
Considering the relative positions of the {object_A} (annotated by the red box) and the {object_B} in the image provided, where is the {object_A} (annotated by the red box) located with respect to the {object_B}?
```

### 真实示例

| 问题 | 答案 | 选项 |
|------|------|------|
| Considering the relative positions of the cushion and the sofa in the image provided, where is the cushion located with respect to the sofa? | (A) left | left / right |
| Considering the relative positions of the wall (annotated by the red box) and the basket in the image provided, where is the wall located with respect to the basket? | (A) left | left / right |
| Considering the relative positions of the beam and the curtain in the image provided, where is the beam located with respect to the curtain? | (A) above | above / below |
| Considering the relative positions of the cabinet (annotated by the red box) and the window in the image provided, where is the cabinet located with respect to the window? | (A) left | left / right |
| Considering the relative positions of the potatoes and the vase in the image provided, where is the potatoes located with respect to the vase? | (B) right | left / right |
| Considering the relative positions of the sign and the curtain in the image provided, where is the sign located with respect to the curtain? | (A) left | left / right |
| Considering the relative positions of the person (annotated by the red box) and the chandelier in the image provided, where is the person located with respect to the chandelier? | (B) below | above / below |
| Considering the relative positions of the wall (annotated by the red box) and the side table in the image provided, where is the wall located with respect to the side table? | (B) right | left / right |

---

## 类型 3: 3D Depth（深度距离判断）

**作答形式**: F1（单选题，2 选 1）
**考察能力**: C6 3D 空间关系
**GT 依赖**: depth（可见物体深度信息，取物体区域平均深度）

### 模板

```
Which object is closer to the camera taking this photo, the {object_A} (highlighted by a red box) or the {object_B} (highlighted by a blue box)?
```

### 真实示例

| 问题 | 答案 | 选项 |
|------|------|------|
| Which object is closer to the camera, the table (red box) or the bookcase (blue box)? | (A) table | table / bookcase |
| Which object is closer to the camera, the door (red box) or the books (blue box)? | (A) door | door / books |
| Which object is closer to the camera, the table (red box) or the television (blue box)? | (A) table | table / television |
| Which object is closer to the camera, the refrigerator (red box) or the door (blue box)? | (A) refrigerator | refrigerator / door |
| Which object is closer to the camera, the door (red box) or the lamp (blue box)? | (B) lamp | door / lamp |
| Which object is closer to the camera, the desk (red box) or the chair (blue box)? | (B) chair | desk / chair |
| Which object is closer to the camera, the television (red box) or the sofa (blue box)? | (B) sofa | television / sofa |

---

## 类型 4: 3D Distance（物体间距离判断）

**作答形式**: F1（单选题，2 选 1）
**考察能力**: C7 定量距离理解
**GT 依赖**: depth（可见物体深度信息）、mask（计算物体间三维距离）

### 模板

```
Estimate the real-world distances between objects in this image. Which object is closer to the {reference} (highlighted by a red box), the {object_A} (highlighted by a blue box) or the {object_B} (highlighted by a green box)?
```

### 真实示例

| 问题 | 答案 | 选项 |
|------|------|------|
| Which object is closer to the books (red box), the bookcase (blue box) or the table (green box)? | (B) table | bookcase / table |
| Which object is closer to the mouse (red box), the television (blue box) or the keyboard (green box)? | (B) keyboard | television / keyboard |
| Which object is closer to the books (red box), the cup (blue box) or the remote (green box)? | (B) remote | cup / remote |
| Which object is closer to the potted plant (red box), the kitchen pan (blue box) or the cup (green box)? | (B) cup | kitchen pan / cup |
| Which object is closer to the barrier (red box), the traffic cone (blue box) or the trailer (green box)? | (A) traffic cone | traffic cone / trailer |
| Which object is closer to the pedestrian (red box), the truck (blue box) or the car (green box)? | (B) car | truck / car |
| Which object is closer to the traffic cone (red box), the motorcycle (blue box) or the bicycle (green box)? | (A) motorcycle | motorcycle / bicycle |

---

## 占位符说明

| 占位符 | 含义 | 示例值 |
|--------|------|--------|
| `{object_type}` | 物体类别 | organs, cushions, table lamps, curtains, pictures |
| `{object_A}` / `{object_B}` | 比较物体（可带 bounding box 标注说明） | cushion, wall, beam, cabinet, table, door |
| `{reference}` | 参照物体（3D Distance 任务） | books, mouse, potted plant, barrier, pedestrian |

---

## 答案特征

- **Count**：数字选项，exact match 字母标签
- **Relation**：`left` / `right` 或 `above` / `below`（2选1）
- **Depth / Distance**：物体名称（2选1）
- 所有答案格式为 `({字母}) {内容}`，评测取字母标签

## 可自动化检查

- 所有类型：Exact Match（选项字母）
- Count 类：从可见物体列表自动统计验证 GT
- Relation 类：从 mask 质心坐标自动验证 GT 方向
- Depth 类：从 depth 图自动验证哪个物体更近
- Distance 类：从 depth + mask 计算三维距离自动验证
