#!/usr/bin/env python3
import argparse, json
from pathlib import Path

ap=argparse.ArgumentParser()
ap.add_argument('used_inputs')
ap.add_argument('node_id')
ap.add_argument('--contracts', default='contracts/node_io_contracts.json')
args=ap.parse_args()
contracts=json.load(open(args.contracts, encoding='utf-8'))['node_contracts'][args.node_id]
used=json.load(open(args.used_inputs, encoding='utf-8'))
used_paths=used.get('used_inputs', [])
for p in used_paths:
    for banned in contracts.get('must_not_read', []):
        prefix=banned.rstrip('/**')
        if p.startswith(prefix):
            raise SystemExit(f'ERROR: node {args.node_id} used forbidden input {p}')
print('OK: USED_INPUTS respects must_not_read prefixes.')
