# Node 21 — real-image-unified-format

全局路径约束：`BENCHCLAW_ROOT` 仅作只读输入；`WORKSPACE_ROOT` 是本次流程唯一总工作目录，所有写操作和流程产物只能落在其下。

## Role

Convert real-image records into the Stage3 unified multimodal-record schema.

## Parents

```text
15
```

## May read

- `WORKSPACE_ROOT/stage3/15-stage2-real-image-source-ingest/**`
- `schemas/unified_multimodal_record.schema.json`
- `templates/unified_record.example.json`

## Must write

- `WORKSPACE_ROOT/stage3/21-real-image-unified-format/unified_records.jsonl`
- `WORKSPACE_ROOT/stage3/21-real-image-unified-format/field_mapping.md`
- `WORKSPACE_ROOT/stage3/21-real-image-unified-format/modality_inventory.json`
- `WORKSPACE_ROOT/stage3/21-real-image-unified-format/normalization_report.md`
- `WORKSPACE_ROOT/stage3/21-real-image-unified-format/DONE.json`
- `WORKSPACE_ROOT/stage3/21-real-image-unified-format/USED_INPUTS.json`

## Must not read

- `WORKSPACE_ROOT/stage3/16-stage2-existing-benchmark-source-ingest/**`
- `WORKSPACE_ROOT/stage3/17-stage2-simulator-gt-source-ingest/**`
- `WORKSPACE_ROOT/stage3/22-benchmark-unified-format/**`
- `WORKSPACE_ROOT/stage3/23-simulator-unified-format/**`
- `WORKSPACE_ROOT/stage3/24-real-image-data-juicer-cleaning/**`
- `WORKSPACE_ROOT/stage3/25-benchmark-data-juicer-cleaning/**`
- `WORKSPACE_ROOT/stage3/26-simulator-data-juicer-cleaning/**`
- `WORKSPACE_ROOT/stage3/27-semi-supervised-tool-registry/**`
- `WORKSPACE_ROOT/stage3/18-real-image-semi-supervised-gt/**`
- `WORKSPACE_ROOT/stage3/19-benchmark-image-semi-supervised-gt/**`
- `WORKSPACE_ROOT/stage3/20-simulator-clean-gt-pack/**`

## Completion

完成后必须写：

```json
{
  "node_id": "21",
  "status": "DONE",
  "output_dir": "WORKSPACE_ROOT/stage3/21-real-image-unified-format",
  "timestamp_utc": "<ISO-8601>"
}
```

并运行：

```bash
python scripts/check_used_inputs.py --node 21
python scripts/ready_set_runner.py --workspace WORKSPACE_ROOT
```
