#!/usr/bin/env python3
import json, sys, py_compile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
required=[
    'SKILL.md','README.md','template_system/00_unified_logic.md',
    'template_system/01_capability_map.md','template_system/02_question_format_map.md',
    'template_system/03_benchmark_reference_synthesis.md','template_system/08_executable_synthesis_engine.md',
    'template_library/templates_100_unified.md','template_library/templates_100_unified.index.json',
    'template_library/executable_template_coverage.csv','template_library/executable_template_coverage.json',
    'schemas/eval_item.schema.json','schemas/entity_annotations.schema.json',
    'examples/ai2thor_qa1_reference_items.jsonl',
    'examples/uav_static_demo/generated_eval_dataset.jsonl','examples/uav_static_demo/generated_report.json',
    'tools/score_eval_dataset.py','tools/synthesize_static_vlm_benchmark.py'
]
errors=[]
for rel in required:
    if not (ROOT/rel).exists(): errors.append(f'missing: {rel}')
try:
    idx=json.loads((ROOT/'template_library/templates_100_unified.index.json').read_text(encoding='utf-8'))
    if len(idx)!=100: errors.append(f'template index expected 100, got {len(idx)}')
except Exception as e:
    errors.append(f'cannot read template index: {e}')
try:
    bench=json.loads((ROOT/'template_system/references/benchmark_cards.index.json').read_text(encoding='utf-8'))
    if len(bench)!=12: errors.append(f'benchmark cards expected 12, got {len(bench)}')
except Exception as e:
    errors.append(f'cannot read benchmark card index: {e}')
try:
    qa=sum(1 for line in (ROOT/'examples/ai2thor_qa1_reference_items.jsonl').read_text(encoding='utf-8').splitlines() if line.strip())
    if qa!=111: errors.append(f'qa1 items expected 111, got {qa}')
except Exception as e:
    errors.append(f'cannot read qa1 items: {e}')
try:
    cov=json.loads((ROOT/'template_library/executable_template_coverage.json').read_text(encoding='utf-8'))
    if len(cov)!=51: errors.append(f'executable template coverage expected 51, got {len(cov)}')
except Exception as e:
    errors.append(f'cannot read executable coverage: {e}')
try:
    generated=sum(1 for line in (ROOT/'examples/uav_static_demo/generated_eval_dataset.jsonl').read_text(encoding='utf-8').splitlines() if line.strip())
    if generated <= 0: errors.append('generated demo dataset is empty')
except Exception as e:
    errors.append(f'cannot read generated demo dataset: {e}')
for tool in ['tools/score_eval_dataset.py','tools/synthesize_static_vlm_benchmark.py']:
    try:
        py_compile.compile(str(ROOT/tool), doraise=True)
    except Exception as e:
        errors.append(f'python compile failed for {tool}: {e}')
for banned in ['source_preserved','raw_from_uploaded_zip','raw_from_uploaded']:
    if any(banned in str(p) for p in ROOT.rglob('*')):
        errors.append(f'banned raw folder pattern found: {banned}')
if errors:
    print('VALIDATION FAILED')
    for e in errors: print('-',e)
    sys.exit(1)
print('VALIDATION PASSED')
print({'templates':100,'benchmark_cards':12,'qa1_items':111,'executable_templates':51,'demo_items':generated})
