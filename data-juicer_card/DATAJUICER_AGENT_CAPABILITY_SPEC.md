# Data-Juicer 能力说明文档（供大模型 Agent 灵活调用）

> 版本：v0.1  
> 适用对象：具备文件系统、Shell、Python、YAML 编辑、日志读取能力的大模型 Agent  
> 文档目的：让 Agent 能够判断什么时候使用 Data-Juicer、如何生成可执行配置、如何选择算子、如何调试与回退，以及如何把 Data-Juicer 嵌入数据构建、RAG、智能体轨迹清洗、多模态数据处理和 Benchmark 数据生产流水线。  
> 依据：用户提供的 README，以及其中链接到的 Data-Juicer 官方文档、算子池、Hub、Agents、分布式处理、导出、追踪、阿里云 PAI 页面和 Data-Juicer 2.0 论文页面。

---

## 1. 能力定位

Data-Juicer（简称 DJ）是面向基础模型时代的数据处理系统。它把数据清洗、过滤、去重、转换、合成、分析、追踪和导出组织为可组合的算子流水线。Agent 应将它视为一个“数据处理与质量控制工具箱”，而不是单一脚本。

### 1.1 一句话能力摘要

当任务涉及 **大规模文本/图像/音频/视频/多模态数据的清洗、规范化、去重、质量过滤、合成、抽取、RAG 预处理、智能体轨迹清洗、导出与追踪** 时，优先考虑调用 Data-Juicer。

### 1.2 典型使用价值

- 将原始数据转为训练、微调、RAG、评测或分析可用的数据集。
- 通过 YAML 配方记录数据处理过程，保证可复现、可审计、可版本管理。
- 使用 200+ 算子覆盖文本、图像、音频、视频、多模态和 Agent 交互数据。
- 从本机处理扩展到 Ray 分布式或云平台处理。
- 通过分析器和追踪器定位“哪些样本被改了、为什么被过滤、哪些算子影响最大”。

---

## 2. 何时调用 Data-Juicer

### 2.1 强推荐调用场景

Agent 遇到下列任务时，应优先使用 Data-Juicer：

| 任务意图 | 是否推荐 | 推荐能力 |
|---|---:|---|
| 清洗网页文本、HTML、链接、邮箱、IP、版权声明、异常 Unicode | 是 | Mapper 类文本清洗算子 |
| 过滤低质量语料，如过短、重复、乱码、特殊字符过多、停用词异常、困惑度异常 | 是 | Filter 类质量过滤算子 |
| 去重预训练语料、网页语料、RAG 文档、图片/视频样本 | 是 | Deduplicator；大规模时用 Ray 版本 |
| 构造 RAG 文档索引前的数据清理、分块、抽取、标签化 | 是 | text_chunk、extract、dedup、selector 等 |
| 清洗智能体交互日志、工具调用轨迹、多轮对话 bad case | 是 | agent_*、dialog_*、tool_success_tagger、usage_counter 等 |
| 做 PII 脱敏、隐私风险复查 | 是 | pii_redaction_mapper、pii_llm_suspect_mapper |
| 处理图像、视频、音频数据，如 caption、tag、检测、分割、抽帧、深度估计 | 是 | Image/Video/Audio/Multimodal Mapper 与 Filter |
| 从文本生成 QA、优化 query/response、构造偏好数据 | 是 | generate_qa、optimize_qa、pair_preference 等 |
| 对处理流程做可视化分析、统计分布、质量画像 | 是 | dj-analyze |
| 希望记录每个算子的样本级影响，用于审计和 Debug | 是 | Data Tracing |
| 数据量较大、单机处理慢、需要分布式处理 | 是 | Ray executor、ray_* deduplicator |
| 希望复用社区配方 | 是 | data-juicer-hub |

### 2.2 不建议调用场景

| 场景 | 原因 | 替代方案 |
|---|---|---|
| 只处理一两个字符串、一次性正则替换 | Data-Juicer 配置成本高于收益 | 直接 Python/awk/sed |
| 任务核心是模型训练、推理服务部署、评测打分而非数据处理 | Data-Juicer 不是训练框架本体 | LLaMA-Factory、Swift、EvalScope、训练脚本 |
| 需要人工标注策略设计，而非自动处理 | DJ 可辅助预处理，但不能代替标注规范 | 先写标注说明，再接入 DJ |
| 需要强业务语义判定但没有模型/API/GPU | 相关 LLM/VLM 算子需要 API、HF、vLLM 或 GPU 资源 | 先用 CPU 规则算子做粗筛 |

---

## 3. Agent 调用接口

Agent 可通过四类接口调用 Data-Juicer。

### 3.1 CLI：标准生产方式

适合可复现批处理。

```bash
uv pip install py-data-juicer
dj-process --config path/to/process.yaml
```

常用覆盖参数：

