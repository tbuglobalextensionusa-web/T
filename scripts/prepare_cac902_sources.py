#!/usr/bin/env python3
"""Prepare attributed, format-adapted OER readings for CAC.902.

Sources are pinned GitHub mirrors of CC BY 4.0 texts:
- Kelland, Personality Theory in a Cultural Context (OpenStax CNX)
- Spielman et al., Psychology 2e (OpenStax)
Only text is adapted; original figures are replaced by new vector diagrams.
"""
from __future__ import annotations
import json, re, hashlib, tarfile, urllib.request
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
BOOK = ROOT / 'books/CAC-902'
CACHE = ROOT / '.cache/book-sources'
NS = {'x': 'http://cnx.rice.edu/cnxml', 'm': 'http://www.w3.org/1998/Math/MathML', 'c': 'http://cnx.rice.edu/collxml'}
X = '{http://cnx.rice.edu/cnxml}'
M = '{http://www.w3.org/1998/Math/MathML}'
SOURCES = {
    'kelland': {
        'repo': 'cnx-user-books/cnxbook-personality-theory-in-a-cultural-context',
        'commit': 'a5228369950933a4739cbeab9f617f652439f219',
        'dir': 'cnxbook-personality-theory-in-a-cultural-context-main',
        'title': 'Personality Theory in a Cultural Context',
        'authors': 'Mark D. Kelland',
        'publisher': 'OpenStax CNX / Lansing Community College',
        'year': '2015',
        'license': 'CC BY 4.0',
        'license_url': 'https://creativecommons.org/licenses/by/4.0/',
    },
    'openstax': {
        'repo': 'cnx-user-books/cnxbook-psychology-2e',
        'commit': 'f5c9cf50686749d28cc5a594e0fdc487398f8307',
        'dir': 'cnxbook-psychology-2e-f5c9cf50686749d28cc5a594e0fdc487398f8307',
        'title': 'Psychology 2e',
        'authors': 'Rose M. Spielman, William J. Jenkins, and Marilyn D. Lovett',
        'publisher': 'OpenStax, Rice University',
        'year': '2020',
        'license': 'CC BY 4.0',
        'license_url': 'https://creativecommons.org/licenses/by/4.0/',
    },
}

def clean(s):
    return re.sub(r'\s+', ' ', s or '').strip()

def inline(el):
    if el is None: return ''
    tag = el.tag.split('}')[-1]
    if tag in ('math',): return math_text(el)
    if tag in ('image', 'media'): return ''
    parts = [el.text or '']
    for child in el:
        ctag = child.tag.split('}')[-1]
        if ctag == 'link':
            txt = inline(child) or child.attrib.get('document','')
            url = child.attrib.get('url') or child.attrib.get('resource') or ''
            parts.append(f'[{txt}]({url})' if url else txt)
        elif ctag == 'emphasis':
            txt = inline(child)
            effect = child.attrib.get('effect','italics')
            parts.append(f'**{txt}**' if effect in ('bold','bf') else f'*{txt}*')
        elif ctag == 'term':
            parts.append(f"**{inline(child)}**")
        elif ctag == 'quote':
            q = inline(child)
            cls = child.attrib.get('class','')
            parts.append(f'“{q}”' if cls != 'inline' else q)
        elif ctag == 'cite':
            parts.append(f"*{inline(child)}*")
        elif ctag == 'sup':
            parts.append('^' + inline(child))
        elif ctag == 'sub':
            parts.append('_' + inline(child))
        elif ctag in ('newline',):
            parts.append(' ')
        else:
            parts.append(inline(child))
        parts.append(child.tail or '')
    return clean(''.join(parts))

def math_text(el):
    tag = el.tag.split('}')[-1]
    if tag in ('mi','mn','mo','mtext'): return clean(''.join(el.itertext()))
    kids = [math_text(k) for k in el if k.tag.split('}')[-1] not in ('annotation','annotation-xml')]
    if tag == 'mfrac' and len(kids)==2: return f'({kids[0]})/({kids[1]})'
    if tag == 'msup' and len(kids)==2: return f'{kids[0]}^{kids[1]}'
    if tag == 'msub' and len(kids)==2: return f'{kids[0]}_{kids[1]}'
    if tag == 'msqrt': return 'sqrt(' + ' '.join(kids) + ')'
    if tag in ('mrow','math','mstyle','semantics'): return ' '.join(k for k in kids if k)
    return ' '.join(k for k in kids if k)

def table_md(table):
    rows = []
    for row in table.findall('.//x:row', NS):
        cells = [inline(entry) for entry in row.findall('x:entry', NS)]
        cells = [c.replace('|','\\|') for c in cells]
        if any(cells): rows.append(cells)
    if not rows: return []
    width = max(len(r) for r in rows)
    # A single-cell first row is usually a spanning table title; render as caption.
    out = []
    start = 0
    if len(rows[0]) == 1 and width > 1:
        out.append('**' + rows[0][0] + '**')
        start = 1
    if start >= len(rows): return out
    body = [r + ['']*(width-len(r)) for r in rows[start:]]
    out.append('| ' + ' | '.join(body[0]) + ' |')
    out.append('| ' + ' | '.join(['---']*width) + ' |')
    for r in body[1:]:
        out.append('| ' + ' | '.join(r) + ' |')
    return out

