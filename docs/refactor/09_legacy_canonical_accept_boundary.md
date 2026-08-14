# Legacy Canonical Accept Boundary

## Status

`canonical_candidates.v1` is no longer part of the current Suggest → Review → Apply flow, and the `canonical accept` CLI has now been removed.

The current production flow is:

```text
Dedup Detect
  → RelationCandidate
  → explicit RelationDecision
  → ApplyDecision
  → Canonical planning / mutation
```

There is no supported user-facing command that consumes `data/manifests/canonical/canonical_candidates.json`.

## Remaining internal compatibility boundary

The legacy model currently survives only behind internal runtime compatibility:

```text
Composition Root canonical.accept
        ↓
Canonical Accept Application
        ↓
LegacyCanonicalCandidateRepository
        ↓
legacy-canonical-candidate-repositories.js
        ↓
canonical_candidates.v1
        ↓
operation=accept MutationPlan
```

The current Dedup flow must never depend on this repository or manifest.

### Remaining allowed production dependencies

- `src/bootstrap/create-application.js`
  - temporarily wires internal `canonical.accept` during staged removal.
- `src/application/canonical/accept-canonical.js`
  - may consume `LegacyCanonicalCandidateRepository`;
  - is deprecated and must not be used by current Dedup Suggest/Apply.
- `src/ports/repositories/legacy-canonical-candidate-repository.js`
  - compatibility-only read contract.
- `src/infrastructure/filesystem/legacy-canonical-candidate-repositories.js`
  - compatibility-only filesystem adapter.
- `src/infrastructure/filesystem/canonical-paths.js`
  - retains `legacyCandidateManifest` plus a deprecated `candidateManifest` alias during staged cleanup.
- `src/infrastructure/filesystem/canonical-repositories.js`
  - still resolves `canonical-candidate:<id>` revision evidence for legacy MutationStore CAS.

The previous generic Port/adapter module names remain only as deprecated re-exports.

## Removed Interface dependencies

The first runtime-removal slice has completed:

```text
scripts/commands/canonical.js::runAccept       removed
canonical accept command dispatch             removed
canonical command help entry                  removed
scripts/xhs.js top-level help entry            removed
canonical-accept-presenter.js                  removed
presenter / CLI success characterization      removed
```

Calling `node scripts/xhs.js canonical accept ...` now fails as an unknown Canonical command before any Canonical or Question mutation.

## Forbidden dependencies

The following must not read, write, or derive executable state from `canonical_candidates.v1`:

- CLI / Interface layer;
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

The staged removal therefore proceeds with that residual risk explicitly recorded rather than claiming global certainty.

## Next removal slice

The next boundary is the Production Composition Root:

```text
remove createApplication().canonical.accept
        ↓
then delete Accept Application
        ↓
then delete Legacy Port / filesystem adapter
        ↓
then remove canonical-candidate CAS support
        ↓
then remove operation=accept / test support / aliases / empty data
```

Do not delete `src/domain/canonical/accept-policy.js` merely because the legacy command has been retired. Current Canonicalization projection still reuses its Canonical aggregate create/extend semantics as an SSOT.

## Separation-of-concerns rule

> RelationCandidate is current review state. LegacyCanonicalCandidate is internal compatibility input. They are different concepts and must not share a generic candidate repository boundary.

The forbidden shortcut remains:

```text
Detect → generated candidate → direct Accept
```

The required current boundary remains:

```text
Detect → RelationCandidate → explicit Decision → Apply
```
