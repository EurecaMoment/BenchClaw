#!/usr/bin/env python3
import argparse, json
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument('--workspace', default='WORKSPACE_ROOT')
ap.add_argument('--dag', default='dag.json')
args = ap.parse_args()

dag = json.loads(Path(args.dag).read_text(encoding='utf-8'))
nodes = dag['nodes']

def workspace_path(path_value):
    text = str(path_value).replace('\\', '/')
    if text == 'WORKSPACE_ROOT':
        return Path(args.workspace)
    if text.startswith('WORKSPACE_ROOT/'):
        return Path(args.workspace) / text[len('WORKSPACE_ROOT/'):]
    return Path(path_value)

def done(nid):
    out = workspace_path(nodes[nid]['output_dir'])
    return (out / 'DONE.json').exists()

done_nodes = {nid for nid in nodes if done(nid)}
ready = []
for nid, node in nodes.items():
    if nid in done_nodes:
        continue
    if set(node.get('parents', [])) <= done_nodes:
        ready.append(nid)
ready = sorted(ready, key=lambda x: (len(x), x))
print('DONE: ' + (' '.join(sorted(done_nodes, key=lambda x:(len(x),x))) if done_nodes else '(none)'))
print('READY: ' + (' '.join(ready) if ready else '(none)'))
if ready:
    print('READY_SKILLS:')
    for nid in ready:
        print(f'  {nid}: {nodes[nid]["skill"]}')
