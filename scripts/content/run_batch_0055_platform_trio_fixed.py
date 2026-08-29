#!/usr/bin/env python3
"""Execute the Batch 0055 platform-trio builder after repairing its embedded SQLite test quoting."""

from __future__ import annotations

import subprocess
from pathlib import Path

BROKEN_PATH = 'scripts/content/build_batch_0055_platform_trio.py'
OLD = "sql='''WITH ranked AS (SELECT employee_id,employee_name,department_id,salary,DENSE_RANK() OVER (PARTITION BY department_id ORDER BY salary DESC) AS salary_rank FROM employee) SELECT employee_id,employee_name,department_id,salary,salary_rank FROM ranked WHERE salary_rank<=3 ORDER BY department_id,salary DESC,employee_id'''"
NEW = 'sql=\'WITH ranked AS (SELECT employee_id,employee_name,department_id,salary,DENSE_RANK() OVER (PARTITION BY department_id ORDER BY salary DESC) AS salary_rank FROM employee) SELECT employee_id,employee_name,department_id,salary,salary_rank FROM ranked WHERE salary_rank<=3 ORDER BY department_id,salary DESC,employee_id\''


def main() -> int:
    text = subprocess.run(
        ['git', 'show', f'origin/master:{BROKEN_PATH}'],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=True,
    ).stdout
    if text.count(OLD) != 1:
        raise SystemExit('expected exactly one embedded SQL quoting defect')
    fixed = text.replace(OLD, NEW)
    path = Path('/tmp/build_batch_0055_platform_trio_fixed.py')
    path.write_text(fixed, encoding='utf-8')
    subprocess.run(['python3', '-m', 'py_compile', str(path)], check=True)
    return subprocess.run(['python3', str(path)]).returncode


if __name__ == '__main__':
    raise SystemExit(main())
