#!/usr/bin/env python3
"""Prepare the attributed, CC-BY-4.0 OpenStax readings for CAC.901.

The source is a pinned public GitHub snapshot. No network access is needed after
that snapshot has been downloaded. Source images are not reproduced; their alt
text and captions are retained as explicitly labelled descriptions. Twenty new
vector diagrams are supplied separately in the course lectures.
"""
from __future__ import annotations
import json
import re
import shutil
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / '.cache/book-sources/cnxbook-psychology-2e-main'
BOOK = ROOT / 'books/CAC-901'
NS = {'x': 'http://cnx.rice.edu/cnxml', 'md': 'http://cnx.rice.edu/mdml'}
PIN = 'f5c9cf50686749d28cc5a594e0fdc487398f8307'
SKIP_CLASSES = {'references', 'splash', 'learning-objectives', 'link-to-learning'}
LOCAL = lambda el: el.tag.split('}')[-1]
WORD = re.compile(r'(?=\S*[^\W\d_])[\w]+(?:[’\'-][\w]+)*', re.UNICODE)

def words(text: str) -> int:
    return len(WORD.findall(text))

def clean(text: str) -> str:
    return re.sub(r'\s+', ' ', text.replace('\xa0', ' ')).strip()

def inline(el: ET.Element | None, module: str) -> str:
    if el is None:
        return ''
    tag = LOCAL(el)
    if tag in {'image', 'media'}:
        return ''
    if tag == 'newline':
        return '\n'
    if tag == 'link':
        target = el.get('target-id')
        url = el.get('url') or el.get('resource')
        text = clean(''.join(el.itertext()))
        if target:
            return text or 'the accompanying source-figure description'
        if url:
            return f'{text} ({url})' if text else url
        return text
    if tag == 'footnote':
        return ' [Source note: ' + clean(''.join(el.itertext())) + '] '
    parts = [el.text or '']
    for child in el:
        parts.append(inline(child, module))
        parts.append(child.tail or '')
    text = ''.join(parts)
    return text

def section_class(el: ET.Element) -> str:
    return el.get('class', '').lower()

def parse_children(el: ET.Element, module: str, depth: int = 0) -> list[dict]:
    result: list[dict] = []
    for child in el:
        result.extend(parse_node(child, module, depth))
    return result

def parse_node(el: ET.Element, module: str, depth: int = 0) -> list[dict]:
    tag = LOCAL(el)
    cls = section_class(el)
    if tag in {'metadata', 'image', 'media', 'label', 'caption'}:
        return []
    if any(c in cls.split() for c in SKIP_CLASSES):
        return []
    if tag == 'section':
        title = el.find('x:title', NS)
        blocks = []
        if title is not None:
            blocks.append({'type': 'heading', 'level': min(4, 2 + depth), 'text': clean(''.join(title.itertext()))})
        for child in el:
            if child is title:
                continue
            blocks.extend(parse_node(child, module, depth + 1))
        return blocks
    if tag == 'title':
        return [{'type': 'heading', 'level': min(4, 2 + depth), 'text': clean(''.join(el.itertext()))}]
    if tag == 'para':
        text = clean(inline(el, module))
        return [{'type': 'paragraph', 'text': text}] if text else []
    if tag in {'list', 'problem', 'solution'}:
        kind = {'list': 'list', 'problem': 'question', 'solution': 'answer'}[tag]
        items = []
        preamble = clean(el.text or '')
        if preamble:
            items.append(preamble)
        for child in el:
            if LOCAL(child) == 'item':
                value = clean(inline(child, module))
                if not value:
                    nested = parse_children(child, module, depth)
                    value = ' '.join(b.get('text', '') for b in nested if b.get('text'))
                if value:
                    items.append(value)
            elif LOCAL(child) not in {'label', 'title'}:
                # Preserve complex question/solution content without dropping it.
                sub = parse_node(child, module, depth)
                items.extend(b.get('text', '') for b in sub if b.get('type') == 'paragraph')
        return [{'type': kind, 'numbered': el.get('list-type') == 'enumerated', 'items': items}] if items else []
    if tag == 'item':
        text = clean(inline(el, module))
        return [{'type': 'list', 'numbered': False, 'items': [text]}] if text else []
    if tag == 'figure':
        media = el.find('.//x:media', NS)
        caption = el.find('x:caption', NS)
        alt = clean(media.get('alt', '')) if media is not None else ''
        cap = clean(inline(caption, module)) if caption is not None else ''
        text = ' '.join(x for x in [alt, cap] if x)
        return [{'type': 'source_figure_description', 'text': text, 'anchor': f'{module}-{el.get("id", "")}'}] if text else []
    if tag == 'table':
        title = el.find('.//x:title', NS)
        rows = []
        for row in el.findall('.//x:row', NS):
            rows.append([clean(inline(entry, module)) for entry in row.findall('x:entry', NS)])
        if rows:
            return [{'type': 'table', 'text': clean(''.join(title.itertext())) if title is not None else 'Source comparison table', 'rows': rows}]
        return parse_children(el, module, depth)
    if tag == 'note':
        label = el.find('x:label', NS)
        title = el.find('x:title', NS)
        heading = clean(''.join((label if label is not None else title).itertext())) if (label is not None or title is not None) else 'Source note'
        blocks = [{'type': 'note_start', 'text': heading}]
        for child in el:
            if child is not label and child is not title:
                blocks.extend(parse_node(child, module, depth))
        blocks.append({'type': 'note_end', 'text': ''})
        return blocks
    if tag == 'exercise':
        blocks = [{'type': 'note_start', 'text': 'OpenStax learning exercise'}]
        blocks.extend(parse_children(el, module, depth))
        blocks.append({'type': 'note_end', 'text': ''})
        return blocks
    if tag == 'quote':
        text = clean(inline(el, module))
        return [{'type': 'quote', 'text': text}] if text else []
    if tag == 'definition':
        term = el.find('x:term', NS)
        meaning = el.find('x:meaning', NS)
        text = clean(''.join(term.itertext())) + ': ' + clean(inline(meaning, module)) if term is not None and meaning is not None else clean(inline(el, module))
        return [{'type': 'paragraph', 'text': text}] if text else []
    if tag == 'equation' or el.tag.startswith('{http://www.w3.org/1998/Math/MathML}'):
        text = clean(' '.join(el.itertext()))
        return [{'type': 'equation', 'text': text}] if text else []
    if tag in {'content', 'glossary', 'tgroup', 'tbody', 'thead'}:
        return parse_children(el, module, depth)
    if tag in {'term', 'emphasis', 'foreign'}:
        text = clean(inline(el, module))
        return [{'type': 'paragraph', 'text': text}] if text else []
    # Unknown containers are traversed rather than silently discarded.
    if len(el):
        return parse_children(el, module, depth)
    text = clean(''.join(el.itertext()))
    return [{'type': 'paragraph', 'text': text}] if text else []

