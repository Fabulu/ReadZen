#!/usr/bin/env python3
"""F1 full-case re-read, corpus side: the T48n2025 XML context around
the two sibling [Dehui] windows (1144b03 for 一日不作一日不食;
1127c04 for 粥飯) plus the correctly-attributed 1119b01 (Baizhang)
as the in-file contrast. Plain-text extraction (tags stripped) with
section-header context, so the institutional-voice reading can be
judged against the actual document, not the termbase notes.
"""
from __future__ import annotations

import re
from pathlib import Path

XML = Path(r"C:\programmieren\CbetaZenTexts"
           r"\xml-p5\T\T48\T48n2025.xml")
xml = XML.read_text(encoding="utf-8")


def window(lb: str, before: int = 1800, after: int = 1400) -> None:
    i = xml.find(f'lb n="{lb}"')
    print(f"======== {lb} (char {i}) " + "=" * 40)
    if i < 0:
        print("NOT FOUND")
        return
    seg = xml[max(0, i - before):i + after]
    txt = re.sub(r"<[^>]+>", "", seg)
    txt = re.sub(r"[ \t]+", " ", txt)
    txt = re.sub(r"\n{2,}", "\n", txt)
    print(txt.strip())


window("1119b01")
window("1144b03")
window("1127c04")

# which juan/division headings precede each window?
for lb in ("1119b01", "1144b03", "1127c04"):
    i = xml.find(f'lb n="{lb}"')
    heads = re.findall(r'<head[^>]*>([^<]{1,40})</head>', xml[:i])
    print(f"{lb}: preceding heads -> {heads[-3:]}")
