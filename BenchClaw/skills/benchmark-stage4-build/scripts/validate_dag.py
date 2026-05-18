#!/usr/bin/env python3
import json, sys
from collections import defaultdict, deque

path = sys.argv[1] if len(sys.argv) > 1 else 'dag.json'
with open(path, 'r', encoding='utf-8') as f:
    dag = json.load(f)
nodes = dag['nodes']

# parent existence
for nid, node in nodes.items():
    for p in node.get('parents', []):
        if p not in nodes:
            raise SystemExit(f'ERROR: node {nid} has unknown parent {p}')

# acyclic + levels
indeg = {nid: len(node.get('parents', [])) for nid, node in nodes.items()}
children = defaultdict(list)
for nid, node in nodes.items():
    for p in node.get('parents', []):
        children[p].append(nid)
q = deque(sorted([nid for nid,d in indeg.items() if d == 0]))
order = []
level = {nid: 0 for nid in q}
while q:
    n = q.popleft()
    order.append(n)
    for c in sorted(children[n]):
        level[c] = max(level.get(c, 0), level[n] + 1)
        indeg[c] -= 1
        if indeg[c] == 0:
            q.append(c)
if len(order) != len(nodes):
    raise SystemExit('ERROR: DAG has a cycle or disconnected indegree issue')

# terminal check
terms = dag.get('terminal_nodes', [])
if terms != ['37']:
    raise SystemExit(f'ERROR: terminal_nodes must be ["37"], got {terms}')

# non-serial check: at least one level has >1 node
levels = defaultdict(list)
for nid,l in level.items():
    levels[l].append(nid)
if not any(len(v) > 1 for v in levels.values()):
    raise SystemExit('ERROR: DAG was collapsed into a serial chain')

# Expected critical deps
expected = {
    '28':['09'], '29':['18','19','20'], '30':['28','29'],
    '31':['30'], '32':['30'], '33':['31','32'], '34':['33'],
    '35':['31','32','34'], '36':['31','32','35'], '37':['36']
}
for nid, parents in expected.items():
    got = nodes[nid].get('parents', [])
    if got != parents:
        raise SystemExit(f'ERROR: node {nid}.parents expected {parents}, got {got}')

print('OK: Stage4 DAG is valid and non-serial.')
for l in sorted(levels):
    print(f'L{l}: ' + ' | '.join(sorted(levels[l])))
