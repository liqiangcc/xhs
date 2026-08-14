# Legacy Canonical Accept Boundary

## Status

`canonical_candidates.v1` is no longer part of the current Suggest → Review → Apply flow. The `canonical accept` CLI has been removed, Production `createApplication()` no longer constructs or exposes `canonical.accept`, and the legacy Accept Application itself has now been deleted.

The current production flow is:

```text
Dedup Detect
  → RelationCandidate
  → explicit RelationDecision
  → ApplyDecision
  → Canonical planning / mutation
```

There is no supported user-facing command, Production Composition Root capability, or Accept Application use case that consumes `data/manifests/canonical/canonical_candidates.json`.

## Remaining lower-level compatibility boundary

The legacy model now survives only as lower-level compatibility contracts awaiting staged cleanup:

```text
LegacyCanonicalCandidateRepository
        ↓
legacy-canonical-candidate-repositories.js
        ↓
canonical_candidates.v1

canonical-candidate:<id> revision bridge
        ↓
operation=accept MutationPlan compatibility
```

The current Dedup flow, Interface layer, Production Composition Root, and Application use cases must never depend on this repository or manifest.

### Remaining internal dependencies

- `src/ports/repositories/legacy-canonical-candidate-repository.js`
  - compatibility-only read contract.
- `src/infrastructure/filesystem/legacy-canonical-candidate-repositories.js`
  - compatibility-only filesystem adapter, now used only by direct lower-level characterization.
- `src/infrastructure/filesystem/canonical-paths.js`
  - retains `legacyCandidateManifest` plus a deprecated `candidateManifest` alias during staged cleanup.
- `src/infrastructure/filesystem/canonical-repositories.js`
  - still resolves `canonical-candidate:<id>` revision evidence for later CAS cleanup.
- `src/application/canonical/mutation-plan.js`
  - still accepts `operation=accept` until a later removal slice.

The previous generic Port/adapter module names remain only as deprecated re-exports.

## Removed runtime dependencies

Three runtime-removal slices have completed.

Interface removal:

```text
scripts/commands/canonical.js::runAccept       removed
canonical accept command dispatch             removed
canonical command help entry                  removed
scripts/xhs.js top-level help entry            removed
canonical-accept-presenter.js                  removed
presenter / CLI success characterization      removed
```

Production Composition Root removal:

```text
createAcceptCanonicalUseCase import            removed
createFsLegacyCanonicalCandidateRepository     removed
Legacy Candidate adapter construction          removed
Accept use case construction                   removed
app.canonical.accept capability                removed
```

Application removal:

```text
src/application/canonical/accept-canonical.js  removed
test/canonical_accept_application.test.js      removed
```

`canonical_accept_filesystem_integration.test.js` now characterizes only the lower-level legacy candidate repository / revision contract; it no longer recreates Accept orchestration.

## Forbidden dependencies

The following must not read, write, or derive executable state from `canonical_candidates.v1`:

- CLI / Interface layer;
- Production Composition Root;
- Application use cases;
- Dedup entity detection;
- Dedup hotspot detection;
- `SuggestCanonicalRelations`;
- RelationCandidate review queues;
- RelationDecision recording;
- `PrepareRelationApply` / `ApplyRelationDecision`;
- Canonicalization planning and execution;
- GitHub Actions Suggest tasks.

A similarity signal or RelationCandidate must never be converted into a legacy candidate manifest to bypass explicit review.

## GitHub Actions

`xhs-manage` Suggest tasks publish:

```text
data/manifests/dedup/relation_candidate_queues.json
```

They do not upload, commit, or create PRs for:

```text
data/manifests/canonical/canonical_candidates.json
```

A generated review queue still requires an explicit `dedup decide` before `dedup apply` can mutate Canonical state.

## External-consumer evidence

As of 2026-08-14, repository-local consumers are classified and project-specific GitHub code search found zero observable external consumers. This does not prove the absence of local shell scripts, uncommitted automation, or inaccessible/unindexed private repositories.

The staged removal proceeds with that residual risk explicitly recorded rather than claiming global certainty.

## Next removal slice

The next boundary is the Legacy Candidate Port / filesystem adapter:

```text
delete LegacyCanonicalCandidateRepository + FS adapter
        ↓
then remove canonical-candidate CAS support
        ↓
then remove operation=accept / test support / aliases / empty data
```

Do not delete `src/domain/canonical/accept-policy.js` merely because the legacy Accept Application is gone. Current Canonicalization projection still reuses its Canonical aggregate create/extend semantics as an SSOT.

Likewise, do not delete `CanonicalMutationStore`; only legacy candidate evidence should be removed from it in the later CAS slice.

## Separation-of-concerns rule

> RelationCandidate is current review state. LegacyCanonicalCandidate is a lower-level compatibility data contract awaiting deletion. They are different concepts and must not share a generic candidate repository boundary.

The forbidden shortcut remains:

```text
Detect → generated candidate → direct Accept
```

The required current boundary remains:

```text
Detect → RelationCandidate → explicit Decision → Apply
```
