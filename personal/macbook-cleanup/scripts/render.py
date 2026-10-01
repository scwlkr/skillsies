"""Standalone HTML rendering; no remote assets or path interpolation into script."""
from html import escape


def size(number):
    number = float(number)
    for unit in ("B", "KiB", "MiB", "GiB", "TiB", "PiB"):
        if number < 1024 or unit == "PiB":
            return f"{number:,.1f} {unit}" if unit != "B" else f"{number:,.0f} B"
        number /= 1024


def safe(value):
    return escape(str(value), quote=True)


def _table(items, candidate=False):
    heading = "<th>Allocated</th><th>Logical</th><th>Path</th>"
    if candidate:
        heading += "<th>Review / next step</th>"
    rows = []
    for item in items:
        row = f"<td class='number'>{size(item['allocated_bytes'])}</td><td class='number muted'>{size(item.get('logical_bytes', 0))}</td><td class='path'>{safe(item['path'])}</td>"
        if candidate:
            row += (f"<td><span class='tag'>{safe(item.get('category', 'review'))}</span>"
                    f"<p>{safe(item['action'])}</p><small class='muted'>"
                    f"Risk: {safe(item.get('risk', 'requires review'))}</small></td>")
        rows.append(f"<tr>{row}</tr>")
    if not rows:
        rows.append(f"<tr><td colspan='{4 if candidate else 3}' class='muted'>No items found in this scan.</td></tr>")
    return f"<div class='scroll'><table><thead><tr>{heading}</tr></thead><tbody>{''.join(rows)}</tbody></table></div>"


def _list(values):
    return "<ul>" + "".join(f"<li>{safe(value)}</li>" for value in values) + "</ul>"