```bash
# 覆盖输入输出路径
dj-process --config config.yaml \
  --dataset_path ./input.jsonl \
  --export_path ./output/result.jsonl

# 开启追踪
dj-process --config config.yaml --open_tracer true --trace_num 50

# 仅追踪指定算子
dj-process --config config.yaml --open_tracer true \
  --op_list_to_trace clean_email_mapper,words_num_filter

# 保留 stats 字段，便于后续质量分析
dj-process --config config.yaml --keep_stats_in_res_ds true
```

### 3.2 YAML 配方：Agent 应优先生成的调用载体

最小结构：

```yaml
project_name: 'datajuicer-task'
dataset_path: './input.jsonl'
export_path: './outputs/result.jsonl'
np: 4

process:
  - clean_html_mapper: {}
  - clean_links_mapper: {}
  - text_length_filter:
      min_len: 10
      max_len: 10000
  - words_num_filter:
      lang: en
      tokenization: false
      min_num: 10
      max_num: 10000
```

Agent 生成 YAML 时必须确保：

1. `dataset_path` 指向真实存在的数据文件或目录。
2. `export_path` 指向可写路径；分布式模式下建议使用目录或按官方说明设置。
3. `process` 中每个算子名必须来自官方算子池或本地安装版本。
4. 参数名必须与当前版本算子参数一致；不确定时先查 `config_all.yaml` 或算子详情页。
5. 需要 GPU/API/vLLM/HF 模型的算子，应先检查环境变量、API Key、模型缓存和显存。

### 3.3 Python API：适合小样本原型验证

```python
from data_juicer.core.data import NestedDataset
from data_juicer.ops.filter import TextLengthFilter
from data_juicer.ops.mapper import WhitespaceNormalizationMapper

samples = NestedDataset.from_dict({
    "text": ["Short", "This passes the filter.", "Text   with   spaces"]
})

processed = samples.process([
    TextLengthFilter(min_len=10),
    WhitespaceNormalizationMapper()
])

for sample in processed:
    print(sample)
```

Agent 使用 Python API 的原则：

- 用于 10～1000 条样本的小规模探索、算子效果验证、单元测试。
- 不应用 Python API 替代正式批处理；正式处理应落到 YAML + `dj-process`。

### 3.4 Docker：适合隔离依赖与复现环境

```bash
docker run --rm \
  --privileged \
  --shm-size 256g \
  --network host \
  --gpus all \
  --name dj \
  -v <host_data_path>:<image_data_path> \
  -v ~/.cache/:/root/.cache/ \
  datajuicer/data-juicer:<version_tag> \
  dj-process --config /path/to/config.yaml
```

---

## 4. 输入与输出契约

### 4.1 输入数据

Data-Juicer 支持本地数据、远程 HuggingFace 数据、远程 arXiv 数据，以及复杂数据源的预处理工具。

常见本地格式：

- `jsonl`
- `json`
- `parquet`
- `csv`
- `tsv`
- `txt`
- `jsonl.gz` / `json.gz` 等压缩 JSON/JSONL 格式

示例：本地 JSONL

```yaml
dataset:
  configs:
    - type: local
      path: path/to/your/local/dataset.jsonl
      format: jsonl
```

示例：HuggingFace 数据集

```yaml
dataset:
  configs:
    - type: remote
      source: huggingface
      path: HuggingFaceFW/fineweb
      name: CC-MAIN-2024-10
      split: train
      limit: 1000
```

示例：多数据混合

```yaml
dataset:
  max_sample_num: 10000
  configs:
    - type: local
      weight: 1.0
      path: path/to/json/file
    - type: local
      weight: 1.0
      path: path/to/csv/file
```

示例：数据校验

```yaml
dataset:
  configs:
    - type: local
      path: path/to/data.json
validators:
  - type: required_fields
    required_fields:
      - text
      - metadata
      - language
    field_types:
      text: str
      metadata: dict
      language: str
```

### 4.2 输出数据

常见导出配置：

```yaml
export_path: ./outputs/result.jsonl
export_type: jsonl
export_shard_size: 0
export_in_parallel: false
keep_stats_in_res_ds: false
keep_hashes_in_res_ds: false
export_extra_args: {}
```

导出能力：

| 模式 | 常见格式 |
|---|---|
| Default Exporter | JSONL、JSON、Parquet |
| RayExporter | JSONL、JSON、Parquet、CSV、TFRecords、WebDataset、Lance |

大数据导出建议：

```yaml
export_path: ./outputs/result.jsonl
export_shard_size: 268435456   # 256MB per shard
```

---

## 5. 算子体系

Data-Juicer 的算子按 8 类组织。Agent 选择算子时，必须先判定任务属于哪类数据处理动作。

