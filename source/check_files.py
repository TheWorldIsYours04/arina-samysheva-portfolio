#!/usr/bin/env python3
"""Offline structural validation; standard library only. Never contacts Formspree."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit, unquote
import json, hashlib
ROOT=Path(__file__).resolve().parents[1];SITE=ROOT/'site'
class Links(HTMLParser):
 def __init__(self):super().__init__();self.links=[];self.h1=0;self.main=0
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if tag=='h1':self.h1+=1
  if tag=='main':self.main+=1
  key={'a':'href','img':'src','script':'src','link':'href'}.get(tag)
  if key and a.get(key):self.links.append(a[key])
  if tag=='img' and 'srcset' in a:self.links.extend(x.strip().split()[0] for x in a['srcset'].split(','))
count=0
for path in sorted(SITE.rglob('*.html')):
 parser=Links();parser.feed(path.read_text(encoding='utf-8'))
 assert parser.h1==1 and parser.main==1,(path,'Expected one main and one h1')
 for value in parser.links:
  parts=urlsplit(value)
  if parts.scheme or not parts.path:continue
  target=(SITE/unquote(parts.path).lstrip('/')) if parts.path.startswith('/') else (path.parent/unquote(parts.path))
  assert target.exists(),(path,value,'missing')
  count+=1
projects=json.loads((ROOT/'source/projects.json').read_text())
assert len(projects)==9
# One editorial paragraph per project: no inconsistent credits, years or software footers.
introductions=json.loads((ROOT/'source/introductions.json').read_text(encoding='utf-8'))
assert set(introductions)=={p['slug'] for p in projects},'Missing project introductions'
for slug, intro in introductions.items():
 paragraphs=intro.get('paragraphs',[])
 assert len(paragraphs)==1 and paragraphs[0].strip(),(slug,'One editorial paragraph required')
 body=paragraphs[0]
 assert '\n' not in body and '\r' not in body,(slug,'No forced line breaks in intro')
 for forbidden in ('Арина Самышева','2026','Adobe','Illustrator','Photoshop','Figma','Инструмент'):
  assert forbidden.casefold() not in body.casefold(),(slug,'Credit/year/tool in introduction:',forbidden)
for p in projects:
 assert len(p['slides'])>0
 for s in p['slides']:
  assert s['width']>0 and s['height']>0 and (SITE/s['src']).is_file()
assert not any(p.suffix.lower() in {'.ttf','.otf','.woff','.woff2'} for p in SITE.rglob('*'))
print('OK:',len(list(SITE.rglob('*.html'))),'HTML;',len(projects),'projects;',sum(len(p['slides']) for p in projects),'slides;',count,'references')
