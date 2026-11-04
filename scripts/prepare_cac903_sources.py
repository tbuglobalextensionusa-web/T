#!/usr/bin/env python3
"""Prepare attributed, format-adapted OER readings for CAC.903.

Primary source: Petersen, Principles of Psychological Assessment (CC BY 4.0),
pinned GitHub snapshot. Quarto/R code, raw HTML, and original figures are omitted;
prose is reformatted for a counseling course PDF. New lectures supply child-
adolescent application and critical framing.
"""
from __future__ import annotations
import json, re, hashlib, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BOOK = ROOT / 'books/CAC-903'
CACHE = ROOT / '.cache/cac903-source'
REPO = 'isaactpetersen/Principles-Psychological-Assessment'
COMMIT = 'a424bfcbad1860a746411c6934b06c3c95b2a089'
SOURCE = {
    'key': 'petersen', 'repo': REPO, 'commit': COMMIT,
    'title': 'Principles of Psychological Assessment: With Applied Examples in R',
    'authors': 'Isaac T. Petersen', 'publisher': 'University of Iowa Libraries',
    'year': '2026', 'version': '1.0.9', 'license': 'CC BY 4.0',
    'license_url': 'https://creativecommons.org/licenses/by/4.0/',
    'url': 'https://isaactpetersen.github.io/Principles-Psychological-Assessment/',
    'doi': '10.25820/work.007199',
}
OPENSTAX = {
    'key': 'openstax', 'repo': 'cnx-user-books/cnxbook-psychology-2e',
    'commit': 'f5c9cf50686749d28cc5a594e0fdc487398f8307',
    'title': 'Psychology 2e', 'authors': 'Rose M. Spielman, William J. Jenkins, and Marilyn D. Lovett',
    'publisher': 'OpenStax, Rice University', 'year': '2020', 'license': 'CC BY 4.0',
    'license_url': 'https://creativecommons.org/licenses/by/4.0/',
}

def fetch(path: str) -> bytes:
    CACHE.mkdir(parents=True, exist_ok=True)
    dest = CACHE / path
    if dest.exists(): return dest.read_bytes()
    url = f'https://api.github.com/repos/{REPO}/contents/{path}?ref={COMMIT}'
    req = urllib.request.Request(url, headers={'User-Agent': 'Coursebook-production', 'Accept': 'application/vnd.github.raw+json'})
    data = urllib.request.urlopen(req, timeout=90).read()
    dest.write_bytes(data)
    return data

def clean(s: str) -> str:
    return re.sub(r'[ \t]+', ' ', s).strip()

def parse_bib(data: str):
    entries = {}
    # Split on entry starts at line beginning.
    parts = re.split(r'(?m)^@', data)
    for part in parts[1:]:
        m = re.match(r'(\w+)\s*\{\s*([^,\s]+)\s*,', part)
        if not m: continue
        key = m.group(2)
        body = part[m.end():]
        fields = {}
        i = 0
        while i < len(body):
            fm = re.search(r'(\w+)\s*=\s*', body[i:])
            if not fm: break
            fname = fm.group(1).lower(); start = i + fm.end()
            if start >= len(body): break
            if body[start] == '{':
                depth = 0; j = start
                while j < len(body):
                    if body[j] == '{': depth += 1
                    elif body[j] == '}':
                        depth -= 1
                        if depth == 0: break
                    j += 1
                val = body[start+1:j]; i = j + 1
            elif body[start] == '"':
                j = body.find('"', start+1)
                if j == -1: break
                val = body[start+1:j]; i = j + 1
            else:
                j = start
                while j < len(body) and body[j] not in ',\n}': j += 1
                val = body[start:j]; i = j
            fields[fname] = clean(re.sub(r'[{}]', '', val))
            # stop at next field or end
            nm = re.search(r',\s*\w+\s*=', body[i:])
            if not nm: break
            i = i + nm.start() + 1
        entries[key] = fields
    return entries

