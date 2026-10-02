---
name: wstack-code-review
description: "Review a branch, PR or working diff against repository standards and its originating spec. Report the two axes separately using Wstack principles."
---
Apply [Wstack](../wstack/SKILL.md) shared rules; don't reroute. Review-only: no target edits, commits or external posts unless requested.

1. Pin scope: explicit base/range wins; otherwise infer PR target/branch merge-base, or `HEAD` for worktree review. Resolve base/head SHAs; snapshot requested staged/unstaged/untracked changes + relevant contents; record comparison/artifact hash. Bad ref → block; empty → no changes; ambiguous scope → ask.
2. Spec: user-supplied source → repository tracker issue/discussion + commit references → matching local spec. Missing → report “Spec not assessed: no spec available”; continue Standards.
3. Standards: applicable `AGENTS.md` + repository coding docs + [smells](references/smells.md). Repository rules override heuristics; label smells “possible”, never hard violations. Skip cosmetic/tool-enforced noise; report actual failing checks/regressions.
4. Nontrivial diff → independent Standards/Spec reviewers in parallel when available + authorized; otherwise → separate passes; missing spec → Standards only. Give both pinned artifact + commit list; Standards gets rule sources/smells, Spec gets requirements/discussion. Parent validates findings against evidence; discard unsupported claims.
5. Standards: documented breaches + consequential smells. Spec: missing/partial requirements, wrong behavior, unrequested scope. Each finding → severity, file:line, evidence/rule, affected scenario, minimal fix. Separate reports; prioritize within each axis, never combine/rerank across axes. Include per-axis count/worst finding, checks + coverage gaps; one passing axis cannot imply overall acceptance.

Adapted from [Matt Pocock's code-review](https://github.com/mattpocock/skills/blob/d81f3a183412e71a5b1e84ca21bc1a35eea03a60/skills/engineering/code-review/SKILL.md); [MIT license](LICENSE).
