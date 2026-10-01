#!/usr/bin/env python3
"""Review and approve a measured cleanup entirely inside an interactive Terminal."""
import argparse
import curses
import json
import os
from pathlib import Path
import sys
import threading

try:
    from . import terminal_view as view
    from .access import ACCESS_STEPS, open_settings
    from .cleanup_items import build_items
    from .cleanup_plan import SafetyError, create_plan, public_plan, validate_confirmation
    from .cleanup_execute import execute
except ImportError:
    import terminal_view as view
    from access import ACCESS_STEPS, open_settings
    from cleanup_items import build_items
    from cleanup_plan import SafetyError, create_plan, public_plan, validate_confirmation
    from cleanup_execute import execute


class Selection:
    def __init__(self, items):
        self.items, self.selected = items, set()
        self.query, self.category, self.cursor = "", "all", 0

    def visible(self):
        rows = [row for row in self.items
                if self.query.casefold() in (row["path"] + " " + row["category"]).casefold()
                and (self.category == "all" or
                     self.category == "selectable" and row["selectable"] or
                     row["category"] == self.category)]
        self.cursor = min(max(0, self.cursor), max(0, len(rows) - 1))
        return rows

    def current(self):
        rows = self.visible()
        return rows[self.cursor] if rows else None

    def toggle(self):
        row = self.current()
        if not row:
            return "No item selected."
        if not row["selectable"]:
            return "Unavailable: " + row["reason"] + " (d: details)"
        if row["id"] in self.selected:
            self.selected.remove(row["id"])
        elif len(self.selected) < 200:
            self.selected.add(row["id"])
        else:
            return "Choose at most 200 items in one batch."
        return "Selection changed. r: review exact paths before deletion."

    def select_page(self, count):
        start = self.cursor // count * count
        for row in self.visible()[start:start + count]:
            if row["selectable"] and len(self.selected) < 200:
                self.selected.add(row["id"])

    def filter_next(self):
        options = ["all", "selectable"] + sorted({row["category"] for row in self.items})
        self.category = options[(options.index(self.category) + 1) % len(options)]
        self.cursor = 0


def load_report(report_dir, name):
    path = report_dir / name
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"A regular local {name} is required")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Invalid {name}")
    return value


def job(screen, title, function, approved=False):
    """Keep progress drawing on the curses thread while inspection runs."""
    values, done = {}, threading.Event()
    def work():
        try:
            values["result"] = function()
        except Exception as error:
            values["error"] = error
        finally:
            done.set()
    worker = threading.Thread(target=work)
    worker.start()
    tick, interrupted = 0, False
    while not done.is_set():
        try:
            if done.wait(0.12):
                break
            label = ("Already approved: finishing safely and saving results..." if approved else
                     "Cancelling preparation; waiting for inspection to finish...") if interrupted else title
            view.draw_work(screen, label, tick)
            tick += 1
        except KeyboardInterrupt:
            interrupted = True
    worker.join()
    if interrupted and not approved:
        raise KeyboardInterrupt
    if "error" in values:
        raise values["error"]
    return values.get("result")


def read_text(screen, title, initial=""):
    value = initial
    while True:
        view.draw_panel(screen, title, [], footer="Enter: accept | Esc: cancel", prompt=value)
        key = screen.get_wch()
        if key in ("\n", "\r", curses.KEY_ENTER):
            return value
        if key == "\x1b":
            return None
        if key in (curses.KEY_BACKSPACE, "\x7f", "\b"):
            value = value[:-1]
        elif isinstance(key, str) and key.isprintable() and len(value) < 200:
            value += key


def scroll_panel(screen, title, lines):
    offset = 0
    while True:
        offset, maximum = view.draw_panel(screen, title, lines, offset)
        key = screen.get_wch()
        if key in ("\x1b", "q", "\n", "\r"):
            return
        offset = scroll_offset(key, offset, screen, maximum)


def scroll_offset(key, offset, screen, maximum):
    changes = {curses.KEY_DOWN: 1, curses.KEY_UP: -1,
               curses.KEY_NPAGE: max(1, screen.getmaxyx()[0] - 6),
               curses.KEY_PPAGE: -max(1, screen.getmaxyx()[0] - 6)}
    return min(maximum, max(0, offset + changes.get(key, 0)))


def approval_lines(plan, preview):
    reviewed = public_plan(plan)
    lines = ["PREVIEW ONLY: nothing will be deleted." if preview else
             "PERMANENT deletion. Only these validated exact paths will be removed.",
             "APFS snapshots/shared data can reduce actual recovery.", ""]
    for row in reviewed["items"]:
        lines += [f"DELETE {view.size(row['allocated_bytes'])}: {row['path']}"]
    if reviewed["blocked"]:
        lines += ["", "SKIPPED: these paths WILL NOT be deleted:"]
        for row in reviewed["blocked"]:
            lines += [row["path"], "  Reason: " + row["reason"]]
    lines += ["", f"Validated batch: {len(reviewed['items'])} items, up to {view.size(reviewed['estimated_bytes'])}"]
    if reviewed.get("shared_bytes"):
        lines += [f"{view.size(reviewed['shared_bytes'])} linked outside this batch; kept out of recovery estimate."]
    return lines


