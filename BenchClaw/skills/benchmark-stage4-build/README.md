# benchclaw_stage4_opencode_ready_skill_pack

Stage4 的 Opencode-ready DAG Skill 包。

本包按手绘图解释 Stage4：`09/18/19/20` 为并行根节点，`33 小批量合成` 与 `34 灰度测试` 按要求留空，最终输出 `37-benchmark-artifact-pack`。

快速检查：

```bash
python scripts/validate_dag.py dag.json
python scripts/ready_set_runner.py --workspace WORKSPACE_ROOT
```
