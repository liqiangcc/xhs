# 首批 60 题试点：待人工签核清单

生成日期：2026-07-11。以下 26 题均已完成 candidate、evidence、独立审查和候选审计；尚未写入正式答案。根据 `answer_quality.v1`，在首批 60 题全部完成签核前，不能用自动化或 Agent 代替人工批准。

## 人工审查边界

每题只读取 Canonical/来源问法、候选答案、evidence 和质量合同；确认事实、题型、覆盖、口述质量和边界后，独立作出 `approved` 或 `rejected` 决定。拒绝时不得晋级，保留 `needs_update` 并记录具体缺陷。

人工签核记录必须包含：

```json
{
  "canonical_id": "<本表 ID>",
  "candidate_sha256": "<本表 SHA-256>",
  "reviewer_id": "<人工审查者标识>",
  "reviewer_type": "human",
  "reviewed_at": "YYYY-MM-DD",
  "decision": "approved",
  "attestation": "I reviewed the canonical, candidate, evidence, and quality contract.",
  "batch_id": "pilot-20260711"
}
```

保存为 `review/human-review/<canonical_id>.json` 后执行：

```bash
node scripts/xhs.js answer human-review --canonical-id <canonical_id> --evidence review/evidence/<canonical_id>.json --review review/human-review/<canonical_id>.json
node scripts/xhs.js answer promote --canonical-id <canonical_id> --candidate review/candidates/answers/<canonical_id>.md --evidence review/evidence/<canonical_id>.json
```

## 待签核（26）

| Canonical | 当前题型 | Candidate SHA-256 |
|---|---|---|
| `cq_spring_bean_conflict_fb864867` | behavior | `9640c01f77c3f086e50b35d11ba485348ee8ccaf8fcda23344628057e1659124` |
| `cq_binlog_86a375fd` | coding | `5ee0272cda3dbf1925f9544b91c6667852f46c0e919ea16cca98721bfec57d05` |
| `cq_cache_consistency_a83eeb36` | coding | `f83c93f51468987c4a509faae3bd3da265f23fd8d4fc7a9c60048d94224d1a8d` |
| `cq_clustered_index_8c8cbedb` | coding | `375f15d27488defb9a903aa49f69d55d877aa271cf8a3604d4358412372f70c7` |
| `cq_lbs_00924ec8` | coding | `97ae868fc20f88296a2b3523a2f5fb90144df66a48ebeb7554cebb07851a1c4a` |
| `cq_mysql_isolation_c43c6784` | coding | `30a17dae22d8efff55259fbd0ebbdbf2af813be18cd6536526f95858e595b22b` |
| `cq_topic_99ffa229` | coding | `75cbfb89d420b378fe7e67301017c3e9bb9c67370998c4f71d3ea85a305a1bdd` |
| `cq_undo_log_ed9636b1` | coding | `03b5a7342edebe77521f26cb7384008e98d9413b61ac734d32261d9b63934c95` |
| `cq_http_c439559c` | concept | `a7204093c76b98913e56dec0f4334cffaafed2f46bbcb4a3a6ef0e243fdabc58` |
| `cq_innodb_myisam_754c10e6` | concept | `1fba3e13327010f431e21bad92610a0b0dadb6f8c0dc895b669b3271ca6e9cdb` |
| `cq_spring_injection_5060c47f` | concept | `a497af0850d75679bb15c3810374bff0cd6440e4ef2fa8a13f5e112eb0e2c0bb` |
| `cq_stringbuffer_8b8caf0d` | concept | `b2bf092e0e0a9525082488e0f5414efda6a922dafcef786d0f825cbb236d5fd0` |
| `cq_tcp_e9932fa7` | concept | `974c16923b6b51651b0b188406f0ead976fb9921361ee0dffebb22f81fdc2933` |
| `cq_thread_states_2db7d11` | concept | `4786a73a186b272cf14cae47df5d0605166a432faafc88c67888f4694781454f` |
| `cq_topic_c569b06e` | concept | `88f30dc30561bfe1470fba78cc697c029fe96d399c758c82d40c6bcb61d72e4d` |
| `cq_arraylist_9d3444a1` | mechanism | `6cfbb0fa8e4bf259baec17e72fe56928d648933e1c40700fcc39129182138d1e` |
| `cq_bean_319a398d` | mechanism | `bbb7501ad35d4a226769a7ad2072fbafe80b8b030451b7a333c61952694adb90` |
| `cq_daemon_thread_a38b0a9b` | mechanism | `8066962d690463733589a9c9adf9a55d29e3b1206fe350a84b71e0680818c002` |
| `cq_rag_2ff8f969` | mechanism | `55be5ee2eb5a56f7eb967630d1c95dce73b9bee33f59b775d100a045be58894d` |
| `cq_spi_3342eb14` | mechanism | `8bedc54db81698b68bfcb541ec278bf41bcee07a699e9dc13aeccded2fdae4b9` |
| `cq_topic_2494ec69` | mechanism | `9693fd181b2457fe647a12dfc6eca9bbc7e51cfe3b278aada5d51410fcad0e63` |
| `cq_zero_copy_e7b6486b` | mechanism | `33bd740e84ee59fc5d3450bb1265d8c91403b0afd4cdda60f2d9e266194a1f66` |
| `cq_arch_layering_02c49d25` | scenario | `59586af040ee42246bbe1affe1ae9ece2faf34ad20af486dd567068e0270e7aa` |
| `cq_coroutine_878b831f` | scenario | `99711109de7daae36d943051044895cbd857c03a3fc8639031e5a195b7fec402` |
| `cq_rocketmq_b7347b07` | scenario | `d40c372023871a318eaa84547d37cda56229f979af79397718217e000f728cfc` |
| `cq_zookeeper_lock_2808e178` | scenario | `8ee3f5bc34f5726b4a467e9f412cc05267c91b82adeea24ee0337ed1203cfaf4` |

候选与证据路径均按表中 Canonical ID 代入：`review/candidates/answers/<id>.md`、`review/evidence/<id>.json`。
