---
name: test-audit
description: "Use when adding or changing tests, or when reviewing a test suite for weak, redundant, or implementation-coupled coverage. Follow the current repository's own guidance and tools."
---

# Test Audit

Use three modes with one value bar:

- **Authoring:** evaluate each new or changed test before writing it.
- **Audit:** inspect a focused area for weak, duplicative, or implementation-coupled tests and test-only production seams.
- **Campaign:** audit one subsystem's full test surface; read [CAMPAIGN.md](CAMPAIGN.md) first.

## Authoring gate

Before adding a test or materially changing its assertions, answer:

1. What observable behavior, invariant, or independent contract does it protect?
2. What credible regression makes it fail?
3. Why does existing coverage not already catch that failure? Give each contract one primary test owner at the strongest practical boundary. Another layer needs a distinct risk, such as a transport or lifecycle failure the owner cannot reach. Prefer extending a table-driven case or shared fixture over a near-duplicate test.
4. Does it need a production seam (export, flag, wrapper, injection hook) that no production caller needs? If so, move the test to a real user or system boundary when practical.

Check every candidate against [Junk patterns](#junk-patterns). A new test that matches one fails the gate unless the [retention bar](#retention-bar) names the independent contract it guards. A test that breaks under behavior-preserving refactoring is likely asserting implementation; move it to the owning boundary or explain the stable contract it protects.

For a regression test, establish that it fails on the pre-fix behavior for the intended reason and passes after the repair. A test that never demonstrably failed may be proving its mock rather than the fix. One regression at the owner boundary is usually enough; add another layer only for a separate risk.

## Junk patterns

Use this checklist when authoring or auditing:

- assertion-free coverage probes;
- self-comparisons and identity copiers;
- copied fixtures, inventories, manifests, or export lists;
- exact source, import, or string greps that duplicate behavioral coverage;
- private predicate or call-shape tests duplicated at real boundaries;
- duplicate invocations of the same contract;
- implementation-local replays of shared helpers;
- tests whose only purpose is preserving test-only exports, globals, or wrappers;
- dead production code whose only callers are tests;
- expected values produced by the helper or renderer under test;
- mocks that implement the asserted behavior, or one identical mock standing in for different APIs;
- fixtures that supply the receipt, admission, or callback ordering the owner should produce, or persistence asserted against a store the path never writes;
- capability tests that restate declared flags instead of exercising the delivery or acknowledgement the flag promises;
- negative controls that pass for an unrelated reason or never reach the production path;
- names or fixtures that promise more than the input exercises.

## Value bar

Tests justify their maintenance cost by protecting behavior, a credible regression, or an independently meaningful contract. A test that must change after behavior-preserving source reorganization is suspect, but that alone does not prove it should be deleted.

Before judging a candidate, read the complete test and production owner, relevant entry points and callers, sibling implementations, overlapping tests, applicable CI routing, and history when available. Read repository-level and scoped `AGENTS.md` files first. If a test claims dependency-backed behavior, inspect the dependency source or types directly.

## Discovery

Keep discovery read-only and report evidence before editing. For broad scope, organize discovery around the repository's actual ownership boundaries. Parallel lanes or independent reviewers can help when available and appropriate; do not assume a particular directory layout or delegate when the task's instructions do not allow it.

Outside campaign mode, prefer a few high-confidence candidates over a large speculative inventory. Hunt for the [junk patterns](#junk-patterns).

## Retention bar

Keep a test when it independently enforces a public API, protocol, configuration, migration, storage, security, platform, default, prompt or generated-artifact, package, release, or architecture contract. Also keep:

- call ordering when order is observable behavior;
- regressions with a credible failure mode;
- source inspection when it is the cheapest independent guard for a stable contract and survives identifier-only refactoring;
- a retained test that fails on the baseline, as a possible product bug to reproduce and report to the owner.

Static or slow is not by itself a deletion reason. A test that resembles implementation may still be the independent contract; prove otherwise before removing it.

## Candidate evidence

Before deleting or consolidating a candidate, record:

- exact test name and location;
- the failure it can actually detect;
- non-test callers of the covered production or support seam, if any;
- stronger remaining owner-boundary proof, or why no proof is needed;
- relevant history and why the test or seam exists, when available;
- production or test-support deletion unlocked;
- risk and the focused validation command used or planned.

A missing field means the candidate is not ready for deletion.

## Edit shape

Choose one coherent owner-boundary batch. Remove obsolete test-only exports, globals, wrappers, and dead production paths instead of preserving aliases. Move retained regressions to their canonical owners. Consolidate repeated package or dependency assertions into one generic contract when that preserves the behavior being protected.

Prefer net-negative production LOC. Do not add replacement tests that restate the same implementation or turn uncertain candidates into cleanup to increase deletion counts.

## Validation

Use the current repository's documented commands and gates; never copy commands from another project or assume a particular runner, script, CI service, or review tool.

1. Follow the task's governing instructions about test execution. When tests are permitted and relevant, run the smallest owner and sibling tests for the change. For a discovery-only audit, keep this phase read-only and report whether tests were run.
2. If removing a source-level guard or plan assertion, exercise the executable behavior or contract that guard was meant to protect when one exists.
3. Run the repository's targeted formatter and diff checks when defined.
4. Run applicable changed-file, CI, or review gates documented by the repository. Do not invent a gate when none is defined.
5. Inspect the final diff and report production code separately from tests and test support.
6. Use independent review when the risk and available workflow justify it; do not require a specific skill or tool by name.

Never modify files that an active test run is reading when doing so could make the result unreliable. If a command is unavailable or a gate cannot be run, report that limitation instead of substituting an assumed command.

## Landing and continuation

Commit, push, open a pull request, or land only when authorized. Follow the repository's documented contribution and release workflow. After a coherent batch lands, refresh from the repository's current target branch and repeat read-only discovery before starting the next batch.

## Handoff

For test changes, report the contract protected and relevant verification. For audits, summarize the evidence, candidates retained or removed, production simplifications when applicable, and follow-ups. In either case, state what proof actually ran and the landing state when relevant.
