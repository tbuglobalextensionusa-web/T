#!/usr/bin/env python3
"""Build the complete CAC.901 course PDF with vector diagrams and navigation."""
from __future__ import annotations
import json
import math
import re
from pathlib import Path
from xml.sax.saxutils import escape
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer,
                                PageBreak, KeepTogether, Table, TableStyle, Flowable)
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.graphics.shapes import Drawing, Rect, Circle, Line, String, Polygon, PolyLine
from reportlab.graphics import renderPDF

ROOT = Path(__file__).resolve().parents[1]
BOOK = ROOT / 'books/CAC-901'
OUT = ROOT / 'deliverables/CAC-901-advanced-developmental-psychology.pdf'
PAGE_W, PAGE_H = A4
MARGIN = 20 * mm
CONTENT_W = PAGE_W - 2 * MARGIN
INK = colors.HexColor('#172C3B')
TEAL = colors.HexColor('#176B70')
LIGHT = colors.HexColor('#EDF5F4')
PALE = colors.HexColor('#F4F6F8')
GOLD = colors.HexColor('#B77A24')
MUTED = colors.HexColor('#526571')
FONT_DIR = Path('/usr/share/fonts/truetype/dejavu')
for name, file in [('BookSerif','DejaVuSerif.ttf'),('BookSerif-Bold','DejaVuSerif-Bold.ttf'),
                   ('BookSans','DejaVuSans.ttf'),('BookSans-Bold','DejaVuSans-Bold.ttf')]:
    pdfmetrics.registerFont(TTFont(name, str(FONT_DIR / file)))
pdfmetrics.registerFontFamily('BookSerif', normal='BookSerif', bold='BookSerif-Bold')
pdfmetrics.registerFontFamily('BookSans', normal='BookSans', bold='BookSans-Bold')

ST = {}
ST['body'] = ParagraphStyle('Body', fontName='BookSerif', fontSize=9.4, leading=14.1,
                            spaceAfter=7, alignment=TA_JUSTIFY, textColor=INK,
                            splitLongWords=True, allowWidows=0, allowOrphans=0)
ST['reading'] = ParagraphStyle('Reading', parent=ST['body'], fontSize=9.1, leading=13.5)
ST['lecture_heading'] = ParagraphStyle('LectureHeading', fontName='BookSans-Bold', fontSize=15,
                                       leading=20, textColor=TEAL, spaceBefore=7, spaceAfter=13, keepWithNext=True)
ST['h2'] = ParagraphStyle('H2', fontName='BookSans-Bold', fontSize=12, leading=16,
                          textColor=INK, spaceBefore=13, spaceAfter=7, keepWithNext=True)
ST['h3'] = ParagraphStyle('H3', fontName='BookSans-Bold', fontSize=10.2, leading=14,
                          textColor=TEAL, spaceBefore=10, spaceAfter=5, keepWithNext=True)
ST['h4'] = ParagraphStyle('H4', fontName='BookSans-Bold', fontSize=9.5, leading=13,
                          textColor=INK, spaceBefore=8, spaceAfter=4, keepWithNext=True)
ST['chapter_no'] = ParagraphStyle('ChapterNo', fontName='BookSans-Bold', fontSize=11, leading=15,
                                  textColor=TEAL, spaceAfter=9, keepWithNext=True)
ST['chapter_title'] = ParagraphStyle('ChapterTitle', fontName='BookSans-Bold', fontSize=24,
                                     leading=30, textColor=INK, spaceAfter=18, keepWithNext=True)
ST['small'] = ParagraphStyle('Small', fontName='BookSans', fontSize=7.7, leading=11,
                             textColor=MUTED, spaceAfter=6)
ST['caption'] = ParagraphStyle('Caption', fontName='BookSans', fontSize=8, leading=11.5,
                               textColor=MUTED, spaceBefore=6, spaceAfter=12)
ST['note'] = ParagraphStyle('Note', fontName='BookSans', fontSize=8.3, leading=12,
                            textColor=INK, spaceAfter=5)