| 算子类型 | 数量（官方 main 文档） | 用途 | Agent 选择逻辑 |
|---|---:|---|---|
| aggregator | 4 | 对批量样本汇总，如总结实体属性 | 需要跨样本总结、聚合洞察时使用 |
| deduplicator | 10 | 识别和删除重复样本 | 数据重复、RAG 文档重复、网页语料重复时优先 |
| filter | 57 | 过滤低质量样本 | 需要“保留/剔除”样本时使用 |
| formatter | 8 | 加载和规范化源数据 | 原始文件格式复杂或多来源加载时使用 |
| grouper | 3 | 将样本分组或拆分批样本 | 需要 batch-level 处理或聚合前置时使用 |
| mapper | 123 | 修改、增强、抽取、转换样本 | 需要“改写/生成/抽取/脱敏/清洗”时使用 |
| pipeline | 2 | 数据集级别处理，如 Ray+vLLM 推理 | 大模型推理管道场景使用 |
| selector | 5 | 基于排序、频率、标签选择样本 | 需要抽样、top-k、字段范围选择时使用 |

算子标签含义：

| 标签类型 | 值 | 含义 |
|---|---|---|
| Modality | Text/Image/Audio/Video/Multimodal | 处理的数据模态 |
| Resource | CPU/GPU | 是否需要 GPU/CUDA |
| Usability | Alpha/Beta/Stable | 成熟度；Agent 默认优先 Stable |
| Model | API/vLLM/HF | 是否依赖 API 模型、vLLM 或 HuggingFace 模型 |

Agent 选算子优先级：

1. `Stable + CPU` 优先。
2. 规则类算子优先于 LLM/VLM 算子。
3. 数据规模较大时优先考虑 Ray 兼容算子。
4. 需要语义判断、生成、抽取时再使用 `API`、`HF`、`vLLM`、`GPU` 算子。
5. `Alpha` 算子只在没有稳定替代方案时使用，并必须开启追踪或小样本验证。

---

## 6. 能力分组与推荐算子

### 6.1 文本清洗与规范化

适用：网页抓取、PDF/HTML 转文本、RAG 文档、预训练文本、SFT 数据。

推荐算子：

| 目标 | 算子 |
|---|---|
| 清理 HTML | `clean_html_mapper` |
| 清理链接 | `clean_links_mapper` |
| 清理邮箱 | `clean_email_mapper` |
| 清理 IP | `clean_ip_mapper` |
| 修复 Unicode | `fix_unicode_mapper` |
| 删除重复句子 | `remove_repeat_sentences_mapper` |
| 删除过长词 | `remove_long_words_mapper` |
| 删除表格文本 | `remove_table_text_mapper` |
| 正则替换 | `replace_content_mapper` |
| 分句 | `sentence_split_mapper` |
| 分块 | `text_chunk_mapper` |
| 简繁/汉字转换 | `chinese_convert_mapper` |

典型 YAML：

```yaml
project_name: 'text-cleaning'
dataset_path: './raw.jsonl'
export_path: './outputs/cleaned.jsonl'
np: 8

process:
  - clean_html_mapper: {}
  - clean_links_mapper: {}
  - clean_email_mapper: {}
  - clean_ip_mapper: {}
  - fix_unicode_mapper: {}
  - remove_repeat_sentences_mapper: {}
  - text_length_filter:
      min_len: 20
      max_len: 20000
  - words_num_filter:
      lang: en
      tokenization: false
      min_num: 5
      max_num: 5000
```

### 6.2 质量过滤

适用：过滤乱码、低信息密度、异常重复、异常长度、低相关性样本。

推荐算子：

| 目标 | 算子 |
|---|---|
| 字母/数字比例 | `alphanumeric_filter` |
| 文本长度 | `text_length_filter` |
| 词数 | `words_num_filter` |
| token 数 | `token_num_filter` |
| 字符重复 | `character_repetition_filter` |
| 词重复 | `word_repetition_filter` |
| 停用词比例 | `stopwords_filter` |
| 特殊字符比例 | `special_characters_filter` |
| 困惑度过滤 | `perplexity_filter` |
| 违规/敏感词比例 | `flagged_words_filter` |
| 语言识别置信度 | `language_id_score_filter` |
| 字段规则过滤 | `specified_field_filter`、`specified_numeric_field_filter`、`general_field_filter` |
| LLM 条件过滤 | `llm_condition_filter`、`llm_analysis_filter` |
| 与验证任务相关性过滤 | `llm_task_relevance_filter` 或同类 LLM 相关性算子 |

典型 YAML：

