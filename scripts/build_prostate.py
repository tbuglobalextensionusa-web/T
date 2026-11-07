#!/usr/bin/env python3
"""Build the EAT WELL, LIVE WELL, PROTECT YOUR PROSTATE textbook PDF.

Pipeline: cover artwork first, front matter, contents, six part dividers,
forty chapters with figures. Missing figure files render as a labelled
placeholder frame so partial asset sets still produce a reviewable build.
"""
from __future__ import annotations
import json
import re
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (BaseDocTemplate, PageTemplate, Frame, Paragraph,
                                Spacer, PageBreak, Image as RLImage,
                                Flowable, NextPageTemplate)
from reportlab.platypus.tableofcontents import TableOfContents

ROOT = Path(__file__).resolve().parents[1]
BOOK = ROOT / 'books/eat-well-live-well-prostate'
CHDIR = BOOK / 'manuscript' / 'chapters'
OUT = ROOT / 'deliverables/eat-well-live-well-protect-your-prostate.pdf'

PAGE_W, PAGE_H = A4
MARGIN = 20 * mm
INK = colors.HexColor('#172C3B')
TEAL = colors.HexColor('#176B70')
GOLD = colors.HexColor('#B77A24')
MUTED = colors.HexColor('#526571')
LIGHT = colors.HexColor('#EDF5F4')
PALE = colors.HexColor('#F4F6F8')

FONT_DIR = Path('/usr/share/fonts/truetype/dejavu')
for name, file in [('BookSerif', 'DejaVuSerif.ttf'), ('BookSerif-Bold', 'DejaVuSerif-Bold.ttf'),
                   ('BookSans', 'DejaVuSans.ttf'), ('BookSans-Bold', 'DejaVuSans-Bold.ttf')]:
    pdfmetrics.registerFont(TTFont(name, str(FONT_DIR / file)))
pdfmetrics.registerFontFamily('BookSerif', normal='BookSerif', bold='BookSerif-Bold')
pdfmetrics.registerFontFamily('BookSans', normal='BookSans', bold='BookSans-Bold')

TITLE = 'EAT WELL, LIVE WELL, PROTECT YOUR PROSTATE'
SUBTITLE = ('A Comprehensive Guide to Prostate-Friendly Nutrition, Healthy Sexual '
            'Living, Weight Management, and Practical Strategies for Reducing '
            'Urinary Symptoms')
IMPRINT = 'TRIUNE BIBLICAL UNIVERSITY GLOBAL EXTENSION USA'
RUNNING = 'Eat Well, Live Well, Protect Your Prostate'

ST = {}
ST['body'] = ParagraphStyle('Body', fontName='BookSerif', fontSize=9.5, leading=14.4,
                            spaceAfter=7, alignment=TA_JUSTIFY, textColor=INK,
                            splitLongWords=True, allowWidows=0, allowOrphans=0)
ST['h2'] = ParagraphStyle('H2', fontName='BookSans-Bold', fontSize=16.5, leading=21,
                          textColor=INK, spaceBefore=2, spaceAfter=14, keepWithNext=True)
ST['h3'] = ParagraphStyle('H3', fontName='BookSans-Bold', fontSize=11, leading=15,
                          textColor=TEAL, spaceBefore=13, spaceAfter=6, keepWithNext=True)
ST['chapter_no'] = ParagraphStyle('ChapterNo', fontName='BookSans-Bold', fontSize=11,
                                  leading=15, textColor=GOLD, spaceAfter=8, keepWithNext=True)
ST['caption'] = ParagraphStyle('Caption', fontName='BookSans', fontSize=8, leading=11.5,
                               textColor=MUTED, spaceBefore=5, spaceAfter=12,
                               alignment=TA_LEFT)
ST['part_kicker'] = ParagraphStyle('PartKicker', fontName='BookSans-Bold', fontSize=13,
                                   leading=18, textColor=GOLD, spaceAfter=10,
                                   alignment=TA_CENTER)
ST['part_title'] = ParagraphStyle('PartTitle', fontName='BookSerif-Bold', fontSize=27,
                                  leading=34, textColor=INK, spaceAfter=14,
                                  alignment=TA_CENTER)
ST['fm_h'] = ParagraphStyle('FmH', fontName='BookSans-Bold', fontSize=15, leading=20,
                            textColor=TEAL, spaceBefore=10, spaceAfter=10)
ST['center'] = ParagraphStyle('Center', fontName='BookSerif', fontSize=11, leading=17,
                              textColor=INK, alignment=TA_CENTER, spaceAfter=9)
ST['center_bold'] = ParagraphStyle('CenterBold', parent=ST['center'],
                                   fontName='BookSans-Bold', fontSize=15, leading=21)
ST['toc'] = ParagraphStyle('TOC', fontName='BookSans', fontSize=9.3, leading=15,
                           textColor=INK, leftIndent=0, firstLineIndent=0, spaceBefore=5)


