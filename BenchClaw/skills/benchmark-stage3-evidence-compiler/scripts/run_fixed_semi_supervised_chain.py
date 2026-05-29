#!/usr/bin/env python3
"""
DEPRECATED — Stage3 半监督标注的唯一入口已经替换为:

    scripts/run_semi_supervised_annotation.py   (conda env: sam3)

调用方应使用新脚本的 --workspace-root / --branch / --group-name / --record-id 参数
让脚本自动完成 stage3 contract 四件套落盘和 semi_gt_manifest.jsonl 写入。

旧脚本（只构造 JSON manifest 而不真正执行推理）已经全部移除，
保留这个 stub 仅用于防止外部调用静默成功。
"""

import sys


def main() -> int:
    sys.stderr.write(
        "[deprecated] run_fixed_semi_supervised_chain.py has been retired.\n"
        "Use scripts/run_semi_supervised_annotation.py under conda env 'sam3' instead.\n"
        "See ../skills/27-semi-supervised-tool-registry/SKILL.md for the canonical contract.\n"
    )
    return 2


if __name__ == "__main__":
    sys.exit(main())
