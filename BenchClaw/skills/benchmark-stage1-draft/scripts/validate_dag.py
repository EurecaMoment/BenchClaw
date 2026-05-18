#!/usr/bin/env python3
import json, sys
from pathlib import Path

path = Path(sys.argv[1] if len(sys.argv) > 1 else 'dag.json')
dag = json.loads(path.read_text(encoding='utf-8'))
nodes = {n['id']: n for n in dag['nodes']}

# parent existence
for nid, n in nodes.items():
    for p in n.get('parents', []):
        if p not in nodes:
            raise SystemExit(f'ERROR: node {nid} has missing parent {p}')

# cycle check
visiting=set(); visited=set()
def dfs(x, stack):
    if x in visiting:
        raise SystemExit('ERROR: cycle detected: ' + ' -> '.join(stack+[x]))
    if x in visited:
        return
    visiting.add(x)
    for y in nodes[x].get('parents', []):
        dfs(y, stack+[x])
    visiting.remove(x); visited.add(x)
for nid in nodes:
    dfs(nid, [])

# anti-serial check: fail if every non-root node depends only on immediately previous numbered node
serial_edges = 0
non_root = 0
for nid, n in nodes.items():
    ps = n.get('parents', [])
    if ps:
        non_root += 1
        try:
            prev = f'{int(nid)-1:02d}'
        except ValueError:
            prev = None
        if ps == [prev]:
            serial_edges += 1
if non_root and serial_edges == non_root:
    raise SystemExit('ERROR: DAG degenerates to a pure serial chain')

layers = dag.get('parallel_layers', [])
multi_layers = [ly for ly in layers if len(ly) > 1]
if len(multi_layers) < 3:
    raise SystemExit('ERROR: expected at least three multi-node parallel layers')

# terminal dependency check: 13 must depend only on 12
if dag.get('terminal_nodes', []) != ['13']:
    raise SystemExit('ERROR: terminal_nodes must be exactly [13]')
if nodes['13'].get('parents', []) != ['12']:
    raise SystemExit('ERROR: node 13 must depend only on node 12')
if '13' not in layers[-1] or '12' not in layers[-2]:
    raise SystemExit('ERROR: node 13 must be the final layer and node 12 must be the previous layer')

# ready layer parent check
pos={nid:i for i,ly in enumerate(layers) for nid in ly}
for nid,n in nodes.items():
    if nid not in pos:
        raise SystemExit(f'ERROR: node {nid} missing from parallel_layers')
    for p in n.get('parents', []):
        if pos[p] >= pos[nid]:
            raise SystemExit(f'ERROR: parent {p} of {nid} is not in an earlier layer')

print('OK: DAG is valid and non-serial.')
print('Parallel layers:')
for i, ly in enumerate(layers):
    print(f'  L{i}: ' + ', '.join(ly))
