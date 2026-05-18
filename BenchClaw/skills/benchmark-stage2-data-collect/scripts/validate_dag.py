#!/usr/bin/env python3
import json
import sys
from pathlib import Path
from collections import defaultdict, deque

def load(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def main():
    dag_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("dag.json")
    dag = load(dag_path)
    nodes = dag["nodes"]
    ids = set(nodes.keys())

    # parent existence
    for nid, node in nodes.items():
        for p in node.get("parents", []):
            if p not in ids:
                raise SystemExit(f"ERROR: node {nid} has unknown parent {p}")

    # cycle check and topo
    indeg = {nid: len(node.get("parents", [])) for nid, node in nodes.items()}
    children = defaultdict(list)
    for nid, node in nodes.items():
        for p in node.get("parents", []):
            children[p].append(nid)

    q = deque([nid for nid, d in indeg.items() if d == 0])
    topo = []
    while q:
        n = q.popleft()
        topo.append(n)
        for c in children[n]:
            indeg[c] -= 1
            if indeg[c] == 0:
                q.append(c)

    if len(topo) != len(nodes):
        raise SystemExit("ERROR: DAG has a cycle")

    # exact dependency checks from the user's diagram
    expected = {
        "13": [],
        "14": [],
        "15": ["13"],
        "16": ["13"],
        "17": ["13", "14"],
    }
    for nid, parents in expected.items():
        got = nodes[nid].get("parents", [])
        if sorted(got) != sorted(parents):
            raise SystemExit(f"ERROR: node {nid} parents should be {parents}, got {got}")

    terminals = sorted(dag.get("terminal_nodes", []))
    if terminals != ["15", "16", "17"]:
        raise SystemExit(f"ERROR: terminal_nodes should be ['15','16','17'], got {terminals}")

    # reject a serial chain 13->14->15->16->17
    serial_edges = [
        nodes["14"].get("parents", []) == ["13"],
        nodes["15"].get("parents", []) == ["14"],
        nodes["16"].get("parents", []) == ["15"],
        nodes["17"].get("parents", []) == ["16"],
    ]
    if all(serial_edges):
        raise SystemExit("ERROR: DAG was collapsed into a serial chain")

    # compute layers
    level = {}
    for n in topo:
        ps = nodes[n].get("parents", [])
        level[n] = 0 if not ps else max(level[p] + 1 for p in ps)
    layers = defaultdict(list)
    for n, l in level.items():
        layers[l].append(n)

    print("OK: Stage2 DAG is valid and non-serial.")
    for l in sorted(layers):
        print(f"L{l}: " + " | ".join(sorted(layers[l])))

if __name__ == "__main__":
    main()
