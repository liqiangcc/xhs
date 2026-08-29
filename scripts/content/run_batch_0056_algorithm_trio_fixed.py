#!/usr/bin/env python3
"""Run the Batch 0056 algorithm-trio builder with explicit prose in each 3-minute section."""

from __future__ import annotations

import importlib.util
from pathlib import Path

BASE = Path('/tmp/build_batch_0056_algorithm_trio_base.py')

spec = importlib.util.spec_from_file_location('batch0056_algorithm_base', BASE)
if spec is None or spec.loader is None:
    raise SystemExit('cannot load base Batch 0056 algorithm builder')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

marker = '\n```\n\n## 关键细节'
insert = '\n```\n\n这段代码对应上面的口头推导；面试时应先说明输入合同和不变量，再边写边用一个最小样例验证边界，而不是只贴实现。\n\n## 关键细节'
for target in mod.TARGETS:
    body = target['candidate']
    if body.count(marker) != 1:
        raise SystemExit(f"{target['cid']}: expected one 3-minute code-tail marker")
    target['candidate'] = body.replace(marker, insert, 1)

raise SystemExit(mod.main())
