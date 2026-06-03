#!/usr/bin/env python3
"""Score a BenchClaw unified eval dataset.

Supported metrics:
- exact_match / accuracy
- set_exact_match + macro_f1 for multi-choice answers
- numeric_exact / tolerance_accuracy for numeric answers
- ordered_list_pairwise_accuracy for ordering questions
- json_field_accuracy for JSON object/array structured answers

The scorer accepts both the unified schema fields (`item_id`, `gold_answer`) and
backward-compatible aliases emitted by the executable synthesizer (`id`, `answer`).
"""
import argparse
import json
import math
import re
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple


def load_jsonl(path: str) -> List[Dict[str, Any]]:
    out=[]
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line=line.strip()
            if line:
                out.append(json.loads(line))
    return out


def norm(x: Any) -> str:
    if x is None:
        return ''
    if isinstance(x, (list, tuple, set)):
        return ','.join(norm(v) for v in x)
    if isinstance(x, dict):
        return json.dumps(x, ensure_ascii=False, sort_keys=True)
    return re.sub(r'\s+', ' ', str(x).strip()).upper()


def as_set(x: Any) -> set:
    if x is None:
        return set()
    if isinstance(x, (list, tuple, set)):
        return {norm(v) for v in x if norm(v) != ''}
    if isinstance(x, str):
        # Try JSON first so '["A", "B"]' is treated as a set of values.
        try:
            parsed=json.loads(x)
            if isinstance(parsed, (list, tuple, set)):
                return {norm(v) for v in parsed if norm(v) != ''}
        except Exception:
            pass
    return {v for v in re.split(r'[,，;；\s]+', norm(x)) if v}


def as_list(x: Any) -> List[str]:
    if x is None:
        return []
    if isinstance(x, (list, tuple)):
        return [norm(v) for v in x if norm(v) != '']
    if isinstance(x, str):
        try:
            parsed=json.loads(x)
            if isinstance(parsed, list):
                return [norm(v) for v in parsed if norm(v) != '']
        except Exception:
            pass
    return [v for v in re.split(r'[,，;；>\s]+', norm(x)) if v]


def as_float(x: Any):
    try:
        return float(x)
    except Exception:
        m=re.search(r'-?\d+(?:\.\d+)?', str(x))
        return float(m.group(0)) if m else None


def parse_json_like(x: Any) -> Any:
    if isinstance(x, (dict, list)):
        return x
    if isinstance(x, str):
        try:
            return json.loads(x)
        except Exception:
            # Common model output: wrapped in code fences or with explanatory text.
            m=re.search(r'```(?:json)?\s*(.*?)```', x, flags=re.S|re.I)
            if m:
                try:
                    return json.loads(m.group(1).strip())
                except Exception:
                    pass
            m=re.search(r'(\{.*\}|\[.*\])', x, flags=re.S)
            if m:
                try:
                    return json.loads(m.group(1))
                except Exception:
                    pass
    return x


def flatten_json(x: Any, prefix: str='') -> Dict[str, str]:
    if isinstance(x, dict):
        out={}
        for k,v in x.items():
            key=f'{prefix}.{k}' if prefix else str(k)
            out.update(flatten_json(v, key))
        return out
    if isinstance(x, list):
        # For arrays, compare positionally by default.
        out={}
        for i,v in enumerate(x):
            key=f'{prefix}[{i}]' if prefix else f'[{i}]'
            out.update(flatten_json(v, key))
        return out
    return {prefix: norm(x)}


def score_json_field_accuracy(gold: Any, pred: Any) -> Tuple[float, Dict[str, Any]]:
    g=parse_json_like(gold)
    p=parse_json_like(pred)
    if type(g) is not type(p):
        # Allow arrays to be scored as sets when both are list-like after parsing failed.
        if isinstance(g, list):
            gs, ps = as_set(g), as_set(p)
            score = 1.0 if gs == ps else 0.0
            return score, {'mode':'array_set_fallback','gold_set':sorted(gs),'pred_set':sorted(ps)}
        return 0.0, {'error':'type_mismatch','gold_type':type(g).__name__,'pred_type':type(p).__name__,'parsed_pred':p}
    if isinstance(g, list):
        gs, ps = as_set(g), as_set(p)
        if not gs and not ps:
            return 1.0, {'mode':'array_set','gold_set':[], 'pred_set':[]}
        tp=len(gs & ps)
        precision=tp/len(ps) if ps else 0.0
        recall=tp/len(gs) if gs else 0.0
        f1=0.0 if precision+recall==0 else 2*precision*recall/(precision+recall)
        return f1, {'mode':'array_set','precision':precision,'recall':recall,'f1':f1,'gold_set':sorted(gs),'pred_set':sorted(ps)}
    if isinstance(g, dict):
        gf, pf = flatten_json(g), flatten_json(p)
        if not gf:
            return 1.0 if not pf else 0.0, {'mode':'object_fields','num_fields':0}
        correct=sum(1 for k,v in gf.items() if pf.get(k)==v)
        return correct/len(gf), {'mode':'object_fields','correct':correct,'num_fields':len(gf),'missing_fields':sorted(set(gf)-set(pf))}
    return (1.0 if norm(g)==norm(p) else 0.0), {'mode':'scalar_json','gold_norm':norm(g),'pred_norm':norm(p)}


