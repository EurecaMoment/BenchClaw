# Node Skill — 文献调研

## 输入

- `data_03_intent_expansion_doc`
- `data_04_retrieved_literature`

## 处理

1. 首先读取 `data_04_retrieved_literature/literature_index.jsonl`、`download_manifest.jsonl`、`paper_checksums.json`、`papers/`、`extracted_text/` 和 `reading_notes.md`；不得跳过本地文件核验。
2. 只有同时满足以下条件的论文才可进入综述证据池：`access_status: downloaded`、`reading_status: read_verified`、本地 PDF/HTML 原文存在且非空、提取文本存在且非空、sha256/文件大小已记录、阅读笔记包含章节或页码级证据。
3. 汇总相关 benchmark 的能力维度、题型、数据形态、指标与不足时，每条事实性结论都必须引用证据池中的 `paper_id`，并给出本地原文路径、页码或章节、关键文本片段位置；不得引用未下载论文、摘要页、搜索结果、二手博客、空链接或模型记忆。
4. 明确哪些结论来自已下载已阅读论文，哪些只是从用户意图或数据源卡得到的启发；启发不得伪装成文献结论。
5. 生成 `citation_audit.jsonl`：每条记录至少包含 `claim_id`、`claim_text`、`paper_id`、`local_paper_path`、`local_text_path`、`section_or_page`、`evidence_snippet`、`confidence`、`used_in_review_section`。找不到本地证据的 claim 必须删除或降级为非文献启发。
6. 生成 `used_papers.jsonl`：列出所有被综述实际引用的论文及其下载校验、阅读状态、可复用 benchmark 启发和限制。
7. 对 `data_04` 中不可访问、下载失败、文本提取失败或未读的候选论文，必须在综述中单列“未采用/不可引用文献”并说明原因；不得把这些条目写进主要证据或参考文献。
8. 若没有足够的已下载、已阅读、可本地核验的核心论文支撑综述，必须写 `BLOCKED.json` 与 `BLOCKED.md`，停止本节点；严禁用假论文、伪 DOI、伪 arXiv、伪页码或只看摘要的条目糊弄完成。
9. 产出后续能力维度划分可直接引用的综述文档；所有可被下游引用的文献结论都必须能通过 `citation_audit.jsonl` 追溯到本地原文。

## 输出

- `artifacts/data_07_literature_review/review.md`
- `artifacts/data_07_literature_review/citation_audit.jsonl`
- `artifacts/data_07_literature_review/used_papers.jsonl`
- 节点执行记录文件
