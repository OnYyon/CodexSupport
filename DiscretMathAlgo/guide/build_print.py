from pathlib import Path
import re, json, math
from html import escape, unescape
from xml.etree import ElementTree as ET
import sys
sys.path.insert(0,str(Path(__file__).parent))
from export_markdown import Tree, Node, plain
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.platypus import BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, PageBreak, KeepTogether, LongTable, TableStyle, Flowable, NextPageTemplate
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.graphics.shapes import Drawing, Rect, Line, String, Polygon
from reportlab.graphics import renderPDF
import pymupdf
from PIL import Image
from docx import Document
from docx.shared import Pt, Cm, Inches, RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT

ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'output/documents'; QA=ROOT/'tmp/document_qa'; OUT.mkdir(parents=True,exist_ok=True);QA.mkdir(parents=True,exist_ok=True)
FONT=Path('/System/Library/Fonts/Supplemental')
for name,file in [('Body','Arial.ttf'),('Body-Bold','Arial Bold.ttf'),('Body-Italic','Arial Italic.ttf'),('Body-BoldItalic','Arial Bold Italic.ttf'),('Math','Arial Unicode.ttf')]:
 pdfmetrics.registerFont(TTFont(name,str(FONT/file)))
pdfmetrics.registerFontFamily('Body',normal='Body',bold='Body-Bold',italic='Body-Italic',boldItalic='Body-BoldItalic')
COL=colors.HexColor('#111827');GRAY=colors.HexColor('#536170'); BORDER=colors.HexColor('#d9d9d9')
PAGE_W,PAGE_H=A4; LEFT=54; RIGHT=54; TOP=52;BOTTOM=48; WIDTH=PAGE_W-LEFT-RIGHT
styles={
 'body':ParagraphStyle('body',fontName='Body',fontSize=11,leading=16,spaceAfter=8,textColor=COL,allowWidows=0,allowOrphans=0),
 'h1':ParagraphStyle('h1',fontName='Body-Bold',fontSize=24,leading=29,spaceAfter=18,keepWithNext=True,textColor=colors.black),
 'h2':ParagraphStyle('h2',fontName='Body-Bold',fontSize=15,leading=20,spaceBefore=18,spaceAfter=9,keepWithNext=True,textColor=colors.black),
 'h3':ParagraphStyle('h3',fontName='Body-Bold',fontSize=11.5,leading=16,spaceBefore=10,spaceAfter=6,keepWithNext=True,textColor=colors.black),
 'caption':ParagraphStyle('caption',fontName='Body-Italic',fontSize=9,leading=12,spaceBefore=6,spaceAfter=12,textColor=GRAY),
 'small':ParagraphStyle('small',fontName='Body',fontSize=9,leading=12,spaceAfter=5,textColor=COL),
 'cell':ParagraphStyle('cell',fontName='Body',fontSize=9,leading=12,textColor=COL),
 'formula':ParagraphStyle('formula',fontName='Body-Italic',fontSize=12,leading=19,alignment=TA_CENTER,spaceBefore=10,spaceAfter=12,textColor=colors.black),
}
# The source already contains the complete editorial content and all original illustrations.
source=(ROOT/'guide/structures.html').read_text()
main=re.search(r'<main>(.*)</main>',source,re.S)[1]
main=re.sub(r'^<header>.*?</header>','',main,flags=re.S)
main=main.replace('SVG-схемы встроены в этот файл и не требуют сети. ','')
main=main.replace('Этот вариант использует parent и общий чёрный NIL.','При разборе связей используются родитель узла и общий чёрный NIL.')
tree=Tree(); tree.feed(main)
figures={}
for f in (ROOT/'guide/svg').glob('*.svg'):figures[int(f.stem)]=f

def natural(t):
 t=t.replace('Вместо программного кода здесь используются последовательности состояний, словесные шаги и математические обозначения.','Операции разобраны через последовательности состояний, словесные шаги и математические обозначения.')
 return t

