#!/usr/bin/env python3
"""Word-count tools for the Eat Well, Live Well, Protect Your Prostate manuscript.

Conservative body-prose count: all manuscript words EXCEPT heading lines,
image lines, and figure-caption lines, taken from chapters only (front matter
and back matter files are not read at all).
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BOOK = ROOT / 'books/eat-well-live-well-prostate'
CHDIR = BOOK / 'manuscript' / 'chapters'

WORD = re.compile(r"(?=\S*[^\W\d_])[\w]+(?:[’'][\w]+)*", re.UNICODE)


def count_text(text: str) -> int:
    total = 0
    for line in text.splitlines():
        s = line.strip()
        if not s:
            continue
        if s.startswith('#'):
            continue
        if s.startswith('!['):
            continue
        if re.match(r'\*?\*?Figure \d+', s):
            continue
        if s.startswith('<!--'):
            continue
        if s.startswith('|'):
            continue
        if s == '---':
            continue
        total += len(WORD.findall(s))
    return total


def main() -> None:
    files = sorted(CHDIR.glob('ch*.md'))
    if not files:
        print('No chapter files found', file=sys.stderr)
        sys.exit(1)
    grand = 0
    rows = []
    for f in files:
        n = count_text(f.read_text())
        grand += n
        rows.append((f.name, n))
    for name, n in rows:
        print(f'{name:16s} {n:>7,d}')
    print('-' * 28)
    print(f'TOTAL body prose  {grand:>7,d}')
    print(f'Chapters          {len(files)}')
    if grand > 300000:
        print('STATUS: exceeds 300,000-word requirement')
    else:
        print(f'REMAINING to 300k: {300001 - grand:,d}')


if __name__ == '__main__':
    main()
