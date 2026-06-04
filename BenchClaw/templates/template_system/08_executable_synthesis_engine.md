# 严格可执行合成引擎

入口：`tools/synthesize_static_vlm_benchmark.py`。

默认命令：

```bash
python tools/synthesize_static_vlm_benchmark.py \
  --input examples/uav_static_demo/sample_0001 \
  --output examples/uav_static_demo/generated_eval_dataset.jsonl \
  --template-set strict_core
```

关键默认值：

- `--template-set strict_core`：只跑 agent-safe 核心模板；
- `--drop-categories sky,cloud,clouds,road,ground,terrain,floor,ceiling,wall`：过滤背景/大平面；
- `--max-area-frac 0.35`：过滤占图过大的区域；
- deprecated 模板硬锁，即使指定也不会生成。

可选模板集：

- `strict_core`：默认生产集；
- `strict_depth`：有可靠 depth 时使用；
- `strict_all_supported`：字段齐全时使用全部非废弃模板。
