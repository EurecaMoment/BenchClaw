---
name: depthanything3-local
description: "Use this skill when the user wants local Depth Anything 3 inference on images, image folders, videos, or COLMAP-style inputs; needs depth maps, camera pose estimation, GLB scene export, feature visualization export, backend task submission, backend status inspection, or a localhost Depth Anything 3 service on port 8008 backed by the local DA3NESTED-GIANT-LARGE-1.1 model. Always reuse an already running local backend if available; otherwise start it through depthanything3_client.py."
license: Proprietary. Local workspace tool.
---

# Depth Anything 3 local skill

This folder exposes the local Depth Anything 3 deployment as a reusable localhost service and CLI wrapper.

The deployment is backed by:

- model: `/home/maqiang/model/DA3NESTED-GIANT-LARGE-1.1`
- conda env: `depthanythingv3`
- project repo: `BENCHCLAW_ROOT/../thirty_part/annotationTools/Depth-Anything-3`
- backend URL: `http://127.0.0.1:8008`

The goal is to preserve as much of DA3's checked-in capability surface as the local code reliably exposes.

This local skill now treats depth outputs as absolute depth by default. Calls made through the backend wrapper request metric depth silently, instead of falling back to relative depth.

## When to use

Use this skill when the task needs any of the following:

- monocular or multi-view depth estimation from images
- pose-consistent geometry reconstruction from image folders
- video frame extraction plus DA3 inference
- COLMAP-style input processing
- exported `scene.glb`, preview JPG, and `depth_vis/` outputs
- feature-visualization export via `feat_vis`
- a persistent localhost DA3 backend that keeps the model loaded on GPU
- backend task submission, polling, status inspection, GPU memory inspection, or model reload

## First step: ensure the local backend exists

Always do this before inference or backend inspection:

```bash
python3 BENCHCLAW_ROOT/annotation-tool/depthanything3/depthanything3_client.py ensure-server
python3 BENCHCLAW_ROOT/annotation-tool/depthanything3/depthanything3_client.py status
```

Behavior:

- if a DA3 backend is already running on `127.0.0.1:8008`, reuse it
- otherwise start a new background backend in conda env `depthanythingv3`
- the service stays local and listens only on localhost by default
- the backend process log is written to `service.log` in this folder

## Capability split: backend API vs full CLI surface

There are two reliable calling modes.

### 1. Backend API mode

Use this when the task wants a persistent port-based service or explicit task queueing.

This mode reaches the DA3 FastAPI backend at `127.0.0.1:8008` and supports:

- submit inference tasks without reloading the model
- poll task state
- inspect backend status and GPU memory
- reload the loaded model
- clean up historical tasks
- access integrated gallery output if the gallery directory exists
- request absolute depth silently by default

### 2. CLI wrapper mode

Use this when the task wants DA3's higher-level input routing for:

- auto-detecting single image, image directory, video, or COLMAP input
- video frame extraction before backend submission
- normal DA3 CLI workflow with `da3 auto ... --use-backend`

This wrapper still reuses the port-based backend, but the preprocessing and input handling happen through the DA3 CLI.

## Important implementation note

The local DA3 backend on port `8008` now forwards these advanced inference controls through the HTTP request path into `model.inference(...)`:

- `use_ray_pose`
- `ref_view_strategy`

That means both the backend submission path and the `auto` wrapper can preserve these options end-to-end in the current local deployment.

## Capabilities

### 1. Health and backend status

Health:

```bash
python3 BENCHCLAW_ROOT/annotation-tool/depthanything3/depthanything3_client.py health
```

Detailed backend status:

```bash
python3 BENCHCLAW_ROOT/annotation-tool/depthanything3/depthanything3_client.py status
```

GPU memory:

```bash
python3 BENCHCLAW_ROOT/annotation-tool/depthanything3/depthanything3_client.py gpu-memory
```

Directly available status data typically includes:

- `model_loaded`
- `model_dir`
- `device`
- `load_time`
- `last_used`
- `uptime`
- `gpu_memory.total_gb`
- `gpu_memory.allocated_gb`
- `gpu_memory.reserved_gb`
- `gpu_memory.free_gb`
- `gpu_memory.utilization_percent`

### 2. Submit direct backend inference tasks

Use this when you already have the exact image paths and want explicit queued backend execution.

```bash
python3 BENCHCLAW_ROOT/annotation-tool/depthanything3/depthanything3_client.py submit \
  --image-path /abs/path/to/000.png \
  --image-path /abs/path/to/001.png \
  --export-dir /abs/path/to/output \
  --export-format glb
```

Optional arguments supported by this wrapper include:

- `--process-res`
- `--process-res-method`
- `--export-feat`
- `--use-ray-pose`
- `--ref-view-strategy`
- `--conf-thresh-percentile`
- `--num-max-points`
- `--feat-vis-fps`
- `--extrinsics-json`
- `--intrinsics-json`

Direct submission returns structured JSON including:

- `success`
- `message`
- `task_id`
- `export_dir`
- `export_format`

