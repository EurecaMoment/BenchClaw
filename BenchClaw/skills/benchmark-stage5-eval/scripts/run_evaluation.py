#!/usr/bin/env python3
"""
Generic Stage5 evaluation fallback.

This script scores materialized predictions when the Stage4 package does not provide a specialized evaluator.
It expects prediction JSONL files with rows such as:
  {"sample_id":"...", "model":"...", "prediction":"..."}

Evalset rows should contain an id and a gold answer using common field names:
  sample_id/id/qid and answer/gold/label/target
"""

import argparse, csv, hashlib, json, os, sys, time
from pathlib import Path

try:
    import yaml
except Exception:
    yaml = None

ID_KEYS = ["sample_id", "id", "qid", "question_id"]
GOLD_KEYS = ["answer", "gold", "label", "target", "correct_answer"]
DIM_KEYS = ["dimension", "capability", "skill", "category", "domain"]
FALLBACK_METRICS = {
    "single_choice_exact_match",
    "normalize_choice_letter_then_exact_match",
    "exact_match",
    "exact_match_fallback",
}


def load_jsonl(path):
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSONL at {path}:{i}: {e}")
    return rows


def get_first(d, keys, default=None):
    for k in keys:
        if k in d and d[k] is not None:
            return d[k]
    return default


def norm(x):
    if x is None:
        return ""
    return str(x).strip().lower()


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def validate_fallback_compatibility(stage4, rows):
    metric_entry = stage4 / "EVALSET_DATASET" / "metrics" / "evaluate.py"
    if not metric_entry.exists():
        raise SystemExit(f"missing metric entry: {metric_entry}")

    fallback_safe_metric_ids = set(FALLBACK_METRICS)

    unsupported = []
    for idx, row in enumerate(rows):
        item_id = get_first(row, ID_KEYS, str(idx))
        metric_id = row.get("metric_id")
        if metric_id and metric_id not in fallback_safe_metric_ids:
            unsupported.append(
                f"sample {item_id} uses unsupported metric_id={metric_id}"
            )

    if unsupported:
        detail = "\n".join(f"- {item}" for item in unsupported[:20])
        extra = (
            ""
            if len(unsupported) <= 20
            else f"\n- ... and {len(unsupported) - 20} more"
        )
        raise SystemExit(
            "Stage5 fallback evaluator cannot score this Stage4 package safely. "
            "Provide materialized scored outputs or implement the declared metric/answer-program execution.\n"
            f"{detail}{extra}"
        )


def workspace_path(path_value, workspace):
    text = str(path_value).replace("\\", "/")
    if text == "WORKSPACE_ROOT":
        return Path(workspace)
    if text.startswith("WORKSPACE_ROOT/"):
        return Path(workspace) / text[len("WORKSPACE_ROOT/") :]
    return Path(path_value)


