#!/usr/bin/env python3
import argparse, csv, json, time
from pathlib import Path


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_jsonl(path):
    rows = []
    p = Path(path)
    if not p.exists():
        return rows
    for line in p.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def workspace_path(path_value, workspace):
    text = str(path_value).replace("\\", "/")
    if text == "WORKSPACE_ROOT":
        return Path(workspace)
    if text.startswith("WORKSPACE_ROOT/"):
        return Path(workspace) / text[len("WORKSPACE_ROOT/") :]
    return Path(path_value)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workspace", default="WORKSPACE_ROOT")
    ap.add_argument("--in-dir", default="WORKSPACE_ROOT/stage5/38-evaluation-run")
    ap.add_argument("--outdir", default="WORKSPACE_ROOT/stage5/39-evaluation-report")
    args = ap.parse_args()
    indir = workspace_path(args.in_dir, args.workspace)
    out = workspace_path(args.outdir, args.workspace)
    out.mkdir(parents=True, exist_ok=True)

    done = indir / "DONE.json"
    if not done.exists():
        raise SystemExit(f"node 38 is not done: missing {done}")
    done_payload = load_json(done)
    if done_payload.get("status") != "done":
        raise SystemExit(
            f"node 38 is not complete: unexpected DONE status {done_payload.get('status')!r}"
        )
    eval_results = load_json(indir / "eval_results.json")
    if eval_results.get("status") != "scored":
        raise SystemExit(
            f"node 38 is not score-complete: eval_results.status={eval_results.get('status')!r}"
        )
    payload = load_json(indir / "report_payload.json")
    model_call_summary = load_json(indir / "model_call_summary.json")
    failures = load_jsonl(indir / "failure_cases.jsonl")

    leaderboard = eval_results.get("leaderboard", [])
    per_dim = eval_results.get("per_dimension", [])

    with open(out / "leaderboard.csv", "w", newline="", encoding="utf-8") as f:
        fieldnames = ["rank", "model", "overall_score", "n", "missing", "invalid"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in leaderboard:
            writer.writerow({k: r.get(k, "") for k in fieldnames})

    with open(out / "per_dimension.csv", "w", newline="", encoding="utf-8") as f:
        fieldnames = ["model", "dimension", "score", "n"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in per_dim:
            writer.writerow({k: r.get(k, "") for k in fieldnames})

    # Simple failure grouping
    groups = {}
    for r in failures:
        key = (
            r.get("model", "UNKNOWN"),
            r.get("dimension", "UNKNOWN"),
            r.get("reason", "UNKNOWN"),
        )
        groups[key] = groups.get(key, 0) + 1

    err_lines = ["# Error Analysis", ""]
    if not failures:
        err_lines.append("No failure cases were recorded.")
    else:
        err_lines.append("| Model | Dimension | Reason | Count |")
        err_lines.append("|---|---|---|---:|")
        for (model, dim, reason), cnt in sorted(
            groups.items(), key=lambda x: x[1], reverse=True
        ):
            err_lines.append(f"| {model} | {dim} | {reason} | {cnt} |")
    (out / "error_analysis.md").write_text(
        "\n".join(err_lines) + "\n", encoding="utf-8"
    )

    report = ["# Stage5 Evaluation Report", ""]
    report.append("## Benchmark Handoff")
    report.append("")
    report.append(f"- Stage4 package: `{payload.get('benchmark_package', '')}`")
    report.append(f"- Evalset SHA256: `{payload.get('evalset_sha256', '')}`")
    report.append(f"- Sample count: `{payload.get('sample_count', '')}`")
    report.append(f"- Evaluation status: `{eval_results.get('status', '')}`")
    report.append(
        f"- Required model count: `{len(payload.get('required_models', []))}`"
    )
    report.append("")
    report.append("## Model Calls")
    report.append("")
    report.append(f"- Provider: `{model_call_summary.get('provider', '')}`")
    for row in model_call_summary.get("models", []):
        report.append(
            f"- `{row.get('model', '')}` -> endpoint `{row.get('endpoint', '')}`, predictions `{row.get('prediction_file', '')}`"
        )
    report.append("")
    report.append("## Leaderboard")
    report.append("")
    if leaderboard:
        report.append("| Rank | Model | Overall Score | N | Missing | Invalid |")
        report.append("|---:|---|---:|---:|---:|---:|")
        for r in leaderboard:
            report.append(
                f"| {r.get('rank', '')} | {r.get('model', '')} | {r.get('overall_score', 0):.6f} | {r.get('n', '')} | {r.get('missing', '')} | {r.get('invalid', '')} |"
            )
    else:
        report.append("No model predictions were available for scoring.")
    report.append("")
    report.append("## Per-Dimension Results")
    report.append("")
    if per_dim:
        report.append("| Model | Dimension | Score | N |")
        report.append("|---|---|---:|---:|")
        for r in per_dim:
            report.append(
                f"| {r.get('model', '')} | {r.get('dimension', '')} | {r.get('score', 0):.6f} | {r.get('n', '')} |"
            )
    else:
        report.append("No per-dimension scores were available.")
    report.append("")
    report.append("## Failure Summary")
    report.append("")
    report.append(f"Failure case count: `{len(failures)}`")
    report.append("")
    report.append("See `error_analysis.md` for grouped failure cases.")
    report.append("")
    report.append("## Reproducibility Artifacts")
    report.append("")
    report.append("- `../38-evaluation-run/eval_results.json`")
    report.append("- `../38-evaluation-run/prediction_logs.jsonl`")
    report.append("- `../38-evaluation-run/failure_cases.jsonl`")
    report.append("- `../38-evaluation-run/model_call_summary.json`")
    report.append("- `leaderboard.csv`")
    report.append("- `per_dimension.csv`")
    (out / "report.md").write_text("\n".join(report) + "\n", encoding="utf-8")

    (out / "DONE.json").write_text(
        json.dumps(
            {"node": "39", "status": "done", "time": time.time()},
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
