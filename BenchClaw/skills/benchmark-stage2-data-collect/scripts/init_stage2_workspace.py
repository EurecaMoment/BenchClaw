#!/usr/bin/env python3
import argparse
from pathlib import Path

DIRS = [
    "stage2/13-execution-plan-ingest",
    "stage2/14-simulator-skill-registry",
    "stage2/15-real-image-acquisition/images",
    "stage2/16-existing-benchmark-acquisition/raw",
    "stage2/17-simulator-multimodal-gt-acquisition/observations",
    "stage2/17-simulator-multimodal-gt-acquisition/provenance",
    "config",
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workspace", default="WORKSPACE_ROOT")
    args = ap.parse_args()
    base = Path(args.workspace)
    for d in DIRS:
        (base / d).mkdir(parents=True, exist_ok=True)
    print(f"OK: initialized {base}/stage2 workspace skeleton")


if __name__ == "__main__":
    main()
