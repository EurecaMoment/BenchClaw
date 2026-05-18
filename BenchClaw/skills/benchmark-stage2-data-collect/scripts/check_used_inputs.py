#!/usr/bin/env python3
import argparse
import fnmatch
import json
from pathlib import Path

def load(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def allowed(path, patterns):
    p = path.replace("\\", "/")
    for pat in patterns:
        pat = pat.replace("\\", "/")
        if pat.endswith("/**"):
            if p.startswith(pat[:-3]):
                return True
        if fnmatch.fnmatch(p, pat):
            return True
    return False

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workspace", default="WORKSPACE_ROOT")
    ap.add_argument("--contracts", default="contracts/node_io_contracts.json")
    args = ap.parse_args()

    contracts = load(args.contracts)["node_contracts"]
    errors = []

    for node_id, c in contracts.items():
        # output dir naming convention from DAG
        dag = load("dag.json")
        rel = dag["nodes"][node_id]["output_dir"]
        if rel.startswith("WORKSPACE_ROOT/"):
            rel = rel[len("WORKSPACE_ROOT/"):]
        used_path = Path(args.workspace) / rel / "USED_INPUTS.json"
        if not used_path.exists():
            continue
        used = load(used_path).get("used_inputs", [])
        for item in used:
            if not allowed(item, c.get("may_read", [])):
                errors.append(f"node {node_id} used forbidden input: {item}")

    if errors:
        print("ERROR: used input contract violation")
        for e in errors:
            print(" - " + e)
        raise SystemExit(1)
    print("OK: USED_INPUTS respect node read whitelist.")

if __name__ == "__main__":
    main()