```yaml
project_name: 'quality-filtering'
dataset_path: './raw.jsonl'
export_path: './outputs/filtered.jsonl'
np: 8
keep_stats_in_res_ds: true

process:
  - alphanumeric_filter:
      tokenization: false
      min_ratio: 0.0
      max_ratio: 0.9
  - character_repetition_filter:
      rep_len: 10
      min_ratio: 0.0
      max_ratio: 0.5
  - word_repetition_filter:
      lang: en
      tokenization: false
      rep_len: 10
      min_ratio: 0.0
      max_ratio: 0.5
  - flagged_words_filter:
      lang: en
      tokenization: false
      max_ratio: 0.0045
  - text_length_filter:
      min_len: 10
      max_len: 10000
  - words_num_filter:
      lang: en
      tokenization: false
      min_num: 10
      max_num: 10000
```

### 6.3 去重

适用：预训练语料、网页数据、RAG 文档、合成数据、图片/视频样本。

推荐算子：

| 场景 | 算子 |
|---|---|
| 文档精确去重 | `document_deduplicator` |
| 行级去重 | `document_line_deduplicator` |
| 文档近似去重 | `document_minhash_deduplicator` |
| SimHash 去重 | `document_simhash_deduplicator` |
| 图像精确去重 | `image_deduplicator` |
| 视频精确去重 | `video_deduplicator` |
| Ray 文档精确去重 | `ray_document_deduplicator` |
| Ray MinHash 去重 | `ray_bts_minhash_deduplicator` |
| Ray 图像/视频去重 | `ray_image_deduplicator`、`ray_video_deduplicator` |

单机示例：

```yaml
project_name: 'dedup-single-node'
dataset_path: './corpus.jsonl'
export_path: './outputs/deduped.jsonl'
np: 16

process:
  - document_minhash_deduplicator: {}
```

Ray 示例：

```yaml
project_name: 'dedup-ray'
dataset_path: './data/'
export_path: './outputs/dedup-ray/'
executor_type: 'ray'
ray_address: 'auto'
np: 64

process:
  - ray_bts_minhash_deduplicator: {}
```

### 6.4 RAG 数据预处理

适用：企业知识库、论文库、网页文档、技术文档、代码文档的 RAG 索引前处理。

推荐流程：

1. 格式加载与规范化。
2. HTML/链接/隐私信息清理。
3. 文档级去重。
4. 长度、特殊字符、重复率过滤。
5. 语义分块。
6. 抽取关键词、实体、关系或支持句。
7. 导出 JSONL/Parquet，供向量库或索引工具消费。

推荐算子：

- `clean_html_mapper`
- `clean_links_mapper`
- `clean_email_mapper`
- `pii_redaction_mapper`
- `document_minhash_deduplicator`
- `text_length_filter`
- `words_num_filter`
- `text_chunk_mapper`
- `extract_keyword_mapper`
- `extract_entity_attribute_mapper`
- `extract_entity_relation_mapper`
- `extract_support_text_mapper`

示例骨架：

```yaml
project_name: 'rag-prep'
dataset_path: './docs.jsonl'
export_path: './outputs/rag_chunks.jsonl'
np: 8
keep_stats_in_res_ds: true

process:
  - clean_html_mapper: {}
  - clean_links_mapper: {}
  - clean_email_mapper: {}
  - pii_redaction_mapper: {}
  - document_minhash_deduplicator: {}
  - text_length_filter:
      min_len: 50
      max_len: 50000
  - text_chunk_mapper: {}
  - extract_keyword_mapper: {}
```

### 6.5 智能体轨迹与对话数据处理

适用：Agent 工具调用日志、多轮对话、OpenAI/Anthropic 风格 messages、bad case 分析、智能体评测数据构造。

推荐算子：

| 目标 | 算子 |
|---|---|
| 规范化 Agent 对话字段 | `agent_dialog_normalize_mapper` |
| 生成 bad-case 信号 | `agent_bad_case_signal_mapper` |
| 工具相关性分析 | `agent_tool_relevance_mapper` |
| 汇总 agent 工具/技能洞察 | `agent_skill_insight_mapper` |
| LLM 生成 agent insight | `agent_insight_llm_mapper` |
| 工具成功率统计 | `tool_success_tagger_mapper` |
| token/usage 统计 | `usage_counter_mapper` |
| 用户意图识别 | `dialog_intent_detection_mapper` |
| 情绪识别 | `dialog_sentiment_detection_mapper` |
| 澄清质量 | `dialog_clarification_quality_mapper` |
| 指代消解质量 | `dialog_coreference_mapper` |
| 错误恢复质量 | `dialog_error_recovery_mapper` |
| 记忆一致性 | `dialog_memory_consistency_mapper` |
| 非重复性 | `dialog_non_repetition_mapper` |
| 主动性 | `dialog_proactivity_mapper` |
| PII 脱敏 | `pii_redaction_mapper`、`pii_llm_suspect_mapper` |

示例骨架：

