Fowler baseline, adapted from Matt Pocock's code-review. Repository rules win; heuristics need concrete consequences. No speculative refactors; skip cosmetic/tool-enforced noise.

- Mysterious Name: unclear purpose → rename/rethink design.
- Duplicated Code: repeated behavior → share when contracts match.
- Feature Envy: behavior coupled to another owner's data → move to owner.
- Data Clumps: repeated fields/parameters travel together → domain type.
- Primitive Obsession: primitive hides domain constraints → domain type.
- Repeated Switches: repeated dispatch → shared table/state model/polymorphism.
- Shotgun Surgery: one concern forces scattered edits → group what changes together.
- Divergent Change: module changes for unrelated reasons → split responsibilities.
- Speculative Generality: unused abstraction/hooks/parameters → delete/inline.
- Message Chains: caller depends on deep navigation → hide traversal at owner boundary.
- Middle Man: delegation adds no contract → inline/remove.
- Refused Bequest: inherited contract mostly ignored → composition.
