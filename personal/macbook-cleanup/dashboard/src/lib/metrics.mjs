export function size(bytes) {
  let value = Number(bytes) || 0;
  const units = ["B", "KiB", "MiB", "GiB", "TiB"];
  let unit = 0;
  while (Math.abs(value) >= 1024 && unit < units.length - 1) {
    value /= 1024;
    unit++;
  }
  return `${value.toLocaleString("en-US", { maximumFractionDigits: unit ? 1 : 0 })} ${units[unit]}`;
}
export function projection(capacity, items, selected) {
  const unique = new Map(
    items
      .filter((i) => i.selectable && selected.has(i.id))
      .map((i) => [i.id, i]),
  );
  const bytes = [...unique.values()].reduce(
    (n, i) => n + Math.max(0, i.allocated_bytes),
    0,
  );
  const after = Math.max(0, capacity.used_bytes - bytes);
  return {
    bytes,
    percent: (after / capacity.total_bytes) * 100,
    gap: Math.max(
      0,
      after - (capacity.total_bytes * capacity.target_percent) / 100,
    ),
  };
}
export function shortPath(path) {
  return path
    .replace(/^\/System\/Volumes\/Data(?=\/)/, "")
    .replace(/^\/Users\/[^/]+(?=\/|$)/, "~");
}
export function displayName(item) {
  const parts = shortPath(item.path).split("/");
  return ["target", "node_modules"].includes(item.label)
    ? `${parts.at(-2)} · ${item.label}`
    : item.label;
}