ST['bullet'] = ParagraphStyle('Bullet', parent=ST['reading'], leftIndent=13, firstLineIndent=0,
                              bulletIndent=1, spaceAfter=4)
ST['ref'] = ParagraphStyle('Reference', fontName='BookSerif', fontSize=8, leading=11.5,
                           textColor=INK, spaceAfter=6, leftIndent=12, firstLineIndent=-12,
                           splitLongWords=True)
ST['toc'] = ParagraphStyle('TOC', fontName='BookSans', fontSize=9, leading=14,
                           textColor=INK, leftIndent=0, firstLineIndent=0, spaceBefore=7)
ST['cover_kicker'] = ParagraphStyle('CoverKicker', fontName='BookSans-Bold', fontSize=12,
                                    leading=18, textColor=TEAL, spaceAfter=28)
ST['cover_title'] = ParagraphStyle('CoverTitle', fontName='BookSans-Bold', fontSize=34,
                                   leading=42, textColor=INK, spaceAfter=22)
ST['cover_sub'] = ParagraphStyle('CoverSub', fontName='BookSerif', fontSize=14, leading=22,
                                 textColor=MUTED, spaceAfter=25)

WORD = re.compile(r'(?=\S*[^\W\d_])[\w]+(?:[’\'-][\w]+)*', re.UNICODE)
def word_count(text): return len(WORD.findall(text))
def p(text, style='body'):
    import textwrap
    text = re.sub(r'\s+', ' ', text)
    if style in {'ref', 'small'}:
        # Explicit line breaks keep historical source URLs inside the frame.
        parts=[]; cursor=0
        for match in re.finditer(r'https?://[^\s]+', text):
            parts.append(escape(text[cursor:match.start()]))
            url=match.group(0)
            parts.append('<br/>'.join(escape(line) for line in textwrap.wrap(url, width=72, break_long_words=True, break_on_hyphens=False)))
            cursor=match.end()
        parts.append(escape(text[cursor:]))
        markup=''.join(parts)
    else:
        markup=escape(text)
    return Paragraph(markup.replace('\n','<br/>'), ST[style])

class BookDoc(BaseDocTemplate):
    def __init__(self, filename):
        super().__init__(filename, pagesize=A4, leftMargin=MARGIN, rightMargin=MARGIN,
                         topMargin=22*mm, bottomMargin=20*mm,
                         title='CAC.901 — Advanced Developmental Psychology',
                         author='Coursebook project; includes adapted OpenStax readings',
                         subject='Doctoral lecture coursebook for child and adolescent counseling',
                         creator='Coursebook PDF production pipeline', pageCompression=1)
        frame = Frame(self.leftMargin, self.bottomMargin, self.width, self.height,
                      leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0, id='main')
        self.addPageTemplates(PageTemplate(id='book', frames=[frame], onPage=self.decorate))
        self.chapter_pages = {}
        self.section_pages = {}
        self.running = 'CAC.901 | Advanced Developmental Psychology'
    def beforeDocument(self):
        self.chapter_pages = {}; self.section_pages = {}; self.running = 'CAC.901 | Advanced Developmental Psychology'
    def decorate(self, canvas, doc):
        canvas.saveState()
        if doc.page > 1:
            canvas.setStrokeColor(colors.HexColor('#CEDCDF'))
            canvas.setLineWidth(.45)
            canvas.line(MARGIN, PAGE_H-15*mm, PAGE_W-MARGIN, PAGE_H-15*mm)
            canvas.setFont('BookSans', 7)
            canvas.setFillColor(MUTED)
            canvas.drawString(MARGIN, PAGE_H-11.5*mm, 'CAC.901  |  ADVANCED DEVELOPMENTAL PSYCHOLOGY')
            canvas.drawRightString(PAGE_W-MARGIN, PAGE_H-11.5*mm, 'DOCTORAL LECTURE COURSEBOOK')
            canvas.line(MARGIN, 13*mm, PAGE_W-MARGIN, 13*mm)
            canvas.drawCentredString(PAGE_W/2, 8.5*mm, str(doc.page))
        canvas.restoreState()
    def afterFlowable(self, flowable):
        if isinstance(flowable, Paragraph):
            key = getattr(flowable, '_bookmark', None)
            if key:
                self.canv.bookmarkPage(key)
                text = flowable.getPlainText()
                level = getattr(flowable, '_outline_level', 0)
                self.canv.addOutlineEntry(text, key, level=level, closed=False)
                if level == 0 and key not in {'frontmatter', 'contents'}:
                    self.notify('TOCEntry', (0, text, self.page, key))
            if hasattr(flowable, '_chapter_number'):
                self.chapter_pages[str(flowable._chapter_number)] = self.page
            for name in ['references_start', 'glossary_start', 'attribution_start', 'frontmatter_start']:
                if getattr(flowable, '_marker', None) == name:
                    self.section_pages[name] = self.page

