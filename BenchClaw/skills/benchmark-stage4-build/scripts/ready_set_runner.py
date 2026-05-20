#!/usr/bin/env python3
import argparse, json
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("--workspace", default="WORKSPACE_ROOT")
ap.add_argument("--dag", default="dag.json")
args = ap.parse_args()
with open(args.dag, "r", encoding="utf-8") as f:
    dag = json.load(f)
nodes = dag["nodes"]


def workspace_path(path_value):
    text = str(path_value).replace("\\", "/")
    if text == "WORKSPACE_ROOT":
        return Path(args.workspace)
    if text.startswith("WORKSPACE_ROOT/"):
        return Path(args.workspace) / text[len("WORKSPACE_ROOT/") :]
    return Path(path_value)


def done(nid):
    done_path = workspace_path(nodes[nid]["output_dir"]) / "DONE.json"
    if not done_path.exists():
        return False
    try:
        payload = json.loads(done_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return False
    if str(payload.get("node_id")) != str(nid):
        return False
    expected_status = "waived" if nid in {"33", "34"} else "done"
    return payload.get("status") == expected_status


ready = []
for nid, node in nodes.items():
    if done(nid):
        continue
    if all(done(p) for p in node.get("parents", [])):
        ready.append(nid)
print("READY: " + (" ".join(sorted(ready)) if ready else "<none>"))
