# ViewSpatial-Bench 统一参考卡片

> 本卡片来自用户提供的 `ViewSpatial-Bench.md`，已纳入统一模板系统作为设计依据。它不是原始资料备份，而是用于 Stage1/Stage4 的参考切片。

## 在统一模板包中的作用

| 字段 | 内容 |
|---|---|
| benchmark | ViewSpatial-Bench |
| 场景 | 室内 3D 场景（ScanNet、COCO 等），多视角空间理解 |
| 任务范式 | 多选题 VQA（4 选 1），方向答案为复合方向词 |
| 主要能力 | C5 2D 空间关系、C6 3D 空间关系、C9 方位/朝向理解、C10 视角变换理解 |
| 作答形式 | F1（单选题，4 选 1） |
| 指标 | Accuracy (exact match on choice label) |
| 自动评分口径 | Exact Match（选项字母标签或方向词） |
| 可迁移用法 | Stage1 用于能力/题型/指标设计依据；Stage4 用于模板实例化和评分口径参考，不直接照搬数据。 |

---

# ViewSpatial-Bench 模板库

**来源**: ViewSpatial-Bench (Li et al., 2025)
**场景**: 室内 3D 场景（ScanNet、COCO 等），多视角空间理解
**任务格式**: 多选题 VQA（4 选 1），方向答案为复合方向词
**数据规模**: ~5.7k 问答对
**评测指标**: Accuracy (exact match on choice label)

---

## 模板元信息

| 字段 | 值 |
|------|-----|
| 作答形式 | F1（单选题，4 选 1） |
| 考察能力 | C5 2D 空间关系、C6 3D 空间关系、C9 方位/朝向理解、C10 视角变换理解 |
| 数据类型 | 单张图像 + GT（Camera/Person perspective）；多张有时序图像 + GT（Scene Simulation） |
| GT 依赖字段 | 物体绝对坐标（3D coordinates）、三维包围盒（3D bbox）、图本体绝对坐标（camera pose）、可见物体分割结果（mask） |
| 自动评分方式 | Exact Match（选项字母标签或方向词） |
| 人工检查要点 | 16 方向词体系中边界方向是否存在歧义（如 front vs front-left）；Person perspective 中人物朝向是否可从图像明确判断；Scene Simulation 中站立位置和朝向是否唯一确定 |

---

## 核心特征：三视角空间推理

ViewSpatial-Bench 将空间理解分为三种视角，测试模型在不同参考系下的方向推理能力：

1. **Camera perspective**：以摄像机为参考系，判断物体间相对方向
2. **Person perspective - Object View Orientation**：以图中人/动物为参考系，判断其朝向
3. **Person perspective - Scene Simulation**：模拟站在场景中某位置朝向某物体，判断第三物体的方向

**方向词体系**（16 方向）：front, back, left, right, above, down, front-left, front-right, back-left, back-right, above-left, above-right, front-up, back-up, down-left, down-right

---

## 问题类型概览

| 类型 | 说明 | 答案形式 |
|------|------|----------|
| Camera perspective - Relative Direction | 从摄像机视角判断两物体的相对方向 | 方向词（4选1） |
| Person perspective - Object View Orientation | 判断图中人/动物的朝向 | 方向词（4选1） |
| Person perspective - Scene Simulation Relative Direction | 模拟站在场景中，判断第三物体方向 | 方向词（4选1） |

---

## 类型 1: Camera perspective - Relative Direction

**作答形式**: F1（单选题，4 选 1）
**考察能力**: C5 2D 空间关系、C6 3D 空间关系
**GT 依赖**: 3D coordinates、3D bbox、camera pose

### 模板

```
Could you tell me the location of {object_A} in comparison to {object_B}?
How is the {object_A} positioned with respect to the {object_B}?
If you're looking at the {object_A}, where would you find the {object_B}?
Where is the {object_A} in relation to the {object_B}?
Can you describe the position of {object_A} relative to {object_B}?
Where is the {object_A} located compared to the {object_B} from the camera's perspective?
```

### 真实示例

| 问题 | 答案 | 选项 |
|------|------|------|
| Could you tell me the location of the counter in comparison to the refrigerator? | A. right | A. right / B. front-up / C. back-left / D. front |
| How is the cabinet positioned with respect to the table? | D. back | A. left / B. front-left / C. above-left / D. back |
| If you're looking at the counter, where would you find the table? | D. back-right | A. front-right / B. front / C. front-up / D. back-right |
| Could you tell me the location of the table in comparison to the television? | B. down | A. above / B. down / C. back-left / D. back-up |
| How is the table positioned with respect to the refrigerator? | C. back-down | A. above / B. front-up / C. back-down / D. back-up |
| Where is the door located compared to the whiteboard from the camera's perspective? | B. front | A. down / B. front / C. above-left / D. back-up |
| Where is the table in relation to the cabinet? | C. front-left | A. above / B. above-right / C. front-left / D. down-left |
| Can you describe the position of the whiteboard relative to the window? | C. left | A. right / B. back / C. left / D. above-right |
| Where is the cabinet in relation to the window? | D. down | A. left / B. front-right / C. above / D. down |
| Could you tell me the location of the sofa in comparison to the desk? | B. back | A. right / B. back / C. front / D. front-down |

