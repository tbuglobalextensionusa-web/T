#!/usr/bin/env python3
"""Build the complete CAC.902 course PDF with vector diagrams and navigation."""
from __future__ import annotations
import json, re, html, textwrap
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer,
                                PageBreak, Table, TableStyle, Flowable, KeepTogether)

ROOT = Path(__file__).resolve().parents[1]
BOOK = ROOT / 'books/CAC-902'
OUT = ROOT / 'deliverables/CAC-902-theories-of-counseling-and-psychotherapy.pdf'
FONT_DIR = Path('/usr/share/fonts/truetype/dejavu')
for name, file in [('DejaVu', 'DejaVuSans.ttf'), ('DejaVu-Bold', 'DejaVuSans-Bold.ttf'),
                   ('DejaVuSerif', 'DejaVuSerif.ttf'), ('DejaVuSerif-Bold', 'DejaVuSerif-Bold.ttf')]:
    pdfmetrics.registerFont(TTFont(name, str(FONT_DIR / file)))
pdfmetrics.registerFontFamily('DejaVu', normal='DejaVu', bold='DejaVu-Bold', italic='DejaVu', boldItalic='DejaVu-Bold')
pdfmetrics.registerFontFamily('DejaVuSerif', normal='DejaVuSerif', bold='DejaVuSerif-Bold', italic='DejaVuSerif', boldItalic='DejaVuSerif-Bold')

PAGE_W, PAGE_H = A4
MARGIN = 20*mm
INK = colors.HexColor('#17252A')
TEAL = colors.HexColor('#1F6F78')
LIGHT = colors.HexColor('#EAF3F3')
MUTED = colors.HexColor('#5B6B70')
RULE = colors.HexColor('#C9D6D8')
ST = {}
ST['body'] = ParagraphStyle('body', fontName='DejaVuSerif', fontSize=10.2, leading=15.2, textColor=INK, spaceAfter=7.5, splitLongWords=True, allowWidows=0, allowOrphans=0)
ST['small'] = ParagraphStyle('small', fontName='DejaVu', fontSize=8.2, leading=11.5, textColor=MUTED, spaceAfter=5)
ST['note'] = ParagraphStyle('note', fontName='DejaVu', fontSize=9, leading=13, textColor=INK, spaceAfter=6)
ST['h2'] = ParagraphStyle('h2', fontName='DejaVu-Bold', fontSize=13, leading=17, textColor=TEAL, spaceBefore=12, spaceAfter=7, keepWithNext=True)
ST['h3'] = ParagraphStyle('h3', fontName='DejaVu-Bold', fontSize=11, leading=15, textColor=INK, spaceBefore=10, spaceAfter=5, keepWithNext=True)
ST['chapter_no'] = ParagraphStyle('chapter_no', fontName='DejaVu-Bold', fontSize=10, leading=13, textColor=TEAL, spaceAfter=8)
ST['chapter_title'] = ParagraphStyle('chapter_title', fontName='DejaVu-Bold', fontSize=22, leading=27, textColor=INK, spaceAfter=12)
ST['cover_kicker'] = ParagraphStyle('cover_kicker', fontName='DejaVu-Bold', fontSize=12, leading=16, textColor=TEAL, spaceAfter=12)
ST['cover_title'] = ParagraphStyle('cover_title', fontName='DejaVu-Bold', fontSize=30, leading=36, textColor=INK, spaceAfter=16)
ST['toc'] = ParagraphStyle('toc', fontName='DejaVu', fontSize=9.2, leading=13, textColor=INK, spaceAfter=3)
ST['ref'] = ParagraphStyle('ref', fontName='DejaVu', fontSize=8.3, leading=11.5, textColor=INK, spaceAfter=5)
ST['tablecell'] = ParagraphStyle('tablecell', fontName='DejaVu', fontSize=8.6, leading=11.5, textColor=INK)
ST['caption'] = ParagraphStyle('caption', fontName='DejaVu', fontSize=8.6, leading=12, textColor=MUTED, spaceBefore=4, spaceAfter=8)

