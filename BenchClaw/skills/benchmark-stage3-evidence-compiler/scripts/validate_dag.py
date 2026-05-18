#!/usr/bin/env python3
import json, sys
from pathlib import Path

path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('dag.json')
dag = json.loads(path.read_text(encoding='utf-8'))
nodes = dag['nodes']
terminals = set(dag.get('terminal_nodes', []))

for nid, node in nodes.items():
    for p in node.get('parents', []):
        if p not in nodes:
            raise SystemExit(f'ERROR: node {nid} has unknown parent {p}')
for t in terminals:
    if t not in nodes:
        raise SystemExit(f'ERROR: terminal node {t} missing')

# cycle check
visiting, visited = set(), set()
order = []
def dfs(n):
    if n in visiting:
        raise SystemExit(f'ERROR: cycle detected at {n}')
    if n in visited:
        return
    visiting.add(n)
    for p in nodes[n].get('parents', []):
        dfs(p)
    visiting.remove(n)
    visited.add(n)
    order.append(n)
for n in nodes:
    dfs(n)

# exact expected edges for this hand-drawn Stage3 interpretation
expected = {
    '15': [], '16': [], '17': [], '27': [],
    '21': ['15'], '22': ['16'], '23': ['17'],
    '24': ['21'], '25': ['22'], '26': ['23'],
    '18': ['24','27'], '19': ['25','27'], '20': ['26']
}
for nid, parents in expected.items():
    got = nodes.get(nid, {}).get('parents')
    if got is None:
        raise SystemExit(f'ERROR: expected node {nid} is missing')
    if sorted(got) != sorted(parents):
        raise SystemExit(f'ERROR: node {nid} parents should be {parents}, got {got}')
if terminals != {'18','19','20'}:
    raise SystemExit(f'ERROR: terminal_nodes should be [18,19,20], got {sorted(terminals)}')

# reject simple serial chain shape
edge_count = sum(len(n.get('parents', [])) for n in nodes.values())
roots = [n for n,v in nodes.items() if not v.get('parents')]
if len(roots) == 1 and edge_count == len(nodes)-1:
    raise SystemExit('ERROR: DAG degenerates into a serial chain')

# levels
remaining = set(nodes)
done = set()
levels = []
while remaining:
    ready = sorted([n for n in remaining if set(nodes[n].get('parents', [])) <= done], key=lambda x: (len(x), x))
    if not ready:
        raise SystemExit('ERROR: no ready nodes; malformed DAG')
    levels.append(ready)
    for n in ready:
        remaining.remove(n)
        done.add(n)

print('OK: Stage3 DAG is valid and non-serial.')
for i, lvl in enumerate(levels):
    print(f'L{i}: ' + ' | '.join(lvl))
