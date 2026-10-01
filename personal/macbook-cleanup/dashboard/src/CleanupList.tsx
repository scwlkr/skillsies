import { useState } from "react";
import { Search, ChevronDown, ChevronRight, Folder } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { size, shortPath, displayName } from "./lib/metrics.mjs";
import type { Item } from "./types";
export function CleanupList({
  items,
  selected,
  toggle,
  disabled,
}: {
  items: Item[];
  selected: Set<string>;
  toggle: (id: string) => void;
  disabled: boolean;
}) {
  const [query, setQuery] = useState(""),
    [filter, setFilter] = useState("all"),
    [page, setPage] = useState(0),
    [expanded, setExpanded] = useState<string>();
  const filtered = items.filter(
    (i) =>
      (filter === "all" ||
        (filter === "selectable" ? i.selectable : i.category === filter)) &&
      `${i.path} ${i.category}`.toLowerCase().includes(query.toLowerCase()),
  );
  const pages = Math.max(1, Math.ceil(filtered.length / 8)),
    current = Math.min(page, pages - 1);
  return (
    <section className="mt-7" aria-label="Cleanup candidates">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-lg font-semibold tracking-tight">
            Find your next cleanup
          </h2>
          <p className="mt-1 text-xs text-muted-foreground">
            Select specific items. Review and confirm the whole batch when
            you’re ready.
          </p>
        </div>
        <Badge
          variant="outline"
          className="border-border py-1.5 text-muted-foreground"
        >
          Nothing deleted until confirmation
        </Badge>
      </div>
      <div className="my-4 flex flex-wrap gap-3">
        <div className="relative min-w-60 flex-1">
          <Search
            size={15}
            className="absolute left-3 top-3 text-muted-foreground"
          />
          <Input
            aria-label="Search cleanup items"
            placeholder="Search names, paths, or categories…"
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              setPage(0);
            }}
            className="h-10 border-border bg-card pl-9"
          />
        </div>
        <select
          aria-label="Filter cleanup items"
          className="h-10 rounded-md border border-border bg-card px-3 text-sm"
          value={filter}
          onChange={(e) => {
            setFilter(e.target.value);
            setPage(0);
          }}
        >
          <option value="all">All categories</option>
          <option value="selectable">Ready to review</option>
          {[...new Set(items.map((i) => i.category))].map((c) => (
            <option key={c}>{c}</option>
          ))}
        </select>
      </div>
      <div className="overflow-hidden rounded-xl border border-border bg-card">
        <div className="grid grid-cols-[2rem_1fr_auto] gap-3 border-b border-border px-5 py-2.5 text-[11px] uppercase tracking-wider text-muted-foreground">
          <span />
          <span>Item / location</span>
          <span>Allocated space</span>
        </div>
        {filtered.slice(current * 8, current * 8 + 8).map((item) => (
          <div key={item.id} className="border-b border-border last:border-b-0">
            <div
              className={`grid grid-cols-[2rem_1fr_auto] items-center gap-3 px-5 py-3 ${selected.has(item.id) ? "bg-[#243242]" : ""}`}
            >
              <Checkbox
                aria-label={`Select ${displayName(item)}`}
                checked={selected.has(item.id)}
                disabled={!item.selectable || disabled}
                onCheckedChange={() => toggle(item.id)}
                className="size-4"
              />
              <button
                className="min-w-0 text-left"
                onClick={() =>
                  setExpanded(expanded === item.id ? undefined : item.id)
                }
                aria-expanded={expanded === item.id}
              >
                <div className="flex items-center gap-2">
                  <Folder
                    size={15}
                    className="shrink-0 text-muted-foreground"
                  />
                  <span className="truncate text-sm font-medium">
                    {displayName(item)}
                  </span>
                  <span className="hidden rounded bg-secondary px-1.5 py-0.5 text-[10px] text-muted-foreground sm:inline">
                    {item.category}
                  </span>
                  {expanded === item.id ? (
                    <ChevronDown
                      size={13}
                      className="ml-auto shrink-0 text-muted-foreground"
                    />
                  ) : (
                    <ChevronRight
                      size={13}
                      className="ml-auto shrink-0 text-muted-foreground"
                    />
                  )}
                </div>
                <div className="mt-1 truncate text-[11px] text-muted-foreground">
                  {shortPath(item.path)}
                </div>
              </button>
              <div className="text-right">
                <div className="text-sm font-medium tabular-nums">
                  {size(item.allocated_bytes)}
                </div>
                <div
                  className={`mt-1 text-[10px] ${item.selectable ? "text-[#91c5b1]" : "text-muted-foreground"}`}
                >
                  {item.selectable
                    ? "Select for deletion"
                    : "App / manual review"}
                </div>
              </div>
            </div>
            {expanded === item.id && (
              <div className="space-y-2 bg-background/40 px-5 py-4 text-xs leading-relaxed sm:pl-16">
                <p className="break-all font-mono text-muted-foreground">
                  {item.path}
                </p>
                <p>{item.reason}</p>
                <p className="text-muted-foreground">
                  Logical size {size(item.logical_bytes)} · allocated estimate{" "}
                  {size(item.allocated_bytes)}
                </p>
                {item.selectable && (
                  <p className="text-[#e6a377]">
                    Permanent deletion after final approval. Generated data may
                    need rebuilding or downloading again.
                  </p>
                )}
              </div>
            )}
          </div>
        ))}
        {!filtered.length && (
          <div className="p-10 text-center text-sm text-muted-foreground">
            No matching items.
          </div>
        )}
      </div>
      <div className="mt-3 flex items-center justify-between text-xs text-muted-foreground">
        <span>
          {filtered.length} items · {items.filter((i) => i.selectable).length}{" "}
          selectable
        </span>
        <div className="flex items-center gap-3">
          <Button
            variant="ghost"
            size="sm"
            disabled={current === 0}
            onClick={() => setPage(current - 1)}
          >
            Previous
          </Button>
          <span>
            {current + 1} / {pages}
          </span>
          <Button
            variant="ghost"
            size="sm"
            disabled={current >= pages - 1}
            onClick={() => setPage(current + 1)}
          >
            Next
          </Button>
        </div>
      </div>
    </section>
  );
}
