# Legacy Canonical Accept Boundary

## Status

Legacy `canonical accept` is **fully retired inside this repository**.

The current production path is only:

```text
Dedup Detect
  → RelationCandidate
  → explicit RelationDecision
  → ApplyDecision
  → Canonical planning / mutation
```

The following legacy layers have all been removed:

```text
canonical accept CLI / Presenter
Production createApplication().canonical.accept
Accept Application
Legacy Candidate Port / filesystem Repository
canonical-candidate:<id> Filesystem CAS revision bridge
MutationPlan operation=accept
candidate-specific in-memory test support
legacyCandidateManifest / candidateManifest filesystem paths
checked-in canonical_candidates.json
```

There is no repository-local command, Production capability, Application use case, Repository, CAS resource, MutationPlan operation, shared test API, filesystem path, or checked-in manifest that can execute or model the old `canonical_candidates.v1` flow.

## Current invariant

New relation work must remain:

```text
Detect
  ↓
RelationCandidate
  ↓
Explicit Decision
  ↓
Apply
```

Forbidden shortcut:

```text
Detect → generated candidate → direct Accept
```

Similarity/Jaccard/AI output remains evidence only. It cannot authorize Canonical mutation.

## GitHub Actions

`xhs-manage` Suggest tasks publish only:

```text
data/manifests/dedup/relation_candidate_queues.json
```

They do not create or update a legacy Canonical candidate manifest. A generated queue still requires explicit `dedup decide` before `dedup apply` can mutate Canonical state.

## Historical evidence

Historical ADRs and review plans may still contain old `canonical accept` / `canonical_candidates.v1` terminology. They are preserved as historical evidence and are not operational SSOT.

Current operational SSOT:

```text
docs/refactor/10_current_dedup_canonical_operations.md
```

## External-consumer evidence

As of 2026-08-14, project-specific GitHub code searches found zero observable external consumers. This does **not** prove the absence of local shell scripts, uncommitted automation, or inaccessible/unindexed private repositories.

That limitation is recorded as an observability risk, not as a reason to keep dead repository-local compatibility code.

## Current code that must survive

Do not delete:

```text
src/domain/canonical/accept-policy.js
```

Despite its historical name, current Canonicalization still reuses `acceptCanonicalCandidate()` as the Canonical aggregate create/extend Domain SSOT.

Likewise, `CanonicalMutationStore` remains the shared transaction boundary for Merge/Split/Canonicalize.

## Regression rule

Legacy Accept must not return as any of the following:

```text
CLI / help / Presenter
Production capability
Application use case
Repository / adapter
canonical-candidate:* CAS resource
MutationPlan operation
in-memory candidate support
legacy filesystem path
checked-in canonical_candidates.json
```
