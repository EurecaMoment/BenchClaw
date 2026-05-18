#!/usr/bin/env python3
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
dag = json.loads((root / "dag.json").read_text(encoding="utf-8"))

nodes = {n["id"]: n for n in dag["nodes"]}
assert set(nodes) == {"38", "39"}, f"Stage5 must contain exactly nodes 38 and 39, got {set(nodes)}"
assert dag.get("terminal_nodes") == ["39"], f"terminal_nodes must be ['39'], got {dag.get('terminal_nodes')}"
assert nodes["38"].get("parents") == [], "38 must not have internal parents"
assert nodes["38"].get("external_parents") == ["37"], "38 must depend on external Stage4 node 37"
assert nodes["39"].get("parents") == ["38"], "39 must depend only on 38"
assert nodes["39"].get("external_parents") == [], "39 must not depend directly on external node 37"
assert dag.get("levels") == [["38"], ["39"]], f"levels must be [['38'], ['39']], got {dag.get('levels')}"

# cycle check
visited = set()
stack = set()

def dfs(x):
    if x in stack:
        raise AssertionError(f"cycle detected at {x}")
    if x in visited:
        return
    stack.add(x)
    for p in nodes[x].get("parents", []):
        if p not in nodes:
            raise AssertionError(f"unknown parent {p} for node {x}")
        dfs(p)
    stack.remove(x)
    visited.add(x)

for node_id in nodes:
    dfs(node_id)

print("OK: Stage5 DAG is valid.")
print("L0: 38")
print("L1: 39")