def cite_text(keys, bib):
    out = []
    for key in keys:
        f = bib.get(key, {})
        author = f.get('author', key)
        year = f.get('year', 'n.d.')
        # shorten author list
        names = re.split(r'\s+and\s+', author)
        if len(names) == 1:
            a = names[0].split(',')[0]
        elif len(names) == 2:
            a = names[0].split(',')[0] + ' & ' + names[1].split(',')[0]
        else:
            a = names[0].split(',')[0] + ' et al.'
        out.append(f'{a}, {year}')
    return '; '.join(out)

def remove_balanced_command(text: str, name: str) -> str:
    """Remove a LaTeX command and its balanced brace argument, even with nested braces/math."""
    pattern = '\\' + name
    while True:
        idx = text.find(pattern)
        if idx == -1: return text
        j = idx + len(pattern)
        while j < len(text) and text[j].isspace(): j += 1
        if j >= len(text) or text[j] != '{':
            text = text[:idx] + text[idx+len(pattern):]
            continue
        depth = 0; k = j
        while k < len(text):
            if text[k] == '{': depth += 1
            elif text[k] == '}':
                depth -= 1
                if depth == 0: break
            k += 1
        text = text[:idx] + text[k+1:]

def convert_quarto(text: str, bib: dict, include_sections=None, exclude_sections=None):
    # Remove fenced code/output chunks.
    text = re.sub(r'(?ms)^```\{[^}]*\}.*?^```\s*$', '', text)
    text = re.sub(r'(?ms)^```.*?^```\s*$', '', text)
    # Protect autolinks before HTML stripping.
    text = re.sub(r'<(https?://[^>]+)>', r'\1', text)
    # Remove Quarto shortcodes and raw HTML blocks.
    text = re.sub(r'\{\{<.*?>\}\}', '', text, flags=re.S)
    text = re.sub(r'(?ms)^:::.*?^:::\s*$', lambda m: re.sub(r'(?m)^:::.*$', '', m.group(0)), text)
    text = re.sub(r'(?s)<div.*?</div>', '', text)
    text = re.sub(r'(?s)<figure.*?</figure>', '', text)
    # Remove images, index commands, LaTeX structure commands.
    text = re.sub(r'!\[[^\]]*\]\([^)]*\)(\{[^}]*\})?', '', text)
    for cmd in ['index', 'label']:
        text = remove_balanced_command(text, cmd)
    text = re.sub(r'\\(mainmatter|backmatter|printindex|newpage|clearpage|tableofcontents)', '', text)
    text = re.sub(r'\\(textbf|textit|emph)\{([^}]*)\}', r'\2', text)
    text = re.sub(r'\\href\{([^}]*)\}\{([^}]*)\}', r'[\2](\1)', text)
    text = re.sub(r'\\url\{([^}]*)\}', r'\1', text)
    # Display math: replace with a plain-language note rather than broken LaTeX.
    text = re.sub(r'(?s)\$\$.*?\$\$', ' [Formal equation omitted in this course adaptation; see the source for the mathematical expression.] ', text)
    text = re.sub(r'(?s)\\\[.*?\\\]', ' [Formal equation omitted in this course adaptation; see the source for the mathematical expression.] ', text)
    # Inline math: strip delimiters and common commands, keep symbols readable.
    def inline_math(m):
        s = m.group(1)
        s = re.sub(r'\\(?:left|right|,|;|!|quad|qquad)', ' ', s)
        s = s.replace('\\times', '×').replace('\\cdot', '·').replace('\\pm', '±')
        s = s.replace('\\alpha', 'alpha').replace('\\beta', 'beta').replace('\\sigma', 'sigma')
        s = s.replace('\\mu', 'mu').replace('\\rho', 'rho').replace('\\theta', 'theta')
        s = s.replace('\\leq', '≤').replace('\\geq', '≥').replace('\\neq', '≠')
        s = s.replace('\\sum', 'sum').replace('\\sqrt', 'sqrt').replace('\\infty', 'infinity')
        s = re.sub(r'\\frac\{([^{}]*)\}\{([^{}]*)\}', r'(\1)/(\2)', s)
        s = re.sub(r'\\text\{([^}]*)\}', r'\1', s)
        s = re.sub(r'\\[a-zA-Z]+', '', s)
        s = s.replace('{', '').replace('}', '').replace('_', ' ').replace('^', '^')
        s = s.replace('<', ' less than ').replace('>', ' greater than ')
        return clean(s)
    text = re.sub(r'(?<!\$)\$([^$\n]+)\$(?!\$)', inline_math, text)
    text = re.sub(r'\\\((.*?)\\\)', inline_math, text)
    # Citations.
    def cite(m):
        keys = re.findall(r'@([\w:-]+)', m.group(0))
        return '(' + cite_text(keys, bib) + ')' if keys else ''
    text = re.sub(r'\[[^\]]*@[^\]]*\]', cite, text)
    text = re.sub(r'(?<!\w)@([\w:-]+)', lambda m: cite_text([m.group(1)], bib), text)
    # Strip remaining raw HTML tags after math/citation conversion.
    text = re.sub(r'<[^>]+>', '', text)
    # Links: internal cross-references become plain text; external links keep URL.
    text = re.sub(r'\[([^\]]+)\]\(#([^)]*)\)', r'\1', text)
    text = re.sub(r'<(https?://[^>]+)>', r'\1', text)
    # Heading attributes.
    text = re.sub(r'(?m)^(#{1,6} [^\n]+?)\s*\{#[^}]*\}\s*$', r'\1', text)
    text = re.sub(r'\{\.unnumbered\}|\{\.unlisted\}', '', text)
    # Section filtering by H2 slug.
    if include_sections or exclude_sections:
        lines = text.splitlines(); out = []; keep = True
        inc = set(include_sections or []); exc = set(exclude_sections or [])
        for line in lines:
            m = re.match(r'^## (.+)$', line)
            if m:
                slug = re.sub(r'[^a-z0-9]+', '-', m.group(1).lower()).strip('-')
                keep = (not inc or slug in inc) and slug not in exc
            if keep: out.append(line)
        text = '\n'.join(out)
    # Cleanup Quarto/R artifacts that survive code-chunk removal.
    text = re.sub(r'(?m)^>\s?', '', text)
    text = re.sub(r'`r\s+[^`]*`', '[computed value omitted in this course adaptation]', text)
    text = re.sub(r'\{#[^}]*\}', '', text)
    text = re.sub(r'(?m)^\s*\$\$\s*$', '', text)
    text = re.sub(r'\b(sec|fig|tbl|eq)-[\w-]+, n\.d\.', 'the source discussion', text)
    text = re.sub(r'\b(sec|fig|tbl|eq)-[\w-]+', 'the source discussion', text)
    text = re.sub(r'\(archived at\s*\)', '', text)
    text = re.sub(r'located on GitHub:\s*\.', 'located on GitHub.', text)
    text = re.sub(r'\\[a-zA-Z]+\s*', '', text)
    text = text.replace('$', '')
    text = re.sub(r'\(\s*;\s*\)', '', text)
    text = re.sub(r'\(\s*\)', '', text)
    text = re.sub(r'\s+([,.;:)])', r'\1', text)
    # Remove empty headings.
    lines = text.splitlines(); out = []
    for i, line in enumerate(lines):
        if re.match(r'^#{1,6} ', line):
            j = i + 1
            while j < len(lines) and not lines[j].strip(): j += 1
            if j >= len(lines) or re.match(r'^#{1,6} ', lines[j]):
                continue
        out.append(line)
    text = '\n'.join(out)
    # Normalize whitespace.
    text = re.sub(r'\n{3,}', '\n\n', text)
    lines = [clean(l) for l in text.splitlines()]
    text = '\n'.join(lines)
    text = re.sub(r'\n{3,}', '\n\n', text).strip() + '\n'
    return text

