# Node Skill — 文献搜索

## 输入

- `data_02_rewritten_queries`
- `data_03_intent_expansion_doc`

## 处理

1. 按 query 检索与 benchmark、能力维度、任务形式、指标有关的论文、项目、数据集卡，优先选择论文官网、arXiv、ACL Anthology、OpenReview、CVF、ACM/IEEE 公开页、项目主页、数据集官方页等可追溯一手来源。
2. 对每篇可访问核心论文，必须真实下载原文 PDF 或官方 HTML 全文到本节点 artifact 目录，并提取可阅读文本；不得只依赖搜索结果、摘要页、引用页、二手博客或模型记忆。
3. 下载后必须实际阅读论文正文，至少覆盖摘要、引言、方法/任务定义、实验设置、数据集、指标、局限性/讨论；只读 abstract 不算完成。
4. `literature_index.jsonl` 中每条可访问论文必须记录：来源、题名、年份、链接、下载链接、本地原文路径、本地提取文本路径、阅读状态、已读章节、关键证据片段或页码、与本 benchmark 的关系、可复用的数据/任务/指标启发。
5. 对不可访问、缺下载入口、需要授权、下载失败或文本提取失败的记录，必须保留原始记录并显式标记 `access_status`、失败原因和尝试过的 URL/命令；不得自行替代、不得伪造已读证据。
6. 若没有成功下载并阅读至少一批与 benchmark 直接相关的核心文献，必须写 `BLOCKED.json` 与 `BLOCKED.md`，停止本节点，并说明需要的网络、授权或人工下载输入。

## 输出

- `artifacts/data_04_retrieved_literature/literature_index.jsonl`
- `artifacts/data_04_retrieved_literature/papers/`：下载的 PDF/HTML 原文
- `artifacts/data_04_retrieved_literature/extracted_text/`：从原文提取出的可检索文本
- `artifacts/data_04_retrieved_literature/reading_notes.md`：按论文记录真实阅读摘要、关键证据、可复用启发和未读/不可访问项
- 节点执行记录文件
