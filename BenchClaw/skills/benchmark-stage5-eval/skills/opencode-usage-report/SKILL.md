---
name: benchclaw-stage5-opencode-usage-report
description: Use for BenchClaw stage5 when the user asks to report opencode token/cost usage for the latest parent session, including subagent session consumption.
---

## Opencode 子 agent 触发契约

本文件是 BenchClaw child skill module。父级 stage、node 或 pipeline 调度到本文件时，必须通过 opencode 命令 `/benchclaw-subskill` 启动隔离子 agent；该命令在 `BENCHCLAW_ROOT/opencode.json` 中配置为 `subtask: true`，并绑定 `mode: "subagent"` 的 `child-skill-module-runner`。禁止父级 manager 直接在自己的对话上下文中内联执行本文件步骤。

调用 `/benchclaw-subskill` 时必须传入：目标 `SKILL.md` 绝对路径、注册 skill 名、冻结的 `PROJECT_ROOT` / `BENCHCLAW_ROOT` / `WORKSPACE_PARENT` / `WORKSPACE_ROOT`、当前 node 或 work_unit id、已满足的输入 artifact 路径、期望输出 artifact 路径、父级 DAG 依赖与完成判据。子 agent 只返回 `status`、artifact 路径、证据摘要和 blockers，不回灌长日志或完整中间内容。

如果当前执行上下文不是 `/benchclaw-subskill` 产生的 `child-skill-module-runner` 子 agent，本文件不得继续执行；应立即返回 `BLOCKED`，说明必须由父级使用 `/benchclaw-subskill` 重新派发。

# Node/Utility Skill — OpenCode 消耗报告

## 用途

生成最近一个 opencode 父 session 的消耗报告，并按直接子 agent 汇总其递归子树的 token 与 cost。该 skill 是 Stage5 最后节点 `full-evaluation` 完成全部评测任务后的收口审计工具，不改变 Stage5 DAG 依赖，也不得替代真实模型评测结果。

## 脚本

使用内置脚本：

```bash
python3 "$BENCHCLAW_ROOT/skills/benchmark-stage5-eval/skills/opencode-usage-report/scripts/opencode_parent_session_report.py"
```

可选参数：

- `--current`：优先从当前任务 session id 环境变量读取，读不到时回退到 opencode 数据库最新 session，并同时报告该 session 与其父 session/subagent 树。
- `--session-id <session_id>`：显式指定当前任务 session id。
- `--latest-parent`：只按最新父 session 生成报告，保留旧的父 session 口径。
- `--details`：额外打印父 session 树中每个 descendant session 的明细。
- `--json`：输出机器可读 JSON。
- `--db /path/to/opencode.db`：显式指定 opencode SQLite 数据库；默认读取 `OPENCODE_DB` 或 `~/.local/share/opencode/opencode*.db` 中最新数据库。

## 输出口径

- 使用 `--current` 时，当前任务 session id 的来源顺序为：`BENCHCLAW_OPENCODE_SESSION_ID`、`OPENCODE_SESSION_ID`、`OPENCODE_CURRENT_SESSION_ID`、`SESSION_ID`、数据库中 `time_updated` 最新 session。
- JSON 输出包含 `selection.current_session_id`、`selection.source`、`current_session`、`parent`、`total` 与 `subagents`。
- `--latest-parent` 选择 `parent_id is null` 且 `time_updated` 最新的父 session。
- 总量包含父 session 本身与所有递归子 session。
- 子 agent 汇总以父 session 的直接子 session 为分组，组内包含该子 session 及其递归后代。
- `Total = input + output + reasoning + cache_read + cache_write`。
- `Cache` 展示为 `cache_read + cache_write`。

## 使用要求

1. 当用户要求查看 Stage5 执行过程、父 session、子 agent 或 opencode 消耗时，优先使用此脚本。
2. `full-evaluation` 完成全部评测任务后、写 `DONE.json` 前，必须使用 `--current` 运行此脚本，并将 JSON 与文本报告保存到 `WORKSPACE_ROOT/stage5/artifacts/data_23_evaluation_report/`。
3. 若用户要求“最近一个父 session”，运行脚本时传入 `--latest-parent`。
4. 若用户指定数据库或 session 环境，传入 `--db` 或先设置 `OPENCODE_DB`。
5. 报告结果只能作为运行审计/成本统计，不可作为 `metrics.json`、`prediction_audit.jsonl` 或 Stage5 gate 的替代证据。
