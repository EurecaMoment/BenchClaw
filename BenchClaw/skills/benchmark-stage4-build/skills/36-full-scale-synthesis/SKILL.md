# Skill 36 — 全量合成

全局路径约束：`BENCHCLAW_ROOT` 仅作只读输入；`WORKSPACE_ROOT` 是本次流程唯一总工作目录，所有写操作和流程产物只能落在其下。

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

并且每条 item 还必须满足：

- `image_refs`、视频引用或其他媒体引用必须解析到 workspace 内真实存在、可被 Stage5 直接消费的文件；
- `answer` 或 `answer_program_id` 必须可追溯到真实落盘的 Stage3 证据，而不是模板默认值、样例值、placeholder_answer 或人工编造字母；
- 若某条 item 依赖的媒体或证据无法在 workspace 内解析，则该 item 不得进入最终 eval_dataset。

## 输出

```text
WORKSPACE_ROOT/stage4/36-full-scale-synthesis/eval_dataset.jsonl
WORKSPACE_ROOT/stage4/36-full-scale-synthesis/eval_dataset_manifest.json
WORKSPACE_ROOT/stage4/36-full-scale-synthesis/item_traceability.jsonl
WORKSPACE_ROOT/stage4/36-full-scale-synthesis/synthesis_log.md
WORKSPACE_ROOT/stage4/36-full-scale-synthesis/media/
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
