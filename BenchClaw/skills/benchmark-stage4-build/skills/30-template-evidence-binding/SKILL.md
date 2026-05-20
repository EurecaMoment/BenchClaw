# Skill 30 — 模板-证据绑定

全局路径约束：`BENCHCLAW_ROOT` 仅作只读输入；`WORKSPACE_ROOT` 是本次流程唯一总工作目录，所有写操作和流程产物只能落在其下。

## 父节点

`28`, `29`

## 任务

对每个模板契约检查证据池中哪些 record 满足必需字段，输出绑定结果。

绑定必须是代码化检查，不允许只靠 LLM 判断：

- 字段是否存在；
- GT 来源类型是否合法；
- 数值范围/坐标系/单位是否一致；
- 图像、mask、bbox、depth、pose 等证据路径是否可解析；
- 对每个拒绝样本写 `binding_rejection_log.jsonl`。

## 输出

```text
WORKSPACE_ROOT/stage4/30-template-evidence-binding/template_evidence_bindings.jsonl
WORKSPACE_ROOT/stage4/30-template-evidence-binding/binding_rejection_log.jsonl
WORKSPACE_ROOT/stage4/30-template-evidence-binding/binding_summary.md
USED_INPUTS.json
DONE.json
```


---

## I/O 合同摘要

```text
node_id: 30
parents: ['28', '29']
output_dir: WORKSPACE_ROOT/stage4/30-template-evidence-binding
```

完整白名单以 `contracts/node_io_contracts.json` 为准。