def load_python_module(path, module_name):
    import importlib.util

    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load module from {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def load_model_roster(benchclaw_root):
    roster_path = benchclaw_root / "modelNeedMeasured" / "model_roster.yaml"
    if not roster_path.exists():
        raise SystemExit(f"missing model roster: {roster_path}")
    text = roster_path.read_text(encoding="utf-8")
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        if yaml is None:
            raise SystemExit(
                f"cannot parse model roster without PyYAML installed: {roster_path}"
            )
        data = yaml.safe_load(text)
    if not isinstance(data, dict):
        raise SystemExit(f"invalid model roster format: {roster_path}")
    models = data.get("models") or []
    if not isinstance(models, list) or not models:
        raise SystemExit(f"model roster has no models: {roster_path}")
    return data


def media_refs_for_row(row):
    refs = row.get("image_refs") or row.get("media_refs") or []
    if refs is None:
        return []
    if not isinstance(refs, list):
        raise ValueError(f"media refs must be a list, got {type(refs)!r}")
    return [str(r) for r in refs]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workspace", default="WORKSPACE_ROOT")
    ap.add_argument(
        "--stage4-package", default="WORKSPACE_ROOT/stage4/37-benchmark-artifact-pack"
    )
    ap.add_argument("--predictions-dir", default="WORKSPACE_ROOT/stage5/predictions")
    ap.add_argument("--outdir", default="WORKSPACE_ROOT/stage5/38-evaluation-run")
    ap.add_argument("--benchclaw-root", default="BENCHCLAW_ROOT")
    args = ap.parse_args()

    stage4 = workspace_path(args.stage4_package, args.workspace)
    benchclaw_root = Path(args.benchclaw_root)
    out = workspace_path(args.outdir, args.workspace)
    out.mkdir(parents=True, exist_ok=True)
    evalset = stage4 / "EVALSET_DATASET" / "data" / "test.jsonl"
    if not evalset.exists():
        raise SystemExit(f"missing evalset: {evalset}")

    rows = load_jsonl(evalset)
    validate_fallback_compatibility(stage4, rows)
    item_by_id = {}
    for idx, r in enumerate(rows):
        sid = get_first(r, ID_KEYS, str(idx))
        item_by_id[str(sid)] = r

    pred_dir = workspace_path(args.predictions_dir, args.workspace)
    pred_files = sorted(pred_dir.glob("*.jsonl")) if pred_dir.exists() else []
    roster = load_model_roster(benchclaw_root)
    required_models = [
        str(item.get("name")) for item in roster.get("models", []) if item.get("name")
    ]

    if not pred_files:
        media_dir = stage4 / "EVALSET_DATASET" / "images"
        client = load_python_module(
            benchclaw_root / "modelNeedMeasured" / "yeysai_multimodal_client.py",
            "yeysai_multimodal_client",
        )
        api_key, api_key_source = client.resolve_api_key(roster)
        api_base = str(
            roster.get("api_base") or "https://yeysai.com/v1/chat/completions"
        )
        generated_predictions = []
        model_summary = []
        for model_name in required_models:
            started = time.time()
            ok = 0
            failed = 0
            model_rows = []
            for idx, row in enumerate(rows):
                sid = str(get_first(row, ID_KEYS, str(idx)))
                refs = media_refs_for_row(row)
                media_paths = []
                for ref in refs:
                    candidate = media_dir / ref
                    if not candidate.exists():
                        raise SystemExit(f"missing media ref for {sid}: {candidate}")
                    media_paths.append(candidate)
                messages = client.build_messages(row, media_paths)
                try:
                    result = client.chat_completion(
                        api_base, api_key, model_name, messages
                    )
                    ok += 1
                    model_rows.append(
                        {
                            "sample_id": sid,
                            "model": model_name,
                            "prediction": result["prediction"],
                            "metadata": {
                                "response_id": result.get("response_id"),
                                "usage": result.get("usage", {}),
                                "api_base": api_base,
                                "api_key_source": api_key_source,
                                "media_ref_count": len(media_paths),
                                "multimodal": bool(media_paths),
                            },
                        }
                    )
                except Exception as exc:
                    failed += 1
                    model_rows.append(
                        {
                            "sample_id": sid,
                            "model": model_name,
                            "prediction": "",
                            "metadata": {
                                "api_base": api_base,
                                "api_key_source": api_key_source,
                                "media_ref_count": len(media_paths),
                                "multimodal": bool(media_paths),
                                "error": str(exc),
                            },
                        }
                    )
            model_pred_path = pred_dir / f"{model_name}.jsonl"
            model_pred_path.parent.mkdir(parents=True, exist_ok=True)
            with open(model_pred_path, "w", encoding="utf-8") as f:
                for record in model_rows:
                    f.write(json.dumps(record, ensure_ascii=False) + "\n")
            generated_predictions.append(model_pred_path)
            model_summary.append(
                {
                    "model": model_name,
                    "endpoint": api_base,
                    "api_key_source": api_key_source,
                    "sample_count": len(model_rows),
                    "success_count": ok,
                    "failure_count": failed,
                    "prediction_file": str(model_pred_path),
                    "duration_sec": time.time() - started,
                }
            )
            if ok == 0:
                raise SystemExit(
                    f"required model {model_name} produced zero successful API predictions; Stage5 must block instead of completing"
                )
        pred_files = generated_predictions
        (out / "model_call_summary.json").write_text(
            json.dumps(
                {"provider": "yeysai", "models": model_summary},
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
    else:
        observed = {pf.stem for pf in pred_files}
        missing = [m for m in required_models if m not in observed]
        if missing:
            raise SystemExit(
                "Missing prediction files for required models: " + ", ".join(missing)
            )
        (out / "model_call_summary.json").write_text(
            json.dumps(
                {
                    "provider": "materialized_predictions",
                    "models": [
                        {
                            "model": pf.stem,
                            "endpoint": "materialized_predictions",
                            "prediction_file": str(pf),
                        }
                        for pf in pred_files
                    ],
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

    logs = []
    failures = []
    aggregate = {}
    for pf in pred_files:
        preds = load_jsonl(pf)
        for pr in preds:
            model = str(pr.get("model") or pf.stem)
            sid = str(get_first(pr, ID_KEYS, ""))
            item = item_by_id.get(sid)
            if item is None:
                score = 0.0
                gold = None
                dim = "UNKNOWN"
                valid = False
                failures.append(
                    {
                        "sample_id": sid,
                        "model": model,
                        "reason": "prediction_sample_id_not_found",
                        "prediction": pr.get("prediction"),
                    }
                )
            else:
                gold = get_first(item, GOLD_KEYS, "")
                dim = str(get_first(item, DIM_KEYS, "UNKNOWN"))
                pred = pr.get("prediction", pr.get("answer", pr.get("output", "")))
                score = 1.0 if norm(pred) == norm(gold) else 0.0
                valid = True
                if score < 1.0:
                    failures.append(
                        {
                            "sample_id": sid,
                            "model": model,
                            "dimension": dim,
                            "prediction": pred,
                            "gold": gold,
                            "reason": "incorrect",
                        }
                    )
            pred = pr.get("prediction", pr.get("answer", pr.get("output", "")))
            logs.append(
                {
                    "sample_id": sid,
                    "model": model,
                    "prediction": pred,
                    "gold": gold,
                    "score": score,
                    "dimension": dim,
                    "metadata": {"prediction_file": str(pf), "valid": valid},
                }
            )
            rec = aggregate.setdefault(
                model,
                {"n": 0, "score_sum": 0.0, "missing": 0, "invalid": 0, "dims": {}},
            )
            rec["n"] += 1
            rec["score_sum"] += score
            d = rec["dims"].setdefault(dim, {"n": 0, "score_sum": 0.0})
            d["n"] += 1
            d["score_sum"] += score

    with open(out / "prediction_logs.jsonl", "w", encoding="utf-8") as f:
        for r in logs:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    with open(out / "failure_cases.jsonl", "w", encoding="utf-8") as f:
        for r in failures:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    leaderboard = []
    per_dim = []
    for model, rec in aggregate.items():
        overall = rec["score_sum"] / rec["n"] if rec["n"] else 0.0
        leaderboard.append(
            {
                "model": model,
                "overall_score": overall,
                "n": rec["n"],
                "missing": rec["missing"],
                "invalid": rec["invalid"],
            }
        )
        for dim, d in rec["dims"].items():
            per_dim.append(
                {
                    "model": model,
                    "dimension": dim,
                    "score": d["score_sum"] / d["n"] if d["n"] else 0.0,
                    "n": d["n"],
                }
            )
    leaderboard.sort(key=lambda x: x["overall_score"], reverse=True)
    for i, row in enumerate(leaderboard, 1):
        row["rank"] = i

    eval_results = {
        "stage": "stage5",
        "status": "scored",
        "metadata": {
            "evalset_path": str(evalset),
            "evalset_sha256": sha256_file(evalset),
            "sample_count": len(rows),
            "prediction_files": [str(p) for p in pred_files],
        },
        "results": aggregate,
        "leaderboard": leaderboard,
        "per_dimension": per_dim,
    }
    (out / "eval_results.json").write_text(
        json.dumps(eval_results, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    payload = {
        "benchmark_package": str(stage4),
        "evalset_sha256": sha256_file(evalset),
        "sample_count": len(rows),
        "status": "scored",
        "leaderboard": leaderboard,
        "required_models": required_models,
    }

    observed_leaderboard_models = {row.get("model") for row in leaderboard}
    missing_scored_models = [
        m for m in required_models if m not in observed_leaderboard_models
    ]
    if missing_scored_models:
        raise SystemExit(
            "Required models missing from scored leaderboard: "
            + ", ".join(missing_scored_models)
        )
    (out / "report_payload.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (out / "run_config.yaml").write_text(
        f"stage4_package: {stage4}\npredictions_dir: {pred_dir}\nscoring_mode: exact_match_fallback\nmodel_roster: {benchclaw_root / 'modelNeedMeasured' / 'model_roster.yaml'}\napi_client: {benchclaw_root / 'modelNeedMeasured' / 'yeysai_multimodal_client.py'}\n",
        encoding="utf-8",
    )
    (out / "DONE.json").write_text(
        json.dumps(
            {
                "node": "38",
                "status": "done",
                "time": time.time(),
                "model_count": len(aggregate),
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
