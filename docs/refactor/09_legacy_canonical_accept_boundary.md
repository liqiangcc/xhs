# Legacy Canonical Accept Boundary

## Status

`canonical_candidates.v1` is no longer part of the current Suggest → Review → Apply flow.

The current production flow is:

```text
Dedup Detect
  → RelationCandidate
  → explicit RelationDecision
  → ApplyDecision
  → Canonical planning / mutation
```

`canonical accept --candidate-id ...` remains only as a compatibility entry point for historical or manually supplied `data/manifests/canonical/canonical_candidates.json` files.

## Compatibility boundary

The legacy model is allowed to exist only behind these boundaries:

```text
canonical accept CLI
        ↓
Canonical Accept Application
        ↓
LegacyCanonicalCandidateRepository
        ↓
legacy-canonical-candidate-repositories.js
        ↓
canonical_candidates.v1
```

The current Dedup flow must never depend on this repository or manifest.

### Allowed production dependencies

- `scripts/commands/canonical.js`
  - may expose `canonical accept` as a compatibility command;
  - must not generate `canonical_candidates.v1`.
- `src/application/canonical/accept-canonical.js`
  - may consume `LegacyCanonicalCandidateRepository`;
  - must not be used as the output path of current Dedup Suggest.
- `src/ports/repositories/legacy-canonical-candidate-repository.js`
  - compatibility-only read contract.
- `src/infrastructure/filesystem/legacy-canonical-candidate-repositories.js`
  - compatibility-only filesystem adapter.
- `src/infrastructure/filesystem/canonical-paths.js`
  - retains `legacyCandidateManifest` plus a deprecated `candidateManifest` alias for migration compatibility.

The previous generic Port/adapter module names remain only as deprecated re-exports so existing tests or external callers are not broken by this refactor.

## Forbidden dependencies

The following must not read, write, or derive executable state from `canonical_candidates.v1`:

- Dedup entity detection;
- Dedup hotspot detection;
- `SuggestCanonicalRelations`;
- RelationCandidate review queues;
- RelationDecision recording;
- `PrepareRelationApply` / `ApplyRelationDecision`;
- Canonicalization planning and execution;
- GitHub Actions Suggest tasks.

A similarity signal or a generated RelationCandidate must never be converted into a legacy candidate manifest to bypass explicit review.

## GitHub Actions

`xhs-manage` Suggest tasks now publish:

```text
data/manifests/dedup/relation_candidate_queues.json
```

They no longer upload, commit, or create PRs for:

```text
data/manifests/canonical/canonical_candidates.json
```

A generated review queue still requires an explicit `dedup decide` before `dedup apply` can mutate Canonical state.

## Why `canonical accept` is not deleted yet

The command still provides recovery/compatibility for:

1. historical checked-in `canonical_candidates.v1` data;
2. manually prepared manifests used by existing tests or one-off migration workflows;
3. callers that have not yet moved to RelationCandidate + RelationDecision.

Removing it in the same change as Suggest migration would conflate compatibility cleanup with the new Dedup workflow and make rollback harder.

## Removal criteria

`canonical accept` and the legacy candidate manifest model may be removed only when all of the following are true:

1. repository search finds no active workflow, script, skill, or documented operational procedure that generates new `canonical_candidates.v1` manifests;
2. no GitHub Action artifact/PR flow depends on `canonical_candidates.json`;
3. historical/manual manifest consumers have either migrated to `dedup decide/apply` or are explicitly retired;
4. legacy Accept behavior is either no longer required or has a documented data migration path;
5. full CI remains green after deleting:
   - legacy candidate Port;
   - legacy filesystem adapter;
   - compatibility re-exports;
   - `canonical accept` CLI path;
   - legacy-only characterization tests and checked-in candidate data, if no longer needed.

## Separation-of-concerns rule

The naming is intentional:

> RelationCandidate is current review state. LegacyCanonicalCandidate is compatibility input. They are different concepts and must not share a generic "candidate" repository boundary.

This prevents a future change from accidentally restoring the old shortcut:

```text
Detect → generated candidate → direct Accept
```

The required current boundary remains:

```text
Detect → RelationCandidate → explicit Decision → Apply
```
