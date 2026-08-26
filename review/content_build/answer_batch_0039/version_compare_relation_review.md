# Batch 0039 Version Compare Source-First Relation Review

## Primary-source facts

- `9e22dda08d291f9e651d29d69976d97e`: repository structured source preserves “算法：比较版本号大小。”.
- `ad3a48d5db87388f867a2f597860d103`: an independent repository structured source preserves “算法手撕：比较版本号（Compare Version Numbers）。”
- Both are standalone Coding prompts asking for the same observable operation: compare two version numbers. Neither source preserves a distinct variant such as semantic-version prerelease precedence, version-list sorting, or maximum-version selection.

No historical relation/remediation record was consulted before this conclusion.

## Decision

Relation: `same`. The wording difference (“比较版本号大小” versus “Compare Version Numbers”) is presentation only and does not preserve a distinct contract. Consolidate the duplicate singleton `cq_q_ad3a48d5db87388f867a2f597860d103` into survivor `cq_q_9e22dda08d291f9e651d29d69976d97e`; preserve both source Questions as members of the survivor.

## Content consequence

The survivor Answer must remain non-curated until it is rebuilt and independently reviewed against both source wordings. The merge itself does not authorize choosing unstated parsing rules for malformed versions, prerelease labels, or arbitrary-length numeric components; any executable candidate must declare its accepted version-string contract.
