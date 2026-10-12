#!/usr/bin/env python3
"""Rebuild the static HTML. Python 3.9+; standard library only.
Run from any directory: python3 source/build.py
Images and shared CSS/JS are already prepared; no npm or external font service.
"""
from pathlib import Path
import json, html, re, argparse, hashlib
from urllib.parse import urlparse
ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / 'site'
PROJECTS = json.loads((ROOT/'source/projects.json').read_text(encoding='utf-8'))
INTRODUCTIONS = json.loads((ROOT/'source/introductions.json').read_text(encoding='utf-8'))
SETTINGS_PATH = ROOT/'source/settings.json'
SETTINGS = json.loads(SETTINGS_PATH.read_text(encoding='utf-8')) if SETTINGS_PATH.exists() else {'formspreeId':'','siteUrl':''}
EMAIL=SETTINGS.get('email','arina.samysheva@mail.ru')
TELEGRAM=SETTINGS.get('telegram','https://t.me/melonpin')
BEHANCE=SETTINGS.get('behance','https://www.behance.net/6b2cfc8a')
E=lambda s:html.escape(str(s),quote=True)
# All icon outlines are inline; no icon-font dependency.
ICONS={
'behance':'<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M2 5.3h6.7c3.1 0 4.8 1.6 4.8 3.7 0 1.6-.8 2.6-2 3.2 1.7.5 2.6 1.7 2.6 3.6 0 2.9-2.3 4.2-5.3 4.2H2V5.3zm3.1 2.5v3.3h3.2c1.3 0 2-.6 2-1.7s-.8-1.6-2.1-1.6H5.1zm0 5.7v3.9h3.4c1.6 0 2.4-.6 2.4-1.9 0-1.4-.9-2-2.4-2H5.1zM16 5.8h6v2h-6v-2zm7.9 9.5h-6.7c.1 1.6.9 2.5 2.2 2.5 1 0 1.6-.4 1.9-1.1h2.5c-.6 2.2-2.2 3.5-4.6 3.5-3.2 0-5-2.2-5-5.5 0-3.2 1.9-5.5 5-5.5 3.3 0 4.9 2.5 4.7 6.1zm-2.8-1.9c-.1-1.3-.7-2-1.9-2s-1.9.8-2 2h3.9z"/></svg>',
'email':'<svg class="email-icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M3 5h18a1 1 0 0 1 1 1v.4l-10 7.1L2 6.4V6a1 1 0 0 1 1-1zm-1 3.9 9.4 6.6a1 1 0 0 0 1.2 0L22 8.9V18a1 1 0 0 1-1 1H3a1 1 0 0 1-1-1V8.9z"/></svg>',
 'telegram':'<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M21.9 3.5c.3-1.4-.6-1.9-1.6-1.5L2.2 9c-1.3.5-1.3 1.2-.2 1.6l4.7 1.5 11-6.9c.5-.3.9-.1.5.2L9.3 13.5c-.3.3-.4.6 0 1l7 5.2c.8.6 1.4.3 1.6-.7l4-15.5z"/></svg>'
}
ARROW='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="M12 21V3m-8 8 8-8 8 8"/></svg>'

def social(names):
 links={'behance':(BEHANCE,'Behance — профиль Арины Самышевой'),'email':('mailto:'+EMAIL,'Написать Арине по электронной почте'),'telegram':(TELEGRAM,'Написать Арине в Telegram')}
 items=[]
 for name in names:
  href,label=links[name];target='' if name=='email' else ' target="_blank" rel="noopener noreferrer"'
  dynamic_email_attr=' data-contact-email' if name=='email' else ''
  items.append(f'<a class="social-link" href="{E(href)}" aria-label="{E(label)}" title="{E(label)}"{target}{dynamic_email_attr}>{ICONS[name]}</a>')
 return '<div class="social-links">'+''.join(items)+'</div>'

def header(prefix='',active=''):
 links=[('home','index.html','Главная'),('works','works.html','Мои работы'),('contact','contact.html','Контакты')]
 anchors=''.join(f'<a href="{prefix}{href}"'+(' aria-current="page"' if key==active else '')+f'>{label}</a>' for key,href,label in links)
 return f'''<header class="site-header"><div class="header-inner">
 <button class="menu-toggle" type="button" aria-controls="main-navigation" aria-expanded="false" aria-label="Открыть меню"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><path d="M3 6h18M3 12h18M3 18h18"/></svg></button>
 <nav class="site-nav" id="main-navigation" aria-label="Основная навигация">{anchors}</nav>
 <a class="brand" href="{prefix}index.html">Арина Самышева</a>
 </div></header>'''

