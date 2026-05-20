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

## 输出

```text
WORKSPACE_ROOT/stage4/31-question-form-expansion/question_blueprints.jsonl
WORKSPACE_ROOT/stage4/31-question-form-expansion/blueprint_manifest.json
WORKSPACE_ROOT/stage4/31-question-form-expansion/distractor_policy.md
USED_INPUTS.json
DONE.json
```


---

## I/O 合同摘要

```text
node_id: 31
parents: ['30']
output_dir: WORKSPACE_ROOT/stage4/31-question-form-expansion
```

完整白名单以 `contracts/node_io_contracts.json` 为准。
