"""Locate direct tool examples that bypass the standard project CLI."""

import re

RAW_TOOL = re.compile(
    r"(?:^|&&|\|\||;)\s*(?:\$\s*)?"
    r"(?:(?:env\s+)?[A-Za-z_]\w*=(?:\"[^\"]*\"|'[^']*'|\S+)\s+)*"
    r"(?:cargo|npm|pnpm|yarn|bun|make|just|go|pytest|python3?)\s+\S"
)


def command_conflicts(text):
    conflicts, headings = [], []
    fence = ""
    for number, line in enumerate(text.splitlines(), 1):
        marker = re.match(r"^\s*(`{3,}|~{3,})", line)
        if marker:
            value = marker[1]
            if not fence:
                fence = value
            elif value[0] == fence[0] and len(value) >= len(fence):
                fence = ""
            continue
        heading = re.match(r"^(#{1,6})\s+(.+?)\s*#*\s*$", line) if not fence else None
        if heading:
            level = len(heading[1])
            while headings and headings[-1][0] >= level:
                headings.pop()
            headings.append((level, heading[2].lower() in ("cli bootstrap", "cli repair")))
        if any(exempt for _, exempt in headings):
            continue
        examples = [line] if fence else [match[1] for match in re.findall(r"(`+)(.*?)\1", line)]
        for example in examples:
            if RAW_TOOL.search(example):
                conflicts.append({"file": "AGENTS.md", "line": number, "command": example.strip()[:240]})
    return conflicts
