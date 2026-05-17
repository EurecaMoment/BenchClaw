---
name: yoloe-local
description: "Use this skill when the user wants to run the local YOLOE annotation tool with the provided yoloe-11l-seg checkpoint for open-vocabulary detection or segmentation, including text-prompt inference, visual-prompt inference, or prompt-free inference. Always reuse an already running local YOLOE service if available; otherwise start it locally through yoloe_client.py."
license: Proprietary. Local workspace tool.
---

# YOLOE local skill

This folder exposes the local YOLOE deployment as a reusable localhost service so the agent can call it without reloading the model every time.

The deployment is backed by:

- repo: `/home/maqiang/BenchClaw/thirty_part/annotationTools/yoloe`
- conda env: `yoloe`
- checkpoint: `/home/maqiang/model/yoloe_11_l/yoloe-11l-seg.pt`
- text encoder weights: `/home/maqiang/model/yoloe_11_l/mobileclip_blt.pt`
- service URL: `http://127.0.0.1:8766`

The goal is to cover the most practical checked-in YOLOE inference surfaces for local annotation and pseudo-label generation.

Verified locally in this workspace:

- text-prompt inference: verified
- visual-prompt inference: verified
- prompt-free inference: requires a dedicated `*-seg-pf.pt` checkpoint

## When to use

Use this skill when the task needs any of the following:

- text-prompt open-vocabulary detection or segmentation
- visual-prompt detection or segmentation from boxes or masks
- prompt-free open-vocabulary detection or segmentation
- structured YOLOE detections returned directly as JSON
- optional annotated preview image export from YOLOE results

## First step: ensure the local service exists

Always do this before inference requests:

```bash
python3 /home/maqiang/BenchClaw/BenchClaw/annotation-tool/yoloe/yoloe_client.py ensure-server
python3 /home/maqiang/BenchClaw/BenchClaw/annotation-tool/yoloe/yoloe_client.py health
```

Behavior:

- if a YOLOE service is already running on `127.0.0.1:8766`, reuse it
- otherwise start a new background service in conda env `yoloe`
- the service stays local and listens only on localhost
- the service log is written to `service.log` in this folder

## Important runtime note

The current `yoloe` environment can load the model and run inference, but CUDA is not currently available there on this machine because the environment's CUDA build expects a newer NVIDIA driver than the host currently has.

That means the service currently auto-falls back to CPU unless the environment or driver stack changes.

## Capabilities

### 1. Health check

```bash
python3 /home/maqiang/BenchClaw/BenchClaw/annotation-tool/yoloe/yoloe_client.py health
```

Returns direct service metadata such as:

- `ok`
- `repo`
- `default_checkpoint`
- `default_pf_checkpoint`
- `pf_checkpoint_ready`
- `mobileclip_path`
- `mobileclip_ready`
- `default_device`

### 2. Text-prompt inference

Use this for open-vocabulary segmentation/detection with explicit class names.

```bash
python3 /home/maqiang/BenchClaw/BenchClaw/annotation-tool/yoloe/yoloe_client.py text-infer \
  --image-path /abs/path/to/image.jpg \
  --names "person,bus"
```

Optional controls:

- `--imgsz`
- `--conf`
- `--iou`
- `--device`
- `--annotated-output-path`

Returns structured JSON including:

- `mode`
- `checkpoint_path`
- `service_device`
- `class_names`
- `result.path`
- `result.orig_shape`
- `result.names`
- `result.num_detections`
- `result.detections[*].class_id`
- `result.detections[*].class_name`
- `result.detections[*].confidence`
- `result.detections[*].box_xyxy`
- `result.detections[*].box_xywhn`
- `result.detections[*].segment_xy`
- `result.detections[*].segment_xyn`
- `annotated_output_path` when explicitly requested

### 3. Prompt-free inference

Use this when the task wants a built vocabulary without drawing or cross-image prompting.

Important requirement:

- prompt-free is not driven by the base `yoloe-11l-seg.pt` alone
- it requires a dedicated prompt-free checkpoint such as `yoloe-11l-seg-pf.pt`
- the service uses the base checkpoint to generate the vocabulary and the prompt-free checkpoint to run inference

If the dedicated prompt-free checkpoint is missing, the service returns a clear error instead of pretending the mode is available.

