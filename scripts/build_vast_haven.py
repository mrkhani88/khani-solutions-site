"""Scoped builder. Preserves unrelated generated pages and supports the full portfolio builder."""
from pathlib import Path
import re
from vast_haven import body,gallery_card
root=Path(__file__).resolve().parents[1]
p=root/'AISolutions/simulations.html'
s=p.read_text()
s=re.sub(r'<article class="simulation-card filter-item" id="vast-haven-1".*?</article>','',s,flags=re.S)
start=s.index('<main ');end=s.index('</main>',start)+7
page=s[:start]+'<main id="main" tabindex="-1">'+body()+'</main>'+s[end:]
page=re.sub(r'<title>.*?</title>','<title>Haven-1 thermal engineering | Khani Solutions</title>',page,count=1)
page=re.sub(r'<meta name="description" content="[^"]*">','<meta name="description" content="Independent Haven-1 CAD assembly, orbital thermal system, local thermal and structural analysis, internal-flow CFD and interview evidence.">',page,count=1)
page=re.sub(r'<meta property="og:title" content="[^"]*">','<meta property="og:title" content="Haven-1 thermal engineering | Khani Solutions">',page,count=1)
page=re.sub(r'<meta property="og:description" content="[^"]*">','<meta property="og:description" content="Independent public-reference spacecraft CAD, thermal system, local thermoelastic and CFD analysis.">',page,count=1)
page=re.sub(r'<link rel="canonical" href="[^"]*">','<link rel="canonical" href="https://khanisolutions.com/AISolutions/vast-haven-thermal.html">',page,count=1)
page=page.replace('</head>','<link rel="stylesheet" href="vast-haven.css?v=r1"><script type="module" src="vast-haven.mjs?v=r1"></script></head>')
page=page.replace('https://khanisolutions.com/assets/reza-khani-founder.jpeg','https://khanisolutions.com/assets/studies/vast-haven-1/media/assembly-poster.jpg')
(root/'AISolutions/vast-haven-thermal.html').write_text(page)
if 'id="vast-haven-1"' not in s:
 at=s.index('<article class="simulation-card filter-item"')
 s=s[:at]+gallery_card()+s[at:];p.write_text(s)
b=root/'scripts/build_portfolio.py';t=b.read_text()
if 'from vast_haven import' not in t:
 t=t.replace('from sceye_haps import gallery_card as sceye_card, body as sceye_body','from sceye_haps import gallery_card as sceye_card, body as sceye_body\nfrom vast_haven import gallery_card as vast_card, body as vast_body')
 t=t.replace('simcards = sceye_card()', 'simcards = vast_card() + sceye_card()')
 t=t.replace("page('sceye-haps-thermal.html'", "page('vast-haven-thermal.html','Haven-1 thermal engineering','Independent public-reference station CAD, system thermal, thermoelastic and internal-flow CFD study.',vast_body())\npage('sceye-haps-thermal.html'",1)
 t=t.replace(" if file == 'sceye-haps-thermal.html':", " if file == 'vast-haven-thermal.html':\n  html=html.replace('</head>', '<link rel=\"stylesheet\" href=\"/AISolutions/vast-haven.css?v=r1\"><script type=\"module\" src=\"/AISolutions/vast-haven.mjs?v=r1\"></script></head>')\n if file == 'sceye-haps-thermal.html':",1)
 b.write_text(t)
print('Built scoped Haven-1 page and simulations card')
