# Legacy Canonical Accept Boundary

## Status

`canonical_candidates.v1` is no longer part of the current Suggest → Review → Apply flow.

The following legacy execution/contract/test-support layers have been removed:

```text
canonical accept CLI / Presenter
Production createApplication().canonical.accept
Accept Application
Legacy Candidate Port / filesystem Repository
canonical-candidate:<id> Filesystem CAS revision bridge
MutationPlan operation=accept
candidate-specific in-memory Canonical test support
```

The current production flow is only:

```text
Dedup Detect
  → RelationCandidate
  → explicit RelationDecision
  → ApplyDecision
  → Canonical planning / mutation
```

There is no supported user-facing command, Production capability, Application use case, Repository, filesystem candidate reader/CAS route, MutationPlan operation, or shared in-memory candidate test API that can execute or model `data/manifests/canonical/canonical_candidates.json`.

## Remaining non-executable legacy remnants

Only the final path/data cleanup remains:

```text
src/infrastructure/filesystem/canonical-paths.js
  → legacyCandidateManifest / candidateManifest path names still exist

data/manifests/canonical/canonical_candidates.json
  → empty historical snapshot
```

These are inert names/data only. `src/` runtime JavaScript no longer reads `canonical_candidates.v1`, `canonical_mutation_plan.v1` rejects `operation=accept`, and the shared in-memory Canonical adapter no longer carries candidate state or revisions.

## Removed runtime / contract layers

Seven staged layers have completed:

```text
1. Interface
   runAccept / command dispatch / help / Presenter          removed

2. Production Composition Root
   Accept wiring / candidate adapter construction           removed

3. Application
   src/application/canonical/accept-canonical.js            removed

4. Repository layer
   LegacyCanonicalCandidateRepository + FS adapter + aliases removed

5. Filesystem candidate CAS bridge
   canonical-candidate:<id> revision routing                removed
   legacy-canonical-candidate-revision.js                   removed

6. MutationPlan contract
   operation=accept                                         removed

7. In-memory test support
   candidate seed/repository/revision/upsert/snapshot state removed
```

`canonical-repositories.js` is responsible only for current Canonical / Question binding / ownership revisions. A historical `canonical-candidate:*` resource is unsupported and fails closed. `createCanonicalMutationPlan({ operation: 'accept', ... })` is explicitly rejected.

## Forbidden dependencies

The following must not read, write, derive, or model executable state from `canonical_candidates.v1`:

- CLI / Interface layer;
- Production Composition Root;
- Application use cases;
- Repository Ports/adapters;
- filesystem Canonical revision routing;
- Canonical MutationPlan operations;
- shared in-memory Canonical test adapters;
- Dedup entity/hotspot detection;
- RelationCandidate / RelationDecision flows;
- `PrepareRelationApply` / `ApplyRelationDecision`;
- Canonicalization planning/execution;
- GitHub Actions Suggest tasks.

A similarity signal or RelationCandidate must never be converted into a legacy candidate manifest to bypass explicit review.

## GitHub Actions

`xhs-manage` Suggest tasks publish only:

```text
data/manifests/dedup/relation_candidate_queues.json
```

They do not upload, commit, or create PRs for `canonical_candidates.json`. A generated review queue still requires explicit `dedup decide` before `dedup apply` can mutate Canonical state.

## External-consumer evidence

As of 2026-08-14, repository-local consumers are classified and project-specific GitHub code search found zero observable external consumers. This does not prove absence of local shell scripts, uncommitted automation, or inaccessible/unindexed private repositories.

The staged removal proceeds with that residual risk explicitly recorded rather than claiming global certainty.

## Final removal slice

The final cleanup is now limited to inert filesystem path/data residue:

```text
remove legacyCandidateManifest / candidateManifest path aliases
remove empty canonical_candidates.json
update anti-legacy guards / policy wording to final retired state
```

Do not delete `src/domain/canonical/accept-policy.js`. Current Canonicalization projection still reuses its aggregate create/extend semantics as an SSOT.

Likewise, do not delete `CanonicalMutationStore`; it remains the transaction boundary for Merge/Split/Canonicalize.

## Separation-of-concerns rule

> RelationCandidate is current review state. Historical canonical candidate data is now only inert path/data residue; it has no execution, mutation-contract, repository, CAS, or shared test-support path.

The forbidden shortcut remains:

```text
Detect → generated candidate → direct Accept
```

The required current boundary remains:

```text
Detect → RelationCandidate → explicit Decision → Apply
```