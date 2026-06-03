# AI2-THOR qa1 示例族统计

用户提供的 qa1 样例已被转成统一 eval item 示例，用于说明 Stage4 如何将问题、答案和证据绑定。

| question_id | 数量 | 对应能力倾向 | 说明 |
|---|---:|---|---|
| obj_types_in_container_initial | 8 | C13 区域/容器归属, C18/C20 时序 | 容器内物体类型或数量，适合展示 evidence_ref 与 timestep 绑定。 |
| obj_types_in_container_current | 8 | C13 区域/容器归属, C18/C20 时序 | 容器内物体类型或数量，适合展示 evidence_ref 与 timestep 绑定。 |
| obj_types_in_container_n_steps_ago | 8 | C13 区域/容器归属, C18/C20 时序 | 容器内物体类型或数量，适合展示 evidence_ref 与 timestep 绑定。 |
| obj_types_in_container_random_t | 8 | C13 区域/容器归属, C18/C20 时序 | 容器内物体类型或数量，适合展示 evidence_ref 与 timestep 绑定。 |
| obj_count_in_scene_current | 8 | C2 计数, C20 时间变化 | 计数题，适合 Exact Match 或数值误差。 |
| obj_existence_seen | 8 | C1 物体识别, C11 可见性, C18 时序 | 可见性/历史出现类问题，适合多帧证据。 |
| agent_vis_n_steps_ago | 8 | C1 物体识别, C11 可见性, C18 时序 | 可见性/历史出现类问题，适合多帧证据。 |
| obj_count_in_container_initial | 8 | C13 区域/容器归属, C18/C20 时序 | 容器内物体类型或数量，适合展示 evidence_ref 与 timestep 绑定。 |
| obj_count_in_container_current | 8 | C13 区域/容器归属, C18/C20 时序 | 容器内物体类型或数量，适合展示 evidence_ref 与 timestep 绑定。 |
| obj_count_in_container_n_steps_ago | 8 | C13 区域/容器归属, C18/C20 时序 | 容器内物体类型或数量，适合展示 evidence_ref 与 timestep 绑定。 |
| obj_count_in_container_random_t | 8 | C13 区域/容器归属, C18/C20 时序 | 容器内物体类型或数量，适合展示 evidence_ref 与 timestep 绑定。 |
| obj_property_current | 8 | C3 属性识别, C4 状态理解 | 属性/状态题，需要字段明确。 |
| agent_vis_random_t | 7 | C1 物体识别, C11 可见性, C18 时序 | 可见性/历史出现类问题，适合多帧证据。 |
| agent_vis_initial | 4 | C1 物体识别, C11 可见性, C18 时序 | 可见性/历史出现类问题，适合多帧证据。 |
| obj_loc_history | 4 | C18/C20 轨迹与历史理解 | 历史位置或状态追踪。 |

## episode 统计

| episode | questions | images | tracker_sha256 |
|---|---:|---:|---|
| episode_1 | 28 | 9 | `0d8913bdb04a...` |
| episode_2 | 28 | 7 | `62f97df60168...` |
| episode_3 | 28 | 9 | `b7ccc353c278...` |
| episode_4 | 27 | 4 | `3b106372195d...` |
