# Skill 36 — 全量合成

## 父节点

`31`, `32`, `35`

## 任务

按 `question_blueprints.jsonl`、`answer_programs.py`、`metric_registry.json` 与 `quality_filter_spec.json` 生成全量评测集。

每条 item 必须包含：

- `item_id`；
- `question`；
- `options` / answer schema；
- `answer` 或 `answer_program_id`；
- `metric_id`；
- `capability_tags`；
- `source_trace`；
- `template_id`、`binding_id`、`source_record_id`；
- seed / version / generation timestamp。

## 输出

```text
WORKSPACE_ROOT/stage4/36-full-scale-synthesis/eval_dataset.jsonl
WORKSPACE_ROOT/stage4/36-full-scale-synthesis/eval_dataset_manifest.json
WORKSPACE_ROOT/stage4/36-full-scale-synthesis/item_traceability.jsonl
WORKSPACE_ROOT/stage4/36-full-scale-synthesis/synthesis_log.md
USED_INPUTS.json
DONE.json
```


---

## I/O 合同摘要

```text
node_id: 36
parents: ['31', '32', '35']
output_dir: WORKSPACE_ROOT/stage4/36-full-scale-synthesis
```

完整白名单以 `contracts/node_io_contracts.json` 为准。
