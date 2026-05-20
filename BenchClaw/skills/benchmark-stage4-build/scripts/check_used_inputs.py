#!/usr/bin/env python3
import argparse
import fnmatch
import json
from pathlib import Path


def normalize(path_value):
    return str(path_value).replace("\\", "/")


def matches(path_value, patterns):
    value = normalize(path_value)
    for pattern in patterns:
        pat = normalize(pattern)
        if pat.endswith("/**"):
            if value.startswith(pat[:-3]):
                return True
        if fnmatch.fnmatch(value, pat):
            return True
    return False


ap = argparse.ArgumentParser()
ap.add_argument("used_inputs")
ap.add_argument("node_id")
ap.add_argument("--contracts", default="contracts/node_io_contracts.json")
args = ap.parse_args()
contracts = json.load(open(args.contracts, encoding="utf-8"))["node_contracts"][
    args.node_id
]
used = json.load(open(args.used_inputs, encoding="utf-8"))
used_paths = used.get("used_inputs", [])
errors = []
for p in used_paths:
    if not matches(p, contracts.get("may_read", [])):
        errors.append(f"node {args.node_id} used input outside may_read: {p}")
    if matches(p, contracts.get("must_not_read", [])):
        errors.append(f"node {args.node_id} used forbidden input {p}")
if errors:
    raise SystemExit("ERROR: USED_INPUTS validation failed:\n- " + "\n- ".join(errors))
print("OK: USED_INPUTS respects may_read and must_not_read constraints.")
