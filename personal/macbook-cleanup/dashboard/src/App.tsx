import { useEffect, useMemo, useState } from "react";
import {
  HardDrive,
  ArrowRight,
  Info,
  CheckCircle2,
  Loader2,
  X,
  Shield,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { StorageCharts } from "./StorageCharts";
import { CleanupList } from "./CleanupList";
import { ReviewDialog } from "./ReviewDialog";
import { DetailsDialog } from "./DetailsDialog";
import { request, offline } from "./lib/api";
import { size, projection } from "./lib/metrics.mjs";
import type { Session, Plan, Result } from "./types";
export function App() {
  const [session, setSession] = useState<Session | null>(
    window.__MACBOOK_REPORT__ || null,
  );
  const [selected, setSelected] = useState(new Set<string>()),
    [plan, setPlan] = useState<Plan | null>(null);
  const [error, setError] = useState(""),
    [busy, setBusy] = useState(false),
    [details, setDetails] = useState(false);
  useEffect(() => {
    if (!offline)
      request<Session>("session")
        .then(setSession)
        .catch((e) => setError(e.message));
  }, []);
  const completed = ["complete", "preview", "error"].includes(
    session?.status.state || "",
  );
  const projected = useMemo(
    () =>
      session
        ? projection(session.summary.capacity, session.items, selected)
        : { bytes: 0, percent: 0, gap: 0 },
    [session, selected],
  );
  const toggle = (id: string) =>
    setSelected((previous) => {
      const next = new Set(previous);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  async function review() {
    setBusy(true);
    setError("");
    try {
      setPlan(await request<Plan>("plan", { ids: [...selected] }));
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  async function confirm() {
    if (!plan || !session) return;
    setBusy(true);
    setError("");
    try {
      const status = await request<Result>("confirm", {
        plan_id: plan.id,
        digest: plan.digest,
        confirmed: true,
      });
      setSession({ ...session, status });
      setSelected(new Set());
      setPlan(null);
      await request<Result>("status").catch(() => {});
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  if (!session)
    return (
      <main className="mx-auto max-w-xl p-12">
        <HardDrive className="mb-6 text-primary" />
        <h1 className="text-xl font-semibold">MacBook cleanup</h1>
        <p
          role={error ? "alert" : "status"}
          className="mt-4 text-sm text-muted-foreground"
        >
          {error || "Loading your local disk review…"}
        </p>
      </main>
    );
  const c = session.status.capacity_after || session.summary.capacity;
  return (
    <div className="dark min-h-screen pb-32">
      <header className="border-b border-border bg-card/40">
        <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-3 px-6 py-4">
          <div className="flex items-center gap-3">
            <div className="rounded-lg border border-border bg-card p-2">
              <HardDrive size={19} className="text-primary" />
            </div>
            <span className="text-sm font-semibold tracking-tight">
              macbook-cleanup
            </span>
            <Badge
              variant="outline"
              className="hidden border-border text-[10px] text-muted-foreground sm:inline-flex"
            >
              <span className="mr-1.5 size-1.5 rounded-full bg-[#91c5b1]" />
              Local & private
            </Badge>
          </div>
          <div className="flex items-center gap-4 text-xs text-muted-foreground">
            <span className="hidden sm:inline">✓ Scanned</span>
            <ArrowRight size={12} />
            <span className="text-foreground">2. Select</span>
            <ArrowRight size={12} />
            <span>3. Confirm</span>
            <Button variant="ghost" size="sm" onClick={() => setDetails(true)}>
              <Info size={14} />
              {session.summary.coverage.error_count
                ? `${session.summary.coverage.error_count} access gaps`
                : "Scan details"}
            </Button>
          </div>
        </div>
      </header>
      <main className="mx-auto max-w-7xl px-6 pt-8">
        <div className="mb-6 flex flex-wrap items-end justify-between gap-3">
          <div>
            <p className="mb-2 text-[10px] uppercase tracking-[.18em] text-muted-foreground">
              Storage review
            </p>
            <h1 className="text-3xl font-semibold tracking-tight">
              Make space for what’s next.
            </h1>
            <p className="mt-2 text-sm text-muted-foreground">
              {c.reclaim_needed_bytes
                ? `Your disk is ${c.used_percent.toFixed(1)}% full. Let’s work toward ${c.target_percent}%.`
                : `You’re already below the ${c.target_percent}% target. No cleanup needed.`}
            </p>
          </div>
          <p className="text-xs text-muted-foreground">
            {new Date(c.measured_at).toLocaleString()}
          </p>
        </div>
        {offline && (
          <div className="mb-5 flex items-center gap-2 rounded-lg border border-border px-4 py-3 text-xs text-muted-foreground">
            <Shield size={14} />
            Saved report · selections are exploratory. Open a local review
            session to confirm cleanup.
          </div>
        )}
        {session.preview && !offline && (
          <div className="mb-5 rounded-lg border border-primary/30 px-4 py-3 text-xs text-primary">
            Preview session · no files can be deleted.
          </div>
        )}
        {completed && (
          <div
            role="status"
            className={`mb-5 rounded-lg border p-4 text-sm ${session.status.state === "error" ? "border-destructive/40 text-destructive" : "border-[#446454] text-[#9fd2b7]"}`}
          >
            <div className="flex items-center gap-2">
              <CheckCircle2 size={17} />
              {session.status.state === "preview"
                ? "Preview saved. Nothing deleted."
                : session.status.state === "complete"
                  ? "Cleanup complete."
                  : "Cleanup stopped."}
            </div>
            {session.status.error && (
              <p className="mt-2">{session.status.error}</p>
            )}
            {session.status.capacity_after && (
              <p className="mt-2">
                Measured disk usage: {c.used_percent.toFixed(1)}% ·{" "}
                {size(c.reclaim_needed_bytes)} still needed for the target.
              </p>
            )}
            {session.status.results?.map((r) => (
              <p key={r.id} className="mt-1 break-all text-xs">
                {r.status}: {r.path}
              </p>
            ))}
          </div>
        )}
        <StorageCharts
          session={session}
          projection={
            completed
              ? {
                  bytes: 0,
                  percent: c.used_percent,
                  gap: c.reclaim_needed_bytes,
                }
              : projected
          }
        />
        <CleanupList
          items={session.items}
          selected={selected}
          toggle={toggle}
          disabled={busy || completed}
        />
        {error && !plan && (
          <p role="alert" className="mt-4 text-sm text-destructive">
            {error}
          </p>
        )}
        <p className="mt-3 text-[11px] text-muted-foreground">
          Large app, model, cloud and runtime folders require review in their
          owning tool. Expand an item for its next step.
        </p>
      </main>
      <footer className="fixed bottom-0 left-0 right-0 z-20 border-t border-border bg-[#1b222c]/95 backdrop-blur">
        <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-4 px-6 py-4">
          <div className="flex min-w-0 items-center gap-4">
            <div className="flex size-10 shrink-0 items-center justify-center rounded-lg bg-secondary text-sm font-semibold text-primary">
              {selected.size}
            </div>
            <div>
              <p className="text-sm font-medium">
                {selected.size
                  ? `${size(projected.bytes)} selected for review`
                  : "Choose your cleanup items"}
              </p>
              <p className="mt-1 text-xs text-muted-foreground">
                {selected.size
                  ? `Optimistic disk usage after cleanup: ${projected.percent.toFixed(1)}%`
                  : "Choose disposable items, then approve the batch once."}
              </p>
            </div>
          </div>
          <div className="flex gap-3">
            {selected.size > 0 && (
              <Button
                variant="ghost"
                disabled={busy}
                onClick={() => setSelected(new Set())}
              >
                <X size={14} />
                Clear
              </Button>
            )}
            <Button
              disabled={!selected.size || busy || offline || completed}
              onClick={review}
            >
              {busy ? <Loader2 size={14} className="animate-spin" /> : null}
              Review {selected.size || ""} selected
              <ArrowRight size={14} />
            </Button>
          </div>
        </div>
      </footer>
      <ReviewDialog
        plan={plan}
        preview={session.preview}
        busy={busy}
        error={error}
        close={() => {
          setPlan(null);
          setError("");
        }}
        confirm={confirm}
      />
      <DetailsDialog
        session={session}
        open={details}
        close={() => setDetails(false)}
      />
    </div>
  );
}
