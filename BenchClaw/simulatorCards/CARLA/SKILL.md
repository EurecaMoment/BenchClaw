# CARLA Skill

## Core Path

- Simulator root: `/home/maqiang/simulators/CARLA`
- Main capture script: `/home/maqiang/benchclaw/simulator_cards/CARLA/quick_capture.py`
- Health check script: `/home/maqiang/benchclaw/simulator_cards/CARLA/test_connect.py`
- Stable server launcher: `/home/maqiang/simulators/CARLA/start_carla_offscreen.sh`

## Goal

This skill is for reliably launching CARLA 0.9.16, collecting multi-camera driving data, and writing both ego pose and camera pose into `collection_manifest.json`.

If a model only reads this file and follows it exactly, it should be able to:

1. Start CARLA in a clean offscreen session.
2. Verify the server is healthy.
3. Run the validated capture script.
4. Save front/side/rear/top camera images.
5. Save ego world pose, camera mount pose, and camera world pose.

## Environment

1. Activate conda:

```bash
source /home/maqiang/miniconda3/etc/profile.d/conda.sh
conda activate carla_py310
```

2. All commands below assume that environment.

## Start Server

Use a fresh tmux session and the validated launcher:

```bash
tmux new -s carla_skill
cd /home/maqiang/simulators/CARLA
./start_carla_offscreen.sh
```

If you want to keep your shell free, use:

```bash
tmux new-session -d -s carla_skill 'cd /home/maqiang/simulators/CARLA && ./start_carla_offscreen.sh'
```

### Why This Launcher Must Be Used

`start_carla_offscreen.sh` isolates Unreal/Epic cache directories. This avoids the observed `msgpack bad_cast` startup crash caused by stale user cache.

## Verify Server Health

Run these checks exactly:

```bash
cd /home/maqiang/benchclaw/simulator_cards/CARLA
ss -ltnp | grep -E ':2000|:2001'
python test_connect.py
```

Healthy output looks like:

1. `2000` and `2001` are listening.
2. `test_connect.py` prints `Connected map: Carla/Maps/Town10HD_Opt` or another Town map.

If `test_connect.py` fails with `failed to generate map`, the current CARLA world is bad. Restart the CARLA tmux session and test again.

## Capture Script Behavior

The validated script is:

```bash
/home/maqiang/benchclaw/simulator_cards/CARLA/quick_capture.py
```

It supports:

1. Single-map or multi-map collection.
2. Optional `--restart-per-map` clean-session collection.
3. Multi-camera synchronized capture.
4. Distance-based sampling instead of per-tick dumping.
5. Ego pose recording.
6. Camera mount pose recording.
7. Camera world pose recording.
8. Per-frame visible object metadata from instance segmentation.
9. Optional instance segmentation image export.

## Default Camera Rig

Default camera set:

```text
front,side_left,side_right,rear,top
```

Rig policy:

1. Mounts are computed from the vehicle bounding box.
2. Front/rear cameras are placed just outside the vehicle body.
3. Left/right cameras are placed just outside the side body.
4. Top camera is high above the vehicle with vertical downward view.

The current top camera is intentionally configured as high-altitude overhead:

1. `top_z = roof_z + 12.0`
2. `pitch = -90.0`

## Validated Smoke Test

This exact command was validated on a clean CARLA server:

```bash
cd /home/maqiang/benchclaw/simulator_cards/CARLA
python quick_capture.py \
  --port 2000 \
  --tm-port 8000 \
  --maps Town10HD_Opt \
  --frames-per-map 1 \
  --format jpg \
  --warmup-ticks 10 \
  --min-save-distance 6 \
  --metadata-cameras front,top \
  --save-instance-maps \
  --output-dir output_rgb_visiblemeta_final
```

This writes:

```text
/home/maqiang/benchclaw/simulator_cards/CARLA/output_rgb_visiblemeta_final/
```

## Validated Multi-Frame Example

```bash
cd /home/maqiang/benchclaw/simulator_cards/CARLA
python quick_capture.py \
  --port 2000 \
  --tm-port 8000 \
  --maps Town10HD_Opt \
  --frames-per-map 2 \
  --format jpg \
  --warmup-ticks 15 \
  --min-save-distance 8 \
  --output-dir output_rgb_multicam_rig_final
```

## Pose Recording Contract

The output manifest is:

```text
<output_dir>/collection_manifest.json
```

The script now records all of the following.

### Result-Level Fields

1. `map`
2. `saved_frames`
3. `tick_count`
4. `elapsed_seconds`
5. `distance_travelled_m`
6. `frames_per_camera`
7. `camera_names`
8. `camera_mounts`
9. `metadata_cameras`
10. `save_instance_maps`

### Frame-Level Fields

Each entry in `frame_records` contains:

1. `frame_index`
2. `sim_frame`
3. `ego_pose`
4. `speed_mps`
5. `distance_since_start`
6. `cameras`
7. `camera_poses`

### Ego Pose Structure

```json
"ego_pose": {
  "location": {"x": ..., "y": ..., "z": ...},
  "rotation": {"pitch": ..., "yaw": ..., "roll": ...}
}
```

### Camera Pose Structure

```json
"camera_poses": {
  "front": {
    "mount": {
      "location": {...},
      "rotation": {...}
    },
    "world": {
      "location": {...},
      "rotation": {...}
    }
  }
}
```

### Visible Object Metadata Structure

Each `camera_poses.<camera>.visible_objects` entry contains:

```json
{
  "visible_actor_count": 116,
  "visible_actors": [
    {
      "actor_id": 15,
      "semantic_labels": [6, 7, 8],
      "bbox_2d": {
        "xmin": 172,
        "ymin": 118,
        "xmax": 247,
        "ymax": 171,
        "pixel_count": 207
      },
      "type_id": "traffic.traffic_light",
      "actor_pose": {
        "location": {...},
        "rotation": {...}
      },
      "speed_mps": 0.0,
      "distance_to_camera_m": 54.292,
      "bbox_3d_projected": {
        "bbox_2d_from_3d": {
          "xmin": 268,
          "ymin": 153,
          "xmax": 293,
          "ymax": 161
        },
        "projected_edges": [
          [[293.085, 161.846], [293.015, 154.048]]
        ]
      }
    }
  ],
  "semantic_histogram": {
    "7": 743,
    "14": 1201
  }
}
```

## Object Metadata Controls

### `--metadata-cameras`

Controls which cameras compute visible object metadata.

Examples:

```bash
--metadata-cameras all
--metadata-cameras front,top
```

Reason:

1. Metadata extraction is heavier than plain RGB saving.
2. Restricting it to `front,top` is often enough.
3. RGB images are still saved for all cameras unless `--cameras` is changed.

### `--min-visible-pixels`

Controls the minimum actor pixel count required before a visible object is kept.

Example:

```bash
--min-visible-pixels 12
```

Reason:

1. Removes tiny 1-2 pixel noise detections.
2. Produces a cleaner visible object list.

### `--save-instance-maps`

If enabled, raw instance segmentation images are saved only for cameras listed in `--metadata-cameras`.

Example:

```bash
--save-instance-maps
```

Output layout becomes:

```text
<output_dir>/
  Town10HD_Opt/
    front/
    front_instance/
    side_left/
    side_right/
    rear/
    top/
    top_instance/
```

Use this when you need to debug object visibility or inspect actor IDs directly.

### Verified Example

The following manifest was produced successfully:

```text
/home/maqiang/benchclaw/simulator_cards/CARLA/output_rgb_visiblemeta_final/collection_manifest.json
```

It contains:

1. `camera_mounts`
2. `frame_records[0].ego_pose`
3. `frame_records[0].camera_poses`
4. Per-camera `mount` and `world` pose

## Output Layout

The script saves one directory per map, and one subdirectory per camera:

```text
<output_dir>/
  collection_manifest.json
  Town10HD_Opt/
    front/
    side_left/
    side_right/
    rear/
    top/
```

Each camera directory contains synchronized frame files like:

```text
Town10HD_Opt_00000.jpg
Town10HD_Opt_00001.jpg
```

## Multi-Map Guidance

If you need stable multi-map collection, prefer:

```bash
python /home/maqiang/benchclaw/simulator_cards/CARLA/quick_capture.py --restart-per-map --maps Town01_Opt,Town02_Opt --frames-per-map 10 --format jpg
```

Reason:

1. Repeated `load_world()` in one long-lived CARLA process was observed to be unstable.
2. `--restart-per-map` gives each map a fresh CARLA runtime.

## Known Failure Modes

### 1. `msgpack bad_cast`

Cause: stale Unreal/Epic cache.

Fix: always use `./start_carla_offscreen.sh`.

### 2. `failed to generate map`

Cause: CARLA process is alive but current world is broken.

Fix:

1. Kill the CARLA tmux session.
2. Start a fresh one.
3. Run `/home/maqiang/benchclaw/simulator_cards/CARLA/test_connect.py` again.

### 3. `VK_ERROR_OUT_OF_DEVICE_MEMORY`

Cause: starting too many CARLA instances or insufficient available GPU memory.

Fix:

1. Reuse one healthy CARLA server when possible.
2. Avoid parallel CARLA startups.
3. Stop stale CARLA sessions before starting a fresh one.

### 4. Vehicle blocked in traffic

The script already handles this by:

1. Waiting for warmup.
2. Enforcing `min_speed_mps`.
3. Enforcing `min_save_distance`.
4. Respawning the vehicle up to `max_respawns` when blocked too long.

## Mandatory Runbook

If an agent only reads this file, the required execution sequence is:

1. Activate `carla_py310`.
2. Start CARLA with `/home/maqiang/simulators/CARLA/start_carla_offscreen.sh` in tmux.
3. Verify ports with `ss -ltnp | grep -E ':2000|:2001'`.
4. Verify map health with `/home/maqiang/benchclaw/simulator_cards/CARLA/test_connect.py`.
5. Run `/home/maqiang/benchclaw/simulator_cards/CARLA/quick_capture.py` with explicit `--port 2000 --tm-port 8000` unless a different healthy server is intentionally used.
6. Read `<output_dir>/collection_manifest.json`.
7. Confirm `camera_mounts`, `ego_pose`, and `camera_poses` are present.

## Minimal Acceptance Check

After capture, verify with any JSON reader that:

1. `results[0].camera_mounts` exists.
2. `results[0].frame_records[0].ego_pose` exists.
3. `results[0].frame_records[0].camera_poses.front.world` exists.
4. `results[0].frames_per_camera.front >= 1`.
5. All enabled camera names have at least one frame saved.
6. If metadata is enabled for `front`, `results[0].frame_records[0].camera_poses.front.visible_objects` exists.
7. If instance maps are enabled and `front` is in `metadata_cameras`, `<map>/front_instance/` exists and contains at least one frame.

## Notes

1. The archived `/home/maqiang/benchclaw/simulator_cards/CARLA/CARLA_LEGACY.md` is not the execution source of truth.
2. This file is the new self-contained execution skill.
3. The simulator root has already moved to `/home/maqiang/simulators/CARLA`.