def walk(el, out, depth=0):
    tag = el.tag.split('}')[-1]
    if tag in ('link-to-learning',): return
    if tag == 'section':
        title = el.find('x:title', NS)
        if title is not None:
            out.append('#' * min(depth+3, 4) + ' ' + inline(title))
        for ch in el:
            if ch is not title: walk(ch, out, depth+1)
        return
    if tag == 'para':
        txt = inline(el)
        if txt: out.append(txt)
        return
    if tag == 'list':
        ordered = el.attrib.get('list-type') == 'enumerated'
        for i, item in enumerate(el.findall('x:item', NS), 1):
            txt = inline(item)
            if txt: out.append((f'{i}. ' if ordered else '- ') + txt)
        return
    if tag == 'table':
        out.extend(table_md(el)); return
    if tag == 'figure':
        cap = el.find('x:caption', NS)
        if cap is not None:
            txt = inline(cap)
            if txt: out.append('*Source figure caption: ' + txt + '*')
        return
    if tag == 'note':
        label = el.attrib.get('type','').replace('-', ' ').title() or 'Note'
        inner = []
        for ch in el: walk(ch, inner, depth)
        if inner: out.append(f'**{label}:** ' + ' '.join(inner))
        return
    if tag == 'exercise':
        # Keep source review questions as ordinary prose prompts, not interactive widgets.
        for ch in el: walk(ch, out, depth)
        return
    if tag in ('solution',): return
    if tag in ('content','document','col:content'):
        for ch in el: walk(ch, out, depth)
        return
    if tag in ('title','caption'): return
    # Generic container
    for ch in el: walk(ch, out, depth)

def render_module(root, source_key, include_sections=None):
    content = root.find('x:content', NS)
    out = []
    if include_sections:
        wanted = set(include_sections)
        for sec in content.findall('x:section', NS):
            if sec.attrib.get('id') in wanted:
                walk(sec, out, 0)
    else:
        walk(content, out, 0)
    md = '\n\n'.join(out)
    md = re.sub(r'\n{3,}', '\n\n', md).strip() + '\n'
    return md

def extract_refs(root):
    refs = []
    for bibl in root.findall('.//x:bibl', NS):
        txt = inline(bibl)
        if txt: refs.append(txt)
    return refs

def ensure_sources():
    CACHE.mkdir(parents=True, exist_ok=True)
    for key, s in SOURCES.items():
        dest = CACHE / s['dir']
        if dest.exists(): continue
        archive = CACHE / f"{key}.tar.gz"
        if not archive.exists():
            url = f"https://codeload.github.com/{s['repo']}/tar.gz/{s['commit']}"
            urllib.request.urlretrieve(url, archive)
        with tarfile.open(archive) as tf:
            tf.extractall(CACHE, filter='data')

def main():
    ensure_sources()
    chapters = json.loads((BOOK/'chapters.json').read_text())
    blocks, refs, manifest_sources = [], [], []
    for key, s in SOURCES.items():
        base = CACHE / s['dir']
        lic = (base/'LICENSE').read_text()
        assert 'Attribution 4.0 International' in lic
        manifest_sources.append({**s, 'url': f"https://github.com/{s['repo']}", 'retrieved': '2026-11-02', 'license_verified': True, 'modifications': 'Text reformatted for PDF; selected sections adapted; original figures omitted and replaced by new diagrams; historical claims framed by new editorial lectures.'})
    seen_ref = set()
    for ch in chapters:
        for spec in ch['sources']:
            mid = spec['id']
            key = 'kelland' if mid.startswith('m580') else 'openstax'
            base = CACHE / SOURCES[key]['dir']
            path = base/'modules'/mid/'index.cnxml'
            root = ET.parse(path).getroot()
            title = clean(''.join(root.find('x:title', NS).itertext()))
            md = render_module(root, key, spec.get('include_sections'))
            words = len(re.findall(r"\b[\w’'-]+\b", md))
            block_id = f"{mid}-ch{ch['number']}"
            blocks.append({'id': block_id, 'chapter': ch['number'], 'source_id': mid, 'source_key': key, 'title': title, 'markdown': md, 'words': words, 'sha256': hashlib.sha256(md.encode()).hexdigest()})
            if key == 'openstax':
                for r in extract_refs(root):
                    k = re.sub(r'\W+', ' ', r.lower()).strip()
                    if k not in seen_ref:
                        seen_ref.add(k); refs.append({'text': r, 'source_id': mid})
    # Kelland supplies a consolidated reference module; include it as a bibliography, not body prose.
    kbase = CACHE / SOURCES['kelland']['dir']
    kroot = ET.parse(kbase/'modules'/'m58015'/'index.cnxml').getroot()
    for p in kroot.findall('.//x:para', NS):
        txt = inline(p)
        if not txt: continue
        k = re.sub(r'\W+', ' ', txt.lower()).strip()
        if k not in seen_ref:
            seen_ref.add(k); refs.append({'text': txt, 'source_id': 'm58015'})
    (BOOK/'source-blocks.json').write_text(json.dumps(blocks, ensure_ascii=False, indent=2)+'\n')
    (BOOK/'source-references.json').write_text(json.dumps(refs, ensure_ascii=False, indent=2)+'\n')
    (BOOK/'source-manifest.json').write_text(json.dumps({'sources': manifest_sources, 'blocks': len(blocks), 'source_words': sum(b['words'] for b in blocks), 'references': len(refs)}, ensure_ascii=False, indent=2)+'\n')
    print(f"Prepared {len(blocks)} reading blocks, {sum(b['words'] for b in blocks):,} source words, {len(refs)} references")

if __name__ == '__main__':
    main()
