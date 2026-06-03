# SQA3D 统一参考卡片

> 本卡片来自用户提供的 `SQA3D.md`，已纳入统一模板系统作为设计依据。它不是原始资料备份，而是用于 Stage1/Stage4 的参考切片。

## 在统一模板包中的作用

| 字段 | 内容 |
|---|---|
| benchmark | SQA3D |
| 场景 | 室内 3D 点云扫描（ScanNet，650 个场景） |
| 任务范式 | 情境化 VQA（Situated QA）——给定 agent 所处位置与朝向，回答关于周围环境的问题 |
| 主要能力 | C1 物体识别、C3 属性识别、C5 2D 空间关系、C6 3D 空间关系、C2 物体计数、C4 物体状态理解、C9 方位/朝向理解、C17 最短路径推理 |
| 作答形式 | F7（填空题）、F3（判断题）、F1（单选题，方向类） |
| 指标 | Accuracy (top-1 exact match) |
| 自动评分口径 | 归一化后 Exact Match（方向词、颜色词、是/否、数字均可归一化） |
| 可迁移用法 | Stage1 用于能力/题型/指标设计依据；Stage4 用于模板实例化和评分口径参考，不直接照搬数据。 |

---

# SQA3D 模板库

**来源**: SQA3D (UCLA, ICLR 2023)
**场景**: 室内 3D 点云扫描（ScanNet，650 个场景）
**任务格式**: 情境化 VQA（Situated QA）——给定 agent 所处位置与朝向，回答关于周围环境的问题
**数据规模**: 6.8k 情境 × 33.4k 问题
**评测指标**: Accuracy (top-1 exact match)

---

## 模板元信息

| 字段 | 值 |
|------|-----|
| 作答形式 | F7（填空题）、F3（判断题）、F1（单选题，方向类） |
| 考察能力 | C1 物体识别、C3 属性识别、C5 2D 空间关系、C6 3D 空间关系、C2 物体计数、C4 物体状态理解、C9 方位/朝向理解、C17 最短路径推理 |
| 数据类型 | 多张有时序图像 + GT |
| GT 依赖字段 | 物体列表（object category）、物体绝对坐标（3D coordinates）、图本体绝对坐标（camera pose）、三维包围盒（3D bbox） |
| 自动评分方式 | 归一化后 Exact Match（方向词、颜色词、是/否、数字均可归一化） |
| 人工检查要点 | situation 描述是否与 GT 场景一致；方向答案是否依赖 agent 朝向正确计算；数量答案是否唯一 |

---

## 核心特征：情境化（Situated）

SQA3D 的独特之处在于每道题都附带一个 **situation**（情境描述），描述 agent 当前的位置、朝向和正在进行的动作。问题的答案依赖于 agent 的视角，而非绝对场景坐标。

**数据结构**:
```json
{
  "situation": "I am facing a window and there is a desk on my right and a chair behind me.",
  "question": "What color is the desk to my right?",
  "answer": "brown"
}
```

---

## 问题类型概览

SQA3D 覆盖以下主要推理类型（均以第一人称视角提问）：

1. 物体识别（以 agent 视角定位）
2. 空间关系（相对于 agent 的方向）
3. 颜色与外观属性
4. 数量统计
5. 导航与行动推理
6. 状态判断（是/否）
7. 常识与功能推理

---

## 类型 1: 物体识别（以 agent 视角）

**作答形式**: F7（填空题）
**考察能力**: C1 物体识别、C5 2D 空间关系
**GT 依赖**: object category、3D bbox、camera pose

### 模板

```
What is {direction_from_agent}?
What is on top of the {object} that is {direction_from_agent}?
What is below the {object} {direction_from_agent}?
What is next to me on my {direction}?
```

### 真实示例

| 情境 | 问题 | 答案 |
|------|------|------|
| I am standing by the ottoman on my right facing a couple of toolboxes. | What instrument in front of me is ebony and ivory? | piano |
| I am standing ahead of the mat and my backside is facing the window and looking at the chair. | What is on top of the desk that is on my left? | book |
| Crouching and changing the trash bag. | What is below the picture on my left? | toilet |
| I am facing a picture and there is a door on my right. | What is next to me on my left? | trash can |
| I am standing in front of a table and facing it while there is a rack on my left within reach. | What is on the right of the mini fridge that is far away in front of me? | sofa chair |

---

## 类型 2: 空间关系与方向

**作答形式**: F1（单选题，方向词）
**考察能力**: C9 方位/朝向理解、C17 最短路径推理
**GT 依赖**: camera pose、3D coordinates、room graph

### 模板

```
Which direction should I go if I want to {goal}?
Which direction should I go if I wanted to {action}?
If I turned directly around and walked straight, what would I first hit?
```

### 真实示例

| 情境 | 问题 | 答案 |
|------|------|------|
| I am sitting on an armchair while having another one to my left. | Which direction should I go if I wanted to leave the room? | left |
| I am walking into the room. | Which direction should I go if I want to open a window? | right |
| I am standing in front of a table and facing it while there is a rack on my left within reach. | Which direction should I go if I want to use sink? | left |
| I am standing on the rug by the bathroom cabinet and facing the toilet. | To put on my slippers which way do I turn? | left |
| I am facing a chair and there is a printer on my right. | If I turned directly around and walked straight, what would I first hit? | cart |
| Standing by the door on my left, I am pulling the cart out in front of me. | Need to pick up the printouts, which way to go? | backward |

---

## 类型 3: 颜色与外观属性