def esc(s): return html.escape(s, quote=False)
def inline_md(s):
    s = esc(s)
    s = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', lambda m: f'<link href="{html.escape(m.group(2), quote=True)}" color="#1F6F78">{m.group(1)}</link>', s)
    s = re.sub(r'\*\*([^*]+)\*\*', r'<b>\1</b>', s)
    s = re.sub(r'\*([^*]+)\*', r'<i>\1</i>', s)
    s = re.sub(r'`([^`]+)`', r'<font face="DejaVu">\1</font>', s)
    return s
def p(s, style='body'): return Paragraph(inline_md(s), ST[style])
def heading(s, style='h2', key=None, marker=None):
    par = p(s, style)
    if key: par._bookmark_key = key
    if marker: par._marker = marker
    return par
def url_html(url):
    chunks = textwrap.wrap(url, width=72, break_long_words=True, break_on_hyphens=False) or ['']
    safe = '<br/>'.join(esc(c) for c in chunks)
    return f'<link href="{html.escape(url, quote=True)}" color="#1F6F78">{safe}</link>'

def markdown(text):
    lines = text.splitlines(); out=[]; i=0
    while i < len(lines):
        line = lines[i].rstrip()
        if not line.strip(): i+=1; continue
        if line.startswith('|'):
            rows=[]
            while i < len(lines) and lines[i].strip().startswith('|'):
                cells=[c.strip() for c in lines[i].strip().strip('|').split('|')]
                if not all(re.fullmatch(r':?-{3,}:?', c) for c in cells): rows.append(cells)
                i+=1
            if rows:
                width=max(len(r) for r in rows)
                data=[[Paragraph(inline_md(c), ST['tablecell']) for c in r+['']*(width-len(r))] for r in rows]
                t=Table(data, colWidths=[(PAGE_W-2*MARGIN)/width]*width, repeatRows=1, hAlign='LEFT')
                t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),LIGHT),('GRID',(0,0),(-1,-1),0.4,RULE),
                                       ('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),5),('RIGHTPADDING',(0,0),(-1,-1),5),
                                       ('TOPPADDING',(0,0),(-1,-1),4),('BOTTOMPADDING',(0,0),(-1,-1),4)]))
                out += [t, Spacer(1,8)]
            continue
        if line.startswith('#### '): out.append(heading(line[5:], 'h3')); i+=1; continue
        if line.startswith('### '): out.append(heading(line[4:], 'h3')); i+=1; continue
        if line.startswith('## '): out.append(heading(line[3:], 'h2')); i+=1; continue
        if line.startswith('# '): out.append(heading(line[2:], 'h2')); i+=1; continue
        if re.match(r'^[-*] ', line):
            items=[]
            while i < len(lines) and re.match(r'^[-*] ', lines[i].strip()):
                items.append(lines[i].strip()[2:]); i+=1
            for it in items: out.append(p('• '+it, 'body'))
            continue
        if re.match(r'^\d+\. ', line):
            items=[]
            while i < len(lines) and re.match(r'^\d+\. ', lines[i].strip()):
                items.append(re.sub(r'^\d+\. ', '', lines[i].strip())); i+=1
            for n,it in enumerate(items,1): out.append(p(f'{n}. {it}', 'body'))
            continue
        para=[line]; i+=1
        while i < len(lines) and lines[i].strip() and not re.match(r'^(#|\||[-*] |\d+\. )', lines[i].strip()):
            para.append(lines[i].strip()); i+=1
        out.append(p(' '.join(para), 'body'))
    return out

class Rule(Flowable):
    def __init__(self, width=PAGE_W-2*MARGIN): super().__init__(); self.width=width; self.height=6
    def draw(self): self.canv.setStrokeColor(RULE); self.canv.setLineWidth(0.6); self.canv.line(0,3,self.width,3)

