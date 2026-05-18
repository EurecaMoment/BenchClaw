#!/usr/bin/env python3
import argparse, json
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument('--workspace', default='WORKSPACE_ROOT')
ap.add_argument('--dag', default='dag.json')
args = ap.parse_args()
with open(args.dag, 'r', encoding='utf-8') as f:
    dag = json.load(f)
nodes = dag['nodes']

def workspace_path(path_value):
    text = str(path_value).replace('\\', '/')
    if text == 'WORKSPACE_ROOT':
        return Path(args.workspace)
    if text.startswith('WORKSPACE_ROOT/'):
        return Path(args.workspace) / text[len('WORKSPACE_ROOT/'):]
    return Path(path_value)

def done(nid):
    return (workspace_path(nodes[nid]['output_dir']) / 'DONE.json').exists()

ready = []
for nid,node in nodes.items():
    if done(nid):
        continue
    if all(done(p) for p in node.get('parents', [])):
        ready.append(nid)
print('READY: ' + (' '.join(sorted(ready)) if ready else '<none>'))