**作答形式**: F7（填空题）或 F3（判断题）
**考察能力**: C3 属性识别
**GT 依赖**: color 属性字段、object category

### 模板

```
What color is the {object} to my {direction}?
Is the {object_A} the same color as the {object_B} {direction_from_agent}?
Are all the {objects} in the room the same color?
```

### 真实示例

| 情境 | 问题 | 答案 |
|------|------|------|
| I am facing a window and there is a desk on my right and a chair behind me. | What color is the desk to my right? | brown |
| I am facing the sink and the toilet is to my right within reach. | Is the bathroom counter the same color as the bathtub behind me? | no |
| I am standing and the red backpack is on my right side and I am facing wall across the room. | Are all the chairs in the room the same color? | no |

---

## 类型 4: 数量统计

**作答形式**: F7（填空题）或 F3（判断题）
**考察能力**: C2 物体计数
**GT 依赖**: instance id、object category、camera pose

### 模板

```
How many {objects} are directly in front of me?
How many {objects} to my {direction}?
How many {objects} are on top of the {object} {direction_from_agent}?
Can the amount of {objects} {direction_from_agent} be divided by {number}?
Are there more {objects} to my left than there are to my right?
```

### 真实示例

| 情境 | 问题 | 答案 |
|------|------|------|
| I just walked into the room through the doors. | How many armchairs are directly in front of me? | zero |
| I am looking at my backpack and desk is behind me. | How many windows to my left? | one |
| I am sitting on the office chair facing the desk with a window on my left. | How many monitors are on top of the desk in front of me? | three |
| I am sitting on the armchair facing the desk. | How many backpacks are on the ottoman behind me to the left side? | two |
| I am standing in front of the door, while my left is a trash can. | Can the amount of trash can behind me be divided by three? | no |
| I am standing by backpack on my left side and the bed is behind me while the curtain is in my six o'clock direction. | Are there more doors to my left than there are to my right? | no |

---

## 类型 5: 状态判断（是/否）

**作答形式**: F3（判断题）
**考察能力**: C4 物体状态理解、C11 可见性理解
**GT 依赖**: object state、visibility flag

### 模板

```
Is the {object} {state}?
Can I {action}?
Are there {objects} {location}?
```

### 真实示例

| 情境 | 问题 | 答案 |
|------|------|------|
| I am facing a trash can, while there is a door on my right. | Can I still walk forward? | no |
| I am standing between two beds with a nightstand behind me. | Are there pictures on the wall? | yes |
| I am standing in front of a vending machine that is next to another one, while there is a trash can behind me directly. | Can I see clothes where I am standing? | yes |

---

## 类型 6: 形状与物理属性

**作答形式**: F1（单选题）
**考察能力**: C3 属性识别
**GT 依赖**: object category、3D bbox（形状可从 bbox 推断）

### 模板

```
Is the shape of {object} in front of me round, square or rectangular?
Is the amount of {objects} odd or even?
```

### 真实示例

| 情境 | 问题 | 答案 |
|------|------|------|
| I am taking out the white ball from the side pocket while my beer on the table is not being drunk by me. I am also facing the window. | Is the shape of pool table in front of me round, square or rectangular? | rectangular |
| I am sitting on a chair facing the table with the blackboard behind me and a chair on my left within reach. | Is the amount of table I am facing odd or even? | odd |

---

## 类型 7: 常识与功能推理

**作答形式**: F25（开放问答）
**考察能力**: C21 动作可供性、C9 方位/朝向理解
**GT 依赖**: affordance labels、camera pose

### 模板

```
How do I {action} the {object}?
What can I {use/add} to {goal}?
Do I turn right or left to {action}?
```

### 真实示例

| 情境 | 问题 | 答案 |
|------|------|------|
| I am facing office chair and the TV is on my left side. | How do I leave a bottle of water that I am holding on the table? | reach out on my right |
| I am washing my hands facing a shelf. | What can I add to the dryer to keep the clothes from sticking together due to static? | dryer sheets |
| I am sitting on the toilet and there is a sink to my right, we use the sink to brush our teeth. | Do I turn right or left to wash my hands after I am done using the toilet? | right |

---

## 占位符说明

| 占位符 | 含义 | 示例值 |
|--------|------|--------|
| `{situation}` | agent 当前位置与朝向描述 | I am facing a window and there is a desk on my right |
| `{direction_from_agent}` | 相对 agent 的方向短语 | to my left, in front of me, behind me |
| `{direction}` | 方向词 | left, right, forward, backward |
| `{object}` | 目标物体 | desk, toilet, armchair |
| `{objects}` | 物体复数 | chairs, windows, monitors |
| `{goal}` | 目标动作 | leave the room, open a window, use sink |
| `{action}` | 具体动作 | wash my hands, put on my slippers |
| `{number}` | 整除判断数 | three, two |
| `{state}` | 物体状态 | open, closed, same color |

---

## 与 ScanQA 的关键区别

| 维度 | ScanQA | SQA3D |
|------|--------|-------|
| 视角 | 第三人称（场景全局） | 第一人称（agent 情境化） |
| 情境描述 | 无 | 必须提供 situation |
| 空间参考系 | 绝对坐标 | 相对 agent 的方向 |
| 导航推理 | 无 | 有（which direction to go） |
| 答案类型 | 自由文本 | 自由文本（含方向词、是/否） |

## 可自动化检查

- 方向类答案：与 GT camera pose + 3D coordinates 计算结果对比，exact match
- 颜色/数量类：归一化后 exact match
- 是/否类：exact match
- 功能推理类：LLM-judge，需人工抽查
