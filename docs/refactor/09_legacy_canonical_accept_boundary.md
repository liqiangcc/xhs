# Legacy Canonical Accept Boundary

## Status

`canonical_candidates.v1` is no longer part of the current Suggest → Review → Apply flow. The `canonical accept` CLI, Production `canonical.accept`, legacy Accept Application, Legacy Candidate Port, filesystem repository adapter, and deprecated aliases have all been removed.

The current production flow is:

```text
Dedup Detect
  → RelationCandidate
  → explicit RelationDecision
  → ApplyDecision
  → Canonical planning / mutation
```

There is no supported user-facing command, Production capability, Application use case, or candidate Repository that consumes `data/manifests/canonical/canonical_candidates.json`.

## Remaining lower-level compatibility boundary

The legacy model now survives only as residual CAS / contract compatibility awaiting staged cleanup:

```text
legacyCandidateManifest path
        ↓
legacy-canonical-candidate-revision.js
        ↓
canonical-candidate:<id> revision bridge

operation=accept MutationPlan compatibility
```

The revision helper exposes no `get(candidate)` Repository capability. It exists only so the generic Canonical revision router can still validate historical `canonical-candidate:*` evidence until the dedicated CAS removal slice.

### Remaining internal dependencies

- `src/infrastructure/filesystem/canonical-paths.js`
  - retains `legacyCandidateManifest` plus the old `candidateManifest` path alias during staged cleanup.
- `src/infrastructure/filesystem/legacy-canonical-candidate-revision.js`
  - computes semantic opaque revisions for `canonical-candidate:<id>` only; it is not a Repository adapter.
- `src/infrastructure/filesystem/canonical-repositories.js`
  - routes historical `canonical-candidate:<id>` revision evidence to the minimal helper.
- `src/application/canonical/mutation-plan.js`
  - still accepts `operation=accept` until a later removal slice.
- `src/infrastructure/in-memory/canonical-adapters.js`
  - still contains candidate-specific test support that has no current Application consumer.

## Removed runtime dependencies

Four runtime-removal layers have completed.

Interface removal:

```text
runAccept / command dispatch / help             removed
canonical-accept-presenter.js                    removed
```

Production Composition Root removal:

```text
createAcceptCanonicalUseCase wiring              removed
Legacy Candidate adapter construction            removed
app.canonical.accept capability                   removed
```

Application removal:

```text
src/application/canonical/accept-canonical.js    removed
test/canonical_accept_application.test.js        removed
```

Repository layer removal:

```text
LegacyCanonicalCandidateRepository Port          removed
legacy filesystem candidate Repository adapter   removed
canonical-candidate-repository.js alias           removed
canonical-candidate-repositories.js alias         removed
repository characterization                      removed
```

The remaining `test/canonical_legacy_candidate_cas.test.js` characterizes only the CAS revision bridge, not a Repository capability.

## Forbidden dependencies

The following must not read, write, or derive executable state from `canonical_candidates.v1`:

- CLI / Interface layer;
- Production Composition Root;
- Application use cases;
- Repository Ports/adapters;
- Dedup entity/hotspot detection;
- RelationCandidate / RelationDecision flows;
- `PrepareRelationApply` / `ApplyRelationDecision`;
- Canonicalization planning/execution;
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

The next boundary is now the residual `canonical-candidate:*` CAS bridge:

```text
remove canonical-candidate revision routing
remove legacy-canonical-candidate-revision.js
        ↓
then remove operation=accept
        ↓
then remove in-memory candidate test support / legacy path alias / empty data
```

Do not delete `src/domain/canonical/accept-policy.js`. Current Canonicalization projection still reuses its aggregate create/extend semantics as an SSOT.

Likewise, do not delete `CanonicalMutationStore`; only legacy candidate evidence should be removed from the shared store/revision path.

## Separation-of-concerns rule

> RelationCandidate is current review state. Historical canonical candidate data is now only residual CAS evidence awaiting deletion. It is not a Repository model anymore.

The forbidden shortcut remains:

```text
Detect → generated candidate → direct Accept
```

The required current boundary remains:

```text
Detect → RelationCandidate → explicit Decision → Apply
```