def rich(n):
 if isinstance(n,str):
  s=escape(natural(n));font=pdfmetrics.getFont('Body').face.charToGlyph
  return ''.join(c if ord(c) in font or c in '<>&;' else f'<font name="Math">{c}</font>' for c in s)
 if n.tag in ('b','strong'):return '<b>'+''.join(rich(c) for c in n.children)+'</b>'
 if n.tag in ('i','em'):return '<i>'+''.join(rich(c) for c in n.children)+'</i>'
 if n.tag=='a':
  href=n.attrs.get('href','');text=''.join(rich(c) for c in n.children)
  # Internal references retain their natural label; external sources remain clickable.
  if href.startswith('http'):return f'<link href="{escape(href,quote=True)}" color="#274c77">{text}</link>'
  return text
 return ''.join(rich(c) for c in n.children)

def cleanheading(s):
 s=re.sub(r'(?<=\d)\.(?=\s)','',s)
 s=s.replace('–',' ').replace('—',' ').replace('-',' ')
 s=re.sub(r'[^\w\sА-Яа-яЁё]',' ',s)
 return re.sub(r'\s+',' ',s).strip()

def svg_color(value):
 if value.startswith('#') and len(value)==4:value='#'+''.join(c*2 for c in value[1:])
 return colors.toColor(value)

def vector(svg):
 root=ET.parse(svg).getroot();vb=list(map(float,root.attrib['viewBox'].split()));H=vb[3];d=Drawing(vb[2],H)
 for el in root:
  tag=el.tag.split('}')[-1];a=el.attrib
  if tag=='rect':
   d.add(Rect(float(a['x']),H-float(a['y'])-float(a['height']),float(a['width']),float(a['height']),rx=float(a.get('rx',0)),ry=float(a.get('rx',0)),fillColor=svg_color(a.get('fill','#fff')),strokeColor=svg_color(a.get('stroke','#64748b')),strokeWidth=float(a.get('stroke-width',1))))
  elif tag=='path':
   pts=list(map(float,re.findall(r'-?\d+(?:\.\d+)?',a['d'])))
   if len(pts)==4:
    x,y,xx,yy=pts;y=H-y;yy=H-yy
    color=svg_color(a.get('stroke','#64748b'));d.add(Line(x,y,xx,yy,strokeColor=color,strokeWidth=float(a.get('stroke-width',2))))
    if a.get('marker-end'):
     vx=xx-x;vy=yy-y;L=math.hypot(vx,vy);ux=vx/L;uy=vy/L
     d.add(Polygon([xx,yy,xx-8*ux+3.2*uy,yy-8*uy-3.2*ux,xx-8*ux-3.2*uy,yy-8*uy+3.2*ux],fillColor=color,strokeColor=None))
  elif tag=='text':
   text=''.join(el.itertext());face='Body' if all(ord(c) in pdfmetrics.getFont('Body').face.charToGlyph for c in text) else 'Math'
   d.add(String(float(a['x']),H-float(a['y']),text,fontName=face,fontSize=float(a.get('font-size',16)),textAnchor=a.get('text-anchor','start'),fillColor=svg_color(a.get('fill','#475569'))))
 return d

class VectorFigure(Flowable):
 def __init__(self, drawing,width=WIDTH):
  Flowable.__init__(self);self.drawing=drawing;self.scale=width/drawing.width;self.width=width;self.height=drawing.height*self.scale
 def draw(self):
  self.canv.saveState();self.canv.scale(self.scale,self.scale);renderPDF.draw(self.drawing,self.canv,0,0);self.canv.restoreState()

class FigureBlock(Flowable):
 def __init__(self, drawing, caption):
  super().__init__();self.drawing=drawing;self.caption=caption;self.width=WIDTH;self.scale=WIDTH/drawing.width
  self.caption_height=caption.wrap(WIDTH,1000)[1]
  self.height=drawing.height*self.scale+self.caption_height+18
 def wrap(self,availWidth,availHeight):return self.width,self.height
 def draw(self):
  self.caption.drawOn(self.canv,0,0)
  self.canv.saveState();self.canv.translate(0,self.caption_height+12);self.canv.scale(self.scale,self.scale)
  renderPDF.draw(self.drawing,self.canv,0,0);self.canv.restoreState()

