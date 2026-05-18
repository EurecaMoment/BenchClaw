---
name: sam3-local
description: "Use this skill when the user wants to run the local SAM3 annotation tool on images or videos, generate candidate masks, do text-grounded image segmentation, add box prompts, or use the full SAM3 video predictor API. Always reuse an already running local SAM3 service if available; otherwise start it locally through sam3_client.py."
license: Proprietary. Local workspace tool.
---

# SAM3 local skill

This folder exposes the local SAM3 model as a reusable localhost service so the agent can call it without reloading the model every time.

The goal is to cover the public SAM3 capability surface as far as the checked-in code reliably exposes it.

## When to use

Use this skill when the task needs any of the following:

- text-grounded image segmentation
- box-prompted image segmentation
- candidate mask generation for pseudo annotation
- local SAM3 video tracking sessions
- direct access to the SAM3 predictor `handle_request` or `handle_stream_request` APIs

## First step: ensure the local service exists

Always do this before sending inference requests:

```bash
python3 BENCHCLAW_ROOT/annotation-tool/sam3/sam3_client.py ensure-server
python3 BENCHCLAW_ROOT/annotation-tool/sam3/sam3_client.py health
```

Behavior:

- if a SAM3 service is already running on `127.0.0.1:8765`, reuse it
- otherwise start a new background service in conda env `sam3`
- the service stays local and listens only on localhost

## Capabilities

### 1. Image convenience inference

The service can return structured results directly. Saving mask files is optional and should only be requested if the current task explicitly needs files on disk. The agent decides any output path at call time.

Command:

```bash
python3 BENCHCLAW_ROOT/annotation-tool/sam3/sam3_client.py image-infer \
  --image-path /abs/path/to/image.png \
  --text-prompt "car"
```

Optional geometric prompts can be added repeatedly:

```bash
python3 BENCHCLAW_ROOT/annotation-tool/sam3/sam3_client.py image-infer \
  --image-path /abs/path/to/image.png \
  --text-prompt "car" \
  --box-prompt '{"box": [0.5, 0.5, 0.2, 0.1], "label": true}'
```

Notes:

- box format is normalized `[cx, cy, w, h]`
- `label: true` means positive box prompt
- output includes boxes, scores, RLE masks, and optional saved mask PNG paths if `save_masks_dir` is provided

Image result fields that can be returned directly:

- `session_id`
- `image_path`
- `checkpoint_path`
- `service_device`
- `confidence_threshold`
- `has_backbone_out`
- `has_text_prompt`
- `has_geometric_prompt`
- `orig_img_w`
- `orig_img_h`
- `pred_boxes`: normalized `xywh`
- `boxes_xyxy`: absolute pixel coordinates
- `pred_scores`
- `pred_masks`: RLE-encoded masks
- `masks_logits` or `masks_logits_shape` when requested or available
- `saved_mask_paths` only when a save directory is explicitly supplied

### 2. Full image request API

Use `image-request` when you want to stay close to the native `Sam3Processor` and `Sam3Image` interfaces instead of the convenience wrapper.

This mode is also preferred when the agent wants to inspect or transform returned data in memory first, instead of asking the tool to write files.

Supported request types:

- `start_session`
- `set_image`
- `set_text_prompt`
- `add_geometric_prompt`
- `add_geometric_prompts`
- `set_confidence_threshold`
- `reset_all_prompts`
- `get_state`
- `close_session`
- `predict_inst`
- `predict_inst_batch`

Example: start an image session

```json
{
  "type": "start_session",
  "image_path": "/abs/path/to/image.png",
  "confidence_threshold": 0.2
}
```

Example: set text prompt on an existing session

```json
{
  "type": "set_text_prompt",
  "session_id": "<session-id>",
  "prompt": "car"
}
```

Example: add multiple box prompts