def ensure_openstax():
    import tarfile
    base = ROOT / '.cache/book-sources'
    dest = base / 'cnxbook-psychology-2e-f5c9cf50686749d28cc5a594e0fdc487398f8307'
    if dest.exists(): return dest
    base.mkdir(parents=True, exist_ok=True)
    archive = base / 'psych.tar.gz'
    if not archive.exists():
        urllib.request.urlretrieve(f"https://codeload.github.com/{OPENSTAX['repo']}/tar.gz/{OPENSTAX['commit']}", archive)
    with tarfile.open(archive) as tf:
        tf.extractall(base)
    return dest

def main():
    lic = fetch('LICENSE').decode()
    assert 'Attribution 4.0 International' in lic
    bib = parse_bib(fetch('references.bib').decode('utf-8', errors='replace'))
    chapters = json.loads((BOOK/'chapters.json').read_text())
    blocks = []; refs = {}; seen = set()
    import sys
    sys.path.insert(0, str(ROOT/'scripts'))
    import prepare_cac902_sources as p902
    from xml.etree import ElementTree as ET
    osx_base = None
    for ch in chapters:
        for spec in ch['sources']:
            if spec.get('source') == 'openstax':
                if osx_base is None: osx_base = ensure_openstax()
                mid = spec['id']
                root = ET.parse(osx_base/'modules'/mid/'index.cnxml').getroot()
                title = clean(''.join(root.find('x:title', p902.NS).itertext()))
                md = p902.render_module(root, 'openstax', spec.get('include_sections'))
                md = re.sub(r'\(\s*\)', '', md)
                md = re.sub(r'\*Source figure caption: ([^*]+)\*', r'*Source figure description (original figure omitted): \1*', md)
                md = re.sub(r'\s+([,.;:)])', r'\1', md)
                source_key = 'openstax'; fname = mid
                for r in p902.extract_refs(root):
                    k = re.sub(r'\W+', ' ', r.lower()).strip()
                    if k not in seen:
                        seen.add(k); refs[k] = {'text': r}
            else:
                fname = spec['file']
                raw = fetch(fname).decode('utf-8', errors='replace')
                title_m = re.search(r'(?m)^# (.+?)(?:\s*\{#|$)', raw)
                title = clean(re.sub(r'\s*\{#.*$', '', title_m.group(1))) if title_m else fname
                md = convert_quarto(raw, bib, spec.get('include_sections'), spec.get('exclude_sections'))
                source_key = 'petersen'
                for key in re.findall(r'@([\w:-]+)', raw):
                    if key in bib and key not in seen:
                        seen.add(key); refs[key] = bib[key]
            words = len(re.findall(r"\b[\w’'-]+\b", md))
            block_id = fname.replace('.qmd','') + f"-ch{ch['number']}"
            blocks.append({'id': block_id, 'chapter': ch['number'], 'source_file': fname, 'source_key': source_key, 'title': title,
                           'markdown': md, 'words': words, 'sha256': hashlib.sha256(md.encode()).hexdigest()})
    ref_list = []
    for key, f in refs.items():
        if 'text' in f:
            ref_list.append({'key': key, 'text': clean(f['text'])}); continue
        author = f.get('author',''); year = f.get('year','n.d.'); title = f.get('title','')
        journal = f.get('journal', f.get('booktitle','')); vol = f.get('volume',''); pages = f.get('pages','')
        doi = f.get('doi',''); url = f.get('url','')
        cite = f'{author} ({year}). {title}.'
        if journal: cite += f' {journal}'
        if vol: cite += f', {vol}'
        if pages: cite += f', {pages}'
        cite += '.'
        if doi: cite += f' https://doi.org/{doi}'
        elif url: cite += f' {url}'
        ref_list.append({'key': key, 'text': clean(cite)})
    (BOOK/'source-blocks.json').write_text(json.dumps(blocks, ensure_ascii=False, indent=2)+'\n')
    (BOOK/'source-references.json').write_text(json.dumps(ref_list, ensure_ascii=False, indent=2)+'\n')
    manifest = {'sources': [{**SOURCE, 'retrieved': '2026-11-04', 'license_verified': True,
                 'modifications': 'Quarto/R code and original figures omitted; prose reformatted for PDF; formal equations replaced with adaptation notes or plain-text symbols; citations reformatted; new child-adolescent lectures and diagrams added.'},
                 {**OPENSTAX, 'retrieved': '2026-11-04', 'license_verified': True,
                 'modifications': 'Selected CNXML modules reformatted for PDF; original figures omitted; new child-adolescent lectures and diagrams added.'}],
                'blocks': len(blocks), 'source_words': sum(b['words'] for b in blocks), 'references': len(ref_list)}
    (BOOK/'source-manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n')
    print(f"Prepared {len(blocks)} reading blocks, {sum(b['words'] for b in blocks):,} source words, {len(ref_list)} references")

if __name__ == '__main__':
    main()
