#!/usr/bin/env python3
import json, sys
from pathlib import Path
path = Path(sys.argv[1] if len(sys.argv) > 1 else 'dag.json')
dag = json.loads(path.read_text(encoding='utf-8'))
print('Ready-set schedule:')
for i, layer in enumerate(dag['parallel_layers']):
    print(f'L{i}: ' + ' | '.join(layer))
