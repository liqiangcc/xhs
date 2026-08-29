#!/usr/bin/env python3
"""Execute the Batch 0055 platform-trio builder after repairing quoting and EventBus fixture expectations."""

from __future__ import annotations

import subprocess
from pathlib import Path

BROKEN_PATH = 'scripts/content/build_batch_0055_platform_trio.py'
SQL_OLD = "sql='''WITH ranked AS (SELECT employee_id,employee_name,department_id,salary,DENSE_RANK() OVER (PARTITION BY department_id ORDER BY salary DESC) AS salary_rank FROM employee) SELECT employee_id,employee_name,department_id,salary,salary_rank FROM ranked WHERE salary_rank<=3 ORDER BY department_id,salary DESC,employee_id'''"
SQL_NEW = 'sql=\'WITH ranked AS (SELECT employee_id,employee_name,department_id,salary,DENSE_RANK() OVER (PARTITION BY department_id ORDER BY salary DESC) AS salary_rank FROM employee) SELECT employee_id,employee_name,department_id,salary,salary_rank FROM ranked WHERE salary_rank<=3 ORDER BY department_id,salary DESC,employee_id\''
EVENT_OLD = "assert.strictEqual(bus.emit('e', 3), 4);\nassert.deepStrictEqual(calls.slice(-4), ['b3','late3','late3','late3']);"
EVENT_NEW = "assert.strictEqual(bus.emit('e', 3), 3);\nassert.deepStrictEqual(calls.slice(-3), ['b3','late3','late3']);"


def main() -> int:
    text = subprocess.run(
        ['git', 'show', f'origin/master:{BROKEN_PATH}'],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=True,
    ).stdout
    if text.count(SQL_OLD) != 1:
        raise SystemExit('expected exactly one embedded SQL quoting defect')
    if text.count(EVENT_OLD) != 1:
        raise SystemExit('expected exactly one EventBus snapshot fixture defect')
    fixed = text.replace(SQL_OLD, SQL_NEW).replace(EVENT_OLD, EVENT_NEW)
    path = Path('/tmp/build_batch_0055_platform_trio_fixed_v2.py')
    path.write_text(fixed, encoding='utf-8')
    subprocess.run(['python3', '-m', 'py_compile', str(path)], check=True)
    return subprocess.run(['python3', str(path)]).returncode


if __name__ == '__main__':
    raise SystemExit(main())
