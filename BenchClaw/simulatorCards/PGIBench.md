# PGIBench 能力卡片

## !!! 仿真器目录（最重要）

- /home/maqiang/benchclaw/simulators/PGIBench

## 1. Benchmark 基本信息

- 项目路径: /home/maqiang/benchclaw/simulators/PGIBench
- 运行环境: 必须使用 conda 环境 stbench
- 仿真器核心: pgibench/envs/pgi_alfred
- 交互入口: pgibench/envs/pgi_alfred/PGIAlfEnv.py
- 评测入口: pgibench/main.py -> pgibench/evaluator/pgi_alfred_evaluator.py

## 2. 能力总览表

| 维度 | 能力描述 | 代码/文档依据 |
|---|---|---|
| 观测模态 | 视觉主模态为第一视角 RGB 帧，观测键为 head_rgb；支持语言指令；支持语言仅模式 language_only；支持可选检测框可视化 detection_box/visual_prompt；支持代理位置与环境反馈作为提示上下文。 | README.md, pgibench/envs/pgi_alfred/PGIAlfEnv.py, pgibench/evaluator/pgi_alfred_evaluator.py, pgibench/configs/pgi-alf.yaml |
| 动作空间 | 导航与视角动作: LookUp/LookDown/RotateLeft/RotateRight/MoveAhead/MoveBack/MoveLeft/MoveRight；对象交互动作: pick up, put down, open, close, turn on, turn off, slice, drop；支持 goto waypoint 导航；动作空间支持 full 与 visible 两种展示模式。 | pgibench/envs/pgi_alfred/PGIAlfEnv.py, pgibench/envs/pgi_alfred/thor_connector.py |
| 场景与任务类型 | 场景来自 ALFRED FloorPlan 系列，按任务轨迹恢复 object poses/toggles/dirty-empty；AI2-THOR 评测子集包括 base、common_sense、complex_instruction、spatial、visual_appearance、long_horizon；并支持 EQA 时空记忆问答任务。 | README.md, pgibench/envs/pgi_alfred/PGIAlfEnv.py |
| 物理交互能力 | 支持拾取、放置、开关容器、设备开关、切片、丢弃、导航与传送定位；包含失败恢复机制与重试策略；支持可见对象、近邻对象筛选。 | pgibench/envs/pgi_alfred/thor_connector.py |
| API 接口 | 环境 API: reset, step, close；扩展 API: save_image, save_episode_log, save_thor_tracking, save_eqa_questions, explore_scene, get_agent_position；评测 API: evaluate_main/evaluate。 | pgibench/envs/pgi_alfred/PGIAlfEnv.py, pgibench/evaluator/pgi_alfred_evaluator.py |
| 数据采集 | 可采集图像序列、episode 结果、消息日志、Thor 时空追踪、EQA 问题与答案；图像默认落在 running/pgi_alfred/images/episode_1 或带实验名子目录。 | README.md, pgibench/envs/pgi_alfred/PGIAlfEnv.py, pgibench/evaluator/pgi_alfred_evaluator.py |

## 3. 支持的观测模态（详细）

| 模态 | 是否支持 | 说明 |
|---|---|---|
| 第一视角 RGB 图像 | 是 | env.reset 与 env.step 返回 obs，其中包含 head_rgb。 |
| 语言任务指令 | 是 | 每个 episode 提供自然语言任务指令 episode_language_instruction。 |
| 语言仅模式 | 是 | 配置 language_only=True 可关闭视觉输入，使用文本模式。 |
| 检测框增强视图 | 是 | detection_box 或 visual_prompt 开启时，保存图像可叠加实例框。 |
| 代理位姿上下文 | 是 | 评测时会读取代理位置并拼接到 planner 提示。 |
| 环境反馈文本 | 是 | step 返回 env_feedback，用于闭环决策。 |

## 4. 动作空间（详细）

| 类型 | 代表动作 |
|---|---|
| 导航/视角 | LookUp, LookDown, RotateLeft, RotateRight, MoveAhead, MoveBack, MoveLeft, MoveRight |
| 导航到路点 | goto waypoint_#xx |
| 抓取与放置 | pick up objectId, put down in/on receptacle, drop |
| 状态交互 | open, close, turn on, turn off |
| 物体变形 | slice |