class Diagram(Flowable):
    def __init__(self, spec, width=CONTENT_W):
        super().__init__()
        self.spec = spec; self.width = width
        self.height = 235 if spec['kind'] in {'hub','trajectories','pathways','levels'} else 205
        self._data = None
    def wrap(self, availWidth, availHeight):
        self.width = min(self.width, availWidth)
        return self.width, self.height
    def draw(self):
        c = self.canv; w,h = self.width,self.height; s=self.spec; kind=s['kind']
        c.saveState()
        c.setFillColor(PALE); c.setStrokeColor(colors.HexColor('#D8E3E6'))
        c.roundRect(0,0,w,h,8,fill=1,stroke=1)
        def wrap_label(label, maxchars):
            words=label.split(); lines=[]; line=''
            for word in words:
                if line and len(line)+len(word)+1>maxchars:
                    lines.append(line); line=word
                else: line=(line+' '+word).strip()
            if line: lines.append(line)
            return lines
        def box(x,y,bw,bh,title,sub='',fill=colors.white):
            c.setFillColor(fill); c.setStrokeColor(TEAL); c.setLineWidth(.8)
            c.roundRect(x,y,bw,bh,5,fill=1,stroke=1)
            c.setFillColor(INK); c.setFont('BookSans-Bold',8)
            lines=wrap_label(title, max(12,int(bw/4.6)))
            start=y+bh/2+(len(lines)-1)*5 + (5 if sub else 0)
            for i,line in enumerate(lines): c.drawCentredString(x+bw/2,start-i*10,line)
            if sub:
                c.setFont('BookSans',6.8); c.setFillColor(MUTED)
                sl=wrap_label(sub,max(14,int(bw/3.8)))
                for i,line in enumerate(sl[:2]): c.drawCentredString(x+bw/2,start-len(lines)*10-3-i*8,line)
        def arrow(x1,y1,x2,y2,color=TEAL):
            c.setStrokeColor(color); c.setFillColor(color); c.setLineWidth(1.1)
            c.line(x1,y1,x2,y2)
            a=math.atan2(y2-y1,x2-x1); size=5
            path=c.beginPath(); path.moveTo(x2,y2)
            path.lineTo(x2-size*math.cos(a-.45),y2-size*math.sin(a-.45))
            path.lineTo(x2-size*math.cos(a+.45),y2-size*math.sin(a+.45)); path.close()
            c.drawPath(path,fill=1,stroke=0)
        if kind in {'flow','timeline'}:
            nodes=s['nodes']; n=len(nodes); gap=12; bw=(w-36-gap*(n-1))/n; bh=86; y=h/2-bh/2
            for i,(title,sub) in enumerate(nodes):
                x=18+i*(bw+gap); box(x,y,bw,bh,title,sub,colors.white if i%2==0 else LIGHT)
                if i<n-1: arrow(x+bw+1,y+bh/2,x+bw+gap-2,y+bh/2)
            c.setFillColor(MUTED); c.setFont('BookSans',7)
            c.drawCentredString(w/2,22,'Read from left to right. Revisit earlier steps when new information appears.')
        elif kind in {'cycle','hub'}:
            nodes=s['nodes']; cx=w/2; cy=h/2
            if kind=='hub':
                bw=(w-70)/2; bh=55
                coords=[(22,h-75),(w-22-bw,h-75),(22,20),(w-22-bw,20)]
                box(cx-67,cy-27,134,54,s['center'],fill=LIGHT)
                for (title,sub),(x,y) in zip(nodes,coords):
                    box(x,y,bw,bh,title,sub)
                    sx=x+bw if x<cx else x; sy=y+bh/2
                    ex=cx-67 if x<cx else cx+67; ey=cy
                    arrow(sx,sy,ex,ey); arrow(ex,ey,sx,sy,color=GOLD)
            else:
                n=len(nodes); bw=min(128,(w-60)/2); bh=48
                if n==4: coords=[(25,h-67),(w-bw-25,h-67),(w-bw-25,19),(25,19)]
                else: coords=[(20,h-65),(w/2-bw/2,h-65),(w-bw-20,h-65),(w-bw-20,20),(20,20)]
                for i,((title,sub),(x,y)) in enumerate(zip(nodes,coords)):
                    box(x,y,bw,bh,title,sub)
                for i in range(n):
                    x,y=coords[i]; nx,ny=coords[(i+1)%n]
                    if abs(y-ny)<1:
                        if nx>x: arrow(x+bw+2,y+bh/2,nx-2,ny+bh/2)
                        else: arrow(x-2,y+bh/2,nx+bw+2,ny+bh/2)
                    elif abs(x-nx)<1:
                        if ny<y: arrow(x+bw/2,y-2,nx+bw/2,ny+bh+2)
                        else: arrow(x+bw/2,y+bh+2,nx+bw/2,ny-2)
                    else:
                        arrow(x+10,y+5,nx+10,ny+bh-5,color=GOLD)
        elif kind=='levels':
            for i,(title,sub) in enumerate(s['nodes']):
                box(28,h-57-i*62,w-56,47,title,sub,colors.white if i!=1 else LIGHT)
        elif kind=='trajectories':
            left,right,bottom,top=55,25,38,28; gw=w-left-right; gh=h-bottom-top
            c.setStrokeColor(MUTED); c.setLineWidth(.8); c.line(left,bottom,left,top+gh); c.line(left,bottom,left+gw,bottom)
            c.setFont('BookSans',7); c.setFillColor(MUTED)
            c.drawString(12,top+gh+8,'Functioning'); c.drawRightString(w-20,16,'Time and changing context →')
            series=[('Support changes',TEAL,[.30,.36,.51,.64,.71,.78]),('Fluctuating demands',GOLD,[.34,.55,.40,.62,.46,.65]),('Later difficulty',colors.HexColor('#805A87'),[.33,.39,.46,.42,.34,.28])]
            for j,(label,color,vals) in enumerate(series):
                pts=[]
                for i,v in enumerate(vals): pts.extend([left+i*gw/(len(vals)-1),bottom+v*gh])
                c.setStrokeColor(color); c.setLineWidth(2); path=c.beginPath(); path.moveTo(pts[0],pts[1]); [path.lineTo(pts[k],pts[k+1]) for k in range(2,len(pts),2)]; c.drawPath(path)
                c.setFillColor(color); c.setFont('BookSans',7)
                c.drawString(left+8,top+gh-12-j*13,label)
            c.setFillColor(MUTED); c.setFont('BookSans',6.8); c.drawCentredString(w/2,8,'Schematic only: no study data or individual predictions.')
        elif kind=='pathways':
            bw=(w-90)/3; bh=52
            box(20,h-78,bw,bh,'Different starting pathways',fill=LIGHT)
            box(w/2-bw/2,h-78,bw,bh,'Similar presenting concern')
            box(w-bw-20,h-78,bw,bh,'Different later outcomes',fill=LIGHT)
            arrow(20+bw,h-52,w/2-bw/2-3,h-52); arrow(w/2+bw/2,h-52,w-bw-23,h-52)
            c.setFont('BookSans',8); c.setFillColor(TEAL)
            c.drawCentredString(w*.29,55,'Equifinality'); c.drawCentredString(w*.71,55,'Multifinality')
            c.setFont('BookSans',7); c.setFillColor(MUTED)
            c.drawCentredString(w/2,28,'Investigate mechanisms, timing, context, and support; do not predict from the label alone.')
        c.restoreState()