```json
{
  "type": "add_geometric_prompts",
  "session_id": "<session-id>",
  "prompts": [
    {"box": [0.5, 0.5, 0.2, 0.1], "label": true},
    {"box": [0.2, 0.4, 0.1, 0.1], "label": false}
  ]
}
```

Example: call native instance-interactive prediction on a session

```json
{
  "type": "predict_inst",
  "session_id": "<session-id>",
  "kwargs": {}
}
```

Example: call batch instance-interactive prediction without creating a persistent session

```json
{
  "type": "predict_inst_batch",
  "image_paths": [
    "/abs/path/to/a.png",
    "/abs/path/to/b.png"
  ],
  "confidence_threshold": 0.2,
  "kwargs": {}
}
```

Command:

```bash
python3 BENCHCLAW_ROOT/annotation-tool/sam3/sam3_client.py image-request \
  --request-file /abs/path/to/request.json
```

### 3. Full video predictor API

Create a request JSON file and pass it through the local client.

Example request file for starting a session:

```json
{
  "type": "start_session",
  "resource_path": "/abs/path/to/video_frames_dir"
}
```

Call it with:

```bash
python3 BENCHCLAW_ROOT/annotation-tool/sam3/sam3_client.py video-request \
  --request-file /abs/path/to/request.json \
  --version sam3.1
```

For streaming requests such as propagation:

```bash
python3 BENCHCLAW_ROOT/annotation-tool/sam3/sam3_client.py video-request \
  --request-file /abs/path/to/request.json \
  --version sam3.1 \
  --stream
```

The wrapper forwards the request to the local predictor and returns serialized JSON. Cached predictors are reused in-process.

Video responses are returned as structured JSON. The skill does not require a fixed output directory. If the calling task needs files, the agent should decide the path at call time and write derived artifacts itself.

Supported native predictor request types:

- `start_session`
- `add_prompt`
- `remove_object`
- `reset_session`
- `cancel_propagation`
- `close_session`
- streaming `propagate_in_video`

Common `add_prompt` fields supported by the wrapper are inherited from the native predictor layer:

- `text`
- `points`
- `point_labels`
- `clear_old_points`
- `bounding_boxes`
- `bounding_box_labels`
- `clear_old_boxes`
- `output_prob_thresh`
- `obj_id`
- `rel_coordinates`

This means the agent can reach essentially the whole public request surface exposed by `build_sam3_predictor(...).handle_request(...)` and `handle_stream_request(...)`.

Typical video response data that can be returned directly includes:

- `session_id` for session creation
- `frame_index`
- `outputs`
- serialized `out_obj_ids`
- serialized `out_binary_masks`
- serialized `out_boxes_xywh`
- serialized probabilities or additional model outputs when present in the native predictor response

## Files in this skill

- `SKILL.md`: skill contract and usage instructions
- `sam3_client.py`: health check, auto-start, and request wrappers
- `sam3_service.py`: localhost JSON service that keeps the model process alive
- `test.sh`: smoke test and quick entrypoint

## Runtime details

- host: `127.0.0.1`
- port: `8765`
- conda env: `sam3`
- SAM3 repo: `BENCHCLAW_ROOT/../thirty_part/annotationTools/sam3`
- default checkpoint: `/home/maqiang/model/sam3/sam3.pt`
- service log: `BENCHCLAW_ROOT/annotation-tool/sam3/service.log`

## Important output policy

If this skill is used for annotation or benchmark generation, treat SAM3 outputs as candidate or pseudo annotations, not ground-truth labels.

## Practical guidance

- Prefer `image-infer` for one-shot grounding when direct JSON results are enough.
- Prefer `image-request` for iterative image workflows where prompts are added or reset over time.
- Prefer `video-request` whenever the user wants anything resembling tracking, propagation, prompt-conditioned video segmentation, or direct access to SAM3's session-based predictor API.
- Do not assume any fixed save path. If files are needed, choose the path during the current task based on user intent and workspace context.