def asset_url(path):
 # Content hashes prevent in-app browsers from keeping stale navigation CSS/JS.
 digest = hashlib.sha256((SITE/path).read_bytes()).hexdigest()[:12]
 return path + '?v=' + digest

def project_intro(project):
 intro = INTRODUCTIONS[project['slug']]
 paragraphs = ''.join('<p>'+E(text).replace('\n','<br>')+'</p>' for text in intro['paragraphs'])
 return ('<section class="project-intro" aria-labelledby="project-title" style="--intro-color:'
         +E(intro['textColor'])+'"><h1 id="project-title">'+E(project['title'])
         +'</h1><div class="project-description">'+paragraphs+'</div></section>')

def page(title, description, body, prefix='',kind='',style='',og='',path='index.html',extra_head=''):
 base=SETTINGS.get('siteUrl','').rstrip('/')
 og=og or prefix+'assets/images/share.jpg'
 absog=(base+'/'+og.replace('../','')) if base else og
 canonical=base+('/' if path=='index.html' else '/'+path) if base else ''
 urlmeta=f'<link rel="canonical" href="{E(canonical)}"><meta property="og:url" content="{E(canonical)}">' if canonical else ''
 ld={'@context':'https://schema.org','@type':'Person','name':'Арина Самышева','jobTitle':'Графический дизайнер','sameAs':[BEHANCE,TELEGRAM]}
 if base:ld['url']=base+'/'
 structured='<script type="application/ld+json">'+json.dumps(ld,ensure_ascii=False)+'</script>' if kind=='home' else ''
 return f'''<!doctype html>
<html lang="ru" class="no-js"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{E(title)}</title><meta name="description" content="{E(description)}"><meta name="theme-color" content="#EEE7DD">
<meta name="referrer" content="strict-origin-when-cross-origin"><meta name="color-scheme" content="light">
<meta property="og:type" content="website"><meta property="og:locale" content="ru_RU"><meta property="og:title" content="{E(title)}"><meta property="og:description" content="{E(description)}"><meta property="og:image" content="{E(absog)}"><meta name="twitter:card" content="summary_large_image">
{urlmeta}<link rel="icon" type="image/svg+xml" href="{prefix}assets/images/favicon.svg">
<link rel="stylesheet" href="{prefix}{asset_url('assets/css/site.css')}"><link rel="stylesheet" href="{prefix}{asset_url('assets/css/project-layout.css')}"><script src="{prefix}{asset_url('assets/js/config.js')}" defer></script><script src="{prefix}{asset_url('assets/js/site.js')}" defer></script>{structured}{extra_head}
</head><body id="top" class="{kind}"{(' style="'+style+'"') if style else ''}>
<a class="skip-link" href="#main">Перейти к содержимому</a>
{body}
</body></html>'''

def topbutton():
 return f'<a href="#top" class="to-top" aria-label="Вернуться наверх" title="Наверх">{ARROW}</a>'

