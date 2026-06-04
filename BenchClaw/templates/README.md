# BenchClaw Agent-Safe Fixed Template Library

这是严格修好后的模板库，不再要求你手工判断哪些模板能用。

默认给 agent 使用：

```bash
python tools/synthesize_static_vlm_benchmark.py \
  --input examples/uav_static_demo/sample_0001 \
  --output /tmp/benchclaw_strict_eval.jsonl \
  --template-set strict_core
```

关键文件：

- `template_library/benchclaw_fixed_template_registry.yaml`：agent 选择入口。
- `template_library/templates_fixed_strict.md`：全部 100 个模板的修正后处理结果。
- `configs/static_synthesis.default.json`：默认只跑 `strict_core`。
- `tools/validate_strict_template_library.py`：检查三选不可答、裸数值、GT 泄漏、废弃模板是否被锁定。

默认核心模板数：16。深度增强模板总数：29。全部可选模板数：85。废弃锁定模板数：15。

硬规则：禁止三选不可答；数值题全部区间化；禁止输出隐藏 object_id/depth_median；禁止题干出现 GT 字段；实例题必须有 overlay 标注。
