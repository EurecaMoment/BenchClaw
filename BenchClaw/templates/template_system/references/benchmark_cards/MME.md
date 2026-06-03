# MME 统一参考卡片

> 本卡片来自用户提供的 `MME.md`，已纳入统一模板系统作为设计依据。它不是原始资料备份，而是用于 Stage1/Stage4 的参考切片。

## 在统一模板包中的作用

| 字段 | 内容 |
|---|---|
| benchmark | MME |
| 场景 | 通用图像场景，覆盖自然图像、物体、场景、文本、海报、代码等多类视觉输入 |
| 任务范式 | 二分类 VQA，要求回答 yes / no |
| 主要能力 | C5 2D 空间关系、C2 物体计数、C1 物体识别、C13 区域/房间归属 |
| 作答形式 | F3（判断题，yes/no） |
| 指标 | Accuracy + Accuracy+（同一图像成对问题均答对） |
| 自动评分口径 | Exact Match（yes/no）；成对 Accuracy+（同图正负问题均答对） |
| 可迁移用法 | Stage1 用于能力/题型/指标设计依据；Stage4 用于模板实例化和评分口径参考，不直接照搬数据。 |

---

# MME 模板库

**来源**: MME: A Comprehensive Evaluation Benchmark for Multimodal Large Language Models (2023)
**场景**: 通用图像场景，覆盖自然图像、物体、场景、文本、海报、代码等多类视觉输入
**任务格式**: 二分类 VQA，要求回答 yes / no
**数据规模**: ~2.3k 问答对，14 个感知与认知子任务
**评测指标**: Accuracy + Accuracy+（同一图像成对问题均答对）

---

## 模板元信息

| 字段 | 值 |
|------|-----|
| 作答形式 | F3（判断题，yes/no） |
| 考察能力 | C5 2D 空间关系、C2 物体计数、C1 物体识别、C13 区域/房间归属 |
| 数据类型 | 单张图像 + GT |
| GT 依赖字段 | 可见物体列表（object category）、可见物体分割结果（mask）、可见物体深度信息（depth） |
| 自动评分方式 | Exact Match（yes/no）；成对 Accuracy+（同图正负问题均答对） |
| 人工检查要点 | 正负问题是否构成真正互补（非同义重复）；场景类别标注是否准确；计数 GT 是否与图像一致 |

---

## 核心特征：成对 yes/no 判断

MME 的每张图像通常配有一组互补判断题：

- 正例问题：图像中事实成立，答案为 `Yes`
- 反例问题：对同一图像构造相反或错误陈述，答案为 `No`

这种设计可以测试模型是否真正理解图像，而不是依赖语言先验。

```text
Q1: Is the pineapple on the left of the pot in the image? Please answer yes or no.
A1: Yes

Q2: Is the pineapple on the right of the pot in the image? Please answer yes or no.
A2: No
```

---

## 空间/场景相关任务概览

| 类别 | 能力 | 答案形式 |
|------|------|----------|
| position | 判断图像平面中物体的上下左右位置关系 | Yes / No |
| count | 判断图中某类物体数量是否符合陈述 | Yes / No |
| existence | 判断图中是否存在某类物体 | Yes / No |
| scene | 判断图像是否属于某类场景地点 | Yes / No |

---

## 类型 1: position（空间位置判断）

**作答形式**: F3（判断题）
**考察能力**: C5 2D 空间关系
**GT 依赖**: mask（从分割结果计算质心坐标，判断相对位置）

### 模板

```
Is the {object_A} on the {direction} of the {object_B} in the image? Please answer yes or no.
Is the {object_A} above the {object_B} in the image? Please answer yes or no.
Is the {object_A} under the {object_B} in the image? Please answer yes or no.
Is the {object_A} on the top of {object_B}? Please answer yes or no.
```

### 真实示例

