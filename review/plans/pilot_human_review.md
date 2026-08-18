# 首批 60 题试点：待人工签核清单

当前有 33 题已完成 candidate、evidence、独立审查和候选审计；尚未写入正式答案。根据 `answer_quality.v1`，在首批 60 题全部完成人工签核前，不能用自动化或 Agent 代替人工批准。

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
  "batch_id": "pilot-quality-v2"
}
```

保存为 `review/human-review/<canonical_id>.json` 后执行：

```bash
node scripts/xhs.js answer human-review --canonical-id <canonical_id> --evidence review/evidence/<canonical_id>.json --review review/human-review/<canonical_id>.json
node scripts/xhs.js answer promote --canonical-id <canonical_id> --candidate review/candidates/answers/<canonical_id>.md --evidence review/evidence/<canonical_id>.json
```

## 待签核（33）

| Canonical | 当前题型 | Candidate SHA-256 |
|---|---|---|
| `cq_concurrent_transfer_a35181e0` | coding | `cbf21783eb9428f4b3df90df92414eb9f2e7084737d2ae4cbdad29bb98b78033` |
| `cq_linked_list_cycle_2b5bb46d` | coding | `7a712273da1aa0733ceb0264e8550e586cf59cbe23c632815c93a8d308b702d0` |
| `cq_lru_cache_0ef78597` | coding | `ff07a810afc720cd07af39101d2a5d15d54db4ff91e474b421a838e2ba0099b1` |
| `cq_merge_intervals_866286e5` | coding | `48a8eb838a93b0a37b73f6a6be588e710cf2cda6ee382dfe607560a14df8fc1a` |
| `cq_topic_3f61dd36` | coding | `693294bf602963f81deba8fa4a50225de5f15fa571c131ef6c43603ae2946eb8` |
| `cq_topic_722fbd80` | coding | `a97881959cb910139fdb3eae157a3702cc744c183624e4565eb1e5efd540868e` |
| `cq_topic_745b29f7` | coding | `6a23e91625cf4defab273e0624a8920ca6d0791423a23bce2cb6127ccebcaf52` |
| `cq_topic_77ee33f1` | coding | `f9e7a797859459ca0f97af62a1ef69fd9f22175048c402283d1b4dc7c43718f1` |
| `cq_topic_ac84034f` | coding | `c4008168907220c4b5a128b9a06479f24d8340f056073eafe142907dbbd26abf` |
| `cq_topic_cc39dcdb` | coding | `e1d729983594c58a62eb310a176f3872b078ab16036094cee03b5dfcf282496b` |
| `cq_arch_layering_02c49d25` | concept | `59586af040ee42246bbe1affe1ae9ece2faf34ad20af486dd567068e0270e7aa` |
| `cq_arraylist_9d3444a1` | concept | `6cfbb0fa8e4bf259baec17e72fe56928d648933e1c40700fcc39129182138d1e` |
| `cq_http_c439559c` | concept | `a7204093c76b98913e56dec0f4334cffaafed2f46bbcb4a3a6ef0e243fdabc58` |
| `cq_kafka_isr_3e780e46` | concept | `90acee9c8b94f6e09d1ef7707b97e65892ce3a4272371d31e7096bd44b03c9be` |
| `cq_synchronized_lock_2886cc94` | concept | `56f9e4a95ce2b213862c8c157ca71e930dce847f077696e348aa3368649a95eb` |
| `cq_synchronized_volatile_2801d05c` | concept | `f62d38a1cdf70d0db619c5bc3257a06957195efad9ba615059166360c92e8dba` |
| `cq_tcp_e9932fa7` | concept | `974c16923b6b51651b0b188406f0ead976fb9921361ee0dffebb22f81fdc2933` |
| `cq_tcp_wait_states_c808f88e` | concept | `e717d4bfc25687e2a8ea66485525ed29b5d8eb3ba1d61e235501b73b692904b5` |
| `cq_topic_99ffa229` | concept | `75cbfb89d420b378fe7e67301017c3e9bb9c67370998c4f71d3ea85a305a1bdd` |
| `cq_mysql_index_types_8ee09a1a` | concept | `1614aca4fca3832347421d3a3f2b98453bbd920f0e34aa3525c1a46035238f72` |
| `cq_bean_319a398d` | mechanism | `bbb7501ad35d4a226769a7ad2072fbafe80b8b030451b7a333c61952694adb90` |
| `cq_cms_collector_c069b541` | mechanism | `cf1dc9ebdda56110a361fc6f9035c6fd94c0621397b4c52326e526463568874f` |
| `cq_daemon_thread_a38b0a9b` | mechanism | `8066962d690463733589a9c9adf9a55d29e3b1206fe350a84b71e0680818c002` |
| `cq_hash_table_286e0112` | mechanism | `e143cb816655ca128f26bea3df381da8d1f9332c58c3d16f98cfed8d084ecaa9` |
| `cq_hashmap_4d9f15d2` | mechanism | `fdfa1eb69b9e430e1c9eceb169fb1b3dbdeed455d4bb81a4d3791079ff82848b` |
| `cq_mysql_backup_0daa23c7` | mechanism | `67fc49381e1f3ab17299adfa9bfc17df78ecb7d8048c22e4f06c0ad12cc682b1` |
| `cq_rag_2ff8f969` | mechanism | `55be5ee2eb5a56f7eb967630d1c95dce73b9bee33f59b775d100a045be58894d` |
| `cq_redis_ff848e90` | mechanism | `84049403887eed260f04f67ef15d1ef1588199fd60bac791bd834cab767460fa` |
| `cq_tcp_handshake_39cc7c09` | mechanism | `ecf5e62414e3a678170ba53fd2337ffe8dccc8ff3be1958f268d9ff02b3558cc` |
| `cq_topic_2494ec69` | mechanism | `9693fd181b2457fe647a12dfc6eca9bbc7e51cfe3b278aada5d51410fcad0e63` |
| `cq_message_exactly_once_4aede2ce` | scenario | `d0ffb196270e5017f1b215fd63a2d18cb0dbb894bf60a547d40fe817f0e76ca6` |
| `cq_mq_selection_9293dfad` | scenario | `6750ab70afa87c2714c7661f41d9c347d1cc8702f27174e8cbf24c39819906db` |
| `cq_rocketmq_b7347b07` | scenario | `d40c372023871a318eaa84547d37cda56229f979af79397718217e000f728cfc` |

候选与证据路径均按表中 Canonical ID 代入：`review/candidates/answers/<id>.md`、`review/evidence/<id>.json`。