```yaml
project_name: 'agent-log-cleaning'
dataset_path: './agent_logs.jsonl'
export_path: './outputs/agent_logs_cleaned.jsonl'
np: 4
open_tracer: true
trace_num: 20
trace_keys:
  - sample_id
  - source_file

process:
  - agent_dialog_normalize_mapper: {}
  - usage_counter_mapper: {}
  - tool_success_tagger_mapper: {}
  - pii_redaction_mapper: {}
  - agent_bad_case_signal_mapper: {}
```

Agent 注意事项：

- 如果输入是 OpenAI/Anthropic 风格 messages，应先做字段探查，确认 `messages`、`choices`、`usage`、`tool_calls` 等字段是否存在。
- 对 `Alpha` 的 dialog/agent 质量算子，必须先小样本运行并人工抽查。
- 涉及隐私信息时，先脱敏再做语义分析。

### 6.6 图像与多模态数据处理

适用：图文对、VLM 数据、图像 Benchmark、合成图像质量控制。

推荐算子：

| 目标 | 算子 |
|---|---|
| 图像质量/美学过滤 | `image_aesthetics_filter` |
| 图像纵横比过滤 | `image_aspect_ratio_filter` |
| 人脸数量/比例过滤 | `image_face_count_filter`、`image_face_ratio_filter` |
| NSFW 图像过滤 | `image_nsfw_filter` |
| 图像 pair 相似度过滤 | `image_pair_similarity_filter` |
| 图像 caption | `image_captioning_mapper` |
| 目标检测 | `image_detection_yolo_mapper` |
| 图像分割 | `image_segment_mapper` |
| 图像标签 | `image_tagging_mapper`、`image_tagging_vlm_mapper` |
| 人脸模糊 | `image_face_blur_mapper` |
| 背景移除 | `image_remove_background_mapper` |
| 人体关键点 | `image_mmpose_mapper` |
| 单图 3D 人体网格 | `image_sam_3d_body_mapper` |
| VQA/MLLM 推理 | `mllm_mapper` |
| 图像生成 | `image_diffusion_mapper`、`sdxl_prompt2prompt_mapper` |

示例骨架：

```yaml
project_name: 'image-vlm-prep'
dataset_path: './image_samples.jsonl'
export_path: './outputs/image_vlm_cleaned.jsonl'
np: 4

process:
  - image_aspect_ratio_filter: {}
  - image_nsfw_filter: {}
  - image_captioning_mapper: {}
  - image_tagging_mapper: {}
```

### 6.7 视频与具身智能数据处理

适用：具身智能 Benchmark、机器人/自动驾驶/UGV 视频、视频理解、视频问答、仿真器轨迹视频。

推荐算子：

| 目标 | 算子 |
|---|---|
| 视频去重 | `video_deduplicator`、`ray_video_deduplicator` |
| 视频时长过滤 | `video_duration_filter` |
| 视频纵横比过滤 | `video_aspect_ratio_filter` |
| 视频运动分数过滤 | `video_motion_score_filter`、`video_motion_score_raft_filter`、`video_motion_score_ptlflow_filter` |
| 视频水印过滤 | `video_watermark_filter` |
| 视频 NSFW 过滤 | `video_nsfw_filter` |
| 视频帧-文本相似度过滤 | `video_frames_text_similarity_filter` |
| 视频抽帧 | `video_extract_frames_mapper` |
| 视频人脸模糊 | `video_face_blur_mapper` |
| 视频 caption | `video_captioning_from_frames_mapper`、`video_captioning_from_video_mapper`、`video_captioning_from_audio_mapper`、`video_captioning_from_summarizer_mapper`、`video_captioning_from_vlm_mapper` |
| 深度估计 | `video_depth_estimation_mapper` |
| 相机标定/相机姿态 | `video_camera_calibration_static_deepcalib_mapper` 及相关具身视频算子 |
| 3D/场景结构抽取 | `vggt_mapper` |

具身智能/Benchmark 流水线建议：

```yaml
project_name: 'embodied-video-cleaning'
dataset_path: './embodied_videos.jsonl'
export_path: './outputs/embodied_video_cleaned.jsonl'
np: 4
open_tracer: true
trace_num: 20

process:
  - video_duration_filter: {}
  - video_motion_score_filter: {}
  - video_extract_frames_mapper: {}
  - video_captioning_from_frames_mapper: {}
```

Agent 注意事项：

- 视频/图像相关算子经常需要 GPU、HF 模型、vLLM 或第三方依赖。
- 大规模视频数据处理前，应先抽样验证依赖和输出字段。
- 对 Benchmark 生成流程，应把 Data-Juicer 作为“数据清洗/质量闸门/灰度评测前置环节”，不要直接让它替代 Benchmark 的指标评测。

### 6.8 音频数据处理

推荐算子：

| 目标 | 算子 |
|---|---|
| 音频时长过滤 | `audio_duration_filter` |
| 音频 SNR 过滤 | `audio_nmf_snr_filter` |
| FFmpeg 音频处理 | `audio_ffmpeg_wrapped_mapper` |
| 视频音频 caption | `video_captioning_from_audio_mapper` |