def html_report(summary, scan):
    cap = summary["capacity"]
    coverage = summary["coverage"]
    percent = min(100, max(0, cap["used_percent"]))
    target = min(100, max(0, cap["target_percent"]))
    warnings = "".join(f"<p class='notice'>{safe(item)}</p>" for item in cap.get("warnings", []))
    if coverage["error_count"]:
        warnings += (f"<p class='notice'><strong>Coverage incomplete: {coverage['error_count']:,} scan errors.</strong> "
                     f"Some paths remain unmeasured. {safe(coverage['permission_guidance'])}</p>")
    errors = _list(coverage["errors"]) if coverage["errors"] else "<p>No scan errors recorded.</p>"
    excluded = _list(coverage["excluded"]) if coverage["excluded"] else "<p>No explicit exclusions.</p>"
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; img-src 'none'; connect-src 'none'; script-src 'none'">
<title>MacBook disk review</title><style>
:root {{ color-scheme:light; --ink:#17252c; --muted:#607278; --accent:#0a7164; --line:#dfe8e5; }}
* {{ box-sizing:border-box; }} body {{ margin:0; background:#f3f6f4; color:var(--ink); font:16px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; }}
main {{ max-width:1160px; margin:auto; padding:36px 24px 72px; }} h1 {{ font-size:clamp(28px,4vw,42px); letter-spacing:-1.5px; margin:6px 0; }}
h2 {{ font-size:21px; margin:30px 0 12px; }} h3 {{ font-size:17px; }} p {{ margin:8px 0; }} .eyebrow {{ color:var(--accent); font-size:12px; font-weight:700; text-transform:uppercase; letter-spacing:1.5px; }}
.muted,small {{ color:var(--muted); }} .card {{ padding:24px; background:white; border:1px solid var(--line); border-radius:16px; margin-top:24px; }}
.hero {{ display:flex; gap:28px; align-items:center; justify-content:space-between; flex-wrap:wrap; }} .big {{ font-size:56px; letter-spacing:-2px; line-height:1.2; font-weight:700; }}
.goal {{ background:#e7f3ed; padding:18px 24px; border-radius:12px; }} .goal strong {{ font-size:26px; display:block; }}
.bar {{ position:relative; height:16px; background:#e4ece9; border-radius:8px; margin:24px 0 8px; }} .fill {{ height:100%; background:var(--accent); border-radius:8px; }}
.marker {{ position:absolute; top:-5px; height:26px; border-left:2px solid #a66b29; }} .legend {{ display:flex; justify-content:space-between; font-size:13px; color:var(--muted); }}
.notice {{ padding:12px 16px; border-left:3px solid #aa752d; background:#faf4e8; }} .stats {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(200px,1fr)); gap:20px; margin:20px 0; }}
.stats strong {{ display:block; font-size:25px; }} .scroll {{ overflow-x:auto; border:1px solid var(--line); border-radius:12px; background:white; }}
table {{ border-collapse:collapse; width:100%; font-size:14px; }} th {{ background:#eaf0ed; font-size:12px; text-align:left; text-transform:uppercase; letter-spacing:.5px; padding:13px; }}
td {{ padding:14px; border-top:1px solid var(--line); vertical-align:top; }} td p {{ margin:8px 0; min-width:220px; }} .number {{ white-space:nowrap; font-variant-numeric:tabular-nums; }}
.path {{ font:12px/1.6 ui-monospace,SFMono-Regular,Menlo,monospace; overflow-wrap:anywhere; min-width:160px; }} .tag {{ display:inline-block; background:#edf4f1; border-radius:5px; padding:2px 6px; font-size:12px; }}
details {{ margin-top:16px; }} summary {{ cursor:pointer; font-weight:600; }} li {{ margin:6px 0; overflow-wrap:anywhere; }} footer {{ margin-top:32px; font-size:13px; color:var(--muted); }}
@media print {{ body {{ background:white; }} main {{ padding:0; }} .scroll {{ overflow:visible; }} details {{ display:block; }} .card {{ break-inside:avoid; }} }}
</style></head><body><main>
<div class="eyebrow">Local storage review · no files deleted</div><h1>Make room for what matters.</h1>
<p class="muted">Measured {safe(cap['measured_at'])} · {safe(cap['source'])}</p>
<section class="card"><div class="hero"><div><div class="big">{cap['used_percent']:.1f}%</div>
<p>{size(cap['used_bytes'])} used of {size(cap['total_bytes'])} · {size(cap['free_bytes'])} available</p></div>
<div class="goal"><span>Space needed for {cap['target_percent']:g}% or less</span><strong>{size(cap['reclaim_needed_bytes'])}</strong></div></div>
<div class="bar" role="meter" aria-label="Disk usage" aria-valuemin="0" aria-valuemax="100" aria-valuenow="{percent:.1f}"><div class="fill" style="width:{percent:.3f}%"></div><span class="marker" style="left:{target:.3f}%"></span></div>
<div class="legend"><span>0% used</span><span>Gold marker: {cap['target_percent']:g}% target</span><span>100%</span></div>{warnings}</section>
<section class="card"><h2 style="margin-top:0">What the scan suggests</h2><p>{safe(summary['assessment'])}</p>
<div class="stats"><div><span class="muted">Candidate upper bound</span><strong>{size(summary['candidate_upper_bound_bytes'])}</strong></div>
<div><span class="muted">Optimistic usage after all candidates</span><strong>{summary['optimistic_used_percent']:.1f}%</strong></div>
<div><span class="muted">Optimistic remaining target gap</span><strong>{size(summary['optimistic_residual_gap_bytes'])}</strong></div></div>
<p class="notice">Metadata identifies places to review. These estimates do not confirm recoverable space or authorize removal.</p></section>
<h2>Ranked review candidates</h2><p class="muted">Generated data first, then app-managed storage and personal data. Confirm ownership and backups before acting.</p>
{_table(summary['candidates'], True)}
<h2>Largest directories</h2><p class="muted">Inclusive totals: nested directories and their files overlap. Do not add these rows together.</p>
{_table(scan.get('top_directories', [])[:20])}
<h2>Largest files</h2><p class="muted">Ranked by allocated size. Logical size shows how large the file appears to applications.</p>
{_table(scan.get('top_files', [])[:20])}
<section class="card"><h2 style="margin-top:0">Scan coverage</h2><p><strong>Scope: {safe(coverage['scope'])}.</strong> Capacity describes the target disk; inventory covers only the selected roots below.</p>
<p>{coverage['elapsed_seconds']:.2f}s · {coverage['files']:,} files · {coverage['directories']:,} directories · {size(coverage['allocated_bytes'])} allocated observed</p>
<p>Skipped: {coverage['hardlink_duplicates']:,} duplicate hard links, {coverage['symlinks_skipped']:,} symlinks, {coverage['dataless_skipped']:,} cloud placeholders, {coverage['external_mounts_skipped']:,} external mounts.</p>
<p><strong>{coverage['error_count']:,} scan errors</strong> · up to 100 details retained. Permission errors leave parts of the disk unmeasured.</p>
<details><summary>Selected scan roots</summary>{_list(coverage['roots'])}</details>
<details><summary>Explicit exclusions</summary>{excluded}</details>
<details><summary>Error details</summary>{errors}</details></section>
<section class="card"><h2 style="margin-top:0">Limits and next step</h2>{_list(summary['limitations'])}
<p><strong>Review the contents, confirm backups, then choose specific cleanup actions.</strong> Rescan after cleanup to verify the actual disk percentage.</p></section>
<footer>Private report · no external assets, analytics, or network requests · paths remain in these local files.</footer>
</main></body></html>"""
