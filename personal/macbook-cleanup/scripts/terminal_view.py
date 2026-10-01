"""Terminal drawing only: no file operations or permission decisions."""
import curses
import unicodedata
import textwrap
from pathlib import Path


def safe(value):
    """Render every control/format character literally, including terminal escapes."""
    return "".join(f"\\u{ord(char):04x}" if unicodedata.category(char).startswith("C")
                   else char for char in str(value))


def size(number):
    value = float(number or 0)
    for unit in ("B", "KiB", "MiB", "GiB", "TiB"):
        if abs(value) < 1024 or unit == "TiB":
            return f"{value:.1f} {unit}"
        value /= 1024


def put(screen, y, text, attr=0, x=2):
    height, width = screen.getmaxyx()
    if y < 0 or y >= height or x >= width - 1:
        return
    try:
        screen.addnstr(y, x, safe(text), max(0, width - x - 1), attr)
    except curses.error:
        pass


def bar(percent, width=30):
    count = round(max(0, min(100, percent)) * width / 100)
    return "[" + "#" * count + "." * (width - count) + "]"


def capacity_lines(summary, selected_bytes, width):
    capacity = summary.get("capacity", {})
    total, used = capacity.get("total_bytes", 0), capacity.get("used_bytes", 0)
    percent = used * 100 / total if total else 0
    target = capacity.get("target_percent", 50)
    projected = max(0, used - selected_bytes) * 100 / total if total else 0
    return [f"DISK {bar(percent, min(36, max(10, width - 58)))} {percent:.1f}% used | goal {target:g}%",
            f"{size(used)} used / {size(total)} total | {size(capacity.get('free_bytes'))} free",
            f"Gap to goal: {size(capacity.get('reclaim_needed_bytes'))} | selected: {size(selected_bytes)}",
            f"Optimistic usage after selections: {projected:.1f}% (physical recovery can differ)"]


def page_size(screen):
    return max(1, screen.getmaxyx()[0] - 19)


def compact_path(value, width):
    text = safe(value)
    home = safe(Path.home()) + "/"
    if text.startswith(home):
        text = "~/" + text[len(home):]
    width = max(1, width)
    if len(text) <= width:
        return text
    if width < 8:
        return text[-width:]
    prefix = min(12, width // 3)
    return text[:prefix] + "…" + text[-(width - prefix - 1):]


def draw_list(screen, state, summary, scan, message="", preview=False):
    screen.erase()
    height, width = screen.getmaxyx()
    put(screen, 0, "MACBOOK CLEANUP | TERMINAL" + (" | PREVIEW: NO DELETION" if preview else ""), curses.A_BOLD)
    selected_bytes = sum(row["allocated_bytes"] for row in state.items if row["id"] in state.selected)
    for y, line in enumerate(capacity_lines(summary, selected_bytes, width), 2):
        put(screen, y, line)
    categories = sorted(scan.get("storage_categories", []),
                        key=lambda row: row.get("allocated_bytes", 0), reverse=True)[:3]
    maximum = max((row.get("allocated_bytes", 0) for row in categories), default=1) or 1
    for y, row in enumerate(categories, 7):
        number = row.get("allocated_bytes", 0)
        label = row.get("label", row.get("category", row.get("name", "Files")))
        put(screen, y, f"{safe(label)[:18]:18} {bar(number * 100 / maximum, 18)} {size(number)}")
    put(screen, 10, "Category bars = observed file allocation; APFS shared data may overlap physical use.")
    errors = summary.get("coverage", {}).get("error_count", 0)
    put(screen, 11, f"Access gaps: {errors} | p: permission setup | filter: {state.category} | search: {state.query or '(none)'}")
    put(screen, 12, "  SELECT  ALLOCATED     CATEGORY       EXACT PATH", curses.A_BOLD)
    rows, count = state.visible(), page_size(screen)
    start = state.cursor // count * count
    for offset, row in enumerate(rows[start:start + count]):
        index = start + offset
        marker = "[x]" if row["id"] in state.selected else "[ ]" if row["selectable"] else " --"
        prefix = f"  {marker}  {size(row['allocated_bytes']):>11}  {safe(row['category'])[:12]:12} "
        line = prefix + compact_path(row["path"], width - len(prefix) - 3)
        put(screen, 13 + offset, line, curses.A_REVERSE if index == state.cursor else 0)
    if not rows:
        put(screen, 13, "No matches. / clears or changes search; f changes filter.")
    put(screen, height - 5, message or "Choose generated files to delete. -- items require owning-tool review.")
    put(screen, height - 4, f"{len(state.selected)} selected | {len(rows)} shown | {state.cursor + 1 if rows else 0}/{len(rows)}")
    put(screen, height - 3, "Arrows: move | Space: select | a: visible page | c: clear | /: search | f: filter")
    put(screen, height - 2, "Enter/r: REVIEW SELECTED | d: details | p: access setup | q: quit (nothing approved)", curses.A_BOLD)
    screen.refresh()


def wrap_lines(lines, width):
    result = []
    for line in lines:
        result.extend(textwrap.wrap(safe(line), max(20, width - 5),
                                    replace_whitespace=False, drop_whitespace=False) or [""])
    return result


def draw_panel(screen, title, lines, offset=0, footer="Esc: return", prompt=""):
    screen.erase()
    height, width = screen.getmaxyx()
    put(screen, 0, title, curses.A_BOLD)
    wrapped = wrap_lines(lines, width)
    count = max(1, height - 6)
    maximum = max(0, len(wrapped) - count)
    offset = min(maximum, max(0, offset))
    for y, line in enumerate(wrapped[offset:offset + count], 2):
        put(screen, y, line)
    put(screen, height - 3, f"Lines {offset + 1}-{min(len(wrapped), offset + count)}/{len(wrapped)} | arrows/PgUp/PgDn: scroll")
    put(screen, height - 2, footer, curses.A_BOLD)
    if prompt:
        put(screen, height - 1, prompt)
    screen.refresh()
    return offset, maximum


def draw_work(screen, title, tick):
    screen.erase()
    spinner = "|/-\\"[tick % 4]
    put(screen, 2, f"{spinner} {title}", curses.A_BOLD)
    put(screen, 4, "Checking exact paths, tree identity, ownership and active processes.")
    put(screen, 6, "No terminal approval is assumed. Final deletion needs typed DELETE.")
    screen.refresh()
