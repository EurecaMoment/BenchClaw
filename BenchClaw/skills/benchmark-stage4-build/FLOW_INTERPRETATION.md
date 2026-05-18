# FLOW_INTERPRETATION — Stage4 手绘图解释

我把图解释为：

```text
09 初版模板集+指标集
18 真实图+半监督GT
19 旧benchmark图文+半监督GT
20 仿真器多模态数据+privileged GT
        ↓
模板契约规范化 + 证据池规范化
        ↓
模板-证据绑定
        ↓
对象/关系/能力/题型/干扰项选择
        ↓
小批量合成 + 灰度测试（本包按要求留空）
        ↓
质量过滤、选择策略、CTT/IRT/CDM/Scope hooks
        ↓
全量合成
        ↓
最终 benchmark artifact
```

注意：图中 CTT/IRT、CDM/Q-matrix、Qwen-scope、Gemma-scope、Llama-scope 都需要 pilot/model-response 或 scope activation 数据。由于小批量合成和灰度测试被要求留空，本包不会伪造这些数值，只输出 deferred hook 规范。
