#!/usr/bin/env python3
from pathlib import Path
import json, argparse

ap = argparse.ArgumentParser()
ap.add_argument("--workspace", default="WORKSPACE_ROOT")
ap.add_argument("--dag", default="dag.json")
args = ap.parse_args()
dag = json.loads(Path(args.dag).read_text(encoding="utf-8"))


def workspace_path(path_value):
    text = str(path_value).replace("\\", "/")
    if text == "WORKSPACE_ROOT":
        return Path(args.workspace)
    if text.startswith("WORKSPACE_ROOT/"):
        return Path(args.workspace) / text[len("WORKSPACE_ROOT/") :]
    return Path(path_value)


for nid, node in dag["nodes"].items():
    workspace_path(node["output_dir"]).mkdir(parents=True, exist_ok=True)
print(f"OK: initialized Stage3 workspace dirs for {len(dag['nodes'])} nodes")