### 3. Poll or inspect backend tasks

List tasks:

```bash
python3 BENCHCLAW_ROOT/annotation-tool/depthanything3/depthanything3_client.py tasks
```

Inspect one task:

```bash
python3 BENCHCLAW_ROOT/annotation-tool/depthanything3/depthanything3_client.py task \
  --task-id <task-id>
```

Wait until completion:

```bash
python3 BENCHCLAW_ROOT/annotation-tool/depthanything3/depthanything3_client.py wait-task \
  --task-id <task-id>
```

Typical task fields available directly:

- `task_id`
- `status`
- `message`
- `progress`
- `created_at`
- `started_at`
- `completed_at`
- `export_dir`
- `num_images`
- `export_format`
- `process_res_method`

### 4. Run the full DA3 auto pipeline while reusing the backend

Use this when the task wants DA3's own input-type detection and preprocessing logic.

```bash
python3 BENCHCLAW_ROOT/annotation-tool/depthanything3/depthanything3_client.py auto \
  --input-path /abs/path/to/input \
  --export-dir /abs/path/to/output \
  --export-format glb \
  --auto-cleanup
```

Supported DA3 auto inputs:

- single image file
- directory of images
- video file
- COLMAP directory containing `images/` and `sparse/`

Useful options exposed by this wrapper include:

- `--fps` for video sampling
- `--process-res`
- `--process-res-method`
- `--export-feat`
- `--auto-cleanup`
- `--sparse-subdir`
- `--conf-thresh-percentile`
- `--num-max-points`
- `--feat-vis-fps`

This is the best default choice when the user simply says "run DA3 on this path".

### 5. Access common export types

The checked-in DA3 repo and this skill are most practical for these export styles:

- `glb`
- `mini_npz`
- `mini_npz-glb`
- `feat_vis`
- `glb-feat_vis`

Typical exported files include:

- `scene.glb`
- `scene.jpg`
- `depth_vis/*.jpg`
- feature-visualization videos or artifacts when `feat_vis` is requested

### 6. Reload model or clean task history

Reload model:

```bash
python3 BENCHCLAW_ROOT/annotation-tool/depthanything3/depthanything3_client.py reload
```

Cleanup task history:

```bash
python3 BENCHCLAW_ROOT/annotation-tool/depthanything3/depthanything3_client.py cleanup
```

Delete one completed task:

```bash
python3 BENCHCLAW_ROOT/annotation-tool/depthanything3/depthanything3_client.py delete-task \
  --task-id <task-id>
```

## Recommended usage patterns

### Pattern A: one-shot image folder inference

```bash
python3 BENCHCLAW_ROOT/annotation-tool/depthanything3/depthanything3_client.py auto \
  --input-path /abs/path/to/image_dir \
  --export-dir /abs/path/to/output \
  --export-format glb \
  --auto-cleanup
```

### Pattern B: asynchronous backend task workflow

```bash
python3 BENCHCLAW_ROOT/annotation-tool/depthanything3/depthanything3_client.py submit \
  --image-path /abs/path/to/000.png \
  --image-path /abs/path/to/001.png \
  --export-dir /abs/path/to/output \
  --export-format glb

python3 BENCHCLAW_ROOT/annotation-tool/depthanything3/depthanything3_client.py wait-task \
  --task-id <task-id>
```

### Pattern C: feature visualization export

```bash
python3 BENCHCLAW_ROOT/annotation-tool/depthanything3/depthanything3_client.py auto \
  --input-path /abs/path/to/video.mp4 \
  --export-dir /abs/path/to/output \
  --export-format glb-feat_vis \
  --export-feat 11,21,31 \
  --feat-vis-fps 15 \
  --auto-cleanup
```

## Runtime details

- host: `127.0.0.1`
- port: `8008`
- conda env: `depthanythingv3`
- model dir: `/home/maqiang/model/DA3NESTED-GIANT-LARGE-1.1`
- project repo: `BENCHCLAW_ROOT/../thirty_part/annotationTools/Depth-Anything-3`
- service log: `BENCHCLAW_ROOT/annotation-tool/depthanything3/service.log`
- launcher helper: `BENCHCLAW_ROOT/annotation-tool/depthanything3/start_backend.sh`

## Files in this skill

- `SKILL.md`: skill contract and usage instructions
- `depthanything3_client.py`: auto-start, health check, backend task submission, task polling, and DA3 auto wrapper
- `start_backend.sh`: thin helper to bring up the backend quickly

## Practical guidance

- Prefer `auto` for most user tasks because it preserves DA3's own input detection and preprocessing.
- Prefer `submit` when you already have concrete image paths and want direct task queue control.
- Prefer backend status and task endpoints when you want to keep the model hot on GPU across multiple jobs.
- This skill silently requests metric/absolute depth by default. If the underlying model/input cannot resolve metric depth, the run should fail instead of returning relative depth.
- If the task requires exact preservation of every advanced DA3 flag, verify that the checked-in backend actually forwards that option before relying on the port API.
- Do not assume a fixed output directory unless the current task explicitly needs one.