### 6.9 数据合成、后训练数据与偏好数据

适用：SFT、DPO/RLHF、问答生成、prompt 优化、领域指令数据扩展。

推荐算子：

| 目标 | 算子 |
|---|---|
| 从文本生成 QA | `generate_qa_from_text_mapper` |
| 从示例生成 QA | `generate_qa_from_examples_mapper` |
| 优化 QA | `optimize_qa_mapper` |
| 优化 query | `optimize_query_mapper` |
| 优化 response | `optimize_response_mapper` |
| 优化 prompt | `optimize_prompt_mapper` |
| 构造偏好 pair | `pair_preference_mapper` |
| 英文增强 | `nlpaug_en_mapper`、`sentence_augmentation_mapper` |
| 中文增强 | `nlpcda_zh_mapper` |
| LLM 抽取结构字段 | `llm_extract_mapper` |
| 文本标签生成 | `text_tagging_by_prompt_mapper` |

---

## 7. 推荐 Agent 决策流程

### 7.1 总流程

```text
用户任务
  ↓
判断是否是数据处理任务
  ↓
读取 README/官方文档/本地版本算子列表
  ↓
探查输入数据：格式、字段、样本量、模态、隐私风险、资源需求
  ↓
选择处理目标：清洗 / 过滤 / 去重 / 抽取 / 合成 / 分析 / 导出
  ↓
生成 YAML 配方
  ↓
小样本灰度运行
  ↓
读取输出样例、日志、trace、stats
  ↓
修正参数或替换算子
  ↓
全量运行
  ↓
生成质量报告和可复现实验记录
```

### 7.2 Agent 的最小行为规范

Agent 在调用 Data-Juicer 前必须完成：

1. 识别输入文件路径和格式。
2. 抽样读取 3～20 条样本，确认字段名。
3. 判断数据模态：文本、图像、音频、视频、多模态、Agent 轨迹。
4. 判断是否存在 PII、版权、NSFW、重复、低质量、字段缺失风险。
5. 判断资源：CPU、GPU、API Key、HF/vLLM 模型、本地缓存、磁盘空间。
6. 生成 YAML，并注明每个算子选择理由。
7. 先运行小样本或低成本配置，再全量处理。
8. 开启追踪或保留 stats，用于调参和审计。

### 7.3 Agent 的资源选择策略

| 条件 | 执行策略 |
|---|---|
| 数据量小于数十万条、主要是 CPU 文本清洗 | 单机 `dj-process` |
| 数据量较大但只做简单清洗 | 提高 `np`，优先单机多进程 |
| 需要大规模去重或 TB 级数据 | Ray executor + ray_* deduplicator |
| 图像/视频/MLLM/VLM 算子 | 检查 GPU、CUDA、模型缓存、显存 |
| LLM API 算子 | 检查 API Key、成本、速率限制 |
| 需要可审计处理 | `open_tracer: true`，保留 stats/hash |
| 云上 PAI/DLC | 镜像必须包含 `dj-process`；单节点用 default，分布式用 `executor_type: ray` |

---

## 8. 分析、追踪与调试能力

### 8.1 数据分析：`dj-analyze`

用于查看数据质量统计分布、不同 stats 之间的相关性，以及过滤器产生的统计指标。

```bash
dj-analyze --config demos/analyze_simple/analyzer.yaml
```

自动分析小样本：

```bash
dj-analyze --auto --dataset_path xx.jsonl --auto_num 1000
```

适用场景：

- 不知道该设置哪些过滤阈值。
- 想看长度、重复率、特殊字符比例等指标分布。
- 希望先用统计画像指导后续 YAML 配方。

### 8.2 样本级追踪：Data Tracing

开启方式：

```yaml
open_tracer: true
op_list_to_trace: []
trace_num: 10
trace_keys:
  - sample_id
  - source_file
```

命令行方式：

```bash
dj-process --config config.yaml --open_tracer true --trace_num 50
```

输出位置：

```text
{work_dir}/trace/
├── sample_trace-clean_email_mapper.jsonl
├── sample_trace-words_num_filter.jsonl
├── duplicate-document_deduplicator.jsonl
└── ...
```

Agent 应读取 trace 并回答：

- 哪些样本被过滤？
- 哪些字段被修改？
- 哪个算子造成最大数据损失？
- 是否存在误删、过清洗、字段破坏？
- 是否需要回退某个算子或放宽阈值？

---

## 9. 分布式处理与云上运行

### 9.1 Ray 模式

安装分布式依赖：

```bash
uv pip install -v -e .
uv pip install -v -e ".[dist]"
```

启动 Ray：

```bash
ray start --head
ray start --address='{head_ip}:6379'
```

