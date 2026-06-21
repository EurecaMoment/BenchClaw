---
name: benchclaw-stage4-small-batch-result-evaluation
description: Use for the specific BenchClaw subskill `stage4-small-batch-result-evaluation` only when its parent node explicitly dispatches to it.
---

# Subskill - 小批量合成数据集评测结果获取

对灰度小批量合成数据集进行抽样、外部模型推理、预测打分和结果汇总。该 subskill 参考 `/home/maqiang/uav_grey_eval.py` 的流程，但将通用评测逻辑沉淀到本目录，并把 API、API key、评测模型、模型难度层级放到独立用户配置文件。

## 用户配置文件

用户只修改：

```text
config/user_eval_config.json
```

配置项：

- `endpoint`: OpenAI-compatible chat completions 接口地址。
- `api_keys`: API key 空槽位，支持 `key1`、`key2`、`key3` 等命名。
- `model_key_map`: 将模型名、难度层级或 `*` 映射到 key 槽位。
- `tiers`: 本轮要评测的模型难度层级。
- `models`: 可选模型白名单；留空表示使用所选层级下全部模型。
- `model_groups`: 按难度层级组织的评测模型列表。
- `temperature`、`max_tokens`、`timeout`、`retries`、`parallel_per_key`: 推理参数。

也可以用环境变量 `EPHONE_KEY_1`、`EPHONE_KEY_2`、`EPHONE_KEY_3` 提供 key。命令行参数会覆盖配置文件中的同名值。

## 工具脚本

```text
scripts/grey_batch_eval.py
```

## tmux 后台实际评测监控硬约束

本 subskill 的抽样、外部模型推理、预测打分和结果汇总都必须后台 `tmux` 执行，并每 15 秒检查一次直到结束。尤其是 `infer-ephone` 会调用外部模型 API，严禁在前台长时间运行或只依赖聊天上下文输出。

1. 启动前必须创建 `WORKSPACE_ROOT/stage4/nodes/grey-batch-validation/run_logs/`。
2. 每个实际评测命令必须使用：

```text
tmux new-session -d -s <tmux_session_name> "<command> > <log_path> 2>&1; printf '\nEXIT_CODE:%s\n' \$? >> <log_path>"
```

3. `tmux_session_name` 建议格式：`benchclaw_s4_grey_batch_eval_<mode>_<YYYYMMDDHHMMSS>`；`prepare`、`infer-ephone`、`score` 可分别写入 `run_logs/small-batch-eval-prepare.log`、`run_logs/small-batch-eval-infer.log`、`run_logs/small-batch-eval-score.log`，监控记录写入同名 `.monitoring.jsonl`。
4. 启动后立即检查一次 `tmux has-session -t <tmux_session_name>`、`tmux capture-pane -pt <tmux_session_name>` 和 `tail -n 100 <log_path>`。
5. 只要会话仍存在，就必须每 15 秒检查一次状态；每次记录最近日志摘要、`sampled_gold.jsonl` 行数、`raw_inference/` 文件数、`predictions/` 行数、`scores/` item 级记录数、模型汇总表是否生成、失败/重试计数。
6. 会话结束后必须读取最终日志和 `EXIT_CODE`，校验 `sampled_gold.jsonl`、`questions_for_inference.jsonl`、`raw_inference/`、`predictions/`、`scores/`、`model_question_format_scores.csv/json`、`model_overall_scores.csv/json`；缺少 15 秒监控记录、最终日志、退出码或真实推理/评分产物时，不得向父节点报告完成。
7. 除非用户显式要求 smoke test，实际灰度评测不得用 `--dry-run`、placeholder prediction 或空预测文件冒充模型评测结果；使用外部已物化预测文件时，也必须 tmux 后台运行 `score` 并记录 15 秒监控。

主要模式：

```bash
python scripts/grey_batch_eval.py prepare \
  --dataset artifacts/data_20_grey_batch/items.jsonl \
  --out-dir artifacts/data_21_grey_eval_results/run_001 \
  --per-format 100
```

输出：

- `sampled_gold.jsonl`: 带答案的抽样评测集。
- `questions_for_inference.jsonl`: 去除 gold 字段后的外部推理题目。
- `prediction_template.jsonl`: 外部预测 JSONL 模板。
- `manifest.json`: 抽样配置和数据统计。

```bash
python scripts/grey_batch_eval.py infer-ephone \
  --gold artifacts/data_21_grey_eval_results/run_001/sampled_gold.jsonl \
  --out-dir artifacts/data_21_grey_eval_results/run_001/model_eval \
  --config config/user_eval_config.json
```

输出：

- `raw_inference/`: 每个模型、每个题目的原始 API 返回。
- `predictions/`: 每个模型的预测 JSONL。
- `scores/`: 每个模型的 item 级打分和 summary。
- `model_question_format_scores.csv/json`: 模型 x question_format 汇总。
- `model_overall_scores.csv/json`: 模型整体汇总。

```bash
python scripts/grey_batch_eval.py score \
  --gold artifacts/data_21_grey_eval_results/run_001/sampled_gold.jsonl \
  --pred artifacts/data_21_grey_eval_results/run_001/predictions/external_model.jsonl \
  --out-dir artifacts/data_21_grey_eval_results/run_001/external_score
```

用于给外部推理结果补打分。预测 JSONL 支持 `eval_id`、`id` 或 `item_id` 作为题目 id，支持 `prediction`、`pred`、`answer`、`model_answer`、`response`、`output` 作为预测字段。

## 完成证据

写入父节点报告前必须提供：

- tmux session name、完整命令、日志路径和 monitoring JSONL 路径；
- 每 15 秒监控记录摘要；
- 最终 `EXIT_CODE`；
- 每个模型的预测文件、score item 文件和 summary 文件计数；
- `model_question_format_scores.csv/json` 与 `model_overall_scores.csv/json` 路径。
