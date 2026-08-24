# Answer Batch 0028 — SQL Relation Discovery

Fresh discovery was executed through the current Application `canonical suggest` path after the source split. These results are discovery evidence only and do not authorize any relation.

- source: `e9c5bb8468fd0b37bd3f0abf72df80aa` / `cq_q_e9c5bb8468fd0b37bd3f0abf72df80aa` — SQL：从学生表和成绩表中，查询学生学号、姓名、平均成绩
- source type: `算法手撕_Coding`
- source entities: `['SQL']`
- distinct matching RelationCandidates across fresh runs: `0`

## Runs

- `entity` seed `SQL`: detections `0`, emitted `0`, source matches `0`
- `hotspot` seed `hotspot`: detections `0`, emitted `0`, source matches `0`

## Suggested neighbors

- None from the current entity/hotspot suggestion paths.

## Review boundary

A source-first reviewer must compare the SQL source contract against every suggested neighbor (if any), and may only then record an explicit relation Decision. If discovery produces no reusable same-boundary neighbor, the source-exact split Canonical remains distinct and candidate authoring may proceed with schema names stated only as answer assumptions.
