# HABITAT Skill

## Core Path

- BenchClaw root: resolve `BENCHCLAW_ROOT` as the BenchClaw directory that contains `skills/` and `simulatorCards/`.
- Simulator root: `/home/maqiang/simulators/habitat`
- Skill directory: `BENCHCLAW_ROOT/simulatorCards/HABITAT`
- Environment activator: `/home/maqiang/simulators/habitat/scripts/env_habitat.sh`

## Goal

This skill is the minimal validated workflow for using Habitat-Sim / Habitat-Lab on this machine without exposing the user to Habitat source code entrypoints.

If a model only reads this file and follows it exactly, it should be able to:

1. Activate the correct conda environment.
2. Verify installed Habitat versions.
3. Render one RGB frame with Habitat-Sim.
4. Run the official Habitat-Lab `examples/example.py` workflow.
5. Collect large batches of scene images and GT using only scripts inside this skill directory.

## Verified Environment

Validated state on this machine:

1. Conda environment: `habitat39`
2. `habitat-sim`: `0.3.3`
3. `habitat-lab`: `0.3.3`
4. Habitat-Lab source is expected at:

```text
/home/maqiang/simulators/habitat/src/habitat-lab
```

Do not switch Habitat-Lab away from `v0.3.3` unless you are intentionally revalidating the full stack.

## Environment Activation

Run this first:

```bash
source /home/maqiang/simulators/habitat/scripts/env_habitat.sh
```

This script already does the required setup:

1. Activates `habitat39`
2. Sets `HABITAT_ROOT`
3. Sets `HABITAT_DATA`
4. Unsets `DISPLAY`
5. Sets `CUDA_VISIBLE_DEVICES` if not already set
6. Extends `PYTHONPATH` for Habitat-Lab

## Skill-Local Health Check

Run from the skill directory:

```bash
source /home/maqiang/simulators/habitat/scripts/env_habitat.sh
python BENCHCLAW_ROOT/simulatorCards/HABITAT/test_connect.py
```

Expected output contains:

1. `habitat-sim: 0.3.3`
2. `habitat-lab: 0.3.3`

## Skill-Local RGB Smoke Test

Run:

```bash
source /home/maqiang/simulators/habitat/scripts/env_habitat.sh
python BENCHCLAW_ROOT/simulatorCards/HABITAT/render_rgb.py
```

Expected behavior:

1. Habitat-Sim starts successfully.
2. One RGB frame is saved to:

```text
BENCHCLAW_ROOT/simulatorCards/HABITAT/output/first_rgb.png
```

Observed warning that can be ignored for this test:

```text
SSD Load Failure! ... skokloster-castle.scn exists but failed to load
```

This warning did not block RGB rendering.

## Skill-Local Official Example Run

Run:

```bash
source /home/maqiang/simulators/habitat/scripts/env_habitat.sh
python BENCHCLAW_ROOT/simulatorCards/HABITAT/run_example.py
```

This executes the official:

```text
/home/maqiang/simulators/habitat/src/habitat-lab/examples/example.py
```

but keeps the user-facing entrypoint inside `BENCHCLAW_ROOT/simulatorCards/HABITAT`.

Expected success markers:

```text
Environment creation successful
Agent acting inside environment.
Episode finished after ... steps.
```

On this machine, it completed successfully and finished after `277` steps during validation.

## Skill-Local Batch Dataset Collection

Use this script:

```text
BENCHCLAW_ROOT/simulatorCards/HABITAT/collect_dataset.py
```

It collects multi-scene RGB images and depth maps and writes GT JSON for every scene.

### What It Saves

For each scene it writes:

1. `rgb/*.png`
2. `depth/*.png`
3. `gt.json`

At the output root it also writes:

1. `collection_manifest.json`

### GT Contents

Each frame record contains:

1. `scene`
2. `scene_path`
3. `rgb_path`
4. `depth_path`
5. `agent_state.position`
6. `agent_state.rotation`
7. `sensor_states.color_sensor`
8. `sensor_states.depth_sensor`
9. `navmesh_loaded`

### Validated Batch Command

```bash
source /home/maqiang/simulators/habitat/scripts/env_habitat.sh
python BENCHCLAW_ROOT/simulatorCards/HABITAT/collect_dataset.py \
  --output-dir BENCHCLAW_ROOT/simulatorCards/HABITAT/output_dataset_demo \
  --frames-per-scene 4
```

Validated output scenes:

1. `apartment_1`
2. `skokloster-castle`
3. `van-gogh-room`

Validated result:

1. 3 scenes collected
2. 4 frames per scene
3. RGB + depth + GT saved successfully

### Output Layout

```text
output_dataset_demo/
  collection_manifest.json
  apartment_1/
    rgb/
    depth/
    gt.json
  skokloster-castle/
    rgb/
    depth/
    gt.json
  van-gogh-room/
    rgb/
    depth/
    gt.json
```

### Scene Selection

By default the collector uses these validated test scenes:

1. `/home/maqiang/simulators/habitat/data/scene_datasets/habitat-test-scenes/apartment_1.glb`
2. `/home/maqiang/simulators/habitat/data/scene_datasets/habitat-test-scenes/skokloster-castle.glb`
3. `/home/maqiang/simulators/habitat/data/scene_datasets/habitat-test-scenes/van-gogh-room.glb`

You can override them with:

```bash
--scenes path_a.glb,path_b.glb,path_c.glb
```

## Common Warnings That Did Not Block Execution

These were observed during validation and can be tolerated if the run still reaches the success markers:

1. `Gym has been unmaintained since 2022`
2. `duplicate static plugin ...`
3. `navmesh_instances ... not found`
4. `MeshTools::compile(): ignoring Trade::MeshAttribute::TextureCoordinates ...`

If the run still prints `Environment creation successful` and finishes an episode, the workflow is considered good.

## Known Failure Mode

### `AttributeError: 'RearrangeSim' object has no attribute 'sensors'`

Cause:

Habitat-Lab version drifted away from the validated `v0.3.3` revision.

Fix:

```bash
source /home/maqiang/simulators/habitat/scripts/env_habitat.sh
cd /home/maqiang/simulators/habitat/src/habitat-lab
git fetch --tags
git checkout v0.3.3
python -m pip install -e habitat-lab
```

Then rerun from the skill directory:

```bash
cd BENCHCLAW_ROOT/simulatorCards/HABITAT
python test_connect.py
python render_rgb.py
python run_example.py
```

## Minimal Acceptance Check

The workflow is considered successful if all of the following hold:

1. `python test_connect.py` prints `habitat-sim: 0.3.3`
2. `python test_connect.py` prints `habitat-lab: 0.3.3`
3. `python render_rgb.py` writes `output/first_rgb.png`
4. `python run_example.py` prints `Environment creation successful`
5. `python run_example.py` prints `Episode finished after` with a finite number of steps
6. `python collect_dataset.py` writes `collection_manifest.json`
7. Each collected scene directory contains `rgb/`, `depth/`, and `gt.json`

Note: `env_habitat.sh` changes the current directory to Habitat-Lab. Always invoke the skill-local scripts by absolute path after sourcing it.

## Notes

1. The old top-level file `BENCHCLAW_ROOT/simulatorCards/HABITAT.md` is legacy reference material.
2. The execution source of truth is this file:

```text
BENCHCLAW_ROOT/simulatorCards/HABITAT/SKILL.md
```
