#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("--workspace", default="WORKSPACE_ROOT")
args = parser.parse_args()
ws = Path(args.workspace)

stage4_done = ws / "stage4" / "37-benchmark-artifact-pack" / "DONE.json"
node38_done = ws / "stage5" / "38-evaluation-run" / "DONE.json"
node39_done = ws / "stage5" / "39-evaluation-report" / "DONE.json"

ready = []
blocked = {}

def exists(p):
    return p.exists()

if not exists(node38_done):
    if exists(stage4_done):
        ready.append("38")
    else:
        blocked["38"] = [str(stage4_done)]

if not exists(node39_done):
    if exists(node38_done):
        ready.append("39")
    else:
        blocked["39"] = [str(node38_done)]

print(json.dumps({
    "ready": ready,
    "blocked": blocked,
    "done": {
        "38": exists(node38_done),
        "39": exists(node39_done)
    }
}, ensure_ascii=False, indent=2))
