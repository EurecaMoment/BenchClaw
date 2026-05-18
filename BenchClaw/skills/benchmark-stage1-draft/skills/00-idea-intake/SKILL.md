# 00 idea 接收与边界冻结 Skill

## 节点定位

- 节点 ID：`00`
- 英文名：`idea-intake`
- 父节点：无，根节点
- 作用：把用户粗糙 benchmark idea 固定成不可篡改的 Stage1 输入基准，不做研究、不做拆解。

## 必读输入

- 读取 `input/user_idea.md` 与可选约束文件。

## 必写输出

- `stage1/00_idea/idea_card.md`
- `stage1/00_idea/scope_seed.json`

## 中间文件含义

完整字段、消费方和边界统一维护在仓库根目录的 `contracts/intermediate_files.md`；本节点只保留摘要：

- `idea_card.md`：冻结用户原始 idea、显式约束和开放问题的人读基准卡。
- `scope_seed.json`：把范围、对象、模态、硬约束和禁区编码成后续节点可解析的机器可读种子。

## 具体步骤

1. 读取 `input/user_idea.md`。
2. 保留用户原始表述，不替换研究目标。
3. 抽取：目标领域、期望 benchmark 类型、禁止条件、可用资源、用户显式强调的非人工/自动化要求。
4. 写出 `idea_card.md` 和 `scope_seed.json`。

## 质量门

通用质量门见 `contracts/quality_gates.md`；本节点专属质量门：

- 原始 idea 必须保留，不得被改写成新的研究目标。
- `scope_seed.json` 只能编码用户显式信息和约束，不得提前加入能力拆解或工具选择结论。
- 不做文献检索、能力拆解、仿真器推荐或标注工具推荐。
