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
ap.add_argument("--node", required=True)
ap.add_argument("--contracts", default="contracts/node_io_contracts.json")
ap.add_argument("--used-inputs")
args = ap.parse_args()

contracts = json.loads(Path(args.contracts).read_text(encoding="utf-8"))[
    "node_contracts"
]
if args.node not in contracts:
    raise SystemExit(f"unknown node {args.node}")

path = (
    Path(args.used_inputs)
    if args.used_inputs
    else Path(contracts[args.node]["must_write"][-1])
)
if not path.exists():
    raise SystemExit(f"ERROR: USED_INPUTS missing: {path}")

obj = json.loads(path.read_text(encoding="utf-8"))
if obj.get("node_id") != args.node:
    raise SystemExit(f"ERROR: node_id mismatch in {path}")

inputs = obj.get("inputs")
if not isinstance(inputs, list):
    raise SystemExit(f"ERROR: inputs must be a list in {path}")

contract = contracts[args.node]
errors = []
for item in inputs:
    if not isinstance(item, dict):
        errors.append(f"invalid input entry type: {item!r}")
        continue
    input_path = item.get("path")
    purpose = item.get("purpose")
    if not input_path or not isinstance(input_path, str):
        errors.append(f"missing path in input entry: {item!r}")
        continue
    if not purpose or not isinstance(purpose, str):
        errors.append(f"missing purpose for input path: {input_path}")
    if not matches(input_path, contract.get("may_read", [])):
        errors.append(f"input not allowed by may_read: {input_path}")
    if matches(input_path, contract.get("must_not_read", [])):
        errors.append(f"input forbidden by must_not_read: {input_path}")

if errors:
    raise SystemExit("ERROR: USED_INPUTS validation failed:\n- " + "\n- ".join(errors))

print(f"OK: USED_INPUTS validated for node {args.node}")