class Rule(Flowable):
    def __init__(self,width=CONTENT_W): super().__init__(); self.width=width; self.height=8
    def draw(self): self.canv.setStrokeColor(TEAL); self.canv.setLineWidth(1.3); self.canv.line(0,4,self.width,4)

def heading(text, style, key=None, level=0, chapter=None, marker=None):
    obj=p(text,style)
    if key: obj._bookmark=key; obj._outline_level=level
    if chapter is not None: obj._chapter_number=chapter
    if marker: obj._marker=marker
    return obj

def note_box(title, paragraphs):
    content=[p(title,'h3')]+[p(t,'note') for t in paragraphs]
    table=Table([[content]],colWidths=[CONTENT_W])
    table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),LIGHT),('BOX',(0,0),(-1,-1),.5,colors.HexColor('#BDD7D6')),
                               ('LEFTPADDING',(0,0),(-1,-1),12),('RIGHTPADDING',(0,0),(-1,-1),12),
                               ('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),8)]))
    return table

def parse_lecture(text):
    out=[]
    for line in text.splitlines():
        line=line.strip()
        if not line: continue
        if line.startswith('## '): out.append(p(line[3:],'lecture_heading'))
        elif line.startswith('### '): out.append(p(line[4:],'h3'))
        elif line.startswith('# '): continue
        else: out.append(p(line,'body'))
    return out

def source_table(block):
    rows=block['rows']; n=max(map(len,rows))
    data=[]
    for ri,row in enumerate(rows):
        row=row+['']*(n-len(row))
        data.append([p(x,'note') for x in row])
    # Wide source tables remain readable by allowing tall, wrapping rows.
    t=Table(data,colWidths=[CONTENT_W/n]*n,repeatRows=1,hAlign='LEFT')
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),LIGHT),('VALIGN',(0,0),(-1,-1),'TOP'),
                           ('GRID',(0,0),(-1,-1),.35,colors.HexColor('#C9D5DA')),
                           ('LEFTPADDING',(0,0),(-1,-1),5),('RIGHTPADDING',(0,0),(-1,-1),5),
                           ('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5)]))
    return [p(block['text'],'caption'),t,Spacer(1,9)]

def render_blocks(blocks):
    out=[]; note_depth=0
    for b in blocks:
        typ=b['type']; text=b.get('text','')
        if typ=='heading': out.append(p(text,'h'+str(min(4,max(2,b['level'])))))
        elif typ=='paragraph': out.append(p(text,'note' if note_depth else 'reading'))
        elif typ=='quote': out.append(p(text,'note' if note_depth else 'reading'))
        elif typ in {'list','question','answer'}:
            prefix={'list':'•','question':'Q.','answer':'A.'}[typ]
            for i,item in enumerate(b['items'],1):
                bullet=f'{i}.' if typ=='question' and b.get('numbered') else prefix
                out.append(Paragraph(escape(item),ST['bullet'],bulletText=bullet))
        elif typ=='note_start':
            note_depth+=1; out.append(Spacer(1,5)); out.append(p(text,'h4'))
        elif typ=='note_end': note_depth=max(0,note_depth-1); out.append(Spacer(1,5))
        elif typ=='source_figure_description':
            out.append(p('Source illustration description (image not reproduced): '+text,'caption'))
        elif typ=='equation': out.append(p(text,'note'))
        elif typ=='table': out.extend(source_table(b))
    return out

def build():
    chapters=json.loads((BOOK/'source-blocks.json').read_text())
    diagrams={d['chapter']:d for d in json.loads((BOOK/'diagrams.json').read_text())}
    refs=json.loads((BOOK/'source-references.json').read_text())
    supp=json.loads((BOOK/'supplemental-references.json').read_text())
    manifest=json.loads((BOOK/'source-manifest.json').read_text())
    lectures={}
    for part in sorted((BOOK/'lectures').glob('part-*.md')):
        chunks=re.split(r'^# CHAPTER (\d+)\s*$',part.read_text(),flags=re.M)
        for i in range(1,len(chunks),2): lectures[int(chunks[i])]=chunks[i+1].strip()
    assert len(lectures)==20 and set(lectures)==set(range(1,21))
    story=[]; substantive=0
    # Cover
    story += [Spacer(1,35),p('PhD in Children and Adolescent Counseling','cover_kicker'),
              p('CAC.901','cover_kicker'),p('Advanced Developmental Psychology','cover_title'),Rule(),Spacer(1,20),
              p('A doctoral lecture coursebook','cover_sub'),
              p('Developmental plasticity • Cognition • Emotion • Trajectories • Longitudinal research','note'),
              Spacer(1,25),p('Twenty lecture chapters with real-life applications, original diagrams, seminar tasks, a working glossary, and attributed foundational readings.','body'),
              Spacer(1,30),p('PDF-only course edition • 2026','small'),
              p('Prepared for the supplied curriculum. This independent educational volume is not an official university publication, accreditation document, or clinical practice guideline.','small'),PageBreak()]
    # Front matter
    story.append(heading('How to Use This Book','chapter_title',key='frontmatter',marker='frontmatter_start'))
    front=[
      ('Purpose and scope','This volume covers CAC.901 Advanced Developmental Psychology within the supplied PhD curriculum. It connects developmental science to counseling, family relationships, school participation, research interpretation, and ethical reflection. It is a complete course volume, not a claim to contain the entire discipline.'),
      ('Two clearly identified layers','Each chapter begins with a newly written counseling lecture, a real-life application, and a doctoral seminar task. An original vector diagram makes a central relationship visible. The chapter then provides attributed foundational readings adapted from OpenStax Psychology 2e. The readings supply broader psychological background; the new lectures provide the counseling interpretation and critical cautions.'),
      ('Simple English with doctoral reasoning','Technical terms are introduced in context and collected in the glossary. Simple language is not treated as a reason to avoid uncertainty, competing explanations, measurement limitations, or structural influences. The seminar tasks ask the reader to evaluate evidence and revise decisions rather than memorize labels.'),
      ('How to study a chapter','Read the learning aims, study the lecture, explain the diagram in your own words, and complete the application task. Then read the foundational material critically. Record which claims are supported by the source, which require newer evidence, and which depend on local law or professional guidance. Finish with a short reflective note about implications for practice.'),
      ('Cases and diagrams','All named cases in the new lectures are fictional teaching examples. They are not research participants or evidence of treatment effectiveness. The twenty numbered course diagrams are original conceptual illustrations. Graphs without data are explicitly labeled as schematics. Source photographs and illustrations are not reproduced; their descriptions are retained only as reading support.'),
      ('Clinical and legal caution','This book is for education and professional development. It does not provide individualized diagnosis, treatment, legal advice, or emergency care. The foundational readings come from a 2020 introductory textbook. Diagnostic terminology, prevalence estimates, and examples may be dated. Use current professional standards, applicable law, qualified supervision, and appropriate referral for real cases.'),
      ('Safeguarding and participation','Explain confidentiality and its limits in understandable language. Seek appropriate permission and the child’s informed assent. Follow local safeguarding requirements and urgent safety procedures. Do not use a teaching exercise to investigate an allegation or pressure a child into disclosure. Share only information needed for a legitimate protective or care purpose.'),
      ('Source transparency','The OpenStax readings are used under Creative Commons Attribution 4.0. They have been selected, reorganized, and typeset for this course, with new lectures and diagrams added. They are not presented as wholly original text. Module-level attribution and a pinned source snapshot appear in the attribution register. Inherited references are identified separately from the supplemental sources checked for this edition.'),
      ('Length and verification','The publication check counts lexical words in the actual PDF’s instructional pages and excludes the reference section, front matter, running headers, and page numbers. The minimum is 150,000 words for this individual book. The verification report is saved with the production files; the PDF is the reader-facing deliverable.')]
    for title,text in front: story += [p(title,'h3'),p(text,'body')]
    story += [Spacer(1,8),note_box('Course coverage at a glance',[
        'Developmental plasticity: Chapters 1, 4, 6, 7, 16, and 20.',
        'Cognitive development: Chapters 4, 5, 8, 9, 10, and 11.',
        'Emotional and social development: Chapters 5, 12, 13, 14, and 15.',
        'Developmental trajectories: Chapters 1, 3, 16, 17, and 20.',
        'Longitudinal research and ethics: Chapters 2, 3, 10, 19, and 20.',
        'Integrated clinical assessment and doctoral reflection: Chapters 17–20.']),PageBreak()]
    story.append(heading('Contents','chapter_title',key='contents'))
    toc=TableOfContents(); toc.levelStyles=[ST['toc']]; toc.dotsMinLevel=0
    story += [toc,PageBreak()]
    # Chapters
    for chapter in chapters:
        n=chapter['number']; title=chapter['title']
        story.append(heading(f'CHAPTER {n:02d}  /  CAC.901','chapter_no'))
        story.append(heading(title,'chapter_title',key=f'chapter-{n}',chapter=n))
        lecture=lectures[n]; story.extend(parse_lecture(lecture)); substantive+=word_count(lecture)
        d=diagrams[n]
        story += [Spacer(1,7),KeepTogether([Diagram(d),p(f'Figure {n}.1. {d["title"]}. {d["caption"]} Original course diagram.','caption')])]
        if chapter['readings']:
            story += [PageBreak(),p('Foundational Readings','lecture_heading'),
                      note_box('Attribution and critical-reading note',[
                        'Adapted from Psychology 2e by Rose M. Spielman, William J. Jenkins, and Marilyn D. Lovett, OpenStax, Rice University (2020), CC BY 4.0. Selection, organization, and PDF layout modified for this course; new lectures and course diagrams are separate additions.',
                        'These readings provide introductory foundations, not current diagnostic or legal authority. Read examples and statistical claims critically. Consult the chapter lecture, current professional guidance, and the source record when making real decisions.'])]
            for reading in chapter['readings']:
                story += [Spacer(1,13),heading(reading['title'],'h2',key=f'reading-{reading["module"]}',level=1),
                          p('OpenStax source module '+reading['module']+' • '+reading['url'],'small')]
                rendered=render_blocks(reading['blocks']); story.extend(rendered)
                substantive+=reading['substantive_words']
        story.append(PageBreak())
    # Applied workbook is new course material, not source-text padding.
    workbook=(BOOK/'applied-workbook.md').read_text()
    story.append(heading('Applied Developmental Workbook','chapter_title',key='workbook'))
    for line in workbook.splitlines():
        line=line.strip()
        if not line or line=='# Applied Developmental Workbook': continue
        if line.startswith('## '): story.append(p(line[3:],'h2'))
        else: story.append(p(line,'body'))
    substantive+=word_count(workbook)
    story.append(PageBreak())
    # Glossary included in instructional count.
    glossary=(BOOK/'glossary.md').read_text()
    story.append(heading('Working Glossary','chapter_title',key='glossary',marker='glossary_start'))
    for line in glossary.splitlines():
        line=line.strip()
        if not line or line.startswith('# ') or line.startswith('These short definitions'): continue
        # Only the controlled bold term syntax is used in this file.
        if line.startswith('**') and '.**' in line:
            term,definition=line[2:].split('.**',1)
            story.append(Paragraph('<b>'+escape(term)+'.</b>'+escape(definition),ST['body']))
        else: story.append(p(line,'body'))
    substantive+=word_count(glossary)
    story.append(PageBreak())
    # References are deliberately not counted.
    story.append(heading('References and Source Notes','chapter_title',key='references',marker='references_start'))
    story += [p('Supplemental sources checked for this edition','h2'),
              p('The following sources support the new lectures and editorial framework. Verification means that the cited bibliographic record was located; it does not mean that every claim in a source has been independently replicated.','small')]
    for entry in supp:
        story += [p(entry['citation'],'ref'),p('Use in this volume: '+entry['use'],'small')]
    story += [p('Inherited OpenStax reference lists','h2'),
              p('The entries below are retained from the source textbook to make its reading trail visible. They have not all been independently reverified for this edition. Some URLs, editions, and terminology are historical. Their inclusion is not a current clinical endorsement. These entries are excluded from the substantive word count.','small')]
    seen=set(); ref_count=0
    titles={'m82166':'Psychological research','m82171':'Biopsychology','m82198':'Learning','m82203':'Thinking and intelligence','m82212':'Memory','m82217':'Lifespan development','m82224':'Emotion and motivation','m82232':'Personality','m82242':'Social psychology','m82258':'Stress, lifestyle, and health','m82264':'Psychological disorders','m82280':'Therapy and treatment'}
    for module,entries in refs.items():
        story.append(p(titles.get(module,module),'h3'))
        for entry in entries:
            normalized=re.sub(r'\s+',' ',entry).strip().lower()
            if normalized in seen: continue
            seen.add(normalized); story.append(p(entry,'ref')); ref_count+=1
    story.append(PageBreak())
    story.append(heading('Attribution and Production Record','chapter_title',key='attribution',marker='attribution_start'))
    story += [p('OpenStax attribution','h2'),p('Psychology 2e by Rose M. Spielman, William J. Jenkins, and Marilyn D. Lovett. OpenStax, Rice University, 2020. Used under Creative Commons Attribution 4.0 International. Source repository: '+manifest['repository']+'. Pinned snapshot: '+manifest['snapshot_commit']+'.','body'),
              p('License: '+manifest['license_url']+'. The full license text is included in the source archive accompanying the production files. OpenStax and Rice University do not endorse this adaptation.','body'),
              p('Changes made for this course','h2')]
    story += [p(x,'body') for x in manifest['adaptations']]
    story += [p('Module register','h2')]
    for chapter in chapters:
        if chapter['readings']:
            story.append(p(f'Chapter {chapter["number"]}: '+', '.join(r['module']+' — '+r['title'] for r in chapter['readings'])+'.','small'))
    story += [p('Rights and authorship distinction','h2'),p('The newly written counseling lectures, fictional applications, seminar tasks, glossary, and original vector diagrams are course-specific additions. The foundational reading text remains attributed to the OpenStax authors. Third-party material is not relicensed by this project. No source photographs are reproduced. No endorsement by OpenStax, Rice University, or a university degree program is implied.','body'),
              p('Publication verification','h2'),p('This PDF is generated from the saved manuscript and source blocks. The production check verifies the individual PDF’s instructional word count, page count, chapter navigation, diagrams, and absence of empty pages. The reference section is excluded from the minimum-length check. See the machine-readable verification report in the production workspace for the exact count and file hash.','body')]
    OUT.parent.mkdir(parents=True,exist_ok=True)
    doc=BookDoc(str(OUT))
    print(f'Building {len(story):,} flowables; estimated substantive manuscript words: {substantive:,}',flush=True)
    doc.multiBuild(story)
    report={'course':'CAC.901','title':'Advanced Developmental Psychology','estimated_substantive_manuscript_words':substantive,
            'chapters':20,'original_vector_diagrams':20,'source_modules':len(manifest['modules_used']),
            'deduplicated_inherited_reference_entries':ref_count,'chapter_pages':doc.chapter_pages,'section_pages':doc.section_pages,
            'pdf':str(OUT.relative_to(ROOT))}
    (BOOK/'build-record.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2),flush=True)

if __name__=='__main__': build()
