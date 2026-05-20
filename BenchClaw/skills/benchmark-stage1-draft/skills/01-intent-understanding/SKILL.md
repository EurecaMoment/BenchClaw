# 01 意图理解 Skill

全局路径约束：`BENCHCLAW_ROOT` 仅作只读输入；`WORKSPACE_ROOT` 是本次流程唯一总工作目录，所有写操作和流程产物只能落在其下。

## 节点定位

- 节点 ID：`01`
- 英文名：`intent-understanding`
- 父节点：00
- 作用：从 idea 中抽取评测对象、目标能力、边界、禁区和明显歧义，形成后续并行分支共用的意图理解。

## 必读输入

- 读取父节点 `00` 的 `DONE.json` 和其声明输出。

## 必写输出

- `stage1/01_intent/intent_interpretation.md`
- `stage1/01_intent/ambiguity_log.md`

## 中间文件含义

完整字段、消费方和边界统一维护在仓库根目录的 `contracts/intermediate_files.md`；本节点只保留摘要：

- `intent_interpretation.md`：把冻结 idea 解释成后续 `02`、`03` 和 `12` 共用的评测意图。
- `ambiguity_log.md`：登记不阻塞流程的歧义、默认假设和需要确认的问题。

## 具体步骤

1. 从 `00` 的 idea card 中解析 benchmark 意图。
2. 形成意图对象：被评测主体、目标能力、输入模态、输出形式、评测约束、失败模式。
3. 记录歧义，但不要阻塞流程；把歧义写入 `ambiguity_log.md`。
4. 输出 `intent_interpretation.md`，供 `02` 与 `03` 并行使用。

## 质量门

通用质量门见 `contracts/quality_gates.md`；本节点专属质量门：

- `intent_interpretation.md` 必须可供 `02` 和 `03` 并行读取，不依赖后续节点结论。
- 歧义必须进入 `ambiguity_log.md`，不能被隐式假设吞掉。
- 不得把意图理解直接写成最终能力维度或 benchmark 草稿。
