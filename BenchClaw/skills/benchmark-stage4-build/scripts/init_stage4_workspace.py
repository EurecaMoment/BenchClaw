#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument('--workspace', default='WORKSPACE_ROOT')
ap.add_argument('--dag', default='dag.json')
args = ap.parse_args()

with open(args.dag, encoding='utf-8') as f:
    dag=json.load(f)

def workspace_path(path_value):
    text = str(path_value).replace('\\', '/')
    if text == 'WORKSPACE_ROOT':
        return Path(args.workspace)
    if text.startswith('WORKSPACE_ROOT/'):
        return Path(args.workspace) / text[len('WORKSPACE_ROOT/'):]
    return Path(path_value)

for node in dag['nodes'].values():
    workspace_path(node['output_dir']).mkdir(parents=True, exist_ok=True)
print('OK: Stage4 workspace directories created.')