配置：

```yaml
executor_type: 'ray'
ray_address: 'auto'
```

运行：

```bash
dj-process --config demos/process_on_ray/configs/demo.yaml
```

注意：

- 多机运行时，所有节点必须能访问同一份输入数据和输出路径，例如 NAS、共享文件系统、对象存储挂载。
- Ray 去重算子与单机去重算子不同，名称通常带 `ray_` 前缀。
- 大规模文件过少时，可能需要切分数据文件以提高并行度。

### 9.2 阿里云 PAI/DLC

Agent 在 PAI/DLC 上生成任务时应遵循：

- 镜像中必须预装 Data-Juicer，并包含 `dj-process` 命令。
- 单节点任务：配置中 `executor_type` 设为 `default` 或省略。
- 分布式任务：配置中 `executor_type` 必须设为 `ray`。
- `dataset_path` 应是数据存储挂载到容器内的路径。
- `export_path` 是处理结果输出路径；分布式任务中应按平台要求设置。
- 分布式资源：Head 节点数为 1，Worker 至少 1；Head 内存需满足平台要求。

---

## 10. 社区配方与 Agent 自举能力

### 10.1 data-juicer-hub

Hub 提供社区配方和最佳实践。Agent 在不确定具体配方时，可以优先检索 Hub 中是否已有相似任务。

调用方式：

```bash
git clone https://github.com/datajuicer/data-juicer-hub.git
dj-process --config <root-of-data-juicer-hub>/demo/process.yaml \
  --dataset_path <your-dataset-path>
```

Agent 使用策略：

1. 先搜索 Hub 是否有近似任务配方。
2. 拷贝最接近的 YAML。
3. 只修改 `dataset_path`、`export_path`、字段名、阈值和少量算子。
4. 保留原配方来源，便于审计。

### 10.2 data-juicer-agents

Data-Juicer Agents 是面向 Agentic Data Processing 的组件集合，包含 Copilot、CLI、Tools、Skills、交互式配方构建等方向。Agent 可以将其理解为 Data-Juicer 的“自然语言数据处理助手生态”。

使用建议：

- 用户要求“根据自然语言生成 Data-Juicer 配方”时，可参考 Agents 的思路：先规划，再生成 YAML，再运行，再读取反馈。
- 用户要求“智能体自动选择算子”时，应采用软编排：根据任务目标和数据样例选择算子，而不是把所有算子都堆进 pipeline。
- 对未知数据处理需求，优先产出小样本灰度 YAML，而不是直接全量运行。

---

## 11. 面向 Benchmark/具身智能流水线的集成建议

在自动化 Benchmark 构建流程中，Data-Juicer 适合放在“原始样本生成之后、评测集定稿之前”的数据质量闸门。

推荐位置：

```text
Stage 1: Benchmark 草稿/能力维度/任务模板
Stage 2: 初始样本或轨迹生成
Stage 3: Data-Juicer 数据清洗与质量过滤
Stage 4: 模板一致性检查与结构校验
Stage 5: 灰度评测与全量评测
Stage 6: 过程质量分析与流水线反思
```

Data-Juicer 在该流程中的职责：

- 清理异常字段、空文本、乱码、重复样本。
- 对文本问题、答案、解释、metadata 做长度与结构过滤。
- 对图像/视频样本做时长、纵横比、质量、相似度、去重过滤。
- 对具身视频做抽帧、caption、运动/深度/相机相关预处理。
- 对 Agent 轨迹做工具成功率、bad case 信号、usage 统计。
- 输出 stats 和 trace，作为过程质量度量的证据。

它不应替代：

- Benchmark 任务定义。
- 指标代码的正确性验证。
- 真实模型评测。
- 人工抽样审核。
- 单元测试、集成测试、灰度测试本身。

---

## 12. Agent 可执行能力卡

```yaml
capability_id: datajuicer.data_processing
name: Data-Juicer Data Processing Capability
version: 0.1
primary_interface: yaml_plus_cli

when_to_use:
  - raw dataset cleaning
  - text/image/audio/video/multimodal filtering
  - dataset deduplication
  - RAG preprocessing
  - agent trajectory cleaning
  - synthetic QA or preference data preparation
  - data quality analysis and traceable processing

when_not_to_use:
  - trivial one-off string edit
  - pure model training
  - pure benchmark scoring
  - manual annotation guideline design

required_inputs:
  - dataset_path
  - export_path
  - data_modality
  - sample_schema
  - processing_goal

optional_inputs:
  - resource_budget
  - cpu_workers
  - gpu_available
  - api_keys
  - need_tracing
  - need_distributed
  - target_format
  - quality_thresholds

outputs:
  - process.yaml
  - processed dataset
  - trace files if enabled
  - stats fields if kept
  - run log
  - quality report

execution_steps:
  - inspect_sample_schema
  - choose_operator_groups
  - generate_yaml
  - run_small_sample
  - inspect_output_and_trace
  - revise_yaml
  - run_full_dataset
  - summarize_quality_report

safety_and_quality_gates:
  - verify paths before run
  - prefer stable CPU operators
  - run small sample first
  - enable tracer for destructive operations
  - preserve original data
  - never overwrite raw dataset
  - log config and command
  - report removed sample ratio
```

