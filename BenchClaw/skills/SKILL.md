# BenchClaw Skill Bundle — 总入口

本文件是大模型启动 BenchClaw benchmark 构建流程时首先读取的总入口。进入流程后，必须立即加载并执行：

```text
benchmark-pipeline/SKILL.md
```

本文件不直接展开 Stage1 到 Stage5 的内部 DAG，也不以脚本替代 skill 调度。真正的总控逻辑由 `benchmark-pipeline/SKILL.md` 承担；五个阶段分别由下列 stage skill 承担：

```text
benchmark-stage1-draft/SKILL.md
benchmark-stage2-data-collect/SKILL.md
benchmark-stage3-evidence-compiler/SKILL.md
benchmark-stage4-build/SKILL.md
benchmark-stage5-eval/SKILL.md
```

## 启动规则

1. 先读取 `benchmark-pipeline/SKILL.md`。
2. 按 pipeline skill 冻结 `PROJECT_ROOT`、`BENCHCLAW_ROOT`、`WORKSPACE_PARENT`、`WORKSPACE_ROOT`。
3. 只把五个 stage 当作大阶段顺序调用；stage 内部节点必须由各自的 `dag.json` 和 ready-set 规则调度。
4. 手绘图中的椭圆才是 DAG 节点；带编号的内容是中间流动数据，不是节点。用户输入与结束状态也不是节点。
5. 所有写入只能落在本次 `WORKSPACE_ROOT` 下；`BENCHCLAW_ROOT` 只读。
6. 缺少真实输入、真实采集结果、真实标注结果、真实 GT、真实模型预测或模型调用结果时，必须阻塞并写明原因，不能继续生成完成状态。

## 产物目录约定

每个 stage 统一使用如下结构：

```text
WORKSPACE_ROOT/stageN/
  nodes/<node-id>/
    USED_INPUTS.json
    DONE.json
    NODE_REPORT.md
  artifacts/<data-id>/
    ...
```

其中 `nodes/` 存放椭圆节点的执行记录，`artifacts/` 存放编号数据。禁止把编号数据目录当作节点目录。
