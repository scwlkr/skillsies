---
name: implement-spec
description: "Implement a spec through clear core, integration and ship-qualification stages."
disable-model-invocation: true
---

Implement the requested spec and its ticket dependency graph. Use the owner's tracker and existing repository workflows. If the tracker is missing, discover the repository's configured tracker; ask only if it remains unknown.

## 1. Set the delivery boundary

Read the spec, tickets, discussions and current work before implementation. State the requested endpoint, owning repositories, acceptance evidence and deferred work in a short plan.

| Boundary | Evidence required to claim it verified |
| --- | --- |
| **Core** | Reusable implementation, supported contracts/artifacts and affected behavior pass their owning checks and independent review. Consumers have concrete, pinned inputs and a usable handoff. |
| **Integration** | Required consumers use the qualified core through their actual product surfaces. Verify affected navigation, state, storage, fallback and lifecycle behavior, including required failure paths. |
| **Ship qualification** | Required target builds, packaging, device/browser measurements, budgets and provider/release requirements pass on the actual candidate. Record any remaining external approval. |

The latest owner instruction selects the endpoint. “Core only” or “I'll integrate later” ends at a verified core handoff. A full-spec request includes the integration and qualification requirements explicitly in that spec. Do not silently reduce those requirements or add unrelated product-release gates.

Distinguish verified stage, landed code, issue Done and ready to ship. A completed core does not establish complete consumer or product qualification. Keep deferred parent/consumer work open; close only work that satisfies the tracker's actual completion criteria.

Qualification does not authorize deployment, publication, signing, submission or provider changes. Use existing task-specific authorization; ask only for a consequential ambiguity or required external action.

## 2. Preflight before expensive work

Use each owning project's existing CLI discovery, identity and doctor commands. Inspect current check scripts and verification recipes before adding tooling. Preflight the selected stage before dispatch, and repeat affected checks before a costly build, corpus preparation or target run:

- **Source and inputs:** exact candidate/base, user changes, approved input identities, actual readable/materialized files, required artifact/lock compatibility and safe new outputs.
- **Execution:** pinned tools/SDKs, architecture and minimum target support, PATH/wrappers, dependencies, offline/network access and required private configuration.
- **Resources:** free disk and anticipated output size, build-cache/process ownership, concurrent jobs and cleanup. Serialize work that shares mutable caches or exceeds available capacity.
- **Proof route:** real product/contract entry point, complete workload and pagination support, nonzero selected tests, raw observation/readback and required device access. Exercise a small real request and its continuation where applicable before the full run.

Readiness is not acceptance. If a prerequisite is unavailable, record the exact blocked stage and remediation; continue independent authorized work. A disconnected device can block device qualification without blocking core delivery.

Identify long-running phases, expected cost and the smallest useful prototype before launching them. Report consequential scope/time tradeoffs early. Experimental model or platform work gets its own evidence and outcome; it must not silently extend the requested endpoint.

## 3. Implement the current frontier

Use one integration branch per owning repository; preserve unrelated work. Follow the repository's isolation/worktree rules. Open a draft PR after the first verified change when the workflow requires one. Closing references cover only the work that PR actually delivers.

Tickets form a task graph. Dispatch background implementer subagents only for ready, independent work. Each receives pointers to the spec/tickets, current integration revision, its file ownership, delivery boundary, checks and preflight results. Keep communication sparse and report changed state, blockers or a completed handoff.

Each implementer uses the repository's TDD workflow for meaningful regressions, preserves owner edits, commits focused changes, and synchronizes with the integration tip before handoff. A merger integrates completed, reviewed work and checks the resulting candidate. Avoid concurrent mutation of shared lockfiles, caches or artifacts.

Verify actual affected behavior through existing contracts and product drivers. Keep failed, partial, skipped and interrupted results distinct from passes. Preserve exact candidate/base, runtime/input identities, commands, raw observations and owned-process cleanup.

Reuse evidence only when its candidate, artifact, dependency, input and target identities remain valid. A changed identity needs fresh applicable verification; an unchanged handoff does not need a duplicate broad run. Follow required repository checks and local-first policy.

## 4. Close each stage before expanding

At a stage checkpoint, summarize what passed, its exact revision/artifact, remaining gates by stage, and the next authorized frontier. Make the verified component available for later adoption instead of burying it under unfinished product work.

Continue to the next stage when it is already in scope. If the owner stops or defers it, stop dispatching and starting new work, safely finish or cancel owned jobs, retain useful artifacts/commits and leave a concrete resume handoff. Do not keep pursuing deferred qualification.

If a target/driver repeatedly fails or a long phase exceeds its expected cost, report the new constraint and reassess the smallest route to the current boundary. Fix a required observation gap before repeating the expensive run; do not launch unrelated repair or qualification work.

## 5. Review and deliver the selected boundary

Run independent code review against repository standards and the selected spec requirements. Use a single implementer to fix review findings, then repeat affected checks on the new candidate.

Mark the PR ready, land and close tickets only as the owning workflow and authorization allow. Fresh landed verification is required before a landed/Done claim. Report any actual remaining review, merge or external approval gate separately.

The final handoff states the verified boundary, revisions/PRs/artifacts, checks and real behavior, limitations, and exact remaining owner actions. Preserve useful ignored evidence and inspect uncommitted/untracked data before cleaning only completed inactive worktrees through their owning tools.

Adapted from [Matt Pocock's implement-spec](https://github.com/mattpocock/skills); [MIT license](LICENSE), [source provenance](SOURCE.md).
