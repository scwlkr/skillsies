---
name: wstack-implement
description: "Implement a requested spec or issue through verified delivery, using Wstack principles and code review."
---
Apply [Wstack](../wstack/SKILL.md) shared rules; don't reroute.

1. Read requested spec/issues + discussion; repository tracker owns execution. Acceptance + existing code/work → bounded plan; capture starting SHA + existing changes.
2. TDD where useful, at agreed behavioral seams; typecheck + focused behavior checks as units change; final repository gates.
3. Review task diff with [wstack-code-review](../wstack-code-review/SKILL.md); pass spec + baseline/artifact + check evidence. Fix substantiated in-scope findings → repeat affected checks/review.
4. Commit/deliver per Wstack + repository rules; report acceptance evidence + unresolved gates.

Adapted from [Matt Pocock's implement](https://github.com/mattpocock/skills/blob/d81f3a183412e71a5b1e84ca21bc1a35eea03a60/skills/engineering/implement/SKILL.md); [MIT license](LICENSE).