---

## 13. Agent 输出报告模板

每次调用 Data-Juicer 后，Agent 应输出如下报告：

```markdown
# Data-Juicer 处理报告

## 输入
- 输入路径：
- 输出路径：
- 数据格式：
- 样本量：
- 字段：

## 使用配置
- 配置文件：
- 执行命令：
- 执行模式：default / ray
- worker 数：
- GPU/API 依赖：

## 算子列表与选择理由
| 顺序 | 算子 | 类型 | 选择理由 | 风险 |
|---:|---|---|---|---|

## 结果摘要
- 输出文件：
- 保留样本数：
- 删除样本数：
- 删除比例：
- 关键 stats：

## Trace 摘要
- 被修改样本示例：
- 被过滤样本示例：
- 可能误删风险：
- 建议调整参数：

## 结论
- 是否可进入下一阶段：是/否
- 需要人工抽查的样本：
- 需要回退或修改的算子：
```

---

## 14. 常见失败与处理策略

| 失败现象 | 可能原因 | Agent 处理 |
|---|---|---|
| `dj-process` 找不到 | 未安装或环境未激活 | 检查 conda/venv，执行 `uv pip install py-data-juicer` |
| 输入文件加载失败 | 格式不支持、路径错误、JSONL 坏行 | 检查路径；开启 lenient JSONL；转为 JSONL/Parquet |
| CUDA OOM | GPU 算子显存不足、并发过高、memory 未声明 | 降低 `np`；改 CPU 算子；声明 memory；抽样运行 |
| API 算子失败 | API Key 缺失、限流、网络失败 | 检查环境变量；退回规则算子或 HF/vLLM 本地模型 |
| 输出为空 | 过滤阈值过严或字段名不匹配 | 查看 trace；放宽阈值；检查 text/image/video 字段名 |
| 处理过慢 | 单机资源不足、模型下载慢、大文件未切分 | 开启缓存；提高 np；切分数据；Ray 模式 |
| Ray 多机读不到数据 | 节点未共享输入/输出路径 | 使用 NAS/共享盘/对象存储挂载 |
| 清洗破坏字段 | Mapper 作用字段不正确 | 小样本追踪；限制作用字段；回退算子 |

---

## 15. 推荐默认策略

Agent 在没有更多约束时，采用以下默认策略：

1. **先读样本，不盲跑。**
2. **先规则算子，后模型算子。**
3. **先小样本灰度，后全量处理。**
4. **默认不覆盖原始数据。**
5. **默认保留配置文件和运行日志。**
6. **会删除样本的任务必须开启追踪或保留 stats。**
7. **如果是 Benchmark 数据，Data-Juicer 只负责清洗和质量闸门，不负责最终评测结论。**
8. **如果是 Agent 轨迹数据，先规范化 schema，再做质量分析和 bad case 处理。**
9. **如果是大规模去重，优先考虑 Ray 版本去重算子。**
10. **如果算子参数不确定，先查当前安装版本的 `config_all.yaml`、官方算子详情页或单元测试。**

---

## 16. 访问过的主要来源

- Data-Juicer 官方主页：<https://datajuicer.github.io/data-juicer/zh_CN/main/index_ZH.html>
- Data-Juicer GitHub：<https://github.com/datajuicer/data-juicer>
- Operator Schemas：<https://datajuicer.github.io/data-juicer/en/main/docs/Operators.html>
- Quick Start：<https://datajuicer.github.io/data-juicer/en/main/docs/tutorial/QuickStart.html>
- Dataset Configuration Guide：<https://datajuicer.github.io/data-juicer/en/main/docs/DatasetCfg.html>
- Distributed Data Processing：<https://datajuicer.github.io/data-juicer/en/main/docs/Distributed.html>
- Dataset Export：<https://datajuicer.github.io/data-juicer/en/main/docs/Export.html>
- Data Tracing：<https://datajuicer.github.io/data-juicer/en/main/docs/Tracing.html>
- data-juicer-hub：<https://github.com/datajuicer/data-juicer-hub>
- data-juicer-agents：<https://github.com/datajuicer/data-juicer-agents>
- Data-Juicer 2.0 论文：<https://arxiv.org/abs/2501.14755>
- 阿里云 PAI 快速提交 DataJuicer 任务：<https://www.alibabacloud.com/help/zh/pai/user-guide/quickly-submit-a-datajuicer-task>