class Book(BaseDocTemplate):
 def __init__(self,path):
  super().__init__(str(path),pagesize=A4,leftMargin=LEFT,rightMargin=RIGHT,topMargin=TOP,bottomMargin=BOTTOM,title='Деревья и структуры данных',author='')
  self.chapter='';self.toc_items=[]
  self.addPageTemplates([PageTemplate(id='cover',frames=[Frame(LEFT,BOTTOM,WIDTH,PAGE_H-TOP-BOTTOM,id='cover',leftPadding=0,rightPadding=0,topPadding=0,bottomPadding=0)],onPage=self.coverpage),PageTemplate(id='body',frames=[Frame(LEFT,BOTTOM,WIDTH,PAGE_H-TOP-BOTTOM,id='body',leftPadding=0,rightPadding=0,topPadding=0,bottomPadding=0)],onPage=self.page)])
 def coverpage(self,c,d):pass
 def page(self,c,d):
  c.saveState();c.setFont('Body',8);c.setFillColor(GRAY)
  c.drawString(LEFT,PAGE_H-30,'Деревья и структуры данных')
  c.drawRightString(PAGE_W-RIGHT,27,str(d.page));c.restoreState()
 def afterFlowable(self,f):
  if isinstance(f,Paragraph) and getattr(f,'chapter_key',None):
   key=f.chapter_key; title=f.getPlainText();self.canv.bookmarkPage(key);self.canv.addOutlineEntry(title,key,0)
   self.notify('TOCEntry',(0,title,self.page,key));self.toc_items.append((title,self.page))

story=[]
coverstyle=ParagraphStyle('cover',fontName='Body-Bold',fontSize=32,leading=39,textColor=colors.black,spaceAfter=24)
substyle=ParagraphStyle('sub',fontName='Body',fontSize=16,leading=24,textColor=GRAY,spaceAfter=30)
story += [Spacer(1,72),Paragraph('Деревья и<br/>структуры данных',coverstyle),Paragraph('Устройство и операции<br/>в векторных схемах',substyle),Paragraph('Учебное пособие для подготовки к самостоятельной реализации',styles['body']),Spacer(1,28),Paragraph('AVL · красно-чёрные деревья · B-деревья<br/>Treap · дерево отрезков · Фенвик<br/>Trie · compact trie · PATRICIA',styles['body']),Spacer(1,36),Paragraph('13 разделов · 90 схем · без программного кода',styles['small']),NextPageTemplate('body'),PageBreak()]
story.append(Paragraph('Содержание',styles['h1']))
toc=TableOfContents();toc.levelStyles=[ParagraphStyle('toc',fontName='Body',fontSize=11,leading=17,leftIndent=0,firstLineIndent=0,spaceBefore=7,textColor=COL)];story.extend([toc,PageBreak()])

# Editable companion document with matching styles and SVG images plus PNG fallbacks.
doc=Document();sec=doc.sections[0];sec.page_width=Cm(21);sec.page_height=Cm(29.7);sec.top_margin=Cm(1.8);sec.bottom_margin=Cm(1.8);sec.left_margin=Cm(1.9);sec.right_margin=Cm(1.9)
for name in ['Normal','Body Text','List Bullet','List Number','Caption','Title','Subtitle','Heading 1','Heading 2','Heading 3']:
 st=doc.styles[name];st.font.name='Arial';st.font.color.rgb=RGBColor(0,0,0);st.font.size=Pt(11)
 st.paragraph_format.line_spacing=1.35;st.paragraph_format.space_after=Pt(7)
doc.styles['Title'].font.size=Pt(30);doc.styles['Title'].font.bold=True
doc.styles['Subtitle'].font.size=Pt(16)
for name,size in [('Heading 1',23),('Heading 2',15),('Heading 3',12)]:
 doc.styles[name].font.size=Pt(size);doc.styles[name].font.bold=True;doc.styles[name].paragraph_format.keep_with_next=True
 doc.styles[name].paragraph_format.space_before=Pt(18);doc.styles[name].paragraph_format.space_after=Pt(9)
doc.styles['Caption'].font.size=Pt(9);doc.styles['Caption'].font.italic=True
footer=sec.footer.paragraphs[0];footer.alignment=WD_ALIGN_PARAGRAPH.RIGHT
r=footer.add_run();fld=OxmlElement('w:fldSimple');fld.set(qn('w:instr'),'PAGE');r._r.addnext(fld)
doc.add_paragraph('Деревья и структуры данных','Title');doc.add_paragraph('Устройство и операции в векторных схемах','Subtitle');doc.add_paragraph('Учебное пособие для подготовки к самостоятельной реализации');doc.add_paragraph('13 разделов · 90 схем · без программного кода');doc.add_page_break()
doc.add_paragraph('Содержание','Heading 1')
for section in tree.root.children:
 if isinstance(section,Node) and section.tag=='section':
  title=next(c for c in section.children if isinstance(c,Node) and c.tag=='h2');doc.add_paragraph(plain(title))
