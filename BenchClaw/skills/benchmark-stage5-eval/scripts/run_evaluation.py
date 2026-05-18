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

def load_jsonl(path):
    rows=[]
    with open(path, 'r', encoding='utf-8') as f:
        for i,line in enumerate(f,1):
            line=line.strip()
            if not line: continue
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
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for chunk in iter(lambda:f.read(1024*1024), b''):
            h.update(chunk)
    return h.hexdigest()

def workspace_path(path_value, workspace):
    text=str(path_value).replace('\\', '/')
    if text == 'WORKSPACE_ROOT':
        return Path(workspace)
    if text.startswith('WORKSPACE_ROOT/'):
        return Path(workspace) / text[len('WORKSPACE_ROOT/'):]
    return Path(path_value)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--workspace', default='WORKSPACE_ROOT')
    ap.add_argument('--stage4-package', default='WORKSPACE_ROOT/stage4/37-benchmark-artifact-pack')
    ap.add_argument('--predictions-dir', default='WORKSPACE_ROOT/stage5/predictions')
    ap.add_argument('--outdir', default='WORKSPACE_ROOT/stage5/38-evaluation-run')
    args=ap.parse_args()

    stage4=workspace_path(args.stage4_package, args.workspace)
    out=workspace_path(args.outdir, args.workspace); out.mkdir(parents=True, exist_ok=True)
    evalset=stage4/'EVALSET_DATASET'/'eval_dataset.jsonl'
    if not evalset.exists():
        evalset=stage4/'eval_dataset.jsonl'
    if not evalset.exists():
        raise SystemExit(f"missing evalset: {evalset}")

    rows=load_jsonl(evalset)
    item_by_id={}
    for idx,r in enumerate(rows):
        sid=get_first(r, ID_KEYS, str(idx))
        item_by_id[str(sid)] = r

    pred_dir=workspace_path(args.predictions_dir, args.workspace)
    pred_files=sorted(pred_dir.glob('*.jsonl')) if pred_dir.exists() else []
    if not pred_files:
        # produce empty auditable outputs rather than fabricated metrics
        (out/'prediction_logs.jsonl').write_text('', encoding='utf-8')
        (out/'failure_cases.jsonl').write_text('', encoding='utf-8')
        eval_results={
            'stage':'stage5',
            'status':'no_predictions',
            'metadata':{'evalset_path':str(evalset),'evalset_sha256':sha256_file(evalset),'sample_count':len(rows)},
            'results':{},
            'leaderboard':[],
            'per_dimension':[]
        }
        (out/'eval_results.json').write_text(json.dumps(eval_results,ensure_ascii=False,indent=2), encoding='utf-8')
        payload={'benchmark_package':str(stage4),'evalset_sha256':sha256_file(evalset),'sample_count':len(rows),'status':'no_predictions'}
        (out/'report_payload.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2), encoding='utf-8')
        (out/'run_config.yaml').write_text(f"stage4_package: {stage4}\npredictions_dir: {pred_dir}\nscoring_mode: exact_match_fallback\n", encoding='utf-8')
        (out/'DONE.json').write_text(json.dumps({'node':'38','status':'done_no_predictions','time':time.time()},ensure_ascii=False,indent=2), encoding='utf-8')
        return

    logs=[]; failures=[]; aggregate={}
    for pf in pred_files:
        preds=load_jsonl(pf)
        for pr in preds:
            model=str(pr.get('model') or pf.stem)
            sid=str(get_first(pr, ID_KEYS, ''))
            item=item_by_id.get(sid)
            if item is None:
                score=0.0; gold=None; dim='UNKNOWN'; valid=False
                failures.append({'sample_id':sid,'model':model,'reason':'prediction_sample_id_not_found','prediction':pr.get('prediction')})
            else:
                gold=get_first(item, GOLD_KEYS, '')
                dim=str(get_first(item, DIM_KEYS, 'UNKNOWN'))
                pred=pr.get('prediction', pr.get('answer', pr.get('output','')))
                score=1.0 if norm(pred)==norm(gold) else 0.0
                valid=True
                if score < 1.0:
                    failures.append({'sample_id':sid,'model':model,'dimension':dim,'prediction':pred,'gold':gold,'reason':'incorrect'})
            pred=pr.get('prediction', pr.get('answer', pr.get('output','')))
            logs.append({'sample_id':sid,'model':model,'prediction':pred,'gold':gold,'score':score,'dimension':dim,'metadata':{'prediction_file':str(pf),'valid':valid}})
            rec=aggregate.setdefault(model, {'n':0,'score_sum':0.0,'missing':0,'invalid':0,'dims':{}})
            rec['n']+=1; rec['score_sum']+=score
            d=rec['dims'].setdefault(dim, {'n':0,'score_sum':0.0})
            d['n']+=1; d['score_sum']+=score

    with open(out/'prediction_logs.jsonl','w',encoding='utf-8') as f:
        for r in logs: f.write(json.dumps(r,ensure_ascii=False)+'\n')
    with open(out/'failure_cases.jsonl','w',encoding='utf-8') as f:
        for r in failures: f.write(json.dumps(r,ensure_ascii=False)+'\n')

    leaderboard=[]; per_dim=[]
    for model, rec in aggregate.items():
        overall=rec['score_sum']/rec['n'] if rec['n'] else 0.0
        leaderboard.append({'model':model,'overall_score':overall,'n':rec['n'],'missing':rec['missing'],'invalid':rec['invalid']})
        for dim,d in rec['dims'].items():
            per_dim.append({'model':model,'dimension':dim,'score':d['score_sum']/d['n'] if d['n'] else 0.0,'n':d['n']})
    leaderboard.sort(key=lambda x:x['overall_score'], reverse=True)
    for i,row in enumerate(leaderboard,1): row['rank']=i

    eval_results={'stage':'stage5','status':'scored','metadata':{'evalset_path':str(evalset),'evalset_sha256':sha256_file(evalset),'sample_count':len(rows),'prediction_files':[str(p) for p in pred_files]},'results':aggregate,'leaderboard':leaderboard,'per_dimension':per_dim}
    (out/'eval_results.json').write_text(json.dumps(eval_results,ensure_ascii=False,indent=2), encoding='utf-8')
    payload={'benchmark_package':str(stage4),'evalset_sha256':sha256_file(evalset),'sample_count':len(rows),'status':'scored','leaderboard':leaderboard}
    (out/'report_payload.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2), encoding='utf-8')
    (out/'run_config.yaml').write_text(f"stage4_package: {stage4}\npredictions_dir: {pred_dir}\nscoring_mode: exact_match_fallback\n", encoding='utf-8')
    (out/'DONE.json').write_text(json.dumps({'node':'38','status':'done','time':time.time(),'model_count':len(aggregate)},ensure_ascii=False,indent=2), encoding='utf-8')

if __name__ == '__main__':
    main()