def build():
 SITE.mkdir(exist_ok=True)
 home='''<main class="welcome" id="main">
<img class="welcome-photo" src="assets/images/welcome.webp" width="1672" height="941" alt="" fetchpriority="high">
<div class="welcome-content"><h1>Арина Самышева</h1><p class="welcome-role">Графический дизайнер</p>
<p class="welcome-description">Создаю айдентику и визуальные проекты для цифровой и печатной среды.</p>
<a class="primary-button" href="works.html">Смотреть работы</a>'''+social(['behance','email'])+'</div></main>'
 (SITE/'index.html').write_text(page('Арина Самышева — графический дизайнер','Айдентика, веб-дизайн и печатная графика. Портфолио графического дизайнера Арины Самышевой.',home,kind='home'),encoding='utf-8')
 cards=[]
 for i,p in enumerate(PROJECTS):
  c=p['cover'];load='eager' if i<2 else 'lazy'
  cards.append(f'''<a class="project-card" href="projects/{E(p['slug'])}.html" aria-label="{E(p['title'])}">
<img src="{E(c['src'])}" srcset="{E(c['small'])} 800w, {E(c['src'])} {c['width']}w" sizes="(max-width: 680px) 100vw, (min-width: 1756px) 738px, 43vw" width="{c['width']}" height="{c['height']}" alt="{E(p['name'])}: {E(p['description'])}" loading="{load}" decoding="async">
<div class="card-overlay" aria-hidden="true"><h2 class="card-title">{E(p['title'])}</h2></div></a>''')
 works=header(active='works')+'<main class="works-main" id="main"><h1 class="sr-only">Мои работы — Арина Самышева</h1><div class="project-grid">'+''.join(cards)+'</div></main>'+topbutton()
 (SITE/'works.html').write_text(page('Мои работы — Арина Самышева','Девять проектов: айдентика, веб-дизайн, полиграфия, логотипы, социальные сети и иконки.',works,path='works.html'),encoding='utf-8')
 rows=[]
 labels=[('name','Имя','Как к вам обращаться?','text','name',100),('email','Электронная почта','example@mail.com','email','email',254),('message','Сообщение','Расскажите о вашем предложении...','textarea','off',5000)]
 for key,label,placeholder,typ,auto,length in labels:
  attrib=f'id="{key}" name="{key}" required maxlength="{length}" placeholder="{placeholder}" autocomplete="{auto}" aria-describedby="{key}-error"'
  field=f'<textarea {attrib} rows="5"></textarea>' if typ=='textarea' else f'<input {attrib} type="{typ}">'
  rows.append(f'<div class="form-row"><label for="{key}">{label} <span class="required-mark" aria-hidden="true">*</span></label>{field}<span class="field-error" id="{key}-error" hidden></span></div>')
 contact=header(active='contact')+'''<main class="contact-main" id="main"><h1>Контакты</h1>
<p class="contact-intro">Есть предложение о работе или интересный проект? Напишите мне — буду рада обсудить детали и возможное сотрудничество.</p>
<form class="contact-form" id="contact-form" method="post" novalidate aria-label="Написать Арине">
<div class="hp-field" aria-hidden="true"><label for="website">Не заполняйте это поле</label><input id="website" name="_gotcha" tabindex="-1" autocomplete="off"></div>'''+''.join(rows)+'''
<button class="primary-button" type="submit" disabled>Отправить</button>
<p id="form-status" class="form-status" aria-live="polite" aria-atomic="true" hidden></p>
<noscript><p class="form-note">Для отправки формы включите JavaScript или напишите в <a href="https://t.me/melonpin">Telegram</a>.</p></noscript>
</form><section class="contact-direct" aria-label="Прямые контакты"><p>Или свяжитесь со мной напрямую</p>'''+social(['telegram','behance'])+'</section></main>'+topbutton()
 (SITE/'contact.html').write_text(page('Контакты — Арина Самышева','Предложения о работе и дизайн-проектах. Написать Арине Самышевой через форму, Telegram или Behance.',contact,path='contact.html'),encoding='utf-8')
 for idx,p in enumerate(PROJECTS):
  streams=[]
  for i,s in enumerate(p['slides']):
   srcset=', '.join('../'+E(v['src'])+' '+str(v['width'])+'w' for v in s['variants'])
   streams.append(f'''<a class="slide-link" href="../{E(s['src'])}" target="_blank" rel="noopener" data-caption="{E(p['name'])} · {i+1} / {len(p['slides'])}" aria-label="Увеличить слайд {i+1}: {E(s['section'])}">
<img src="../{E(s['src'])}" srcset="{srcset}" sizes="(min-width: 1920px) 1920px, 100vw" width="{s['width']}" height="{s['height']}" alt="{E(s['alt'])}" loading="{'eager' if i==0 else 'lazy'}" decoding="async"{(' fetchpriority="high"' if i==0 else '')}></a>''')
  prev=PROJECTS[idx-1] if idx else None; nxt=PROJECTS[idx+1] if idx<len(PROJECTS)-1 else None
  prevlink=f'<a class="prev" href="{prev["slug"]}.html"><small>Предыдущий проект</small>← {E(prev["name"])}</a>' if prev else '<span class="prev"></span>'
  nextlink=f'<a class="next" href="{nxt["slug"]}.html"><small>Следующий проект</small>{E(nxt["name"])} →</a>' if nxt else '<span class="next"></span>'
  pager=f'<nav class="project-pager" aria-label="Другие проекты">{prevlink}<a class="all" href="../works.html">Все работы</a>{nextlink}</nav>'
  viewer='''<dialog class="image-viewer" id="image-viewer" aria-label="Просмотр слайда"><div class="viewer-toolbar"><p class="viewer-caption"></p><div class="viewer-controls"><button type="button" data-zoom>Масштаб 100%</button><a data-original target="_blank" rel="noopener">Оригинал ↗</a><button type="button" data-close autofocus>Закрыть ×</button></div></div><div class="viewer-stage"><img alt=""></div></dialog>'''
  body=header('../',active='works')+'<main id="main">'+project_intro(p)+'<div class="project-stream">'+''.join(streams)+'</div>'+pager+'</main>'+topbutton()+viewer
  color='#eee7dd' if p['dark'] else '#022a55'
  filename='projects/'+p['slug']+'.html'
  (SITE/filename).write_text(page(p['title']+' — Арина Самышева',p['description'],body,prefix='../',kind='project-page',style=f'--project-bg:{p["background"]};--project-ink:{color}',og='../'+p['cover']['src'],path=filename),encoding='utf-8')
 # 404 works for root deployments; below JS handles configured subdirectory deployments.
 error=header()+'''<main class="not-found" id="main"><h1>Страница не найдена</h1><p>Давайте вернёмся к работам.</p><a class="primary-button" id="error-home" href="works.html">Смотреть работы</a></main>'''
 base404=SETTINGS.get('siteUrl','').rstrip('/')
 back404=base404+'/works.html' if base404 else '/works.html'
 (SITE/'404.html').write_text(f'''<!doctype html><html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Страница не найдена — Арина Самышева</title><meta name="robots" content="noindex"><style>body{{margin:0;min-height:100vh;display:grid;place-items:center;background:#EEE7DD;color:#022A55;font:18px/1.6 Arial,Helvetica,sans-serif;text-align:center}}main{{padding:32px;max-width:620px}}h1{{font-size:38px;line-height:1.2}}a{{display:inline-block;margin-top:16px;padding:12px 24px;background:#022A55;border-radius:8px;color:white;text-decoration:none;font-weight:bold}}a:focus-visible{{outline:3px solid #022A55;outline-offset:4px}}</style></head><body><main><h1>Страница не найдена</h1><p>Давайте вернёмся к работам.</p><a href="{E(back404)}">Смотреть работы</a></main></body></html>''',encoding='utf-8')
 (SITE/'.nojekyll').write_text('')
 (SITE/'assets/images/favicon.svg').write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" rx="12" fill="#EEE7DD"/><path d="M11 46 24 17h7l13 29h-7l-3-7H20l-3 7zm12-13h9l-4.5-11z" fill="#022A55"/><path d="M53 22a12 12 0 1 0 0 20" fill="none" stroke="#022A55" stroke-width="5" stroke-linecap="round"/></svg>')
 base=SETTINGS.get('siteUrl','').rstrip('/')
 (SITE/'robots.txt').write_text('User-agent: *\nAllow: /\n'+(f'Sitemap: {base}/sitemap.xml\n' if base else ''))
 sitemap=SITE/'sitemap.xml'
 if base:
  paths=['','works.html','contact.html']+['projects/'+p['slug']+'.html' for p in PROJECTS]
  sitemap.write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'+''.join('<url><loc>'+E(base+'/'+x)+'</loc></url>' for x in paths)+'</urlset>')
 elif sitemap.exists():sitemap.unlink()
 print('Built: 12 main pages + 404. No network, no publication, no mail sent.')