def block_words(block: dict) -> int:
    if block['type'] in {'paragraph', 'quote', 'equation', 'heading'}:
        return words(block.get('text', ''))
    if block['type'] in {'list', 'question', 'answer'}:
        return sum(words(x) for x in block.get('items', []))
    if block['type'] == 'table':
        return sum(words(x) for row in block['rows'] for x in row)
    # Captions, source-figure descriptions, attribution and running matter are excluded.
    return 0

def main() -> None:
    if not SOURCE.exists():
        raise SystemExit(f'Missing source snapshot. Download the pinned archive to {SOURCE}.')
    chapters = json.loads((BOOK / 'chapters.json').read_text())
    references: dict[str, list[str]] = {}
    all_modules: set[str] = set()
    for chapter in chapters:
        chapter['readings'] = []
        for module in chapter['modules']:
            root = ET.parse(SOURCE / 'modules' / module / 'index.cnxml').getroot()
            title = clean(root.find('x:title', NS).text)
            content = root.find('x:content', NS)
            blocks = parse_children(content, module)
            chapter['readings'].append({'module': module, 'title': title, 'blocks': blocks,
                                        'substantive_words': sum(block_words(b) for b in blocks),
                                        'url': f'https://github.com/cnx-user-books/cnxbook-psychology-2e/blob/{PIN}/modules/{module}/index.cnxml'})
            all_modules.add(module)
    # References live in the introductions to the source textbook chapters.
    reference_intros = ['m82166','m82171','m82198','m82203','m82212','m82217','m82224','m82232','m82242','m82258','m82264','m82280']
    for module in reference_intros:
        root = ET.parse(SOURCE / 'modules' / module / 'index.cnxml').getroot()
        section = root.find('.//x:section[@class="references"]', NS)
        entries = [clean(inline(p, module)) for p in section.findall('x:para', NS)] if section is not None else []
        references[module] = entries
    (BOOK / 'source-blocks.json').write_text(json.dumps(chapters, ensure_ascii=False, indent=2))
    (BOOK / 'source-references.json').write_text(json.dumps(references, ensure_ascii=False, indent=2))
    shutil.copyfile(SOURCE / 'LICENSE', BOOK / 'assets/OPENSTAX-CC-BY-4.0-LICENSE.txt')
    manifest = {'title': 'Psychology 2e', 'authors': ['Rose M. Spielman', 'William J. Jenkins', 'Marilyn D. Lovett'],
                'publisher': 'OpenStax, Rice University', 'original_publication_year': 2020,
                'license': 'Creative Commons Attribution 4.0 International',
                'license_url': 'https://creativecommons.org/licenses/by/4.0/',
                'repository': 'https://github.com/cnx-user-books/cnxbook-psychology-2e',
                'snapshot_commit': PIN, 'retrieved': '2026-11-01',
                'adaptations': ['Selected and reorganized modules for CAC.901.', 'Converted CNXML to a new PDF layout.',
                                 'Added new course lectures, application tasks, and twenty original vector diagrams.',
                                 'Source photographs and illustrations are not reproduced; their alt text and captions are retained as descriptions.',
                                 'Removed obsolete video-promotion boxes and source learning-objective boxes from the reading stream.',
                                 'Reference lists are collected at the back and excluded from the substantive word count.'],
                'modules_used': sorted(all_modules), 'reference_introductions': reference_intros,
                'editorial_caution': 'The source is a 2020 introductory textbook, not a current diagnostic manual or a local legal authority. Its examples, prevalence estimates, terminology and diagnostic descriptions require critical reading and current professional guidance.'}
    (BOOK / 'source-manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
    total = sum(r['substantive_words'] for c in chapters for r in c['readings'])
    print(f'Prepared {len(all_modules)} attributed readings: {total:,} substantive source words; references excluded.')
    print(f'Prepared {sum(map(len, references.values()))} inherited source-reference entries.')

if __name__ == '__main__':
    main()
