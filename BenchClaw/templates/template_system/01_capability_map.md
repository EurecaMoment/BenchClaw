# 统一能力维度图谱

下表从上传包的 benchmark 卡片和 100 条题目模板中归并而来。Stage1 应使用这些能力维度描述“评测什么”，不要把单选/多选/判断等作答形式当成能力。

| ID | 能力维度 | 定义 | 可观测证据/GT 依赖 | 常见题型 | 代表参考 |
|---|---|---|---|---|---|
| C1 | 物体识别 | 识别图像、帧序列或 3D 场景中的物体类别/实例 | object category、instance id、mask、bbox | F1/F2/F3/F7 | MME、CV-Bench、ScanQA |
| C2 | 物体计数 | 统计某类物体或候选集合的数量 | instance id、object list、visibility | F1/F8/F9/F10 | CV-Bench、VSI-Bench、EmbodiedQA |
| C3 | 属性识别 | 判断颜色、材质、大小、外观属性 | attribute、mask、bbox、视觉帧 | F1/F7/F25 | ScanQA、SQA3D、OpenEQA |
| C4 | 状态理解 | 判断物体开关、清洁、移动、可见、持有等状态 | object state、tracker history、agent inventory | F1/F3/F7 | ALFRED、DriveLM、NuScenesQA |
| C5 | 2D 空间关系 | 判断图像平面上的左/右/上/下、包含、接触等 | mask、2D bbox、pixel coordinates | F1/F3/F12/F16 | MME、CV-Bench |
| C6 | 3D 空间关系 | 判断真实空间中的前后、左右、邻近、容器/支撑关系 | 3D coordinates、3D bbox、camera pose、parentReceptacles | F1/F2/F7/F10 | SQA3D、ViewSpatial、REVERIE |
| C7 | 定量距离理解 | 比较或估计物体间距离、相机距离、相对远近 | depth、3D coordinates、camera pose | F1/F8/F10 | CV-Bench、VSI-Bench |
| C8 | 尺寸/尺度理解 | 估计物体大小、最长边、面积或相对尺寸 | 3D bbox、mask area、depth scale | F1/F8/F10 | VSI-Bench、CV-Bench |
| C9 | 方位/朝向理解 | 相对于 agent/camera/ego vehicle 的方向判断 | agent pose、camera pose、heading、rotation | F1/F3/F7 | SQA3D、DriveLM、NuScenesQA |
| C10 | 视角变换理解 | 在 camera/person/scene simulation 等参考系之间转换方向 | pose、reference frame、3D coordinates | F1/F10 | ViewSpatial-Bench |
| C11 | 可见性理解 | 判断当前或历史帧中某对象是否可见 | isVisible、visible object list、frame index | F3/F2/F11 | qa1 样例、MME |
| C12 | 遮挡/深度层次 | 判断遮挡关系、前景/背景、深度层级 | depth、mask overlap、3D coordinates | F1/F3/F10 | 100 条模板库 |
| C13 | 区域/房间归属 | 判断对象所在房间、区域或容器 | room id、region label、parentReceptacles | F1/F7/F25 | EmbodiedQA、ScanQA、OpenEQA |
| C16 | 导航可达性 | 判断或执行到目标位置的可达性 | navigation path、agent pose、topology/navmesh | F18/F19 | ALFRED、REVERIE |
| C17 | 最短路径推理 | 判断更短路径、经过顺序或路径效率 | path、pose history、graph distance | F1/F5/F8 | SQA3D、REVERIE |
| C18 | 轨迹/时序理解 | 判断出现、消失、移动、状态变化、首次/末次发生 | tracker history、frame sequence、timestamps | F3/F5/F11/F2 | VSI-Bench、qa1 样例 |
| C20 | 时间变化理解 | 比较初始/当前/过去 n 步/任意时刻状态 | tracker history、timestep | F1/F2/F3/F8 | qa1 样例、DriveLM |
| C21 | 动作可供性 | 判断物体是否可拿取、可打开、可切、可清洁等 | pickupable、openable、toggleable、dirtyable、affordance flags | F1/F3/F25 | ALFRED、OpenEQA |
| C22 | 操作前置条件 | 判断动作执行前需要满足的状态/位置条件 | object state、agent inventory、precondition graph | F1/F3/F19 | ALFRED |
| C23 | 操作后果预测 | 判断动作后物体状态、位置或容器关系变化 | state transition、tracker history | F1/F3/F25 | ALFRED、DriveLM |
| C25 | 任务规划 | 将目标拆成可执行步骤或选择下一步动作 | action history、goal conditions、planner trace | F18/F19/F25 | ALFRED、REVERIE |
| C27 | 指代表达理解 | 通过组合属性、位置和上下文定位唯一对象 | object category、attributes、relations、bbox | F1/F7/F16 | REVERIE、100 条模板库 |
| C28 | 复杂约束筛选 | 在类别、位置、深度、面积、可见性等多个条件下筛选唯一或集合答案 | object list、bbox、mask area、depth、3D coordinates | F1/F6/F24 | 100 条模板库、可运行合成引擎 |
| C30 | 不可答判断 | 判断问题是否超出当前图像/GT 字段支持范围，抑制常识臆测 | visible object list、evidence fields、missing-field reason | F4/F20/F3 | 100 条模板库、可运行合成引擎 |

## 使用建议

Stage1 的能力维度不必越多越好。优先选择当前数据已有 GT 字段支持、能自动评分、与目标应用场景强相关、歧义风险低的能力。


## 统一使用规则

1. Stage1 中每个能力维度必须给出数据/GT 可得性说明，否则不能进入正式评测范围。
2. Stage4 中每个 eval item 至少绑定一个 `capability_id`，复杂题可以绑定多个能力，但必须指定 primary capability。
3. `C16/C17/C21/C22/C23/C25` 等执行型能力若当前只有静态图文数据，应作为扩展能力或设计参考，不应强行转成静态题。
4. `C1/C2/C5/C7/C11/C13/C18/C20` 与用户 qa1 样例和 100 条模板重合度最高，适合作为第一版可运行评测核心。
