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

最终进入 Stage4 正式评测集的 item 还必须额外包含，并写入 `eval_dataset.jsonl`：

- `question_type` 与 `dimension`；
- `input_fields`，且其中必须包含该题型真正需要的具体实例变量，而不是只剩 `scene_id + modality_condition`；
- `ground_truth_answer`，且它必须是真正可判分答案，而不是“GT 会在别处计算”的说明文本；
- `expected_output_schema`；
- `evaluation_ready`，且只能在程序化检查全部通过后设为 `true`。

并且每条 item 还必须满足：

- `image_refs`、视频引用或其他媒体引用必须解析到 workspace 内真实存在、可被 Stage5 直接消费的文件；
- `answer` 或 `answer_program_id` 必须可追溯到真实落盘的 Stage3 证据，而不是模板默认值、样例值、placeholder_answer 或人工编造字母；
- 若某条 item 依赖的媒体或证据无法在 workspace 内解析，则该 item 不得进入最终 eval_dataset。
- 题面必须是“已经实例化完成的题目”，不能只保留模板句、家族名、抽象变量名或泛化问法；
- 若题面在问 navigation/path，则必须提供明确的 start/goal/constraint 信息；若题面在问关系、属性、深度、指令、多模态冲突等能力，则题面与 `input_fields` 必须给出相应具体对象、约束、选项或指令；
- `ground_truth_answer` 与 `answer_program_id` / `metric_id` 的接口必须闭合：不能出现自然语言题面对应的答案字段只是“Success metrics computed from simulator_privileged_gt”这类占位说明；
- `question_type`、`template_id`、`capability_tags` 与题面必须构念一致，不得把大量非导航任务统一写成“optimal path from start to goal”一类错位题；
- `modality_condition` 必须与真实任务需求和媒体资产一致；需要 depth 的题必须真的有 depth 相关输入，需要 language 的题必须真的有语言输入或指令。

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
