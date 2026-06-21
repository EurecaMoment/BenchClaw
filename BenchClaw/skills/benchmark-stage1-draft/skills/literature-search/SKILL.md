---
name: benchclaw-stage1-literature-search
description: Use for the specific BenchClaw node skill `stage1-literature-search` only when its parent stage explicitly dispatches to it.
---

# Node Skill — 文献搜索

## 输入

- `data_02_rewritten_queries`
- `data_03_intent_expansion_doc`

## 处理

1. 按 query 检索与 benchmark、能力维度、任务形式、指标有关的论文、项目、数据集卡，优先选择论文官网、arXiv、ACL Anthology、OpenReview、CVF、ACM/IEEE 公开页、项目主页、数据集官方页等可追溯一手来源。
2. 对每篇可访问核心论文，必须真实下载原文 PDF 或官方 HTML 全文到本节点 artifact 目录，并提取可阅读文本；不得只依赖搜索结果、摘要页、引用页、二手博客、LLM 记忆或聊天上下文。
3. 论文必须能被本地文件证明：`papers/` 中存在非空 PDF/HTML，`extracted_text/` 中存在对应文本，`download_manifest.jsonl` 记录下载 URL、命令、HTTP 状态或工具输出、文件大小、sha256、下载时间和本地路径。没有本地原文文件的条目只能标为 `unavailable`/`failed`，不得标为已读或可引用。
4. 严禁编造论文、题名、作者、年份、DOI、arXiv ID、会议、链接、页码、实验结果或指标数字；无法核验的条目必须保留为候选或失败记录，并写明不能用于后续综述。
5. 下载后必须实际阅读论文正文，至少覆盖摘要、引言、方法/任务定义、实验设置、数据集、指标、局限性/讨论；只读 abstract、搜索 snippet 或 metadata 不算完成。
6. `literature_index.jsonl` 中每条可访问论文必须记录：`paper_id`、来源、题名、作者、年份、链接、下载链接、本地原文路径、本地提取文本路径、sha256、文件大小、`access_status: downloaded`、`reading_status: read_verified`、已读章节、关键证据片段或页码、与本 benchmark 的关系、可复用的数据/任务/指标启发。
7. `reading_notes.md` 必须按 `paper_id` 写真实阅读记录；每条结论必须能回指到本地原文路径、页码或章节、提取文本片段。禁止用“常识”“印象”“模型知道”替代引用。
8. 对不可访问、缺下载入口、需要授权、下载失败或文本提取失败的记录，必须保留原始记录并显式标记 `access_status`、失败原因和尝试过的 URL/命令；不得自行替代、不得伪造已读证据。
9. 若没有成功下载并阅读至少一批与 benchmark 直接相关的核心论文，必须写 `BLOCKED.json` 与 `BLOCKED.md`，停止本节点，并说明需要的网络、授权或人工下载输入；不得用假论文、伪引用或空 `literature_index.jsonl` 糊弄完成。

## 输出

- `artifacts/data_04_retrieved_literature/literature_index.jsonl`
- `artifacts/data_04_retrieved_literature/download_manifest.jsonl`：每次论文下载和文本提取的真实执行记录
- `artifacts/data_04_retrieved_literature/paper_checksums.json`：本地 PDF/HTML 与提取文本的 sha256、大小和路径
- `artifacts/data_04_retrieved_literature/papers/`：下载的 PDF/HTML 原文
- `artifacts/data_04_retrieved_literature/extracted_text/`：从原文提取出的可检索文本
- `artifacts/data_04_retrieved_literature/reading_notes.md`：按论文记录真实阅读摘要、关键证据、可复用启发和未读/不可访问项
- 节点执行记录文件
