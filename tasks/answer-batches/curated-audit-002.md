# Curated audit batch 002

- Status: `done`
- Canonical count: `10`
- Disposition: all ten historical `ready/curated` answers lacked an evidence sidecar. The deterministic `missing_evidence` gate atomically changed each to `needs_update/curated_audit_failed`; bodies remain intact only as rewrite inputs, not facts.

## Canonicals

- `cq_jvm_safepoint_f7c9b757`
- `cq_mysql_backup_0daa23c7`
- `cq_redis_ff848e90`
- `cq_redis_lock_wait_a9bfb6eb`
- `cq_reentrantlock_fairness_03dab385`
- `cq_rocketmq_routing_ee386a74`
- `cq_spi_3342eb14`
- `cq_spring_boot_026e4b46`
- `cq_synchronized_lock_2886cc94`
- `cq_synchronized_volatile_2801d05c`
