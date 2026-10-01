import { AlertTriangle, Trash2 } from "lucide-react";
import {
  AlertDialog,
  AlertDialogContent,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogCancel,
} from "@/components/ui/alert-dialog";
import { Button } from "@/components/ui/button";
import { size } from "./lib/metrics.mjs";
import type { Plan } from "./types";
export function ReviewDialog({
  plan,
  preview,
  busy,
  error,
  close,
  confirm,
}: {
  plan: Plan | null;
  preview: boolean;
  busy: boolean;
  error: string;
  close: () => void;
  confirm: () => void;
}) {
  return (
    <AlertDialog
      open={Boolean(plan)}
      onOpenChange={(open) => {
        if (!open && !busy) close();
      }}
    >
      <AlertDialogContent className="max-w-2xl border-border bg-card">
        <AlertDialogHeader>
          <AlertDialogTitle className="flex items-center gap-2">
            <AlertTriangle size={19} className="text-destructive" />
            {preview
              ? "Preview this cleanup batch"
              : "Confirm permanent deletion"}
          </AlertDialogTitle>
          <AlertDialogDescription>
            {preview
              ? "This preview saves your selected plan. It never deletes files."
              : "Approve these exact paths together. The tool rechecks each item, then removes it permanently. This cannot be undone."}
          </AlertDialogDescription>
        </AlertDialogHeader>
        <div className="max-h-72 overflow-y-auto rounded-lg border border-border">
          {plan?.items.map((i) => (
            <div
              key={i.id}
              className="flex gap-4 border-b border-border p-3 last:border-0"
            >
              <div className="min-w-0 flex-1">
                <p className="text-sm font-medium">{i.label}</p>
                <p className="mt-1 break-all font-mono text-[11px] text-muted-foreground">
                  {i.path}
                </p>
              </div>
              <span className="shrink-0 text-xs tabular-nums">
                {size(i.allocated_bytes)}
              </span>
            </div>
          ))}
        </div>
        {Boolean(plan?.blocked.length) && (
          <div className="text-xs text-destructive">
            <p className="mb-2">
              Skipped items stay intact. You can approve the validated items above.
            </p>
            {plan?.blocked.map((i, n) => (
              <p key={n} className="break-all">
                Skipped: {i.path} — {i.reason || i.error}
              </p>
            ))}
          </div>
        )}
        <p className="text-xs text-muted-foreground">
          Estimated allocation: {size(plan?.estimated_bytes || 0)}. Actual
          recovery can be smaller because of APFS shared data and snapshots.
          This approval has a short expiry.
        </p>
        {error && (
          <p role="alert" className="text-sm text-destructive">
            {error}
          </p>
        )}
        <AlertDialogFooter>
          <AlertDialogCancel disabled={busy} onClick={close}>
            Keep editing
          </AlertDialogCancel>
          <Button
            variant={preview ? "default" : "destructive"}
            disabled={busy || !plan?.items.length}
            onClick={confirm}
          >
            <Trash2 size={14} />
            {busy
              ? "Rechecking and cleaning…"
              : preview
                ? "Confirm preview"
                : `Permanently delete ${plan?.items.length} items`}
          </Button>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}
