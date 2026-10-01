import test from "node:test";
import assert from "node:assert/strict";
import { projection, shortPath, displayName } from "../src/lib/metrics.mjs";
const capacity = { used_bytes: 850, total_bytes: 1000, target_percent: 50 };
test("only unique selectable allocations count toward projection", () => {
  const first = { id: "a", selectable: true, allocated_bytes: 100 };
  assert.deepEqual(
    projection(
      capacity,
      [first, first, { id: "b", selectable: false, allocated_bytes: 500 }],
      new Set(["a", "b"]),
    ),
    { bytes: 100, percent: 75, gap: 250 },
  );
});
test("optimistic projection clamps to zero and never uses logical size", () => {
  assert.deepEqual(
    projection(
      capacity,
      [
        {
          id: "a",
          selectable: true,
          allocated_bytes: 900,
          logical_bytes: 99999,
        },
      ],
      new Set(["a"]),
    ),
    { bytes: 900, percent: 0, gap: 0 },
  );
});
test("abbreviated paths retain exact meaningful project identity", () => {
  assert.equal(
    shortPath("/System/Volumes/Data/Users/shane/Desktop/dev/App/target"),
    "~/Desktop/dev/App/target",
  );
  assert.equal(
    displayName({ path: "/Users/shane/projects/App/target", label: "target" }),
    "App · target",
  );
});
