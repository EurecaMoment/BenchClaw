# Simulator I/O Contracts

## HABITAT
- **Input**: scene_name, frames_per_scene (min 50)
- **Output**: 
  - RGB images: <scene>/rgb/frame_<NNNN>.png (per time-step)
  - Depth images: <scene>/depth/frame_<NNNN>.png (per time-step)
  - GT JSON: <scene>/gt.json with agent_state, sensor_states, navmesh_loaded
- **Connection**: http://127.0.0.1:8401
- **Activation**: source /home/maqiang/simulators/habitat/scripts/env_habitat.sh

## CARLA
- **Input**: map_name (Town10HD_Opt), frames_per_map (min 50), cameras (front,side_left,side_right,rear,top)
- **Output**:
  - RGB per camera: <map>/<camera>/frame_<NNNN>.jpg (per time-step)
  - Manifest: collection_manifest.json with ego_pose, camera_poses, visible_actors
- **Connection**: 127.0.0.1:2000:2001
- **Activation**: conda activate carla_py310

## LIBERO
- **Input**: suite (libero_10), max_tasks (3), steps_per_task (50)
- **Output**:
  - RGB per camera: <task>/images/agentview_image/frame_<NNNN>.png
  - RGB per camera: <task>/images/robot0_eye_in_hand_image/frame_<NNNN>.png
  - GT JSON: <task>/gt.json with actions, states, observations
- **Connection**: http://127.0.0.1:8402
- **Activation**: conda activate libero, export MUJOCO_GL=egl
