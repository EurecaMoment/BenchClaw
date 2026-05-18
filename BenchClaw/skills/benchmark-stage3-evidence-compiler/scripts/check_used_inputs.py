#!/usr/bin/env python3
import argparse, json, sys
from pathlib import Path
ap = argparse.ArgumentParser()
ap.add_argument('--node', required=True)
ap.add_argument('--contracts', default='contracts/node_io_contracts.json')
ap.add_argument('--used-inputs')
args = ap.parse_args()
contracts = json.loads(Path(args.contracts).read_text(encoding='utf-8'))['node_contracts']
if args.node not in contracts:
    raise SystemExit(f'unknown node {args.node}')
path = Path(args.used_inputs) if args.used_inputs else Path(contracts[args.node]['must_write'][-1])
if not path.exists():
    raise SystemExit(f'ERROR: USED_INPUTS missing: {path}')
obj = json.loads(path.read_text(encoding='utf-8'))
if obj.get('node_id') != args.node:
    raise SystemExit(f'ERROR: node_id mismatch in {path}')
print(f'OK: USED_INPUTS present for node {args.node}')
