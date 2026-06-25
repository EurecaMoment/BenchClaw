---
name: benchclaw-root
description: Use as the single BenchClaw entry skill. It should immediately delegate to the pipeline skill and never inline Stage1-Stage5 logic itself.
---

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

## Opencode Skill Dispatch Contract

在 opencode 中，本入口 skill 只负责做一件事：显式调用 `benchclaw-pipeline`。执行时必须通过 `skill(name="benchclaw-pipeline")` 或 `/benchclaw-pipeline` 进入 pipeline，不要把 Stage1 到 Stage5 的内容直接内联到当前对话里。

所有下游 stage skill、node skill 与 nested subskill 必须继续触发 opencode 子 agent 流程：

- Stage1 到 Stage5 manager 必须由 `BENCHCLAW_ROOT/opencode.json` 中 `subtask: true` 的 `/benchclaw-stage1` 到 `/benchclaw-stage5` 命令派发。
- 每个 `skills/<node-id>/SKILL.md` 和 `subskills/<subskill-id>/SKILL.md` 必须由 `/benchclaw-subskill` 派发；该命令绑定 `mode: "subagent"` 的 `child-skill-module-runner`。
- 父级只传冻结路径、目标 SKILL 路径、注册 skill 名、输入/输出 artifact 路径和依赖判据；子 agent 只回传结构化摘要、artifact 路径和 blockers。

### Required child skill

- `benchclaw-pipeline`

### Context return protocol

子 skill 返回给本入口时，只保留以下结构化摘要：

```json
{
  "skill_name": "benchclaw-pipeline",
  "status": "READY | DONE | BLOCKED",
  "workspace_root": "...",
  "current_stage": "stage1 | stage2 | stage3 | stage4 | stage5 | pipeline",
  "artifacts": {},
  "quality_gates": {},
  "blocking_issues": [],
  "summary": "..."
}
```

不要把子 skill 的长日志、完整 tool history、长文件正文或中间推理轨迹继续回灌到当前上下文。

## 启动规则

1. 先通过 opencode `skill` 工具调用 `benchclaw-pipeline` 或执行 `/benchclaw-pipeline`，不要只把 `benchmark-pipeline/SKILL.md` 当作普通文本路径。
2. 按 pipeline skill 冻结 `PROJECT_ROOT`、`BENCHCLAW_ROOT`、`WORKSPACE_PARENT`、`WORKSPACE_ROOT`，且 `WORKSPACE_ROOT` 必须严格解析为 `PROJECT_ROOT/workspaces/workspace{I}`。
3. 只把五个 stage 当作大阶段顺序调用；stage 内部节点必须由各自的 `dag.json` 和 ready-set 规则调度。
4. 手绘图中的椭圆才是 DAG 节点；带编号的内容是中间流动数据，不是节点。用户输入与结束状态也不是节点。
5. 所有写入只能落在本次 `WORKSPACE_ROOT` 下；`BENCHCLAW_ROOT` 只读。
6. 缺少真实输入、真实采集结果、真实标注结果、真实 GT、真实模型预测或模型调用结果时，必须阻塞并写明原因，不能继续生成完成状态。
7. 如果某项任务预计执行时间较长、可能等待外部下载/推理/训练/仿真/评测、或结束时间不确定，必须使用 `tmux` 启动后台会话执行，不得长期占用前台 shell；启动后要把 stdout/stderr 重定向到 workspace 日志文件，并定期监控会话与日志进展，避免因超时、断线或前台终止拿不到数据。
8. 长任务默认必须先用 `tmux new-session -d -s <session_name> "<command> > <log> 2>&1"` 启动，再用 `tmux has-session`、`tmux capture-pane`、`tail -f` 等方式周期性查看进度；若未采用 tmux，必须在节点报告中说明为什么该任务确定会在很短时间内完成。

## 产物目录约定

每个 stage 统一使用如下结构：

```text
WORKSPACE_ROOT/stageN/
  nodes/<node-id>/
    USED_INPUTS.json
    DONE.json
    NODE_REPORT.md
    run_logs/
      <task>.log
  artifacts/<data-id>/
    ...
```

其中 `nodes/` 存放椭圆节点的执行记录，`artifacts/` 存放编号数据。禁止把编号数据目录当作节点目录。
