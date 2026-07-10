# C5 Core Topic Map

Completed: 2026-07-10. This map organizes the first 100 Canonical assets into review paths. It is a learning graph, not a claim that long-tail coverage is complete.

## Recommended Learning Order

```text
Java language and collections
  -> concurrency and JVM
  -> Spring container and transactions
  -> MySQL and Redis
  -> message queues and network/OS
  -> distributed consistency
  -> high-concurrency system design
  -> troubleshooting and coding drills
```

## 1. Java Language And Collections

Start with value/reference semantics and data structures, then move to extension and design boundaries.

- Collections: `cq_arraylist_9d3444a1`, `cq_hashmap_4d9f15d2`, `cq_hash_table_286e0112`, `cq_equals_hashcode_e7fe32f7`
- Strings and equality: `cq_stringbuffer_8b8caf0d`, `cq_topic_c569b06e`
- Object model: `cq_java_oop_21912814`, `cq_deep_copy_5cfb8eb4`
- Extension/design: `cq_spi_3342eb14`, `cq_design_patterns_0b3fb4b2`, `cq_language_compilation_0a002e6b`

Key connection: `equals/hashCode` is the contract that makes HashMap key lookup reliable; mutable key fields connect object modeling directly to collection correctness.

## 2. Java Concurrency

Learn visibility and mutual exclusion before framework internals.

- Foundations: `cq_thread_states_2db7d11`, `cq_synchronized_volatile_2801d05c`, `cq_synchronized_lock_2886cc94`, `cq_cas_64fa0b00`
- Synchronizers: `cq_aqs_f718305c`, `cq_reentrantlock_fairness_03dab385`, `cq_topic_36aeccc5`
- Thread context/lifecycle: `cq_threadlocal_leak_1edab066`, `cq_daemon_thread_a38b0a9b`, `cq_coroutine_878b831f`
- Concurrent design: `cq_hashmap_d74d2fd7`, `cq_concurrent_transfer_a35181e0`

Key connection: CAS updates state, AQS handles failed competitors, and ReentrantLock defines acquisition policy. These are three layers of one synchronization story.

## 3. JVM And Runtime

- Collection algorithms and collectors: `cq_gc_algorithms_3f884748`, `cq_cms_collector_c069b541`, `cq_g1_collector_828f806c`
- Runtime coordination: `cq_jvm_safepoint_f7c9b757`
- Failure diagnosis: `cq_jvm_oom_5adc3ce1`

Key connection: safepoint time, collector pause and allocation failure are separate measurements. OOM diagnosis should first identify the memory region, then correlate allocation and GC behavior.

## 4. Spring

- Container: `cq_bean_319a398d`, `cq_spring_bean_conflict_fb864867`, `cq_spring_injection_5060c47f`
- Boot: `cq_spring_boot_026e4b46`
- Transactions: `cq_spring_transaction_a3b170d7`

Key connection: auto-configuration ultimately registers BeanDefinitions; injection and transaction proxies only work after definitions, lifecycle and proxy boundaries are understood.

## 5. MySQL

- Index organization: `cq_clustered_index_8c8cbedb`, `cq_mysql_index_types_8ee09a1a`, `cq_topic_99ffa229`, `cq_force_index_5e733952`
- Transactions/recovery: `cq_mysql_isolation_c43c6784`, `cq_undo_log_ed9636b1`, `cq_binlog_86a375fd`
- Engine and operations: `cq_innodb_myisam_754c10e6`, `cq_mysql_backup_0daa23c7`, `cq_online_migration_3302e67d`
- Performance: `cq_topic_9e860ba7`

Key connection: the clustered primary key shapes every secondary index; MVCC/undo determine read visibility, while redo/binlog coordination determines crash recovery and replication.

## 6. Redis And Cache

- Runtime/persistence: `cq_redis_ff848e90`, `cq_topic_2494ec69`, `cq_aof_e522aa87`
- Coordination: `cq_redis_lock_ec98b854`, `cq_redis_lock_wait_a9bfb6eb`, `cq_zookeeper_lock_2808e178`
- Consistency: `cq_cache_consistency_a83eeb36`

Key connection: a Redis lease provides temporary ownership, not a database transaction. Idempotency, fencing and the database invariant still decide correctness.

## 7. Message Queues

- Architecture/routing: `cq_rocketmq_arch_22d7b629`, `cq_rocketmq_routing_ee386a74`, `cq_kafka_isr_3e780e46`
- Reliability: `cq_kafka_duplicate_0a558c94`, `cq_message_exactly_once_4aede2ce`
- Selection/performance: `cq_mq_selection_9293dfad`, `cq_rocketmq_b7347b07`

Key connection: broker delivery and offset guarantees stop at a system boundary. Business exactly-once requires stable event identity and an idempotent state transition.

## 8. Network And Operating System

- Transport: `cq_tcp_e9932fa7`, `cq_tcp_handshake_39cc7c09`, `cq_tcp_wait_states_c808f88e`
- HTTP/TLS: `cq_http_c439559c`
- I/O: `cq_io_multiplexing_6e30840f`, `cq_zero_copy_e7b6486b`
- Process/runtime: `cq_topic_f575096b`, `cq_ipc_84b09f40`, `cq_linux_commands_76aadb5b`

Key connection: epoll changes readiness waiting and zero-copy changes data movement; neither removes framing, backpressure, application work or connection lifecycle management.

## 9. Distributed And High-Concurrency Design

- Consistency/availability: `cq_multi_active_9d99b369`, `cq_async_tradeoff_bef9a76a`, `cq_topic_20fba961`
- Protection/capacity: `cq_topic_89b69343`, `cq_topic_956bc5ce`, `cq_topic_fe047aa4`
- Product systems: `cq_short_url_c0218e46`, `cq_short_video_bcbcf234`, `cq_netdisk_231b839b`, `cq_lbs_00924ec8`, `cq_coupon_system_eaadc982`, `cq_member_system_5fc59993`, `cq_sensitive_words_1231cc49`
- Architecture/platform: `cq_arch_layering_02c49d25`, `cq_topic_fcc849e5`, `cq_tracing_4b9801ad`, `cq_topic_e60c993a`

Key connection: every design answer starts with capacity and invariants, then chooses cache/partition/async techniques, and finally proves failure convergence through idempotency, compensation, reconciliation and observability.

## 10. Troubleshooting, Project And Coding

- Troubleshooting/project: `cq_topic_f003d8b7`, `cq_incident_diagnosis_4e5a6405`, `cq_ai_055f19f9`
- Linked-list drills: `cq_topic_77ee33f1`, `cq_topic_3f61dd36`, `cq_topic_745b29f7`, `cq_linked_list_cycle_2b5bb46d`
- Arrays/DP/strings: `cq_merge_intervals_866286e5`, `cq_topic_722fbd80`, `cq_topic_ac84034f`, `cq_topic_cc39dcdb`
- Data-structure implementation: `cq_lru_cache_0ef78597`

Key connection: troubleshooting answers use an evidence invariant (“which layer owns the waiting time?”), while coding answers use a state invariant. Both should state the invariant before details.

## Coverage Gaps Kept Open

C5 still does not represent complete repository coverage. Important gaps for C6/C7 include class loading, Java Memory Model depth, Spring AOP/MVC, MVCC Read View, Redis data structures and eviction, Kafka storage, distributed transactions, Kubernetes, behavior/HR questions and the valid long tail.
