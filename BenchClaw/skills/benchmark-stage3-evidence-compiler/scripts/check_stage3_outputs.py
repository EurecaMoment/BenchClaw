#!/usr/bin/env python3
import argparse, json, sys
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument('--workspace', default='WORKSPACE_ROOT')
ap.add_argument('--dag', default='dag.json')
ap.add_argument('--contracts', default='contracts/node_io_contracts.json')
args = ap.parse_args()

dag = json.loads(Path(args.dag).read_text(encoding='utf-8'))
contracts = json.loads(Path(args.contracts).read_text(encoding='utf-8'))['node_contracts']
missing = []

def workspace_path(path_value):
    text = str(path_value).replace('\\', '/')
    if text == 'WORKSPACE_ROOT':
        return Path(args.workspace)
    if text.startswith('WORKSPACE_ROOT/'):
        return Path(args.workspace) / text[len('WORKSPACE_ROOT/'):]
    return Path(path_value)

for nid in dag['terminal_nodes']:
    node = dag['nodes'][nid]
    done = workspace_path(node['output_dir']) / 'DONE.json'
    if not done.exists():
        missing.append(str(done))
    for item in contracts[nid]['must_write']:
        p = workspace_path(item)
        if str(item).endswith('/'):
            if not p.exists() or not p.is_dir():
                missing.append(str(p))
        elif '*' in str(item):
            continue
        else:
            if not p.exists():
                missing.append(str(p))
if missing:
    print('ERROR: missing Stage3 terminal outputs:')
    for m in missing:
        print('  -', m)
    sys.exit(1)
print('OK: Stage3 terminal outputs are complete: 18, 19, 20.')
