from pathlib import Path
import pymupdf, json, re
from PIL import Image,ImageOps,ImageDraw
ROOT=Path(__file__).resolve().parent.parent
QA=ROOT/'tmp/document_qa';pdf=pymupdf.open(ROOT/'output/documents/trees_study_guide.pdf')
(QA/'pages').mkdir(exist_ok=True)
issues=[];stats=[]
for i,page in enumerate(pdf):
 pix=page.get_pixmap(matrix=pymupdf.Matrix(1.5,1.5),alpha=False);pix.save(str(QA/'pages'/f'{i+1:03}.png'))
 data=page.get_text('dict');texts=[]
 for block in data['blocks']:
  for line in block.get('lines',[]):
   for span in line['spans']:
    texts.append(span['text'])
    x0,y0,x1,y1=span['bbox']
    if x0<25 or x1>page.rect.width-25 or y0<15 or y1>page.rect.height-12:issues.append((i+1,'outside',span['text'],span['bbox']))
 text=page.get_text();stats.append({'page':i+1,'characters':len(text),'drawings':len(page.get_drawings()),'images':len(page.get_images())})
 if '\ufffd' in text:issues.append((i+1,'replacement character'))
 if i>0 and len(text)<80:issues.append((i+1,'almost empty',text))
# Inspect all pages on numbered contact sheets, then inspect selected pages at full rendering size.
for start in range(0,len(pdf),9):
 thumb_w=360;thumb_h=510;sheet=Image.new('RGB',(thumb_w*3, (thumb_h+30)*3),'#d6dbe2');draw=ImageDraw.Draw(sheet)
 for offset in range(min(9,len(pdf)-start)):
  im=Image.open(QA/'pages'/f'{start+offset+1:03}.png');im.thumbnail((thumb_w-12,thumb_h-12))
  x=(offset%3)*thumb_w+(thumb_w-im.width)//2;y=(offset//3)*(thumb_h+30)+23
  sheet.paste(im,(x,y));draw.text((x, y-19),f'Page {start+offset+1}',fill='black')
 sheet.save(QA/f'contact-{start//9+1:02}.png')
(QA/'pdf_audit.json').write_text(json.dumps({'pages':len(pdf),'issues':issues,'stats':stats},ensure_ascii=False,indent=2))
text='\n'.join(p.get_text() for p in pdf)
figs=re.findall(r'Рисунок (\d+)\.',text)
assert sorted(map(int,figs))==list(range(1,91)),(len(figs),figs)
assert all(s['images']==0 for s in stats),'Raster images in PDF'
print(json.dumps({'pages':len(pdf),'figures':len(figs),'raster_images':sum(s['images'] for s in stats),'issues':issues},ensure_ascii=False))
