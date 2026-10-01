import {Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription} from '@/components/ui/dialog';
import {Badge} from '@/components/ui/badge';
import type {Session} from './types';
export function DetailsDialog({session, open, close}: {session: Session; open: boolean; close: () => void}) {
  const c = session.summary.coverage;
  return <Dialog open={open} onOpenChange={v => {if (!v) close()}}><DialogContent className="max-h-[85vh] max-w-2xl overflow-auto border-border bg-card"><DialogHeader><DialogTitle>Scan details & access</DialogTitle><DialogDescription>Local metadata scan · {c.scope} · {Number(c.elapsed_seconds).toFixed(1)} seconds</DialogDescription></DialogHeader>
    <p className="text-xs text-muted-foreground">Capacity source: {session.summary.capacity.source}</p>{session.summary.capacity.warnings?.map((warning, i) => <p key={i} className="text-xs text-destructive">{warning}</p>)}
    <div className="flex flex-wrap gap-2"><Badge variant="secondary">{Number(c.files).toLocaleString()} files</Badge><Badge variant="secondary">{c.error_count} access / scan errors</Badge><Badge variant="secondary">{Number(c.dataless_skipped).toLocaleString()} cloud placeholders skipped</Badge></div>
    {Boolean(c.error_count) && <div className="rounded-lg border border-[#725040] bg-[#30251f] p-4 text-sm leading-relaxed"><p className="font-medium">Fill the access gaps</p><ol className="mt-2 list-decimal space-y-1 pl-5 text-muted-foreground"><li>Open System Settings → Privacy & Security → Full Disk Access.</li><li>Enable Terminal (or the app running your scan).</li><li>Quit and relaunch that app, then rerun the audit.</li></ol><p className="mt-3 text-xs">An administrator password covers Unix permissions only. macOS privacy approval is a separate, one-time Settings step.</p></div>}
    <div className="text-xs leading-relaxed"><p className="mb-2 font-medium">Scan roots</p>{(c.roots || []).map((p: string) => <p key={p} className="break-all font-mono text-muted-foreground">{p}</p>)}</div>
    <div className="space-y-2 text-xs leading-relaxed text-muted-foreground">{session.summary.limitations.map((p, i) => <p key={i}>{p}</p>)}</div>
    <details className="text-xs"><summary className="cursor-pointer text-muted-foreground">Excluded paths and error details</summary><div className="mt-3 space-y-1 break-all font-mono text-muted-foreground">{[...(c.excluded || []), ...(c.errors || [])].map((p, i) => <p key={i}>{p}</p>)}</div></details>
  </DialogContent></Dialog>;
}