def configure(args):
 if args.form_id is not None:
  if args.form_id and not re.fullmatch('[A-Za-z0-9]{6,32}',args.form_id):raise SystemExit('Invalid Formspree public form ID')
  SETTINGS['formspreeId']=args.form_id
 if args.site_url is not None:
  u=urlparse(args.site_url)
  if args.site_url and (u.scheme!='https' or not u.netloc or u.query or u.fragment):raise SystemExit('Use full https site URL without query or fragment')
  SETTINGS['siteUrl']=args.site_url.rstrip('/')
 SETTINGS_PATH.write_text(json.dumps(SETTINGS,ensure_ascii=False,indent=2))
 config={'formspreeId':SETTINGS.get('formspreeId',''),'siteUrl':SETTINGS.get('siteUrl',''),'email':EMAIL,'telegram':TELEGRAM,'behance':BEHANCE}
 (SITE/'assets/js/config.js').write_text('// Public configuration only; never insert passwords or API secrets.\nwindow.PORTFOLIO_CONFIG = Object.freeze('+json.dumps(config,ensure_ascii=False,indent=2)+');\n')

if __name__=='__main__':
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--form-id');parser.add_argument('--site-url');args=parser.parse_args()
 if args.form_id is not None or args.site_url is not None:configure(args)
 build()