---

## 类型 2: Person perspective - Object View Orientation

**作答形式**: F1（单选题，4 选 1）
**考察能力**: C9 方位/朝向理解、C10 视角变换理解
**GT 依赖**: mask（人物/动物分割）、camera pose（推算人物朝向）

### 模板

```
Picture yourself as the {subject}; which way are you looking in the scene?
Suppose you are in the {subject}'s position, what direction are you facing?
Imagine you're the {subject} in this image — which direction are you facing?
As the {subject} in the photo, in which direction are you facing?
```

### 真实示例

| 问题 | 答案 | 选项 |
|------|------|------|
| Picture yourself as the giraffe; which way are you looking in the scene? | A. front | A. front / B. left / C. back-left / D. back |
| Picture yourself as the man wearing red trousers; which way are you looking in the scene? | B. right | A. left / B. right / C. front-left / D. back |
| Suppose you are in the cat's position, what direction are you facing? | A. front | A. front / B. back / C. left / D. right |
| Imagine you're the woman in this image — which direction are you facing? | D. front-left | A. right / B. back / C. back-right / D. front-left |
| Suppose you are in the bird's position, what direction are you facing? | A. front-left | A. front-left / B. back-right / C. right / D. back |
| As the man in the photo, in which direction are you facing? | B. front-left | A. right / B. front-left / C. back-right / D. back |
| As the man wearing the white helmet in the photo, in which direction are you facing? | D. front | A. back-left / B. left / C. back-right / D. front |
| Picture yourself as the standing woman; which way are you looking in the scene? | A. front | A. front / B. back-left / C. back-right / D. right |

---

## 类型 3: Person perspective - Scene Simulation Relative Direction

**作答形式**: F1（单选题，4 选 1）
**考察能力**: C10 视角变换理解、C6 3D 空间关系
**GT 依赖**: 3D coordinates、3D bbox、camera pose

### 模板

```
Imagine standing at {location_A} looking towards {location_B}, where is {object_C}?
Standing at {location_A}, gazing at {location_B}, where should {object_C} be?
If you stand at {location_A} facing {location_B}, where is {object_C}?
When positioned at {location_A} facing {location_B}, where can you find {object_C}?
```

### 真实示例

| 问题 | 答案 | 选项 |
|------|------|------|
| Imagine standing at window looking towards cabinet, where is books? | A. front-right | A. front-right / B. back-right / C. front-left / D. back |
| Standing at window, gazing at cabinet, where should whiteboard be? | A. front-left | A. front-left / B. back / C. right / D. front-right |
| Standing at desk, gazing at whiteboard, where should books be? | C. right | A. back-left / B. back / C. right / D. front |
| If you stand at box facing door, where is window? | A. front-right | A. front-right / B. back / C. front-left / D. back-left |
| If you stand at box facing window, where is whiteboard? | A. front-right | A. front-right / B. left / C. back-left / D. back-right |
| Standing at box, gazing at door, where should whiteboard be? | D. right | A. front / B. back / C. back-left / D. right |
| When positioned at door facing window, where can you find whiteboard? | D. front-right | A. back-right / B. back / C. left / D. front-right |
| Imagine standing at desk looking towards cabinet, where is books? | D. front-right | A. back-right / B. left / C. back / D. front-right |

---

## 占位符说明

| 占位符 | 含义 | 示例值 |
|--------|------|--------|
| `{object_A}` / `{object_B}` | 场景中的物体 | counter, cabinet, table, window, whiteboard, sofa, desk |
| `{subject}` | 图中人物或动物 | giraffe, man wearing red trousers, cat, woman, bird |
| `{location_A}` | 站立位置（物体名） | window, desk, box, door |
| `{location_B}` | 朝向目标（物体名） | cabinet, whiteboard, door, window |
| `{object_C}` | 待判断方向的第三物体 | books, whiteboard, window |

---

## 答案特征

- 所有答案为 4 选 1 多选题，格式为 `{字母}. {方向词}`
- 方向词为 16 方向复合词体系（front/back/left/right/above/down 及其组合）
- 评测时取字母标签做 exact match，或取方向词做 exact match

## 可自动化检查

- Camera perspective 类：从 3D coordinates + camera pose 自动计算方向向量，验证 GT
- Scene Simulation 类：从 3D coordinates 模拟站立位置和朝向，自动计算第三物体方向
- Person perspective 类：需人工确认人物朝向（图像中人物姿态无法从 GT 字段直接推算）
- 检查 16 方向边界歧义：当两物体方向角接近 45° 边界时，标记为需人工复核