补充说明:
- 动作是对象 ID 绑定的静态字典 + 基于可见性/近邻状态的动态展示列表。
- visible 模式仅暴露当前可操作候选，减少无效动作。

## 5. 场景与任务类型（详细）

| 维度 | 内容 |
|---|---|
| 场景来源 | ALFRED 任务轨迹，scene_name 如 FloorPlanX，按 traj_data 恢复对象与状态。 |
| 主任务类型 | 家居具身任务，采用 ALFRED 子目标奖励与任务成功判定。 |
| 评测子集 | base, common_sense, complex_instruction, spatial, visual_appearance, long_horizon。 |
| EQA 类型 | 位置、历史、相对位置、属性状态、计数、代理相关可见性与方位（多时间切片）。 |

## 6. 物理交互能力（详细）

| 能力 | 描述 |
|---|---|
| 运动与视角控制 | 支持平移、旋转、抬头低头、导航到路点或指定位置。 |
| 物体操作 | 支持拾取、放置、丢弃、开关容器、开关设备、切片。 |
| 交互鲁棒性 | 提供失败重试、错误恢复（例如动作失败后位置恢复）机制。 |
| 状态感知 | 可见对象与近邻对象可实时查询，用于动态动作过滤与追踪。 |

## 7. API 接口卡片

### 7.1 环境层 API

- reset: 初始化一个 episode 并返回观测
- step(action, reasoning): 执行动作并返回 obs, reward, done, info
- close: 关闭仿真环境
- save_image: 保存当前视角图像
- save_episode_log: 保存当前 episode 过程日志
- save_thor_tracking: 保存时空追踪 JSON
- save_eqa_questions: 保存 EQA 问题集合
- explore_scene: 自动遍历 goto 路点并采集图像

### 7.2 评测层 API

- main(Hydra): 按 env 动态分派 evaluator
- PGI_AlfredEvaluator.evaluate_main: 按 eval_set 执行完整评测
- PGI_AlfredEvaluator.evaluate: 执行 episode 循环与指标统计

## 8. 如何启动（stbench 环境）

### 8.1 进入环境

1. source /home/maqiang/miniconda3/etc/profile.d/conda.sh
2. conda activate stbench
3. cd /home/maqiang/benchclaw/simulators/PGIBench

### 8.2 启动 AI2-THOR 头less 显示服务（服务器推荐）

- python -m pgibench.envs.pgi_alfred.scripts.startx 1
- 或 python -m pgibench.envs.pgi_alfred.scripts.start_xvfb 1

### 8.3 直接体验环境交互

- python -m pgibench.envs.pgi_alfred.PGIAlfEnv

### 8.4 运行标准评测

- python -m pgibench.main env=pgi-alf model_name=gpt-4o-mini exp_name=baseline

## 9. 如何采集数据

### 9.1 交互图像采集

- 方式 A: 运行 PGIAlfEnv.py 示例交互，内部会调用 save_image。
- 方式 B: 在自定义循环中每步调用 env.save_image()。

默认图像目录:
- running/pgi_alfred/images/episode_1
- 若设置 exp_name，则通常位于 running/pgi_alfred/实验名/images/episode_N

### 9.2 轨迹与评测结果采集

- episode 指标: running/pgi_alfred/.../results/episode_N_final_res.json
- 对话消息: running/pgi_alfred/.../results/episode_N_messages.json
- 时空追踪: running/pgi_alfred/.../results/episode_N_thor.json
- EQA 问题: 可通过 save_eqa_questions 输出 episode_N_eqa.json

### 9.3 建议采集流程

1. 启动 stbench 与头less服务。
2. 运行 PGIAlfEnv 进行交互或运行主评测入口。
3. 每步保存图像，每回合保存结果与追踪。
4. 用 results 下 JSON 汇总任务成功率、无效动作率和 EQA 准确率。

## 10. 参考文档优先级

1. 仓库总览: README.md
2. 环境说明: pgibench/envs/pgi_alfred/README.md
3. 环境实现: pgibench/envs/pgi_alfred/PGIAlfEnv.py
4. 仿真交互实现: pgibench/envs/pgi_alfred/thor_connector.py
5. 评测配置: pgibench/configs/pgi-alf.yaml
