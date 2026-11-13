from html.parser import HTMLParser
from html import escape, unescape
from pathlib import Path
import re
class Node:
 def __init__(self, tag='', attrs=()):self.tag=tag; self.attrs=dict(attrs); self.children=[]
class Tree(HTMLParser):
 def __init__(self):super().__init__(convert_charrefs=True); self.root=Node();self.stack=[self.root]
 def handle_starttag(self,tag,attrs):
  n=Node(tag,attrs);self.stack[-1].children.append(n)
  if tag not in ('br','hr','img','meta','link','input'):self.stack.append(n)
 def handle_endtag(self,tag):
  for i in range(len(self.stack)-1,0,-1):
   if self.stack[i].tag==tag:self.stack=self.stack[:i];break
 def handle_data(self,data):self.stack[-1].children.append(data)
def plain(n):
 if isinstance(n,str):return n
 return ''.join(plain(c) for c in n.children)
def children(n):return ''.join(render(c) for c in n.children)
def compact(s):return re.sub(r'\s+',' ',s).strip()
def render(n):
 if isinstance(n,str):return n
 t=n.tag
 if t=='div' and n.attrs.get('id')=='kmp-lab':return '\n\nПошаговый тренажёр доступен в HTML-версии учебника. Таблицы его примеров приведены в этой главе.\n\n'
 if t in ('h1','h2','h3','h4'):
  anchor = '<a id="'+escape(n.attrs['id'], quote=True)+'"></a>\n\n' if n.attrs.get('id') else ''
  return '\n\n'+anchor+'#'*int(t[1])+' '+compact(children(n))+'\n\n'
 if t in ('b','strong'):return '**'+children(n)+'**'
 if t in ('em','i'):return '*'+children(n)+'*'
 if t=='a':return '['+children(n)+']('+n.attrs.get('href','')+')' if n.children else ''
 if t=='figure':
  caption=next(c for c in n.children if isinstance(c,Node) and c.tag=='figcaption')
  text=plain(caption);number=int(text.split('.')[0]);alt=text.replace('[',r'\[').replace(']',r'\]')
  return f'\n\n<a id="figure-{number}"></a>\n\n![{alt}](svg/{number:02}.svg)\n\n*Рисунок {text}*\n\n'
 if t=='table':
  rows=[]
  def scan(x):
   if not isinstance(x,Node):return
   if x.tag=='tr':rows.append([compact(children(c)).replace('|',r'\|') for c in x.children if isinstance(c,Node) and c.tag in ('th','td')])
   else:
    for c in x.children:scan(c)
  scan(n)
  if not rows:return ''
  return '\n\n'+'\n'.join('| '+' | '.join(row)+' |' for row in [rows[0],['---']*len(rows[0]),*rows[1:]])+'\n\n'
 if t in ('ol','ul'):
  result=[];i=0
  for c in n.children:
   if isinstance(c,Node) and c.tag=='li':
    i+=1;result.append((f'{i}. ' if t=='ol' else '- ')+children(c).strip().replace('\n','\n   '))
  return '\n\n'+'\n\n'.join(result)+'\n\n'
 if t=='aside':return '\n\n'+'\n'.join('> '+x for x in children(n).strip().splitlines())+'\n\n'
 if t=='summary':return '\n\n#### '+compact(children(n))+'\n\n'
 if t=='section':return '\n\n<a id="'+n.attrs.get('id','')+'"></a>\n\n'+children(n)
 if t in ('p','details'):return '\n\n'+children(n).strip()+'\n\n'
 if t=='br':return '\n'
 return children(n)
def export_markdown(content, toc, dest):
 content=content.replace('SVG-схемы встроены в этот файл и не требуют сети.', 'SVG-схемы находятся в соседней папке svg и не требуют сети. При переносе Markdown-файла сохраняй эту папку рядом с ним.')
 content=re.sub(r'<svg\b.*?</svg>','',content,flags=re.S)
 tree=Tree();tree.feed(content)
 body=render(tree.root)
 nav='\n'.join(f'- [{i}. {title}](#{key})' for i,(key,title) in enumerate(toc,1))
 text='# Деревья и структуры данных\n\nУстройство, инварианты и операции в векторных схемах.\n\n## Оглавление\n\n'+nav+'\n\n'+body
 text=re.sub(r'\n{3,}','\n\n',text).strip()+'\n'
 dest.write_text(text)
