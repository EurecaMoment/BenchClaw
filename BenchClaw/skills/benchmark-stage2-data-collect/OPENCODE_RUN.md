# OPENCODE_RUN — Stage2 数据采集执行协议

## 一句话原则

你正在执行的是 **DAG**，不是编号串行流程。  
同一 ready-set 中的节点应并行启动 subagent；无法并行时也只能做 ready-set 降级，不能改依赖。

---

## 1. 启动前检查

```bash
python scripts/validate_dag.py dag.json
python scripts/ready_set_runner.py --workspace WORKSPACE_ROOT
```

预期初始输出：

```text
READY: 13 14
```

---

## 2. 推荐 subagent 调度

### Round A：入口与仿真器 Skill 发现并行

```text
Start subagent A: skills/13-stage1-execution-plan-ingest/SKILL.md
Start subagent B: skills/14-simulator-skill-registry/SKILL.md
```

### Round B：13 完成后立即启动两个非仿真数据分支

```text
Start subagent C: skills/15-real-image-acquisition/SKILL.md
Start subagent D: skills/16-existing-benchmark-acquisition/SKILL.md
```

注意：15、16 不依赖 14。

### Round C：13 与 14 都完成后启动仿真器采集

```text
Start subagent E: skills/17-simulator-multimodal-gt-acquisition/SKILL.md
```

注意：17 只依赖 13 和 14，不依赖 15 或 16。

---

## 3. 输出完整性检查

```bash
python scripts/check_stage2_outputs.py --workspace WORKSPACE_ROOT
```

通过后，Stage3 可分别读取：

```text
WORKSPACE_ROOT/stage2/15-real-image-acquisition/
WORKSPACE_ROOT/stage2/16-existing-benchmark-acquisition/
WORKSPACE_ROOT/stage2/17-simulator-multimodal-gt-acquisition/
```

---

## 4. 禁止行为

```text
禁止 1：把 13→14→15→16→17 写死成串行。
禁止 2：让真实图片分支读取仿真器 registry。
禁止 3：让已有 benchmark 分支读取仿真器 registry。
禁止 4：让仿真器分支读取真实图片或已有 benchmark 分支结果。
禁止 5：用 LLM 直接补 GT。
禁止 6：没有官方 label 或 simulator state 时，把“看起来像”写成事实标签。
```