class Diagram(Flowable):
    def __init__(self, spec):
        super().__init__(); self.spec=spec; self.width=PAGE_W-2*MARGIN; self.height=210
    def wrap(self, aw, ah): return self.width, self.height
    def draw(self):
        c=self.canv; s=self.spec; kind=s['type']; labels=s['labels']
        c.saveState()
        c.setFillColor(LIGHT); c.setStrokeColor(RULE); c.roundRect(0,0,self.width,self.height,10,stroke=1,fill=1)
        c.setFillColor(TEAL); c.setFont('DejaVu-Bold',11); c.drawString(14,self.height-22,s['title'])
        def box(x,y,w,h,text,fill=colors.white):
            c.setFillColor(fill); c.setStrokeColor(TEAL); c.setLineWidth(0.8); c.roundRect(x,y,w,h,7,stroke=1,fill=1)
            c.setFillColor(INK); c.setFont('DejaVu',8.5)
            words=text.split(); lines=[]; cur=''
            for wd in words:
                if len(cur+' '+wd)>22 and cur: lines.append(cur); cur=wd
                else: cur=(cur+' '+wd).strip()
            if cur: lines.append(cur)
            ty=y+h/2+(len(lines)-1)*5
            for ln in lines[:4]: c.drawCentredString(x+w/2,ty,ln); ty-=10
        def arrow(x1,y1,x2,y2):
            c.setStrokeColor(TEAL); c.setLineWidth(1.1); c.line(x1,y1,x2,y2)
            import math
            ang=math.atan2(y2-y1,x2-x1); L=6
            c.line(x2,y2,x2-L*math.cos(ang-0.45),y2-L*math.sin(ang-0.45))
            c.line(x2,y2,x2-L*math.cos(ang+0.45),y2-L*math.sin(ang+0.45))
        if kind=='flow':
            n=len(labels); gap=12; w=(self.width-28-gap*(n-1))/n; y=80; h=52
            for i,lab in enumerate(labels):
                x=14+i*(w+gap); box(x,y,w,h,lab)
                if i<n-1: arrow(x+w,y+h/2,x+w+gap,y+h/2)
        elif kind=='cycle':
            import math
            n=len(labels); cx=self.width/2; cy=86; r=66
            bw=min(88, max(64, int(2*math.pi*r/n*0.72))); bh=30
            pts=[]
            for i,lab in enumerate(labels):
                ang=math.pi/2 - 2*math.pi*i/n
                x=cx+r*math.cos(ang)-bw/2; y=cy+r*math.sin(ang)-bh/2
                pts.append((x+bw/2,y+bh/2)); box(x,y,bw,bh,lab)
            for i in range(n):
                x1,y1=pts[i]; x2,y2=pts[(i+1)%n]
                dx=x2-x1; dy=y2-y1; d=(dx*dx+dy*dy)**0.5 or 1
                arrow(x1+dx/d*(bw/2+2),y1+dy/d*(bh/2+2),x2-dx/d*(bw/2+2),y2-dy/d*(bh/2+2))
        elif kind=='layers':
            n=len(labels); h=36; gap=10; y0=24
            for i,lab in enumerate(labels):
                w=self.width-60-i*30; x=(self.width-w)/2; y=y0+i*(h+gap)
                box(x,y,w,h,lab, fill=colors.white if i%2 else LIGHT)
        elif kind=='hub':
            import math
            cx=self.width/2; cy=86; bw=92; bh=30; cw=116; ch=34
            box(cx-cw/2,cy-ch/2,cw,ch,labels[-1],fill=LIGHT)
            outer=labels[:-1]; n=len(outer)
            rx=(self.width-bw)/2-16; ry=58
            for i,lab in enumerate(outer):
                ang=math.pi/2 + 2*math.pi*i/n
                x=cx+rx*math.cos(ang)-bw/2; y=cy+ry*math.sin(ang)-bh/2
                box(x,y,bw,bh,lab)
                # arrow from the outer box edge toward the center box edge
                ox=x+bw/2; oy=y+bh/2
                dx=cx-ox; dy=cy-oy; d=(dx*dx+dy*dy)**0.5 or 1
                ux,uy=dx/d,dy/d
                t_outer=min((bw/2)/max(abs(ux),1e-6),(bh/2)/max(abs(uy),1e-6))+2
                t_center=min((cw/2)/max(abs(ux),1e-6),(ch/2)/max(abs(uy),1e-6))+4
                arrow(ox+ux*t_outer,oy+uy*t_outer,cx-ux*t_center,cy-uy*t_center)
        elif kind=='stairs':
            n=len(labels); w=(self.width-40)/n; h=30
            for i,lab in enumerate(labels):
                x=20+i*w; y=24+i*24; box(x,y,w-8,h,lab)
                if i<n-1: arrow(x+w-8,y+h/2,x+w,y+h/2+24)
        elif kind=='pyramid':
            n=len(labels); base=self.width-80; top=40; h=28; gap=6
            for i,lab in enumerate(labels):
                w=base-(base-top)*i/(n-1 if n>1 else 1); x=(self.width-w)/2; y=24+i*(h+gap)
                box(x,y,w,h,lab)
        c.restoreState()

