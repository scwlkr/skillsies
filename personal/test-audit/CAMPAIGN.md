# Subsystem test-audit campaign

Campaign mode covers one subsystem's full test surface in a coherent effort. The value bar, retention bar, candidate evidence, and validation rules in [SKILL.md](SKILL.md) apply to every lane. This guide adds campaign planning and preservation checks. Finish each step's completion criterion before moving on; adapt the details to the repository's own layout and workflow.

## 1. Baseline

Choose and record the base revision. Identify every in-scope test file and relevant test or support suite. When test execution is authorized, record its baseline pass/fail state using the repository's documented commands; otherwise mark the baseline unverified and say why. Track test, support, and production line counts when they will help evaluate the change. Keep pre-existing failures separate; investigate failures that may be real product defects.

Done when every in-scope suite has a recorded baseline result or a clear reason it remains unverified.

## 2. Lanes and inventory

Split the test surface into lanes along production ownership boundaries, not merely file prefixes. Include relevant tests at shared boundaries and any QA, integration, or live-proof harnesses the subsystem owns. Use the repository's actual structure; do not assume particular package, plugin, or source directories.

Done when every in-scope test file and scenario belongs to exactly one lane.

## 3. Read-only ledger per lane

Keep this pass read-only. If parallel review is available and appropriate, give each reviewer a bounded lane; otherwise work through the lanes sequentially. Read every assigned test in full, including parameterized cases, along with its production owner, entry points, callers, relevant history, and CI routing.

Give each test declaration one mark and an evidence line:

- `R`: retain, naming the contract and failure it catches; note any move to a better-named owner;
- `F`: retain the contract but repair the assertion;
- `C`: consolidate, naming the stronger owner that absorbs the assertion;
- `D`: delete, naming the remaining proof or explaining why there is no independent contract.

Judge tests by their assertions, not their names. Mark parameter rows separately only when they protect different contracts or have different evidence.

Done when every declaration in every lane has a mark and evidence.

## 4. Layer plan per lane

Treat the ledger as evidence, not as an edit list. Make a second read-only pass to find redundant layers and correct ledger errors. Name the keeper suite for each contract; prefer a real boundary with controlled dependencies over a mocked collaborator when it gives stronger, practical proof.

Done when each lane plan names its retired tests or layers, its keeper per contract, assertions to carry into keepers, and test-only production seams that can be removed.

## 5. Cutover

Edit one lane at a time. Assign one owner to shared harnesses and support files to avoid conflicting edits. Remove the test-only seams unlocked by each lane, such as injection parameters, getters, reset exports, and indirection layers. Update test inventories, CI routing, or coverage budgets only when the repository uses them. Add durable test-ownership guidance to a scoped `AGENTS.md` only when the campaign found a reusable rule that belongs there.

Done when every lane plan is applied and each keeper's focused validation is complete or its blocker is recorded.

## 6. Preservation review

Before claiming completion, compare deleted coverage with the remaining keepers. Use independent reviewers for separate boundary groups when that materially improves confidence and the workflow permits it. Look for contracts that lost their only proof and assertions that cannot fail or never reach the intended production path.

For high-risk restored contracts, use a controlled mutation or pre-fix reproduction to show the keeper detects the regression when this is safe and practical. Restore any temporary mutation completely.

Done when each reported gap is restored or rejected with source evidence, and important restored contracts have credible failure evidence.

## 7. Product defects

A baseline failure that persists in a keeper may be a product defect. Reproduce it at the owning boundary, report it, and handle its repair as a separate authorized change. When practical, compare a failing control with a passing candidate on the same harness. Record unrelated discrepancies as follow-ups rather than expanding the campaign.

Done when each repaired defect has evidence for both the prior failure and the candidate behavior, or its unresolved state is clearly reported.

## 8. Reconcile and hand off

Long campaigns can overlap changes on the target branch. Follow the repository's merge or rebase convention. When concurrent changes affect a test being retired, preserve the intended contract in the keeper and confirm new regressions still have an owner. Run the subsystem's required and authorized validation against the resulting revision; report anything left unverified.

Hand off with the [SKILL.md](SKILL.md) report, plus:

- baseline and final test/support counts when collected, with production counted separately;
- lanes, retired layers, and keepers;
- preservation gaps and their evidence;
- product defects with control and candidate proof, when repaired.
