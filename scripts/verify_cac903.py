#!/usr/bin/env python3
"""Verify the delivered CAC.903 PDF, independently of manuscript estimates."""
from __future__ import annotations
import hashlib
import json
import re
from pathlib import Path
import pymupdf

ROOT = Path(__file__).resolve().parents[1]
BOOK = ROOT / 'books/CAC-903'
PDF = ROOT / 'deliverables/CAC-903-child-and-adolescent-assessment-techniques.pdf'
WORD = re.compile(r'(?=\S*[^\W\d_])[\w]+(?:[’\'-][\w]+)*', re.UNICODE)
MIN_WORDS = 150_000


def main() -> None:
    build = json.loads((BOOK / 'build-record.json').read_text())
    chapters = json.loads((BOOK / 'chapters.json').read_text())
    blocks = json.loads((BOOK / 'source-blocks.json').read_text())
    diagrams = json.loads((BOOK / 'diagrams.json').read_text())
    manifest = json.loads((BOOK / 'source-manifest.json').read_text())
    document = pymupdf.open(PDF)
    chapter_starts = [v for k, v in build['chapter_pages'].items() if re.fullmatch(r'ch\d{2}', k)]
    first = min(chapter_starts)
    last = build['section_pages']['references_start'] - 1
    assert len(chapter_starts) == 20
    assert len(chapters) == len(diagrams) == 20
    assert {d['chapter'] for d in diagrams} == set(range(1, 21))

    prose_words = 0
    instructional_words = 0
    empty_pages = []
    out_of_page = []
    out_of_frame = []
    figure_pages = [{'chapter': d['chapter'], 'page': build['section_pages'][f"ch{d['chapter']:02d}_diagram"], 'title': d['title']} for d in diagrams]
    page_word_counts = []
    for index, page in enumerate(document):
        all_text = page.get_text('text')
        if len(all_text.strip()) < 30:
            empty_pages.append(index + 1)
        for block in page.get_text('dict')['blocks']:
            for line in block.get('lines', []):
                for span in line['spans']:
                    x0, y0, x1, y1 = span['bbox']
                    if x0 < -1 or y0 < -1 or x1 > page.rect.width + 1 or y1 > page.rect.height + 1:
                        out_of_page.append({'page': index + 1, 'text': span['text']})
                    if 48 <= y0 and y1 <= page.rect.height - 43:
                        if x0 < 55 or x1 > page.rect.width - 55:
                            out_of_frame.append({'page': index + 1, 'text': span['text']})
        if not (first <= index + 1 <= last):
            continue
        count = 0
        clip = pymupdf.Rect(0, 48, page.rect.width, page.rect.height - 43)
        for block in page.get_text('dict', clip=clip)['blocks']:
            for line in block.get('lines', []):
                for span in line['spans']:
                    n = len(WORD.findall(span['text']))
                    count += n
                    if 'Serif' in span['font']:
                        prose_words += n
        instructional_words += count
        page_word_counts.append({'page': index + 1, 'words': count})

    full_text = '\n'.join(page.get_text('text') for page in document)
    outline = document.get_toc()
    chapter_outline = [entry for entry in outline if entry[0] == 1 and entry[1] in {c['title'] for c in chapters}]
    assert len(chapter_outline) == 20
    assert len(figure_pages) == 20, figure_pages
    assert not empty_pages, empty_pages
    assert not out_of_page, out_of_page[:10]
    assert not out_of_frame, out_of_frame[:10]
    assert prose_words >= MIN_WORDS, prose_words
    assert full_text.count('Applied Workbook') >= 2
    assert full_text.count('Clinical Casebook') >= 2
    workbook_first = build['section_pages']['workbook_start']
    workbook_last = build['section_pages']['casebook_start'] - 1
    workbook_text = '\n'.join(document[i].get_text('text') for i in range(workbook_first - 1, workbook_last))
    assert len(re.findall(r'Exercise \d+:', workbook_text)) == 20
    for phrase in ['TODO', 'TBD', 'PLACEHOLDER', 'ns0:', 'None:']:
        assert phrase not in full_text, phrase
    assert 'Creative Commons Attribution 4.0' in full_text
    for s in manifest['sources']:
        assert s['commit'] in full_text, s['commit']
    assert document.metadata['title'] == 'CAC.903 — Child and Adolescent Assessment Techniques'
    assert not document.is_encrypted

    report = {
        'status': 'PASS',
        'course_code': 'CAC.903',
        'course_title': 'Child and Adolescent Assessment Techniques',
        'pdf': str(PDF.relative_to(ROOT)),
        'pdf_bytes': PDF.stat().st_size,
        'sha256': hashlib.sha256(PDF.read_bytes()).hexdigest(),
        'page_count': len(document),
        'minimum_required_words': MIN_WORDS,
        'conservative_serif_prose_words': prose_words,
        'instructional_words_including_notes_tables_headings': instructional_words,
        'count_range_pages': [first, last],
        'count_method': 'Lexical words containing at least one letter; contractions and hyphenated words count once; pure numbers excluded. Count extracted text from the actual delivered PDF. Front matter, contents, references, attribution register, running headers and footers are outside the counted page range. The conservative measure further restricts to serif body-prose spans, excluding sans-serif notes, tables, headings, captions, URLs and diagram labels.',
        'references_excluded': True,
        'lecture_chapters': 20,
        'original_vector_diagrams': len(figure_pages),
        'figure_pages': figure_pages,
        'workbook_exercises': 20,
        'chapter_bookmarks': len(chapter_outline),
        'total_bookmarks': len(outline),
        'empty_pages': empty_pages,
        'text_outside_page_bounds': out_of_page,
        'text_outside_body_frame': out_of_frame,
        'source_reading_blocks': len(blocks),
        'source_license': 'CC BY 4.0 (Petersen and OpenStax); attribution and changes recorded in the PDF',
        'editorial_limitations': 'Complete educational course volume, not an official university publication or current clinical guideline. Includes newly written counseling material and attributed adaptations of CC BY open educational texts, including general psychological assessment science. No independent clinical peer review is claimed.',
        'chapter_pages': build['chapter_pages'],
        'section_pages': build['section_pages'],
        'page_word_counts': page_word_counts,
    }
    (BOOK / 'verification-report.json').write_text(json.dumps(report, indent=2))
    summary = {k: v for k, v in report.items() if k not in {'page_word_counts', 'chapter_pages', 'section_pages', 'figure_pages', 'count_method'}}
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
