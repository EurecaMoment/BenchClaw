# Data-Juicer Quick Reference

## Locations

- Repo: `/home/maqiang/data-juicer`
- Skill dir: `/home/maqiang/benchclaw/data-juicer_card`

## Main Commands

```bash
uv pip install -e /home/maqiang/data-juicer
dj-process --config /absolute/path/to/config.yaml
dj-analyze --config /absolute/path/to/analyzer.yaml
dj-mcp granular-ops --transport stdio
dj-mcp recipe-flow --transport stdio
```

## Main Docs

- README: `/home/maqiang/data-juicer/README.md`
- Quick start: `/home/maqiang/data-juicer/docs/tutorial/QuickStart.md`
- Dataset config: `/home/maqiang/data-juicer/docs/DatasetCfg.md`
- Operators index: `/home/maqiang/data-juicer/docs/Operators.md`
- Distributed: `/home/maqiang/data-juicer/docs/Distributed.md`
- Tracing: `/home/maqiang/data-juicer/docs/Tracing.md`
- Export: `/home/maqiang/data-juicer/docs/Export.md`

## Useful Demo Configs

- `/home/maqiang/data-juicer/demos/process_simple/process.yaml`
- `/home/maqiang/data-juicer/demos/process_quick_local/process_quick.yaml`
- `/home/maqiang/data-juicer/demos/process_on_ray/configs/demo.yaml`
- `/home/maqiang/data-juicer/demos/analyze_simple/analyzer.yaml`

## Installed CLI Scripts

Defined in `/home/maqiang/data-juicer/pyproject.toml`:

- `dj-process`
- `dj-analyze`
- `dj-install`
- `dj-mcp`

## Heuristics

- Prefer YAML + `dj-process` for repeatable tasks.
- Prefer Python API only for tiny prototypes.
- Prefer `dj-analyze` for profiling or validating results.
- Prefer `dj-mcp` when another agent system needs MCP-exposed DJ capabilities.
- Verify operators against local docs before using them.