doc.add_page_break()

math_displays={
 'Высота и знак баланса':['h(∅) = 0','h(v) = 1 + max(h(L), h(R))','b(v) = h(L) − h(R)'],
 'Агрегаты и два направления работы':['size(v) = 1 + size(L) + size(R)','sum(v) = sum(L) + value(v) + sum(R)'],
 'Откуда берётся логарифмическая высота':['N(0) = 0,   N(1) = 1','N(h) = 1 + N(h − 1) + N(h − 2)'],
 'Прибавление диапазону через разности':['D[i] = A[i] − A[i − 1]','prefixSum(i) = i × prefix(B₁, i) − prefix(B₂, i)'],
}

figure_seen=[]
def add_runs(p,n,bold=False,italic=False):
 if isinstance(n,str):
  r=p.add_run(natural(n));r.bold=bold;r.italic=italic;return
 for c in n.children:add_runs(p,c,bold or n.tag in ('b','strong'),italic or n.tag in ('i','em'))

def png_fallback(number,drawing):
 path=QA/f'figure-{number:02}.png'
 if True:
  pdf=renderPDF.drawToString(drawing);pd=pymupdf.open(stream=pdf,filetype='pdf');pd[0].get_pixmap(matrix=pymupdf.Matrix(1.5,1.5),alpha=False).save(str(path));pd.close()
 return path

def doc_picture(num,drawing):
 p=doc.add_paragraph();p.paragraph_format.keep_with_next=True;p.paragraph_format.space_after=Pt(0)
 run=p.add_run();shape=run.add_picture(str(png_fallback(num,drawing)),width=Cm(17.2))
 part=doc.part;from docx.opc.part import Part
 from docx.opc.packuri import PackURI
 from docx.opc.constants import RELATIONSHIP_TYPE as RT
 svgpart=Part(PackURI(f'/word/media/figure-{num:02}.svg'),'image/svg+xml',figures[num].read_bytes(),part.package)
 rel=part.relate_to(svgpart,RT.IMAGE)
 blip=shape._inline.xpath('.//a:blip')[0]
 extlist=OxmlElement('a:extLst');ext=OxmlElement('a:ext');ext.set('uri','{96DAC541-7B7A-43D3-8B79-37D633B846F1}')
 from lxml import etree
 svgblip=etree.Element('{http://schemas.microsoft.com/office/drawing/2016/SVG/main}svgBlip',nsmap={'asvg':'http://schemas.microsoft.com/office/drawing/2016/SVG/main'});svgblip.set(qn('r:embed'),rel);ext.append(svgblip);extlist.append(ext);blip.append(extlist)

def add_table(n):
 rows=[]
 def scan(x):
  if not isinstance(x,Node):return
  if x.tag=='tr':rows.append([c for c in x.children if isinstance(c,Node) and c.tag in ('th','td')])
  else:
   for c in x.children:scan(c)
 scan(n)
 if not rows:return
 ncols=len(rows[0]);weights=[1]*ncols
 if ncols==2:weights=[0.38,0.62]
 if ncols==3:weights=[0.27,0.36,0.37]
 if ncols==4:weights=[0.22,0.25,0.18,0.35]
 if ncols==5:weights=[0.07,0.13,0.13,0.22,0.45]
 widths=[WIDTH*x/sum(weights) for x in weights]
 data=[[Paragraph(('<b>'+rich(c)+'</b>') if i==0 else rich(c),styles['cell']) for c in row] for i,row in enumerate(rows)]
 t=LongTable(data,colWidths=widths,repeatRows=1,hAlign='LEFT',spaceBefore=8,spaceAfter=14)
 t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#eaf0f5')),('GRID',(0,0),(-1,-1),0.4,BORDER),('VALIGN',(0,0),(-1,-1),'MIDDLE'),('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7)]));story.append(t)
 dt=doc.add_table(rows=0,cols=ncols);dt.alignment=WD_TABLE_ALIGNMENT.CENTER;dt.autofit=False
 for i,row in enumerate(rows):
  cells=dt.add_row().cells
  for j,c in enumerate(row):
   cells[j].width=Inches(widths[j]/72);cells[j].vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
   cp=cells[j].paragraphs[0];add_runs(cp,c,bold=i==0)
   for r in cp.runs:r.font.size=Pt(9)
   cp.paragraph_format.space_after=Pt(4);cp.paragraph_format.line_spacing=1.15
   tcpr=cells[j]._tc.get_or_add_tcPr();bd=OxmlElement('w:tcBorders')
   for side in ['top','left','bottom','right']:
    el=OxmlElement('w:'+side);el.set(qn('w:val'),'single');el.set(qn('w:sz'),'4');el.set(qn('w:color'),'D9D9D9');bd.append(el)
   tcpr.append(bd)
   if i==0:
    sh=OxmlElement('w:shd');sh.set(qn('w:fill'),'EAF0F5');tcpr.append(sh)
  if i==0:
   hdr=OxmlElement('w:tblHeader');dt.rows[0]._tr.get_or_add_trPr().append(hdr)
 doc.add_paragraph()

