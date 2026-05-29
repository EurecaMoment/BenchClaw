#!/usr/bin/env python3
import argparse
from pathlib import Path


DIRS = [
    "stage5/38-evaluation-run",
    "stage5/39-evaluation-report",
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workspace", default="WORKSPACE_ROOT")
    args = ap.parse_args()
    base = Path(args.workspace)
    for d in DIRS:
        (base / d).mkdir(parents=True, exist_ok=True)
    print(f"OK: initialized Stage5 workspace dirs for {base}")


if __name__ == "__main__":
    main()