```bash
python3 /home/maqiang/BenchClaw/BenchClaw/annotation-tool/yoloe/yoloe_client.py prompt-free-infer \
  --image-path /abs/path/to/image.jpg \
  --names "person,bus,car" \
  --pf-checkpoint-path /abs/path/to/yoloe-11l-seg-pf.pt
```

Or provide a class list file:

```bash
python3 /home/maqiang/BenchClaw/BenchClaw/annotation-tool/yoloe/yoloe_client.py prompt-free-infer \
  --image-path /abs/path/to/image.jpg \
  --names-file /abs/path/to/names.txt
```

Additional controls:

- `--pf-head-conf`
- `--max-det`
- `--imgsz`
- `--conf`
- `--iou`
- `--annotated-output-path`

### 4. Visual-prompt inference

Use this when the task wants prompt-conditioned segmentation/detection from boxes or masks.

This mode has been validated locally with box prompts on the bundled `bus.jpg` sample through the localhost service.

This mode is more naturally expressed as a JSON request file because the prompt structure can be nested.

Command:

```bash
python3 /home/maqiang/BenchClaw/BenchClaw/annotation-tool/yoloe/yoloe_client.py visual-infer \
  --request-file /abs/path/to/request.json
```

There is also a direct CLI form for common box-prompt cases:

```bash
python3 /home/maqiang/BenchClaw/BenchClaw/annotation-tool/yoloe/yoloe_client.py visual-infer \
  --image-path /abs/path/to/image.jpg \
  --prompt-type bboxes \
  --bbox 22,230,805,735 \
  --class-names object0
```

Example box-prompt request on the same image:

```json
{
  "image_path": "/abs/path/to/image.jpg",
  "prompt_type": "bboxes",
  "bboxes": [[221.52, 405.8, 344.98, 857.54]],
  "cls": [0],
  "class_names": ["object0"],
  "imgsz": 640,
  "conf": 0.25,
  "iou": 0.7
}
```

Example cross-image request using source prompt image and target image:

```json
{
  "image_path": "/abs/path/to/source.jpg",
  "target_image_path": "/abs/path/to/target.jpg",
  "prompt_type": "bboxes",
  "bboxes": [[120, 120, 300, 400]],
  "cls": [0],
  "class_names": ["object0"],
  "imgsz": 640,
  "conf": 0.15,
  "iou": 0.7
}
```

Example mask-prompt request:

```json
{
  "image_path": "/abs/path/to/image.jpg",
  "prompt_type": "masks",
  "masks": [[[0, 0, 1], [1, 1, 0]]],
  "cls": [0],
  "class_names": ["object0"]
}
```

For masks, pass a binary array structure shaped like `N x H x W`.

### 5. Annotated output export

All inference modes can optionally save an annotated preview image by supplying `annotated_output_path`.

Use this only when the task explicitly needs a file artifact. Otherwise consume the structured JSON directly.

## Files in this skill

- `SKILL.md`: skill contract and usage instructions
- `yoloe_client.py`: health check, auto-start, and request wrappers
- `yoloe_service.py`: localhost JSON service that keeps the YOLOE model process alive
- `test.sh`: smoke test for verified text and visual inference paths, plus optional prompt-free when a pf checkpoint exists

## Runtime details

- host: `127.0.0.1`
- port: `8766`
- conda env: `yoloe`
- repo: `/home/maqiang/BenchClaw/thirty_part/annotationTools/yoloe`
- checkpoint: `/home/maqiang/model/yoloe_11_l/yoloe-11l-seg.pt`
- mobileclip path: `/home/maqiang/model/yoloe_11_l/mobileclip_blt.pt`
- service log: `/home/maqiang/BenchClaw/BenchClaw/annotation-tool/yoloe/service.log`

## Practical guidance

- Prefer `text-infer` for most open-vocabulary object discovery tasks.
- Prefer `visual-infer` when the task genuinely needs box-based or mask-based prompting.
- Use `prompt-free-infer` only when you have the dedicated prompt-free checkpoint available.
- Treat YOLOE outputs as candidate or pseudo annotations unless the task specifically defines them as final labels.
- Do not assume GPU is available in the current `yoloe` environment on this machine.