class HRule(Flowable):
    def __init__(self, width, color=GOLD, thickness=1.1, space=4):
        super().__init__()
        self.width = width
        self.color = color
        self.thickness = thickness
        self.space = space
        self.height = space * 2

    def draw(self):
        self.canv.setStrokeColor(self.color)
        self.canv.setLineWidth(self.thickness)
        self.canv.line(0, self.space, self.width, self.space)


class Placeholder(Flowable):
    """Figure frame used while artwork is still being generated."""
    def __init__(self, width, height, label):
        super().__init__()
        self.width = width
        self.height = height
        self.label = label

    def draw(self):
        c = self.canv
        c.setStrokeColor(colors.HexColor('#9FB6BC'))
        c.setFillColor(PALE)
        c.setLineWidth(0.8)
        c.rect(0, 0, self.width, self.height, stroke=1, fill=1)
        c.setFillColor(MUTED)
        c.setFont('BookSans', 9)
        c.drawCentredString(self.width / 2, self.height / 2 + 5, 'Figure artwork')
        c.drawCentredString(self.width / 2, self.height / 2 - 9, self.label)


def p(text: str, style: str = 'body') -> Paragraph:
    return Paragraph(escape(re.sub(r'\s+', ' ', text)).replace('\n', '<br/>'), ST[style])


class BookDoc(BaseDocTemplate):
    def __init__(self, filename):
        super().__init__(filename, pagesize=A4, leftMargin=MARGIN, rightMargin=MARGIN,
                         topMargin=22 * mm, bottomMargin=20 * mm,
                         title=TITLE, author=IMPRINT, subject=SUBTITLE,
                         creator='Prostate textbook production pipeline', pageCompression=1)
        frame = Frame(self.leftMargin, self.bottomMargin, self.width, self.height,
                      leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0, id='main')
        self.addPageTemplates([
            PageTemplate(id='cover', frames=[Frame(0, 0, PAGE_W, PAGE_H, 0, 0, 0, 0,
                                                   id='coverframe')], onPage=self.cover_page),
            PageTemplate(id='book', frames=[frame], onPage=self.decorate),
        ])
        self.section = ''

    def beforeDocument(self):
        self.section = ''

    def cover_page(self, canvas, doc):
        pass

    def decorate(self, canvas, doc):
        canvas.saveState()
        if doc.page > 1:
            canvas.setStrokeColor(colors.HexColor('#CEDCDF'))
            canvas.setLineWidth(0.45)
            canvas.line(MARGIN, PAGE_H - 15 * mm, PAGE_W - MARGIN, PAGE_H - 15 * mm)
            canvas.setFont('BookSans', 7)
            canvas.setFillColor(MUTED)
            canvas.drawString(MARGIN, PAGE_H - 13 * mm, RUNNING)
            if self.section:
                canvas.drawRightString(PAGE_W - MARGIN, PAGE_H - 13 * mm, self.section[:64])
            canvas.line(MARGIN, 13 * mm, PAGE_W - MARGIN, 13 * mm)
            canvas.setFont('BookSans', 8)
            canvas.setFillColor(INK)
            canvas.drawCentredString(PAGE_W / 2, 9.5 * mm, str(doc.page))
        canvas.restoreState()

    def afterFlowable(self, flowable):
        if isinstance(flowable, Paragraph):
            style = flowable.style.name
            part_entry = getattr(flowable, 'tocEntry', None)
            if part_entry:
                key = f'part-{id(flowable)}'
                self.canv.bookmarkPage(key)
                self.notify('TOCEntry', (0, part_entry, self.page, key))
                self.canv.addOutlineEntry(part_entry, key, 0, 0)
            if style == 'H2':
                self.section = text = re.sub(r'<[^>]+>', '', flowable.getPlainText())
                key = f'ch-{id(flowable)}'
                self.canv.bookmarkPage(key)
                self.notify('TOCEntry', (0, text, self.page, key))
                self.canv.addOutlineEntry(text, key, 0, 0)


def split_chapter(text: str) -> tuple[int, str, list[tuple[str, list[str]]]]:
    lines = text.splitlines()
    ch_no = 0
    title = ''
    sections: list[tuple[str, list[str]]] = []
    current: tuple[str, list[str]] = ('', [])
    in_front = True
    for line in lines:
        s = line.strip()
        if s.startswith('# CHAPTER'):
            m = re.search(r'(\d+)', s)
            ch_no = int(m.group(1)) if m else 0
            in_front = False
            continue
        if in_front:
            if s.startswith('## ') and not title:
                title = s[3:].strip()
            continue
        if s.startswith('## '):
            title = s[3:].strip()
            continue
        if s.startswith('### '):
            current = (s[4:].strip(), [])
            sections.append(current)
            continue
        current[1].append(line)
    return ch_no, title, sections


