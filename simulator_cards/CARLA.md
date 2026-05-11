# CARLA 能力卡片

## !!! 仿真器目录（最重要）

- /home/maqiang/benchclaw/simulators/CARLA

## 1. 基本信息

| 项目 | 内容 |
|---|---|
| 仿真器 | CARLA 0.9.16（预编译包） |
| 服务器环境 | Ubuntu 20.04 + NVIDIA A100 |
| Python 环境 | conda: carla_py310（Python 3.10） |
| Python API | PythonAPI/carla/dist/carla-0.9.16-cp310-cp310-manylinux_2_31_x86_64.whl |
| 验证工作目录 | /home/maqiang/benchclaw/simulators/CARLA/carla_test |

## 2. 能力总览

| 维度 | 能力描述 |
|---|---|
| 支持观测模态 | RGB 相机（已验证）；可通过 CARLA blueprint 扩展到深度/语义分割/LiDAR/IMU/GNSS 等传感器。 |
| 动作空间 | 车辆控制（转向/油门/刹车）+ 自动驾驶（Traffic Manager）；支持同步步进 world.tick()。 |
| 场景与任务类型 | 多 Town 地图（如 Town10HD_Opt）；可做导航、自动驾驶回放、数据采集、感知数据生成。 |
| 物理交互能力 | 车辆动力学、交通参与体、碰撞与传感器物理一致性仿真；支持 actor 生成/销毁和附着传感器。 |
| API 接口 | Python API：Client/World/Map/Blueprint/Actor/Sensor/TrafficManager；支持同步模式和超时控制。 |
| 数据采集 | 已验证自动采图脚本，按帧保存 PNG 到 output_rgb；可扩展多传感器并行采集。 |

## 3. 支持观测模态

| 模态 | 状态 | 说明 |
|---|---|---|
| RGB 图像 | 已验证 | quick_capture.py 使用 sensor.camera.rgb，分辨率 1280x720，按帧落盘 PNG。 |
| 深度图 | 可支持 | 可换用 sensor.camera.depth。 |
| 语义分割 | 可支持 | 可换用 sensor.camera.semantic_segmentation。 |
| LiDAR | 可支持 | 可使用 sensor.lidar.ray_cast。 |
| IMU/GNSS | 可支持 | 可附着车辆进行状态估计数据采集。 |

## 4. 动作空间

| 类别 | 说明 |
|---|---|
| Autopilot | vehicle.set_autopilot(True, tm_port) 交给 Traffic Manager 控制 |
| 手动控制 | carla.VehicleControl(throttle, steer, brake, hand_brake, reverse) |
| 仿真步进 | 同步模式下由 world.tick() 推进，固定时间步可控 |

## 5. 场景与任务类型

| 类型 | 示例 |
|---|---|
| 地图场景 | Town10HD_Opt 等 CARLA 地图 |
| 数据生成任务 | 自动驾驶巡航采图、多传感器标注数据采集 |
| 连通性验证任务 | client.get_world() / get_map() 验证服务可用性 |
| 自动化脚本任务 | actor 生成、传感器挂载、定步长采样、清理回收 |

## 6. 物理交互能力

- 车辆 actor 在交通系统中运动，支持 Traffic Manager 协调。
- 传感器可附着在车辆局部位姿（示例 x=1.5, z=2.4）。
- 世界参数支持同步模式与 fixed_delta_seconds，保证可重复采样节奏。
- 支持 actor 生命周期管理（spawn -> listen -> stop/destroy）。

## 7. API 接口卡片（Python）

| 接口 | 作用 |
|---|---|
| carla.Client(host, port) | 建立到 CARLA server 的连接 |
| client.set_timeout(sec) | 设置 RPC 超时 |
| client.get_world() | 获取当前世界对象 |
| world.get_map().name | 获取当前地图名称 |
| world.get_settings()/apply_settings() | 切换同步模式与步长 |
| client.get_trafficmanager() | 获取交通管理器 |
| world.get_blueprint_library() | 获取车辆/传感器 blueprint |
| world.spawn_actor(bp, transform, attach_to=...) | 生成车辆或传感器 |
| sensor.listen(callback) | 订阅传感器流 |
| world.tick() | 同步推进一帧 |
| image.save_to_disk(path) | 保存图像帧 |

## 8. 如何启动（服务器版）

### 8.1 激活环境

1. source /home/maqiang/miniconda3/etc/profile.d/conda.sh
2. conda activate carla_py310

### 8.2 启动 CARLA server（推荐 tmux）

1. cd /home/maqiang/benchclaw/simulators/CARLA
2. tmux new -s carla
3. ./CarlaUE4.sh -RenderOffScreen -quality-level=Low -nosound

参数说明:
- -RenderOffScreen: 无显示器服务器场景
- -quality-level=Low: 降低占用
- -nosound: 关闭声音

### 8.3 运行最小连通测试

```bash
conda activate carla_py310
python - <<'PY'
import carla
client = carla.Client('127.0.0.1', 2000)
client.set_timeout(60.0)
world = client.get_world()
print('Connected map:', world.get_map().name)
PY
```

## 9. 如何采集数据

### 9.1 最小自动采图脚本位置

- /home/maqiang/benchclaw/simulators/CARLA/carla_test/quick_capture.py

### 9.2 运行采图

```bash
conda activate carla_py310
cd /home/maqiang/benchclaw/simulators/CARLA/carla_test
python quick_capture.py
```

### 9.3 输出目录

- /home/maqiang/benchclaw/simulators/CARLA/carla_test/output_rgb

检查命令:

```bash
cd /home/maqiang/benchclaw/simulators/CARLA/carla_test
ls output_rgb | head
ls output_rgb | tail
ls -lh output_rgb | head
```

## 10. 运行状态检查

```bash
tmux ls
ps -ef | grep CarlaUE4 | grep -v grep
ss -ltnp | grep -E ':2000|:2001'
```

## 11. 常见问题与处理

### 11.1 server 启动崩溃（msgpack bad_cast）

可清理用户缓存后重启:

```bash
rm -rf ~/.config/Epic/CarlaUE4
rm -rf ~/.config/Epic/UnrealEngine/4.26
rm -rf ~/.cache/Epic
rm -rf ~/.cache/UnrealEngine
cd /home/maqiang/benchclaw/simulators/CARLA
./CarlaUE4.sh -RenderOffScreen -quality-level=Low -nosound
```

### 11.2 client.get_world() 超时

优先检查端口监听、进程与 tmux 会话是否仍在。

## 12. 迁移说明

为统一仿真器管理，已完成目录搬运：

- 旧路径 /home/maqiang/apps/carla -> 迁移到 /home/maqiang/benchclaw/simulators/CARLA
- 旧测试路径 /home/maqiang/.openclaw/workspace-test2/carla_test -> 迁移到 /home/maqiang/benchclaw/simulators/CARLA/carla_test

并保留了旧路径软链接以兼容既有脚本。