| 问题 | 答案 |
|------|------|
| Is the pineapple on the left of the pot in the image? Please answer yes or no. | Yes |
| Is the pineapple on the right of the pot in the image? Please answer yes or no. | No |
| Is the dog above the pool in the image? Please answer yes or no. | Yes |
| Is the dog under the pool in the image? Please answer yes or no. | No |
| Is the big red and black umbrella on the top of people? Please answer yes or no. | Yes |
| Is the big red and black umbrella under people? Please answer yes or no. | No |
| Is the person on the right of the train? Please answer yes or no. | Yes |
| Is the person on the left of the train? Please answer yes or no. | No |

---

## 类型 2: count（数量判断）

**作答形式**: F3（判断题）
**考察能力**: C2 物体计数
**GT 依赖**: instance id、object category（从可见物体列表统计）

### 模板

```
Is there only one {object} in the image? Please answer yes or no.
Is there two {object_plural} in the image? Please answer yes or no.
Are there {number} {object_plural} in this image? Please answer yes or no.
Are there only {number} {object_plural} in this image? Please answer yes or no.
Are there {number} {object_plural} appear in this image? Please answer yes or no.
```

### 真实示例

| 问题 | 答案 |
|------|------|
| Is there only one bottle in the image? Please answer yes or no. | Yes |
| Is there two bottles in the image? Please answer yes or no. | No |
| Are there three remotes in this image? Please answer yes or no. | Yes |
| Are there only two remotes in this image? Please answer yes or no. | No |
| Are there three people appear in this image? Please answer yes or no. | Yes |

---

## 类型 3: existence（物体存在判断）

**作答形式**: F3（判断题）
**考察能力**: C1 物体识别
**GT 依赖**: 可见物体列表（object category）

### 模板

```
Is there a {object} in this image? Please answer yes or no.
Is there an {object} in this image? Please answer yes or no.
```

### 真实示例

| 问题 | 答案 |
|------|------|
| Is there a laptop in this image? Please answer yes or no. | Yes |
| Is there a potted plant in this image? Please answer yes or no. | No |
| Is there a bus in this image? Please answer yes or no. | Yes |
| Is there a cow in this image? Please answer yes or no. | No |
| Is there a bottle in this image? Please answer yes or no. | Yes |
| Is there a scissors in this image? Please answer yes or no. | No |

---

## 类型 4: scene（场景地点判断）

**作答形式**: F3（判断题）
**考察能力**: C13 区域/房间归属
**GT 依赖**: room id 或场景类别标签（semantic map）

### 模板

```
Is this picture captured in a place of {scene_type}? Please answer yes or no.
Does this image describe a place of {scene_type}? Please answer yes or no.
```

### 真实示例

| 问题 | 答案 |
|------|------|
| Is this picture captured in a place of bowling alley? Please answer yes or no. | Yes |
| Is this picture captured in a place of hotel outdoor? Please answer yes or no. | No |
| Is this picture captured in a place of beach? Please answer yes or no. | Yes |
| Is this picture captured in a place of library outdoor? Please answer yes or no. | No |
| Does this image describe a place of chalet? Please answer yes or no. | Yes |
| Does this image describe a place of tower? Please answer yes or no. | No |

---

## 占位符说明

| 占位符 | 含义 | 示例值 |
|--------|------|--------|
| `{object_A}` | 待定位物体 | pineapple, dog, umbrella, person |
| `{object_B}` | 空间参照物 | pot, pool, people, train |
| `{direction}` | 图像平面方向 | left, right, above, under, top |
| `{object}` / `{object_plural}` | 计数或存在判断目标 | bottle(s), remote(s), people, laptop, bus |
| `{number}` | 数量词 | one, two, three |
| `{scene_type}` | 场景类别 | bowling alley, hotel outdoor, beach, library outdoor, chalet, tower |

---

## 答案特征

- 所有问题强制要求 `Please answer yes or no.`
- 标准答案只取 `Yes` / `No`
- 成对构造是 MME 的核心：同一图像的正负问题都答对才说明模型对图像事实有稳定理解

## 可自动化检查

- 所有类型：Exact Match（yes/no）
- position 类：从 mask 质心坐标自动验证 GT 方向正确性
- count 类：从可见物体列表自动统计验证
- existence 类：从可见物体列表自动验证
- scene 类：需人工确认场景标签准确性
