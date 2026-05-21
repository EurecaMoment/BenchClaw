# Skill 31 — 题型扩展与 blueprint 生成

全局路径约束：`BENCHCLAW_ROOT` 仅作只读输入；`WORKSPACE_ROOT` 是本次流程唯一总工作目录，所有写操作和流程产物只能落在其下。

## 父节点

`30`

## 任务

把证据绑定扩展成问题 blueprint，而不是直接写最终题目。

每个 blueprint 至少包含：

- `blueprint_id`、`template_id`、`binding_id`；
- question family：空间关系、对象属性、可达性、遮挡、深度顺序、动作前后状态等；
- capability tags；
- 题面变量、选项变量、干扰项生成策略；
- `source_trace`：必须能回溯到 Stage3 source record；
- 不得在 blueprint 中凭空生成 GT。

blueprint 必须是“可实例化题目合同”，不能只是模板名套壳。每个 blueprint 还必须明确：

- 题面需要被实例化的关键变量集合，例如 `start_pose`、`goal_pose`、`target_object`、`subject_object`、`reference_object`、`instruction`、`candidate_options` 等；
- 哪些变量必须进入最终 item 的 `input_fields`；
- 题面如何避免退化成空泛模板句，例如只写“optimal path from start to goal in ...”；
- 该题型实际需要的模态约束，不能只写 family 名称而不约束 `rgb/depth/language`；
- 最终 item 期望输出的 `expected_output_schema`。

若 blueprint 不能说明“最终题面如何被具体变量实例化为可回答问题”，则该 blueprint 不得进入后续全量合成。

## 输出

```text
WORKSPACE_ROOT/stage4/stage4.db
WORKSPACE_ROOT/stage4/31-question-form-expansion/question_blueprints.sqlite_export.jsonl
WORKSPACE_ROOT/stage4/31-question-form-expansion/blueprint_manifest.json
WORKSPACE_ROOT/stage4/31-question-form-expansion/distractor_policy.md
USED_INPUTS.json
DONE.json
```

规范真相源应写入 `stage4.db.question_blueprints`；`question_blueprints.sqlite_export.jsonl` 仅作为兼容性导出。


---

## I/O 合同摘要

```text
node_id: 31
parents: ['30']
output_dir: WORKSPACE_ROOT/stage4/31-question-form-expansion
```

完整白名单以 `contracts/node_io_contracts.json` 为准。