class BookDoc(BaseDocTemplate):
    def __init__(self, filename):
        super().__init__(str(filename), pagesize=A4, leftMargin=MARGIN, rightMargin=MARGIN,
                         topMargin=22*mm, bottomMargin=18*mm,
                         title='CAC.902 — Theories of Counseling and Psychotherapy',
                         author='Coursebook project; includes adapted CC BY readings',
                         subject='PhD in Children and Adolescent Counseling course volume')
        frame=Frame(MARGIN,18*mm,PAGE_W-2*MARGIN,PAGE_H-40*mm,id='normal',leftPadding=0,rightPadding=0,topPadding=0,bottomPadding=0)
        self.addPageTemplates(PageTemplate(id='all',frames=[frame],onPage=self.decorate))
        self.chapter_pages={}; self.section_pages={}; self.running='CAC.902 | Theories of Counseling and Psychotherapy'
    def decorate(self, canvas, doc):
        canvas.saveState()
        if doc.page>1:
            canvas.setFont('DejaVu',7.5); canvas.setFillColor(MUTED)
            canvas.drawString(MARGIN,PAGE_H-11.5*mm,'CAC.902  |  THEORIES OF COUNSELING AND PSYCHOTHERAPY')
            canvas.drawRightString(PAGE_W-MARGIN,PAGE_H-11.5*mm,'Coursebook project')
            canvas.setStrokeColor(RULE); canvas.line(MARGIN,PAGE_H-14*mm,PAGE_W-MARGIN,PAGE_H-14*mm)
            canvas.drawCentredString(PAGE_W/2,10*mm,str(doc.page))
        canvas.restoreState()
    def afterFlowable(self, flowable):
        key=getattr(flowable,'_bookmark_key',None); marker=getattr(flowable,'_marker',None)
        if key:
            self.canv.bookmarkPage(key)
            text=flowable.getPlainText()
            level=1 if (key.startswith('ch') and '-' in key) else 0
            self.canv.addOutlineEntry(text,key,level=level,closed=False)
            if key.startswith('ch'): self.chapter_pages[key]=self.page
            self.section_pages[key]=self.page
        if marker: self.section_pages[marker]=self.page

