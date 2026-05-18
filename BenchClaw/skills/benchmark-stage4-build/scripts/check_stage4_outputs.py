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
errors=[]

def workspace_path(path_value):
    text = str(path_value).replace('\\', '/')
    if text == 'WORKSPACE_ROOT':
        return Path(args.workspace)
    if text.startswith('WORKSPACE_ROOT/'):
        return Path(args.workspace) / text[len('WORKSPACE_ROOT/'):]
    return Path(path_value)

for nid,node in nodes.items():
    out = workspace_path(node['output_dir'])
    if not (out/'DONE.json').exists():
        errors.append(f'missing DONE for node {nid}: {out}/DONE.json')
for nid in ['33','34']:
    out = workspace_path(nodes[nid]['output_dir'])
    if not (out/'WAIVED.json').exists():
        errors.append(f'node {nid} must be waived but WAIVED.json missing')
term = workspace_path(nodes['37']['output_dir'])
required = [
    term/'EVALSET_DATASET'/'eval_dataset.jsonl',
    term/'EVALSET_DATASET'/'metric_registry.json',
    term/'EVALSET_DATASET'/'answer_programs.py',
    term/'FINAL_BENCHMARK_CARD.md',
    term/'STAGE4_REPORT.md',
    term/'DONE.json',
]
for p in required:
    if not p.exists():
        errors.append(f'missing final artifact: {p}')
if errors:
    print('ERROR: Stage4 output check failed:')
    for e in errors:
        print(' - '+e)
    raise SystemExit(1)
print('OK: Stage4 outputs complete.')
