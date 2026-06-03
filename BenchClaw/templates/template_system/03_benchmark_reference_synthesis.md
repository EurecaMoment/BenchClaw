# Benchmark 参考范式综合

本文件把用户提供的 12 个 benchmark 卡片整合成 Stage1/Stage4 的统一设计依据。它不是论文调研综述，而是用于模板设计的参考矩阵。

| Benchmark | 任务范式 | 主要能力 | 可借鉴指标 | 对本模板包的作用 |
|---|---|---|---|---|
| ALFRED | 语言指令 → 具身操作序列（导航 + 物体交互） | C25 任务规划、C16 导航可达性、C21 动作可供性、C22 操作前置条件、C23 操作后果预测、C13 区域/房间归属 | Task Success Rate (SR), Goal Condition Success Rate (GC) | 静态图文 QA/空间题主参考；具身执行/规划扩展参考 |
| CV-Bench | 多选题 VQA（2–6 选 1），测试视觉空间理解能力 | C2 物体计数、C5 2D 空间关系、C6 3D 空间关系、C7 定量距离理解 | Accuracy (exact match on choice label) | 静态图文 QA/空间题主参考 |
| DriveLM | 图文对话式 VQA，覆盖感知→预测→规划完整链路 | C1 物体识别、C4 物体状态理解、C20 时间变化理解、C23 操作后果预测、C25 任务规划、C9 方位/朝向理解 | GPT-Score, Accuracy, BLEU, CIDEr | 静态图文 QA/空间题主参考；具身执行/规划扩展参考；时序/轨迹模板参考 |
| EmbodiedQA | 具身视觉问答——agent 在 3D 环境中导航并回答关于场景的问题 | C1 物体识别、C2 物体计数、C13 区域/房间归属、C16 导航可达性、C25 任务规划 | Accuracy (exact match) | 静态图文 QA/空间题主参考；具身执行/规划扩展参考 |
| MME | 二分类 VQA，要求回答 yes / no | C5 2D 空间关系、C2 物体计数、C1 物体识别、C13 区域/房间归属 | Accuracy + Accuracy+（同一图像成对问题均答对） | 静态图文 QA/空间题主参考 |
| NuScenesQA | 封闭式 VQA，答案为短文本（yes/no、数字、物体类别、状态词） | C1 物体识别、C2 物体计数、C4 物体状态理解、C9 方位/朝向理解、C6 3D 空间关系 | Accuracy (exact match) | 静态图文 QA/空间题主参考 |
| OpenEQA | 开放式 VQA，自由文本回答 | C1 物体识别、C3 属性识别、C5 2D 空间关系、C4 物体状态理解、C21 动作可供性、C13 区域/房间归属 | LLM-Match (GPT-4 打分) | 静态图文 QA/空间题主参考；具身执行/规划扩展参考 |
| REVERIE | 远程对象定位导航——根据高层语言指令导航并定位目标物体 | C25 任务规划、C16 导航可达性、C27 指代表达理解、C13 区域/房间归属、C6 3D 空间关系 | SR (Success Rate), RGS (Remote Grounding Score), RGSPL, SPL | 静态图文 QA/空间题主参考；具身执行/规划扩展参考 |
| SQA3D | 情境化 VQA（Situated QA）——给定 agent 所处位置与朝向，回答关于周围环境的问题 | C1 物体识别、C3 属性识别、C5 2D 空间关系、C6 3D 空间关系、C2 物体计数、C4 物体状态理解、C9 方位/朝向理解、C17 最短路径推理 | Accuracy (top-1 exact match) | 静态图文 QA/空间题主参考；具身执行/规划扩展参考 |
| ScanQA | 开放式 VQA，自由文本回答 | C1 物体识别、C3 属性识别、C5 2D 空间关系、C2 物体计数、C4 物体状态理解、C13 区域/房间归属 | BLEU-1/4, ROUGE-L, METEOR, CIDEr, EM | 静态图文 QA/空间题主参考 |
| VSI-Bench | 选择题（MCQ）+ 数值估计题 | C2 物体计数、C8 尺寸/尺度理解、C7 定量距离理解、C6 3D 空间关系、C9 方位/朝向理解、C18 轨迹理解 | 选择题准确率；数值题相对误差 | 静态图文 QA/空间题主参考；时序/轨迹模板参考 |
| ViewSpatial-Bench | 多选题 VQA（4 选 1），方向答案为复合方向词 | C5 2D 空间关系、C6 3D 空间关系、C9 方位/朝向理解、C10 视角变换理解 | Accuracy (exact match on choice label) | 静态图文 QA/空间题主参考 |

## 综合结论

1. 静态图文评测的主线应从 MME、CV-Bench、VSI-Bench、ViewSpatial-Bench、ScanQA/SQA3D 中吸收题型和空间能力划分。
2. 具身任务/执行任务的设计边界应从 ALFRED、REVERIE、EmbodiedQA、OpenEQA 中吸收，但只有在拥有动作轨迹、导航图或仿真执行环境时才进入主指标。
3. DriveLM、NuScenesQA 的价值在于 ego-centric 视角、时序和驾驶场景空间推理，可迁移到无人车/无人机等外部场景。
4. 本包的第一版可运行核心应聚焦“可见性、计数、2D/3D 空间、距离、容器/区域、时序变化”，这与用户提供的 100 条模板和 qa1 题目最一致。