def ordered_pairwise_accuracy(gold: Any, pred: Any) -> Tuple[float, Dict[str, Any]]:
    g=as_list(gold)
    p=as_list(pred)
    if len(g) < 2:
        return 1.0 if g == p else 0.0, {'gold_order':g,'pred_order':p,'num_pairs':0}
    pos_g={v:i for i,v in enumerate(g)}
    pos_p={v:i for i,v in enumerate(p)}
    pairs=0
    correct=0
    missing=[]
    for i in range(len(g)):
        for j in range(i+1, len(g)):
            a,b=g[i],g[j]
            pairs += 1
            if a not in pos_p or b not in pos_p:
                missing.extend([x for x in (a,b) if x not in pos_p])
                continue
            if pos_p[a] < pos_p[b]:
                correct += 1
    return correct/pairs if pairs else 0.0, {'gold_order':g,'pred_order':p,'correct_pairs':correct,'num_pairs':pairs,'missing':sorted(set(missing))}


def score_one(gold: Any, pred: Any, metric: str, tolerance=None) -> Tuple[float, Dict[str, Any]]:
    metric=(metric or 'exact_match').lower()
    if 'json' in metric or 'schema' in metric or 'field_accuracy' in metric:
        return score_json_field_accuracy(gold, pred)
    if 'ordered' in metric or 'pairwise' in metric or 'kendall' in metric:
        return ordered_pairwise_accuracy(gold, pred)
    if 'set' in metric or 'f1' in metric:
        gs, ps = as_set(gold), as_set(pred)
        set_exact = 1.0 if gs == ps else 0.0
        if not gs and not ps:
            f1=1.0
        elif not gs or not ps:
            f1=0.0
        else:
            tp=len(gs & ps)
            precision=tp/len(ps) if ps else 0.0
            recall=tp/len(gs) if gs else 0.0
            f1=0.0 if precision+recall==0 else 2*precision*recall/(precision+recall)
        if 'f1' in metric and 'set_exact' not in metric:
            return f1, {'set_exact':set_exact, 'f1':f1, 'gold_set':sorted(gs), 'pred_set':sorted(ps)}
        return set_exact, {'set_exact':set_exact, 'f1':f1, 'gold_set':sorted(gs), 'pred_set':sorted(ps)}
    if 'absolute_error' in metric or 'numeric' in metric or 'tolerance' in metric:
        g,p=as_float(gold),as_float(pred)
        if g is None or p is None:
            return 0.0, {'error':'non_numeric','gold':gold,'pred':pred}
        ae=abs(g-p)
        if tolerance is None:
            score = 1.0 if ae == 0 else 0.0
        else:
            score = 1.0 if ae <= float(tolerance) else 0.0
        return score, {'absolute_error':ae,'tolerance':tolerance}
    return (1.0 if norm(gold)==norm(pred) else 0.0), {'gold_norm':norm(gold),'pred_norm':norm(pred)}


def mean(xs: Iterable[float]) -> float:
    xs=list(xs)
    return sum(xs)/len(xs) if xs else 0.0


def item_id(x: Dict[str, Any]) -> str:
    return x.get('item_id') or x.get('id')


def gold_answer(x: Dict[str, Any]) -> Any:
    return x.get('gold_answer', x.get('answer'))


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--gold', required=True)
    ap.add_argument('--pred', required=True)
    ap.add_argument('--out', required=True)
    args=ap.parse_args()
    gold_items=load_jsonl(args.gold)
    pred_items={item_id(x):x.get('prediction', x.get('answer')) for x in load_jsonl(args.pred)}
    item_reports=[]
    groups=defaultdict(list)
    missing=[]
    for it in gold_items:
        iid=item_id(it)
        pred=pred_items.get(iid)
        if iid not in pred_items:
            missing.append(iid)
        scoring=it.get('scoring',{})
        metric=scoring.get('metric','exact_match') if isinstance(scoring,dict) else 'exact_match'
        tol=scoring.get('tolerance') if isinstance(scoring,dict) else None
        s,detail=score_one(gold_answer(it), pred, metric, tol)
        caps=it.get('capability_ids') or it.get('capability') or ['UNKNOWN']
        af=it.get('answer_format') or it.get('question_format') or it.get('answer_type') or 'UNKNOWN'
        fam=scoring.get('aggregation_group') if isinstance(scoring,dict) else it.get('template_id','UNKNOWN')
        item_reports.append({'item_id':iid,'score':s,'metric':metric,'detail':detail})
        groups[('by_answer_format',af)].append(s)
        groups[('by_template_family',fam or 'UNKNOWN')].append(s)
        for c in caps:
            groups[('by_capability',c)].append(s)
    report={
        'overall':{'n':len(gold_items),'mean_score':mean([x['score'] for x in item_reports]),'missing_predictions':missing},
        'by_capability':{},'by_template_family':{},'by_answer_format':{},'items':item_reports
    }
    for (kind,name),vals in groups.items():
        report[kind][name]={'n':len(vals),'mean_score':mean(vals)}
    Path(args.out).write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(report['overall'], ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
