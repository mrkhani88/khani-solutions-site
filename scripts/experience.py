"""Company-first experience, with a curated subset of the public gallery."""
from html import escape as e
from case_studies import video

COMPANIES = [
 ('Boeing / Wisk', 'wisk-experience', [('wisk.svg','Wisk'),('boeing.svg','Boeing')], ''),
 ('Amazon LEO', 'amazon-leo-experience', [('amazon-leo.svg','Amazon LEO')], ''),
 ('Blue Origin', 'blue-origin-experience', [('blue-origin.svg','Blue Origin')], ''),
 ('Alcyone Therapeutics', 'alcyone-experience', [('alcyone.jpg','Alcyone Therapeutics')], ''),
 ('University of Idaho', 'idaho-experience', [('university-idaho.png','University of Idaho')], ''),
 ('National Iranian Oil Company', 'nioc-experience', [('nioc.svg','National Iranian Oil Company')], 'Iranian Oil Terminals Company · NIOC subsidiary'),
]
# Association means a relevant demonstration of methods, not employer-owned output.
COMPANY_SIMULATIONS = {'Blue Origin':['7384687421818519552','7381071965295538176'],
                       'Alcyone Therapeutics':['7345902436043145216']}

def public_demo(sim):
 activity,title,cat,slug,suffix,desc,tags = sim
 return f'''<article class="company-demo"><h4>{e(title)}</h4><p>{e(desc)}</p><div class="embed-shell"><iframe data-demo-src="https://www.linkedin.com/embed/feed/update/urn:li:activity:{activity}?compact=1" title="{e(title)} — public video" loading="lazy" allow="fullscreen" allowfullscreen></iframe></div><a class="text-link" href="https://www.linkedin.com/feed/update/urn:li:activity:{activity}/" target="_blank" rel="noopener noreferrer">Watch on LinkedIn ↗</a></article>'''

def hosted_demo(title,description,src,poster,url):
 return f'<article class="company-demo"><h4>{title}</h4><p>{description}</p>'+video(src,poster,title).replace('preload="metadata"','preload="none"')+f'<a class="text-link" href="{url}">Case study →</a></article>'

def company_experience(roles,sims):
 result=''
 by_activity={s[0]:s for s in sims}
 for company,anchor,logos,subline in COMPANIES:
  artwork=''.join(f'<img src="/assets/company-logos/{file}" alt="{name}" loading="lazy">' for file,name in logos)
  result+=f'<article class="company-experience" id="{anchor}"><header class="company-heading"><div class="experience-logos">{artwork}</div><h2>{company}</h2>'+(f'<p>{subline}</p>' if subline else '')+'</header>'
  for date,c,title,loc,details in roles:
   if c!=company: continue
   result+=f'<section class="company-position"><h3>{e(title)}</h3><p class="position-meta">{date} · {loc}</p><div class="position-work">'+''.join(f'<div><h4>{e(h)}</h4><p>{e(p)}</p></div>' for h,p in details)+'</div></section>'
  demos=''
  note='Independent portfolio demos illustrating related methods; not employer hardware or project results.'
  if company=='Boeing / Wisk':
   demos=hosted_demo('Aircraft exhaust plume','External hot-gas flow around an approximate aircraft center section.','/assets/videos/aircraft-tr-plume-pencil-10s.mp4','/assets/videos/aircraft-tr-plume-pencil-poster.png','/AISolutions/aircraft-plume.html')+hosted_demo('Battery cooling','Transient module temperatures with two liquid cold plates in series.','/assets/videos/battery-module-series-10s.mp4','/assets/videos/battery-module-series-poster.png','/AISolutions/battery-cooling.html')
   note+=' The plume uses a Midnight-inspired aircraft, not a Wisk geometry.'
   count=2
  else:
   selected=COMPANY_SIMULATIONS.get(company,[])
   demos=''.join(public_demo(by_activity[a]) for a in selected)
   count=len(selected)
   if company=='Alcyone Therapeutics': note+=' This video demonstrates particle focusing in an idealized tube; it is not a CSF or thermophoresis result.'
  if demos:
   result+=f'<details class="company-demos"><summary><span class="demos-closed">View demos</span><span class="demos-open">Hide demos</span><span class="demo-count">{count} video'+('s' if count!=1 else '')+f'<span class="sr-only"> for {company}</span></span></summary><div class="company-demos-body"><p class="demo-context">{note}</p><div class="company-demo-grid">{demos}</div><a class="text-link all-demos" href="/AISolutions/simulations.html">All simulations →</a></div></details>'
  if company in ['Alcyone Therapeutics','University of Idaho']:
   result+='<a class="text-link company-research" href="/AISolutions/publications.html">Related publications →</a>'
  result+='</article>'
 return result

def company_navigation():
 return '<nav class="company-jump" aria-label="Jump to a company">'+''.join(f'<a href="#{anchor}">{"Wisk / Boeing" if name=="Boeing / Wisk" else "NIOC" if name=="National Iranian Oil Company" else "Alcyone" if name=="Alcyone Therapeutics" else name}</a>' for name,anchor,*_ in COMPANIES)+'</nav>'
