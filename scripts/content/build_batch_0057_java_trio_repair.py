#!/usr/bin/env python3
"""Repair the Batch 0057 Java trio merge-tree candidate oral section before running the normal builder."""

from __future__ import annotations

import importlib.util
from pathlib import Path

BUILD_PATH = Path('/tmp/build_batch_0057_java_trio.py')


def load_builder():
    spec = importlib.util.spec_from_file_location('batch0057_java_trio', BUILD_PATH)
    if spec is None or spec.loader is None:
        raise SystemExit('cannot load Batch 0057 Java trio builder')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    module = load_builder()
    target = next((x for x in module.TARGETS if x['cid'] == 'cq_q_e787825953b8cf140b0102f3c504960e'), None)
    if target is None:
        raise SystemExit('merge-binary-trees target missing')
    marker = '```\n\n## 关键细节'
    replacement = '''```\n\n两种实现的核心状态其实一致：都在处理同一结构坐标上的 `(a,b)`，生成对应的输出节点，再把左右两个子坐标加入“待处理集合”。递归把这个集合隐式放在调用栈里，BFS 则显式放在队列里；因此时间复杂度同阶，真正需要比较的是调用栈深度、最大层宽以及是否容易对资源使用做显式控制。\n\n## 关键细节'''
    if marker not in target['candidate']:
        raise SystemExit('merge-tree 3-minute section marker drifted')
    target['candidate'] = target['candidate'].replace(marker, replacement, 1)
    return module.main()


if __name__ == '__main__':
    raise SystemExit(main())
