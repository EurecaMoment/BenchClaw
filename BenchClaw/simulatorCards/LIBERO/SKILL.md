# LIBERO Skill

## Core Path

- BenchClaw root: resolve `BENCHCLAW_ROOT` as the BenchClaw directory that contains `skills/` and `simulatorCards/`.
- Simulator root: `/home/maqiang/simulators/LIBERO`
- Skill directory: `BENCHCLAW_ROOT/simulatorCards/LIBERO`
- Conda environment: `libero`

## Goal

This skill exposes a model-facing LIBERO workflow without requiring the model user to enter LIBERO source directories.

If a model only reads this directory and follows this file, it should be able to:

1. Verify the LIBERO environment is installed.
2. Extract RGB images and GT from demonstration HDF5 files.
3. Launch live offscreen LIBERO environments and collect RGB observations plus as much GT as the environment exposes.

## Environment Activation

Run first:

```bash
source /home/maqiang/miniconda3/etc/profile.d/conda.sh
conda activate libero
export MUJOCO_GL=egl
export PYOPENGL_PLATFORM=egl
```

## Skill-Local Health Check

Run:

```bash
python BENCHCLAW_ROOT/simulatorCards/LIBERO/test_connect.py
```

Validated outputs include:

1. `libero package:`
2. `robosuite package:`
3. `benchmark task name:`
4. `OffScreenRenderEnv import OK`

## Available Data Sources

This skill supports two collection paths.

### 1. HDF5 Demonstration Extraction

Source dataset example:

```text
/home/maqiang/simulators/LIBERO/datasets/libero_10/KITCHEN_SCENE3_turn_on_the_stove_and_put_the_moka_pot_on_it_demo.hdf5
```

Validated HDF5 keys include:

1. `actions`
2. `dones`
3. `rewards`
4. `states`
5. `robot_states`
6. `obs/agentview_rgb`
7. `obs/eye_in_hand_rgb`
8. `obs/ee_pos`
9. `obs/ee_ori`
10. `obs/ee_states`
11. `obs/joint_states`
12. `obs/gripper_states`

### 2. Live OffScreenRenderEnv Collection

Validated live observation keys include:

1. `agentview_image`
2. `robot0_eye_in_hand_image`
3. `robot0_joint_pos`
4. `robot0_joint_vel`
5. `robot0_eef_pos`
6. `robot0_eef_quat`
7. `robot0_gripper_qpos`
8. `robot0_gripper_qvel`
9. `robot0_proprio-state`
10. `object-state`
11. Per-object position/quaternion fields like:
   - `alphabet_soup_1_pos`
   - `alphabet_soup_1_quat`
   - `basket_1_pos`
   - `basket_1_quat`
   - `tomato_sauce_1_pos`
   - `tomato_sauce_1_quat`

## HDF5 Batch Extraction

Run:

```bash
python BENCHCLAW_ROOT/simulatorCards/LIBERO/extract_hdf5_dataset.py \
  --output-dir BENCHCLAW_ROOT/simulatorCards/LIBERO/output_hdf5_demo \
  --max-demos 2 \
  --max-frames 16
```

This writes:

```text
output_hdf5_demo/
  collection_manifest.json
  demo_0/
    agentview_rgb/
    eye_in_hand_rgb/
    gt.json
  demo_1/
    agentview_rgb/
    eye_in_hand_rgb/
    gt.json
```

Each `gt.json` contains:

1. RGB frame paths
2. Actions
3. Rewards
4. Dones
5. Full `states`
6. Full `robot_states`
7. End-effector pose fields
8. Joint states
9. Gripper states

## Live Environment Batch Collection

Run:

```bash
python BENCHCLAW_ROOT/simulatorCards/LIBERO/collect_env_dataset.py \
  --suite libero_10 \
  --output-dir BENCHCLAW_ROOT/simulatorCards/LIBERO/output_env_dataset \
  --max-tasks 3 \
  --steps-per-task 8 \
  --image-size 128 \
  --action-source demo
```

This uses `OffScreenRenderEnv` directly and writes:

```text
output_env_dataset/
  collection_manifest.json
  task_00_.../
    images/
      agentview_image/
      robot0_eye_in_hand_image/
    gt.json
  task_01_.../
  task_02_.../
```

Default and recommended behavior uses demo action replay instead of zero actions. This is necessary because zero actions produce little to no manipulation trace and many frames can look nearly identical.

Each task `gt.json` contains:

1. `task_name`
2. `language`
3. `bddl_file`
4. `action_source`
5. `demo_path`
6. `reward`
7. `done`
8. Per-step `action`
9. Image paths for every RGB observation key
10. All non-image observations returned by the env
11. `info`

## Validated Live Probe

The following was successfully validated on this machine:

1. `benchmark.get_benchmark_dict()['libero_10']()`
2. `task_suite.get_task(0)`
3. `OffScreenRenderEnv(**env_args)`
4. `env.reset()`
5. `env.set_init_state(init_states[0])`
6. `env.step(action_from_demo)`

The validated observation keys included both camera images and rich proprio/object GT.

## Minimal Acceptance Check

The workflow is considered successful if all of the following hold:

1. `python test_connect.py` prints `OffScreenRenderEnv import OK`
2. `python extract_hdf5_dataset.py` writes `collection_manifest.json`
3. HDF5 extraction creates `agentview_rgb/`, `eye_in_hand_rgb/`, and `gt.json`
4. `python collect_env_dataset.py --action-source demo` writes `collection_manifest.json`
5. Live collection creates `agentview_image/`, `robot0_eye_in_hand_image/`, and `gt.json`
6. Live collection `gt.json` records `action_source: demo`
7. Live collection `gt.json` records per-step `action`

## Notes

1. The existing `LIBERO终身机器人学习.md` is legacy reference material.
2. The execution source of truth is this file:

```text
BENCHCLAW_ROOT/simulatorCards/LIBERO/SKILL.md
```
