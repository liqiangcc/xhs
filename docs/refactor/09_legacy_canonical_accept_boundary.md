# Legacy Canonical Accept Boundary

## Status

`canonical_candidates.v1` is no longer part of the current Suggest → Review → Apply flow.

The following legacy execution layers have been removed:

```text
canonical accept CLI / Presenter
Production createApplication().canonical.accept
Accept Application
Legacy Candidate Port / filesystem Repository
canonical-candidate:<id> Filesystem CAS revision bridge
```

The current production flow is only:

```text
Dedup Detect
  → RelationCandidate
  → explicit RelationDecision
  → ApplyDecision
  → Canonical planning / mutation
```

There is no supported user-facing command, Production capability, Application use case, Repository, filesystem candidate reader, or candidate CAS route that can execute `data/manifests/canonical/canonical_candidates.json`.

## Remaining non-executable legacy remnants

Only these staged-cleanup remnants remain:

```text
src/application/canonical/mutation-plan.js
  → operation=accept is still accepted by the generic MutationPlan contract

src/infrastructure/filesystem/canonical-paths.js
  → legacyCandidateManifest / candidateManifest path names still exist

src/infrastructure/in-memory/canonical-adapters.js
  → candidate-specific test-support state/revision code remains

data/manifests/canonical/canonical_candidates.json
  → empty historical snapshot
```

None of these forms a runnable legacy Accept workflow. `src/` runtime JavaScript no longer reads `canonical_candidates.v1`.

## Removed runtime dependencies

Five staged layers have completed:

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
```

`canonical-repositories.js` is now again responsible only for current Canonical / Question binding / ownership revisions. A historical `canonical-candidate:*` resource is unsupported and fails closed.

## Forbidden dependencies

The following must not read, write, or derive executable state from `canonical_candidates.v1`:

- CLI / Interface layer;
- Production Composition Root;
- Application use cases;
- Repository Ports/adapters;
- filesystem Canonical revision routing;
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

## Next removal slice

The next boundary is now the generic MutationPlan contract:

```text
remove operation=accept
        ↓
then remove in-memory candidate test support
        ↓
then remove legacy path aliases / empty historical data
```

Do not delete `src/domain/canonical/accept-policy.js`. Current Canonicalization projection still reuses its aggregate create/extend semantics as an SSOT.

Likewise, do not delete `CanonicalMutationStore`; it remains the transaction boundary for Merge/Split/Canonicalize.

## Separation-of-concerns rule

> RelationCandidate is current review state. Historical canonical candidate data is now only inert staged-cleanup residue; it has no current execution path.

The forbidden shortcut remains:

```text
Detect → generated candidate → direct Accept
```

The required current boundary remains:

```text
Detect → RelationCandidate → explicit Decision → Apply
```