def render_body(block_lines: list[str], story: list, missing: list[str]) -> None:
    buf: list[str] = []

    def flush():
        if buf:
            joined = ' '.join(x.strip() for x in buf if x.strip())
            if joined:
                story.append(p(joined))
            buf.clear()

    for raw in block_lines:
        s = raw.strip()
        if not s:
            flush()
            continue
        m = re.match(r'!\[([^\]]*)\]\(([^)]+)\)', s)
        if m:
            flush()
            rel = m.group(2)
            img_path = BOOK / rel
            width = 118 * mm
            if img_path.exists():
                try:
                    from PIL import Image as PILImage
                    with PILImage.open(img_path) as im:
                        iw, ih = im.size
                    height = width * ih / iw
                    max_h = 92 * mm
                    if height > max_h:
                        height = max_h
                        width = height * iw / ih
                    story.append(Spacer(1, 6))
                    story.append(RLImage(str(img_path), width=width, height=height))
                except Exception:
                    story.append(Placeholder(width, 60 * mm, rel))
            else:
                missing.append(rel)
                story.append(Spacer(1, 6))
                story.append(Placeholder(width, 72 * mm, Path(rel).name))
            continue
        if s == '---':
            flush()
            story.append(HRule(118 * mm))
            continue
        if re.match(r'\*Figure \d+', s):
            flush()
            story.append(p(s.strip('*'), 'caption'))
            continue
        buf.append(s)
    flush()


def build() -> None:
    meta = json.loads((BOOK / 'chapters.json').read_text())
    parts = meta['parts']
    chapters = meta['chapters']
    part_of = {}
    for part in parts:
        for n in part['chapters']:
            part_of[n] = part

    doc = BookDoc(str(OUT))
    story: list = []

    # ---- Cover (full bleed) ----
    story.append(NextPageTemplate('book'))
    cover_img = BOOK / 'assets/cover-final.png'
    if cover_img.exists():
        story.append(RLImage(str(cover_img), width=PAGE_W, height=PAGE_H))
    story.append(PageBreak())

    # ---- Title page ----
    story.append(Spacer(1, 46 * mm))
    story.append(p(TITLE, 'center_bold'))
    story.append(Spacer(1, 6 * mm))
    story.append(HRule(120 * mm))
    story.append(Spacer(1, 6 * mm))
    story.append(p(SUBTITLE, 'center'))
    story.append(Spacer(1, 16 * mm))
    story.append(p(IMPRINT, 'center_bold'))
    story.append(PageBreak())

    # ---- Copyright page ----
    fm_text = (BOOK / 'manuscript/front-matter.md').read_text()
    copy_section = re.search(r'## Copyright Page\n(.*?)(?=\n## |\Z)', fm_text, re.S)
    story.append(p('Copyright and Publishing Information', 'fm_h'))
    if copy_section:
        for para in copy_section.group(1).strip().split('\n\n'):
            para = ' '.join(para.split())
            if para:
                story.append(p(para))
    story.append(PageBreak())

    # ---- Contents ----
    story.append(p('Contents', 'fm_h'))
    story.append(HRule(120 * mm))
    toc = TableOfContents()
    toc.levelStyles = [ST['toc']]
    story.append(toc)
    story.append(PageBreak())

    missing: list[str] = []

    # ---- Chapters with part dividers ----
    seen_parts: set[int] = set()
    for ch in chapters:
        n = ch['number']
        part = part_of.get(n)
        if part and part['number'] not in seen_parts:
            seen_parts.add(part['number'])
            story.append(Spacer(1, 26 * mm))
            story.append(p(f"PART {part['number']}", 'part_kicker'))
            story.append(HRule(110 * mm))
            story.append(Spacer(1, 4 * mm))
            part_para = p(part['title'], 'part_title')
            part_para.tocEntry = f"Part {part['number']}: {part['title']}"
            story.append(part_para)
            opener = BOOK / 'assets' / part['opener']
            if opener.exists():
                story.append(Spacer(1, 6 * mm))
                try:
                    from PIL import Image as PILImage
                    with PILImage.open(opener) as im:
                        ow, oh = im.size
                    story.append(RLImage(str(opener), width=104 * mm,
                                         height=104 * mm * oh / ow))
                except Exception:
                    story.append(Placeholder(104 * mm, 52 * mm, part['opener']))
            story.append(PageBreak())

        fpath = CHDIR / f'ch{n:02d}.md'
        ch_no, title, sections = split_chapter(fpath.read_text())
        story.append(p(f'CHAPTER {ch_no}', 'chapter_no'))
        story.append(p(title, 'h2'))
        story.append(HRule(118 * mm))
        story.append(Spacer(1, 4))
        for sec_title, sec_lines in sections:
            if sec_title:
                story.append(p(sec_title, 'h3'))
            render_body(sec_lines, story, missing)
        story.append(PageBreak())

    doc.multiBuild(story)
    print(f'wrote {OUT}')
    if missing:
        print(f'missing figure assets ({len(missing)}):')
        for m in sorted(set(missing)):
            print(' -', m)
    print(f'total pages: {doc.page}')


if __name__ == '__main__':
    build()
