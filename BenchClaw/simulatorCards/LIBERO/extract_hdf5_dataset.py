import argparse
import json
from pathlib import Path

import h5py
import numpy as np
from PIL import Image


def parse_args():
    parser = argparse.ArgumentParser(description="Extract LIBERO demo RGB and GT from HDF5.")
    parser.add_argument(
        "--dataset",
        default="/home/maqiang/simulators/LIBERO/datasets/libero_10/KITCHEN_SCENE3_turn_on_the_stove_and_put_the_moka_pot_on_it_demo.hdf5",
    )
    parser.add_argument("--output-dir", default="output_hdf5_demo")
    parser.add_argument("--max-demos", type=int, default=2)
    parser.add_argument("--max-frames", type=int, default=16)
    return parser.parse_args()


def save_rgb_sequence(frames, out_dir, prefix):
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    for idx, frame in enumerate(frames):
        path = out_dir / f"{prefix}_{idx:05d}.png"
        Image.fromarray(frame).save(path)
        paths.append(str(path))
    return paths


def main():
    args = parse_args()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    manifest = {
        "dataset": args.dataset,
        "demos": [],
    }

    with h5py.File(args.dataset, "r") as f:
        demo_names = sorted(list(f["data"].keys()))[: args.max_demos]
        for demo_name in demo_names:
            demo = f["data"][demo_name]
            demo_dir = output_dir / demo_name

            agent_rgb = np.array(demo["obs/agentview_rgb"])[: args.max_frames]
            hand_rgb = np.array(demo["obs/eye_in_hand_rgb"])[: args.max_frames]

            agent_paths = save_rgb_sequence(agent_rgb, demo_dir / "agentview_rgb", demo_name)
            hand_paths = save_rgb_sequence(hand_rgb, demo_dir / "eye_in_hand_rgb", demo_name)

            record = {
                "demo": demo_name,
                "frames": len(agent_paths),
                "actions": np.array(demo["actions"][: args.max_frames]).tolist(),
                "rewards": np.array(demo["rewards"][: args.max_frames]).tolist(),
                "dones": np.array(demo["dones"][: args.max_frames]).tolist(),
                "states": np.array(demo["states"][: args.max_frames]).tolist(),
                "robot_states": np.array(demo["robot_states"][: args.max_frames]).tolist(),
                "obs": {
                    "agentview_rgb_paths": agent_paths,
                    "eye_in_hand_rgb_paths": hand_paths,
                    "ee_pos": np.array(demo["obs/ee_pos"][: args.max_frames]).tolist(),
                    "ee_ori": np.array(demo["obs/ee_ori"][: args.max_frames]).tolist(),
                    "ee_states": np.array(demo["obs/ee_states"][: args.max_frames]).tolist(),
                    "joint_states": np.array(demo["obs/joint_states"][: args.max_frames]).tolist(),
                    "gripper_states": np.array(demo["obs/gripper_states"][: args.max_frames]).tolist(),
                },
            }

            with open(demo_dir / "gt.json", "w", encoding="utf-8") as fout:
                json.dump(record, fout, indent=2)
            manifest["demos"].append(record)

    with open(output_dir / "collection_manifest.json", "w", encoding="utf-8") as fout:
        json.dump(manifest, fout, indent=2)

    print("Extracted demos:", len(manifest["demos"]))
    for demo in manifest["demos"]:
        print(f"  {demo['demo']}: {demo['frames']} frames")
    print("Output:", output_dir)


if __name__ == "__main__":
    main()
