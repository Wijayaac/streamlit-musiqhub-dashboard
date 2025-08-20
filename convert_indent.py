#!/usr/bin/env python3
import re
from pathlib import Path

def convert_file(path, spaces_per_tab=4):
    text = path.read_text(encoding="utf-8")
    out_lines = []
    for line in text.splitlines(True):
        m = re.match(r'^( +)', line)
        if m:
            spaces = len(m.group(1))
            tabs = spaces // spaces_per_tab
            rem = spaces % spaces_per_tab
            new_line = '\t' * tabs + ' ' * rem + line[m.end():]
        else:
            new_line = line
        out_lines.append(new_line)
    path.write_text(''.join(out_lines), encoding="utf-8")

for p in Path('.').rglob('*.py'):
    # skip venv / .git folders
    if any(part.startswith('.') or part in ('venv','env') for part in p.parts):
        continue
    convert_file(p)
    print(f"Converted: {p}")