section_count=0

def emit(n):
 global section_count
 if isinstance(n,str):return
 t=n.tag
 if t=='section':
  if section_count:story.append(PageBreak());doc.add_page_break()
  section_count+=1
  for child in n.children:emit(child)
 elif t=='h2':
  title=cleanheading(plain(n));pp=Paragraph(escape(title),styles['h1']);pp.chapter_key=f'chapter-{section_count}';story.append(pp);doc.add_paragraph(title,'Heading 1')
 elif t in ('h3','summary'):
  title=plain(n);sty='h2' if t=='h3' else 'h3';story.append(Paragraph(escape(cleanheading(title)),styles[sty]));doc.add_paragraph(cleanheading(title),'Heading 2' if t=='h3' else 'Heading 3')
  if title in math_displays:
   for formula in math_displays[title]:
    story.append(Paragraph(rich(formula),styles['formula']))
    dp=doc.add_paragraph();dp.alignment=WD_ALIGN_PARAGRAPH.CENTER
    om=OxmlElement('m:oMath');mr=OxmlElement('m:r');mt=OxmlElement('m:t');mt.text=formula;mr.append(mt);om.append(mr);dp._p.append(om)
 elif t=='p' or t=='aside':
  if not plain(n).strip():return
  story.append(Paragraph(rich(n),styles['body']));dp=doc.add_paragraph();add_runs(dp,n)
 elif t in ('ol','ul'):
  for i,child in enumerate([c for c in n.children if isinstance(c,Node) and c.tag=='li'],1):
   prefix=f'{i}.' if t=='ol' else '•'
   st=ParagraphStyle('item',parent=styles['body'],leftIndent=18,firstLineIndent=0,bulletIndent=0,spaceAfter=6)
   story.append(Paragraph(rich(child),st,bulletText=prefix))
   dp=doc.add_paragraph(style='List Number' if t=='ol' else 'List Bullet');add_runs(dp,child)
 elif t=='table':add_table(n)
 elif t=='figure':
  cap=next(c for c in n.children if isinstance(c,Node) and c.tag=='figcaption');text=plain(cap);num=int(text.split('.')[0]);drawing=vector(figures[num]);figure_seen.append(num)
  caption=Paragraph('Рисунок '+rich(cap),styles['caption'])
  story.append(FigureBlock(drawing,caption));doc_picture(num,drawing);doc.add_paragraph('Рисунок '+text,'Caption')
 elif t in ('div','details'):
  for c in n.children:emit(c)
for node in tree.root.children:emit(node)
assert figure_seen==list(range(1,91)),figure_seen
pdf=OUT/'trees_study_guide.pdf';book=Book(pdf);book.multiBuild(story)
doc.save(OUT/'trees_study_guide.docx')
(QA/'build_metadata.json').write_text(json.dumps({'figures':len(figure_seen),'chapters':section_count,'pdf_pages':book.page,'toc':book.toc_items},ensure_ascii=False,indent=2))
print(json.dumps({'pdf':str(pdf),'docx':str(OUT/'trees_study_guide.docx'),'pages':book.page,'figures':len(figure_seen)},ensure_ascii=False))
