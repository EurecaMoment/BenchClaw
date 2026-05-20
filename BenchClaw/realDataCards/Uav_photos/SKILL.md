# Uav_photos Skill

## Core Path

- BenchClaw root: resolve `BENCHCLAW_ROOT` as the BenchClaw directory that contains `skills/`, `simulatorCards/`, and `realDataCards/`.
- Skill directory: `BENCHCLAW_ROOT/realDataCards/Uav_photos`
- Real image root: `/home/maqiang/realData/Uav_photos`

## Goal

This skill describes how to use `/home/maqiang/realData/Uav_photos` as a real-image source in BenchClaw.

If a model only reads this file and follows it exactly, it should be able to:

1. Locate the UAV image dataset.
2. Verify the dataset is present and readable.
3. Understand the basic scale and image properties of the dataset.
4. Use it as a Stage2 real-image acquisition source without fabricating ground truth.

## Dataset Facts

- Source path: `/home/maqiang/realData/Uav_photos`
- File count: `6201` images
- On-disk size: about `6.7G`
- Observed format: `JPEG`
- Observed color mode: `RGB`
- Observed resolutions are not uniform

Observed examples:

1. `img_0001.jpg`: `1360 x 765`
2. `img_3101.jpg`: `1916 x 1078`
3. `img_6201.jpg`: `4000 x 3000`

## Recommended Interpretation

Treat this dataset as a real aerial-image source for perception tasks such as:

1. object detection
2. instance segmentation
3. semantic scene understanding
4. depth estimation
5. camera-view reasoning
6. spatial relation reasoning

This dataset is an image source only. It does not provide verified GT in this card.

## Required Safety Rule

Do not claim any of the following as ground truth unless they are produced by a verified downstream annotation or measurement workflow:

1. object boxes
2. segmentation masks
3. depth maps
4. camera parameters
5. captions or scene labels generated directly by an LLM/VLM

## Minimal Verification

Run one or more of the following checks before using the dataset:

```bash
python - <<'PY'
from pathlib import Path
root = Path('/home/maqiang/realData/Uav_photos')
files = sorted([p for p in root.iterdir() if p.is_file()])
print('image_count=', len(files))
print('first_three=', [p.name for p in files[:3]])
PY
```

```bash
python - <<'PY'
from pathlib import Path
from PIL import Image
root = Path('/home/maqiang/realData/Uav_photos')
for name in ['img_0001.jpg', 'img_3101.jpg', 'img_6201.jpg']:
    path = root / name
    with Image.open(path) as im:
        print(name, im.format, im.size, im.mode)
PY
```

Successful verification means:

1. the directory exists
2. images can be enumerated
3. sample JPEG files open successfully

## Stage2 Acquisition Guidance

When this dataset is used by `skills/benchmark-stage2-data-collect/skills/15-real-image-acquisition/SKILL.md`, record it as a real-image source with `gt_status: not_available`.

Recommended manifest interpretation:

```json
{
  "source": "user_provided",
  "license": "unknown",
  "gt_status": "not_available",
  "expected_annotation_fields": [
    "object_detection",
    "instance_segmentation",
    "depth_estimation",
    "camera_geometry",
    "spatial_relations"
  ]
}
```

## Practical Notes

1. The filenames follow a simple sequential pattern: `img_0001.jpg` to `img_6201.jpg`.
2. Image resolutions vary, so downstream preprocessing should not assume a fixed shape.
3. If batching or sampling is needed, prefer deterministic ordering by filename.
4. If duplicate filtering is required, compute hashes on the original files instead of re-encoded copies.

## Source Of Truth

The execution source of truth for this dataset card is:

```text
BENCHCLAW_ROOT/realDataCards/Uav_photos/SKILL.md
```
