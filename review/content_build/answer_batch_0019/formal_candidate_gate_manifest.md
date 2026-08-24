# Answer Batch 0019 formal candidate gate manifest

This manifest records the exact source-bounded candidate snapshots consumed by the registered `master`-side pull-request gates for the active Answer Batch 0019 candidates. It is a controller/verification artifact only; it does not promote content or satisfy the pilot human-review requirement.

| Canonical | Candidate SHA-256 | Executable gate | Formal answer audit |
| --- | --- | --- | --- |
| `cq_q_2d3c2cbca1d43c2ab3acad0e91726695` | `fb546b25e878e86a091eaea6ba201258835b001ea6560d8ccc9b4bcb5c462bbb` | Java tree-equality fixture | `answer audit --require-evidence --require-code` |
| `cq_q_2f07ba5f8d6e6ad366d2cd13c6d1d1ab` | `d83598e1206e067f11b924bc56f11569564c1828ed33bd012c53f27439b0a205` | Java graph-clone fixture | `answer audit --require-evidence --require-code` |
| `cq_q_2f278e6b489feb680f8b173047815566` | `933835a7f303f5dc06dc2bfd8b735153f4871577c25893579cf783ea5e2b699b` | Java equal-sum fixture | `answer audit --require-evidence --require-code` |
| `cq_q_2f351e2a49d14ad9643e8daed49006b0` | `8d567824490d15750d34a4032656b7a077a13277279f9a8c48507baa52d0d87d` | Java min-heap fixture | `answer audit --require-evidence --require-code` |
| `cq_q_2fcd783bcefb0f3ab525b18afe3a7591` | `cac56050241fa799af7222acef4cc76810f27ed3bfe16e0e7094ea973ad184b8` | Node.js Promise.all/native-oracle fixture | `answer audit --require-evidence` plus the dedicated executable JavaScript fixture |
| `cq_q_84bd83ff8f06510515f6b71534cd2ac5` | `e456ec1627231ec5e52e3f92037ea29a2f4a6103100ae51236245d7ea4816be2` | Java binary-tree path-sum fixture | `answer audit --require-evidence --require-code` |
| `cq_q_2a5006d66e022875a36106ef0c25c2c2` | `3c81f326ca291d6de6f7ee006682cf13dc91421791d54d39afa849fbd820f8c6` | Java longest-consecutive-sequence fixture | `answer audit --require-evidence --require-code` |

The exact-hash checks deliberately fail closed if a candidate changes after isolated review/evidence binding. Any candidate-byte change therefore requires a new source-first review/evidence rebind before this manifest or its controller gate may be advanced. Human approval and atomic promotion remain separate downstream gates.
