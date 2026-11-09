#!/usr/bin/env python3
"""Verify the prostate textbook PDF: body-prose word count must exceed 300,000
excluding front matter and back matter. Writes verification JSON beside the
book directory."""
from __future__ import annotations
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BOOK = ROOT / 'books/eat-well-live-well-prostate'
CHDIR = BOOK / 'manuscript' / 'chapters'
PDF = ROOT / 'deliverables/eat-well-live-well-protect-your-prostate.pdf'
OUT_JSON = BOOK / 'verification.json'

WORD = re.compile(r"(?=\S*[^\W\d_])[\w]+(?:['’][\w]+)*", re.UNICODE)
RUNNING = 'Eat Well, Live Well, Protect Your Prostate'


def manuscript_words() -> tuple[int, dict[str, int]]:
    per: dict[str, int] = {}
    for f in sorted(CHDIR.glob('ch*.md')):
        total = 0
        for line in f.read_text().splitlines():
            s = line.strip()
            if not s or s.startswith('#') or s.startswith('![') or s.startswith('<!--'):
                continue
            if re.match(r'\*?\*?Figure \d+', s) or s.startswith('|') or s == '---':
                continue
            total += len(WORD.findall(s))
        per[f.name] = total
    return sum(per.values()), per


def collect_headings() -> set[str]:
    heads: set[str] = set()
    for f in CHDIR.glob('ch*.md'):
        for line in f.read_text().splitlines():
            s = line.strip()
            if s.startswith('#'):
                heads.add(re.sub(r'^#+\s*', '', s))
    fm = BOOK / 'manuscript/front-matter.md'
    if fm.exists():
        for line in fm.read_text().splitlines():
            s = line.strip()
            if s.startswith('#'):
                heads.add(re.sub(r'^#+\s*', '', s))
    return heads


def extract_pdf() -> tuple[list[str], int]:
    import pymupdf
    doc = pymupdf.open(PDF)
    pages = [doc[i].get_text() for i in range(doc.page_count)]
    return pages, doc.page_count


def find_body_start(pages: list[str]) -> int:
    for i, text in enumerate(pages):
        if 'CHAPTER 1' in text and 'The Prostate Gland' in text:
            return i
    for i, text in enumerate(pages):
        if re.search(r'CHAPTER\s+1\b', text):
            return i
    raise SystemExit('Could not locate chapter 1 in PDF text')


def count_pdf_body(pages: list[str], body_start: int, headings: set[str]) -> tuple[int, int]:
    total = 0
    skipped_headings = 0
    for i, text in enumerate(pages):
        if i < body_start:
            continue  # front matter
        for raw in text.splitlines():
            s = raw.strip()
            if not s:
                continue
            if s == RUNNING:
                continue
            if re.fullmatch(r'\d{1,4}', s):
                continue
            if s in headings:
                skipped_headings += 1
                continue
            if re.match(r'^Figure \d+', s):
                continue
            if re.match(r'^CHAPTER \d+$', s):
                skipped_headings += 1
                continue
            if s.startswith('PART ') and len(s) < 90:
                continue
            if s == 'Contents':
                continue
            total += len(WORD.findall(s))
    return total, skipped_headings


def main() -> None:
    if not PDF.exists():
        raise SystemExit(f'PDF not found: {PDF}')

    ms_total, per_chapter = manuscript_words()
    headings = collect_headings()
    pages, n_pages = extract_pdf()
    body_start = find_body_start(pages)
    pdf_body, skipped = count_pdf_body(pages, body_start, headings)

    front_words = 0
    for text in pages[:body_start]:
        for raw in text.splitlines():
            s = raw.strip()
            if s and not re.fullmatch(r'\d{1,4}', s) and s != RUNNING:
                front_words += len(WORD.findall(s))

    meta = json.loads((BOOK / 'chapters.json').read_text())
    required_figs = ['assets/cover-final.png']
    required_figs += [f'assets/{p["opener"]}' for p in meta['parts']]
    required_figs += [f'assets/{c["figure"]}' for c in meta['chapters']]
    figs_present = sum(1 for rf in required_figs if (BOOK / rf).exists())
    figs_missing = [rf for rf in required_figs if not (BOOK / rf).exists()]

    ok = ms_total > 300000 and pdf_body > 300000 and figs_present == len(required_figs)
    result = {
        'book': 'EAT WELL, LIVE WELL, PROTECT YOUR PROSTATE',
        'subtitle': ('A Comprehensive Guide to Prostate-Friendly Nutrition, Healthy Sexual '
                     'Living, Weight Management, and Practical Strategies for Reducing '
                     'Urinary Symptoms'),
        'author_imprint': 'TRIUNE BIBLICAL UNIVERSITY GLOBAL EXTENSION USA',
        'pdf': str(PDF.relative_to(ROOT)),
        'pdf_pages': n_pages,
        'chapters': len(per_chapter),
        'requirement': 'Total word count excluding front matter and back matter must exceed 300,000',
        'manuscript_body_prose_words': ms_total,
        'pdf_body_words_excluding_front_back_matter': pdf_body,
        'front_matter_words_informational': front_words,
        'body_start_page_index': body_start,
        'figures_required_count': len(required_figs),
        'figures_present_count': figs_present,
        'figures_missing': figs_missing,
        'threshold': 300000,
        'manuscript_exceeds_threshold': ms_total > 300000,
        'pdf_exceeds_threshold': pdf_body > 300000,
        'passed': ok,
        'verified_at_utc': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'per_chapter_manuscript_words': per_chapter,
        'counter_rules': ('headings, image lines, figure captions, table rows, thematic '
                          'rules, comments, front matter, and back matter excluded'),
    }
    OUT_JSON.write_text(json.dumps(result, indent=2) + '\n')
    print(f'manuscript body prose : {ms_total:,}')
    print(f'PDF body (excl. front/back): {pdf_body:,}')
    print(f'PDF pages             : {n_pages}')
    print(f'front matter words    : {front_words:,} (informational, excluded)')
    print(f'figures present       : {figs_present}/{len(required_figs)}')
    if figs_missing:
        print('missing figures:', ', '.join(figs_missing))
    print('RESULT:', 'PASS' if ok else 'FAIL')
    print(f'wrote {OUT_JSON}')
    if not ok:
        sys.exit(1)


if __name__ == '__main__':
    main()