def confirm(screen, plan, preview=False):
    typed, offset = "", 0
    lines = approval_lines(plan, preview)
    while True:
        footer = "Type DELETE then Enter to " + ("save preview" if preview else "approve this exact batch") + " | Esc: keep editing"
        offset, maximum = view.draw_panel(screen, "FINAL BATCH REVIEW", lines, offset, footer,
                                         "Approval: " + typed)
        key = screen.get_wch()
        if key == "\x1b":
            return None
        if key in ("\n", "\r", curses.KEY_ENTER):
            if typed == "DELETE" and plan["items"]:
                payload = {"plan_id": plan["id"], "digest": plan["digest"], "confirmed": True}
                validate_confirmation(plan, payload)
                return payload
            typed = ""
        elif key in (curses.KEY_BACKSPACE, "\x7f", "\b"):
            typed = typed[:-1]
        elif isinstance(key, str) and key.isprintable() and len(typed) < 6:
            typed += key
        else:
            offset = scroll_offset(key, offset, screen, maximum)


def interactive(screen, report_dir, summary, scan, items, preview=False):
    try:
        curses.curs_set(0)
    except curses.error:
        pass
    state, message = Selection(items), ""
    while True:
        view.draw_list(screen, state, summary, scan, message, preview)
        key = screen.get_wch()
        if key in ("q", "\x1b"):
            return None
        if key == " ":
            message = state.toggle()
        elif key in (curses.KEY_DOWN, "j"):
            state.cursor += 1
        elif key in (curses.KEY_UP, "k"):
            state.cursor -= 1
        elif key == curses.KEY_NPAGE:
            state.cursor += view.page_size(screen)
        elif key == curses.KEY_PPAGE:
            state.cursor -= view.page_size(screen)
        elif key == "a":
            state.select_page(view.page_size(screen))
        elif key == "c":
            state.selected.clear()
            message = "All selections cleared."
        elif key == "f":
            state.filter_next()
        elif key == "/":
            value = read_text(screen, "SEARCH PATHS / CATEGORIES", state.query)
            if value is not None:
                state.query, state.cursor = value, 0
        elif key == "d" and state.current():
            row = state.current()
            scroll_panel(screen, "ITEM DETAILS", [row["path"], row["category"],
                         "Allocated: " + view.size(row["allocated_bytes"]), row["reason"],
                         row.get("next_step", ""),
                         "Space selects this item; final approval happens in batch review." if row["selectable"]
                         else "This is shown for investigation; it is not yet an exact deletion operation."])
        elif key == "p":
            scroll_panel(screen, "FULL DISK ACCESS SETUP", [ACCESS_STEPS,
                         "Settings will open after this panel. No browser or deletion approval."])
            open_settings()
            return {"state": "access_setup", "exit_code": 78}
        elif key in ("r", "\n", "\r", curses.KEY_ENTER):
            if not state.selected:
                message = "Select at least one item with Space first."
                continue
            try:
                ordered = [row["id"] for row in items if row["id"] in state.selected]
                plan = job(screen, "Preparing exact batch for final review...",
                           lambda: create_plan(ordered, items, Path.home()))
                payload = confirm(screen, plan, preview)
                if payload is None:
                    message = "Final review cancelled. No deletion approved."
                    continue
                return job(screen, "Applying approved batch; preserving outcome evidence...",
                           lambda: execute(plan, payload, report_dir, Path.home(), preview,
                                           summary.get("capacity", {}).get("target_percent", 50)), approved=True)
            except (OSError, ValueError) as error:
                scroll_panel(screen, "BATCH COULD NOT PROCEED", [str(error), "Nothing newly approved. Review a fresh batch."])
                message = "Review failed. Details were displayed; retry after resolving them."


def run_review(report_dir, preview=False):
    os.umask(0o077)
    if not sys.stdin.isatty() or not sys.stdout.isatty():
        raise RuntimeError("Cleanup review needs an interactive Terminal; no approval or deletion occurred.")
    report_dir = Path(report_dir).expanduser()
    if report_dir.is_symlink() or not report_dir.is_dir():
        raise ValueError("A regular local report directory is required")
    report_dir = report_dir.resolve()
    summary, scan = load_report(report_dir, "summary.json"), load_report(report_dir, "scan.json")
    items = build_items(summary, scan)
    return curses.wrapper(interactive, report_dir, summary, scan, items, preview)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report-dir", required=True, type=Path)
    parser.add_argument("--preview", action="store_true")
    args = parser.parse_args(argv)
    result = run_review(args.report_dir, args.preview)
    print(json.dumps(result or {"state": "cancelled", "message": "No deletion approved."}, indent=2))
    return result.get("exit_code", 0) if result else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nReview interrupted; no new approval inferred.", file=sys.stderr)
        sys.exit(130)
    except (OSError, ValueError, RuntimeError, curses.error) as error:
        print("macbook-cleanup terminal: " + view.safe(error), file=sys.stderr)
        sys.exit(1)