def note_box(title, lines):
    data=[[Paragraph(inline_md('**'+title+'**'), ST['note'])]]
    for ln in lines: data.append([Paragraph(inline_md(ln), ST['note'])])
    t=Table(data,colWidths=[PAGE_W-2*MARGIN])
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),LIGHT),('BOX',(0,0),(-1,-1),0.6,RULE),
                           ('LEFTPADDING',(0,0),(-1,-1),9),('RIGHTPADDING',(0,0),(-1,-1),9),
                           ('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7)]))
    return t

def build():
    chapters=json.loads((BOOK/'chapters.json').read_text())
    diagrams={d['chapter']:d for d in json.loads((BOOK/'diagrams.json').read_text())}
    blocks=json.loads((BOOK/'source-blocks.json').read_text())
    refs=json.loads((BOOK/'source-references.json').read_text())
    supp=json.loads((BOOK/'supplemental-references.json').read_text())
    manifest=json.loads((BOOK/'source-manifest.json').read_text())
    lectures={}
    for part in sorted((BOOK/'lectures').glob('part-*.md')):
        text=part.read_text(); current=None; buf=[]
        for line in text.splitlines():
            m=re.match(r'^## Chapter (\d+):',line)
            if m:
                if current: lectures[current]='\n'.join(buf).strip()
                current=int(m.group(1)); buf=[]
            elif current:
                if line.startswith('# '): continue
                buf.append(line)
        if current: lectures[current]='\n'.join(buf).strip()
    story=[]
    story += [Spacer(1,70),p('PHD IN CHILDREN AND ADOLESCENT COUNSELING','cover_kicker'),
              p('CAC.902','cover_kicker'),p('Theories of Counseling and Psychotherapy','cover_title'),Rule(),Spacer(1,20),
              p('A complete course volume with original counseling lectures, real-life applications, vector diagrams, doctoral seminar tasks, and attributed open educational readings.','body'),
              Spacer(1,18),p('Book 2 of 32 • PDF edition','small'),
              p('Educational coursebook. Not an official university publication and not a substitute for supervised clinical training, diagnosis, or emergency care.','small'),PageBreak()]
    front=[
      ('Purpose and scope','This volume covers CAC.902 Theories of Counseling and Psychotherapy within the supplied PhD curriculum. It compares major theoretical traditions and applies them to children, adolescents, families, schools, and community settings. It is a complete course volume, not a claim to contain the entire discipline.'),
      ('Two clearly identified layers','Each chapter begins with a newly written counseling lecture, a real-life application, and a doctoral seminar task. An original vector diagram makes a central relationship visible. The chapter then provides attributed foundational readings adapted from CC BY open educational texts. The readings supply broader theoretical background; the new lectures provide the counseling interpretation and critical cautions.'),
      ('How to study','Read the lecture first, then the diagram, then the adapted reading. Use the workbook to turn theory into a testable professional task. In supervision, compare at least two formulations for the same case before choosing an intervention.'),
      ('Simple English and real-life application','Technical terms are introduced gradually and defined in the glossary. Fictional cases show how theory changes the questions a counselor asks. The cases are teaching examples, not treatment protocols.'),
      ('Doctoral level and safety','The book assumes graduate study in counseling or a related field. It does not authorize unsupervised practice. Crisis, abuse, suicide risk, psychosis, and severe impairment require qualified assessment and local emergency procedures.'),
      ('Source transparency','The adapted readings are used under Creative Commons Attribution 4.0. They have been selected, reorganized, and typeset for this course, with new lectures and diagrams added. They are not presented as wholly original text. Module-level attribution and pinned source snapshots appear in the attribution register. Inherited references are identified separately from the supplemental sources checked for this edition.'),
      ('Integrative areas','Diversity, ethics, research, and supervision are integrated throughout. Chapter 17 gives focused attention to culture, African perspectives, and feminist critique; Chapter 20 consolidates ethics, supervision, and research.'),
    ]
    story.append(heading('How to Use This Book','chapter_title',key='front-how'))
    for h,b in front: story += [heading(h,'h2'),p(b)]
    story.append(PageBreak())
    story.append(heading('Contents','chapter_title',key='front-toc'))
    for ch in chapters:
        story.append(p(f"Chapter {ch['number']:02d} — {esc(ch['title'])}",'toc'))
    story += [Spacer(1,8),p('Glossary','toc'),p('Applied Workbook','toc'),p('References','toc'),p('Attribution and Production Record','toc'),PageBreak()]
    for ch in chapters:
        n=ch['number']
        story.append(heading(f'CHAPTER {n:02d}  /  CAC.902','chapter_no'))
        story.append(heading(ch['title'],'chapter_title',key=f'ch{n:02d}',marker=f'ch{n:02d}_start'))
        story += markdown(lectures[n])
        d=diagrams[n]
        dflow=Diagram(d); dflow._marker=f'ch{n:02d}_diagram'
        story += [Spacer(1,6),dflow,p(d['caption'],'caption')]
        chblocks=[b for b in blocks if b['chapter']==n]
        if chblocks:
            story.append(heading('Attributed Foundational Reading','h2',key=f'ch{n:02d}-reading'))
            for reading in chblocks:
                src=next(s for s in manifest['sources'] if ('Mark' in s['authors']) == (reading['source_key']=='kelland'))
                if reading['source_key']=='kelland':
                    attr='Adapted from Personality Theory in a Cultural Context by Mark D. Kelland, OpenStax CNX / Lansing Community College (2015), CC BY 4.0. Selection, organization, and PDF layout modified for this course; new lectures and course diagrams are separate additions.'
                else:
                    attr='Adapted from Psychology 2e by Rose M. Spielman, William J. Jenkins, and Marilyn D. Lovett, OpenStax, Rice University (2020), CC BY 4.0. Selection, organization, and PDF layout modified for this course; new lectures and course diagrams are separate additions.'
                story += [note_box('Attribution and critical-reading note',[
                    attr,
                    'Read historical and theoretical claims critically. A theory is a lens for inquiry, not a verdict about a child or family. Where source claims are dated or culture-bound, the new lecture supplies cautions and contemporary framing.',
                    'Source module '+reading['source_id']+' • '+src['title']+' • pinned GitHub snapshot '+src['commit'][:12]+'. Full repository and license details appear in the attribution register.',
                ]),Spacer(1,8)]
                story += markdown(reading['markdown'])
        story.append(PageBreak())
    story.append(heading('Glossary','chapter_title',key='glossary',marker='glossary_start'))
    story += markdown((BOOK/'glossary.md').read_text())
    story.append(PageBreak())
    story.append(heading('Applied Workbook','chapter_title',key='workbook',marker='workbook_start'))
    story += markdown((BOOK/'applied-workbook.md').read_text())
    story.append(PageBreak())
    story.append(heading('References','chapter_title',key='references',marker='references_start'))
    story += [p('Supplemental references checked for this edition','h2')]
    for r in supp: story += [p(r['citation'],'ref'),p(r['note'],'small')]
    story += [p('Inherited reference lists from adapted readings','h2'),
              p('The following references are inherited from the open educational readings. They are reproduced for attribution and scholarly traceability, not as a claim that every item was independently verified for this edition.','small')]
    seen=set(); unique=[]
    for r in refs:
        k=re.sub(r'\W+',' ',r['text'].lower()).strip()
        if k not in seen: seen.add(k); unique.append(r)
    for r in unique: story.append(p(r['text'],'ref'))
    story.append(PageBreak())
    story.append(heading('Attribution and Production Record','chapter_title',key='attribution',marker='attribution_start'))
    for s in manifest['sources']:
        story += [p(s['title']+' attribution','h2'),
                  p(f"{s['title']} by {s['authors']}. {s['publisher']}, {s['year']}. Used under {s['license']}. Source repository: https://github.com/{s['repo']}. Pinned snapshot: {s['commit']}.",'body'),
                  p('License: '+s['license_url']+'. The full license text is included in the source archive accompanying the production files. The original authors and publishers do not endorse this adaptation.','body')]
    story += [p('Module-level attribution','h2')]
    for b in blocks:
        s=next(x for x in manifest['sources'] if ('Mark' in x['authors']) == (b['source_key']=='kelland'))
        story.append(p(f"Chapter {b['chapter']:02d} — {b['title']}. Source module {b['source_id']}; {s['title']} by {s['authors']}; {s['license']}; snapshot {s['commit'][:12]}.",'small'))
    story += [p('Rights and authorship distinction','h2'),p('The newly written counseling lectures, fictional applications, seminar tasks, glossary, and original vector diagrams are course-specific additions. The foundational reading text remains attributed to the original authors. Third-party material is not relicensed by this project. No source photographs are reproduced. No endorsement by the original authors, publishers, or a university degree program is implied.','body'),
              p('Production method','h2'),p('The PDF was generated from structured Markdown and JSON sources with ReportLab. Vector diagrams were drawn programmatically. Text was extracted from the finished PDF with PyMuPDF and checked for page count, word count, navigation, bounds, placeholders, and attribution. The verification report is stored with the production files.','body')]
    doc=BookDoc(OUT); doc.build(story)
    substantive=sum(len(re.findall(r"\b[\w’'-]+\b", lectures[c['number']])) for c in chapters)+sum(b['words'] for b in blocks)+len(re.findall(r"\b[\w’'-]+\b",(BOOK/'glossary.md').read_text()))+len(re.findall(r"\b[\w’'-]+\b",(BOOK/'applied-workbook.md').read_text()))
    report={'course':'CAC.902','title':'Theories of Counseling and Psychotherapy','estimated_substantive_manuscript_words':substantive,
            'chapters':len(chapters),'diagrams':len(diagrams),'source_blocks':len(blocks),'source_words':sum(b['words'] for b in blocks),
            'inherited_references':len(refs),'unique_inherited_references':len(unique),'supplemental_references':len(supp),
            'chapter_pages':doc.chapter_pages,'section_pages':doc.section_pages,'pdf':str(OUT.relative_to(ROOT))}
    (BOOK/'build-record.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))

if __name__=='__main__': build()
