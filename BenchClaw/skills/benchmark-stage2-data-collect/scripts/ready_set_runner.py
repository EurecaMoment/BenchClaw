#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def done_path(workspace, node):
    rel = node["output_dir"]
    if rel.startswith("WORKSPACE_ROOT/"):
        rel = rel[len("WORKSPACE_ROOT/"):]
    return Path(workspace) / rel / "DONE.json"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workspace", default="WORKSPACE_ROOT")
    ap.add_argument("--dag", default="dag.json")
    args = ap.parse_args()

    dag = load_json(args.dag)
    nodes = dag["nodes"]

    done = []
    not_done = []
    for nid, node in nodes.items():
        if done_path(args.workspace, node).exists():
            done.append(nid)
        else:
            not_done.append(nid)

    ready = []
    done_set = set(done)
    for nid in not_done:
        parents = nodes[nid].get("parents", [])
        if all(p in done_set for p in parents):
            ready.append(nid)

    print("DONE: " + (" ".join(sorted(done)) if done else "(none)"))
    print("READY: " + (" ".join(sorted(ready)) if ready else "(none)"))
    print("BLOCKED: " + (" ".join(sorted(set(not_done) - set(ready))) if (set(not_done) - set(ready)) else "(none)"))

    if set(dag.get("terminal_nodes", [])) <= done_set:
        print("STAGE2_STATUS: complete")
    else:
        print("STAGE2_STATUS: incomplete")

if __name__ == "__main__":
    main()
