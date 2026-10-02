---
name: wstack
description: "Use Wstack's connected personal workflows when the user asks to work through Wstack. Route project setup to the existing setup skill and carry task context through execution and verification."
---

# Wstack

Wstack owns the shared method and routing; each member owns its workflow. Interpret the text after the invocation as the user's task. In Codex, select `$wstack`, for example `$wstack setup this project`; treat `/wstack setup this project` as the same intent when supplied as a message.

## Shared method

- Establish the requested outcome and completion evidence. Preserve the target repository's instructions, tracker, delivery rules, and the user's scope and authorization.
- Inspect observable facts before asking. Reserve questions for missing information or consequential preferences that inspection cannot resolve.
- Choose the smallest workflow that achieves the outcome. Use additional skills, prototypes, or agents only when they serve the task and delegation is authorized.
- Carry verified results forward. Distinguish completed work, handoffs, blockers, and unverified behavior; a member's partial success does not complete the overall task.

## Route the request

Identify the requested workflow, target project, and relevant task context. Prefer the explicit workflow; otherwise infer it from the outcome. For "this project," use the current working repository unless the user identifies another target.

| Intent | Member to read in full |
| --- | --- |
| `setup`: apply personal project conventions to a new or existing project | [scwlkr-project-setup](../scwlkr-project-setup/SKILL.md) |

Resolve the member path relative to this skill's directory. Load only the selected member and the resources its current workflow requires. Explain the selection briefly, then follow that member's instructions with the original request and target.

For setup, run commands from the setup skill's directory and pass the target project as `ROOT`. Its scripts, scope limits, checks, and handoff own setup behavior. Keep its instructions in the member rather than duplicating them here. Setup remains independently usable.

Setup is currently the only registered member. An implementation request, including an issue URL, does not imply project setup. If no route matches, state that a dedicated Wstack workflow is not yet registered and continue the authorized task using repository instructions and available tools. Do not present that work as a member execution or create or install skills merely to fill the gap.

If a registered member cannot be read, report the missing path as a blocker to that workflow. Do not claim to have followed an unavailable skill.

## Carry the result forward

Keep the handoff in task context unless the repository or member requires an artifact. Carry only what the next stage needs:

- Requested outcome, target, and active constraints.
- Completed changes or artifacts and their verification evidence.
- Remaining work, uncertainties, blockers, and authorization limits.

Use another registered member only when the requested outcome needs it. Finish with the outcome, material verification, and remaining gates. For setup, preserve the distinction between scaffold readiness and application or CI readiness.
