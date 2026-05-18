# 03 意图理解扩写文档 Skill

## 节点定位

- 节点 ID：`03`
- 英文名：`intent-expansion-doc`
- 父节点：01
- 作用：把意图扩写成可被文献分析、能力划分、模板设计共用的结构化文档。

## 必读输入

- 读取父节点 `01` 的 `DONE.json` 和其声明输出。

## 必写输出

- `stage1/03_intent_doc/expanded_intent.md`
- `stage1/03_intent_doc/construct_hypotheses.md`

## 中间文件含义

完整字段、消费方和边界统一维护在仓库根目录的 `contracts/intermediate_files.md`；本节点只保留摘要：

- `expanded_intent.md`：把意图扩写成文献分析、能力拆解和模板设计可用的结构化说明。
- `construct_hypotheses.md`：列出候选 construct 假设及其期望证据和证伪风险。

## 具体步骤

1. 读取 `01_intent/intent_interpretation.md`。
2. 扩写为结构化意图文档：construct、可测行为、输入输出、边界条件、预期证据类型。
3. 形成若干 construct hypotheses，供文献分析、能力拆解和模板设计使用；不要把它写成数据/仿真器或标注工具能力来源。
4. 输出 `expanded_intent.md` 与 `construct_hypotheses.md`。

## 质量门

通用质量门见 `contracts/quality_gates.md`；本节点专属质量门：

- construct hypothesis 必须标为假设，不能写成已验证能力维度。
- 扩写内容必须能回溯到 `01` 的意图理解或歧义记录。
- 不得引入用户 idea 不支持的新研究方向。
- 不做最终模板设计。
