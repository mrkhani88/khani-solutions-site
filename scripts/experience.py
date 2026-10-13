"""Company-first experience, with a curated subset of the public gallery."""
from html import escape as e
from case_studies import video
from research import related_research
from rocket_study import experience_demo

COMPANIES = [
 ('Boeing / Wisk', 'wisk-experience', [('wisk.svg','Wisk'),('boeing.svg','Boeing')], ''),
 ('Amazon LEO', 'amazon-leo-experience', [('amazon-leo.svg','Amazon LEO')], ''),
 ('Blue Origin', 'blue-origin-experience', [('blue-origin.svg','Blue Origin')], ''),
 ('Alcyone Therapeutics', 'alcyone-experience', [('alcyone.jpg','Alcyone Therapeutics')], ''),
 ('University of Idaho', 'idaho-experience', [('university-idaho.png','University of Idaho')], ''),
 ('National Iranian Oil Company', 'nioc-experience', [('nioc.svg','National Iranian Oil Company')], 'Iranian Oil Terminals Company · NIOC subsidiary'),
 ('Iran University of Science & Technology', 'iust-experience', [('iran-science-technology.jpg','Iran University of Science & Technology')], ''),
 ('University of Mazandaran', 'mazandaran-experience', [('university-mazandaran.png','University of Mazandaran')], ''),
]

EDUCATION = [
 ('Jan 2016 — Nov 2019', 'University of Idaho', 'PhD in Biological Engineering', 'Moscow, Idaho', [
  ('Doctoral research', 'Developed MRI-based numerical models of cerebrospinal fluid dynamics for filtration and intrathecal drug delivery. Connected subject-specific anatomy, spinal nerve-root geometry, and physiological flow measurements to computational models.'),
  ('Methods and publications', 'Investigated nonuniform moving boundaries, steady-streaming, catheter-induced flow changes, and blood clearance. Published this work with collaborators and documented the research in my doctoral dissertation.')]),
 ('Aug 2010 — May 2012', 'Iran University of Science & Technology', 'MS in Mechanical Engineering', 'Tehran, Iran', [
  ('Combustion research', 'Studied the response of conical premixed flames to upstream velocity disturbances and the effects of flame-speed development. This master’s research led to a co-authored paper in Propulsion and Power Research, published in 2017.'),
  ('Related propulsion research', 'Co-authored a three-dimensional CFD study of a novel rotary-piston engine in motoring mode, examining internal flow and thermal behavior. The related publication is linked below.')]),
 ('Aug 2006 — May 2010', 'University of Mazandaran', 'BS in Mechanical Engineering', 'Babol, Iran', [])
]
# Association means a relevant demonstration of methods, not employer-owned output.
COMPANY_SIMULATIONS = {'Blue Origin':['7384687421818519552','7381071965295538176'],
                       'Alcyone Therapeutics':['7345902436043145216']}

def public_demo(sim):
 activity,title,cat,slug,suffix,desc,tags = sim
 return f'''<article class="company-demo"><h4>{e(title)}</h4><p>{e(desc)}</p><div class="embed-shell"><iframe data-demo-src="https://www.linkedin.com/embed/feed/update/urn:li:activity:{activity}?compact=1" title="{e(title)} — public video" loading="lazy" allow="fullscreen" allowfullscreen></iframe></div><a class="text-link" href="https://www.linkedin.com/feed/update/urn:li:activity:{activity}/" target="_blank" rel="noopener noreferrer">Watch on LinkedIn ↗</a></article>'''

def hosted_demo(title,description,src,poster,url):
 return f'<article class="company-demo"><h4>{title}</h4><p>{description}</p>'+video(src,poster,title).replace('preload="metadata"','preload="none"')+f'<a class="text-link" href="{url}">Case study →</a></article>'

def company_experience(roles,sims,papers,link):
 result=''
 by_activity={s[0]:s for s in sims}
 for company,anchor,logos,subline in COMPANIES:
  artwork=''.join(f'<img src="/assets/company-logos/{file}" alt="{name}" loading="lazy">' for file,name in logos)
  result+=f'<article class="company-experience" id="{anchor}"><header class="company-heading"><div class="experience-logos">{artwork}</div><h2>{company}</h2>'+(f'<p>{subline}</p>' if subline else '')+'</header>'
  for date,c,title,loc,details in roles + EDUCATION:
   if c!=company: continue
   result+=f'<section class="company-position"><h3>{e(title)}</h3><p class="position-meta">{date} · {loc}</p>'
   if details: result+='<div class="position-work">'+''.join(f'<div><h4>{e(h)}</h4><p>{e(p)}</p></div>' for h,p in details)+'</div>'
   result+='</section>'
  demos=''
  note='Independent portfolio demos illustrating related methods; not employer hardware or project results.'
  if company=='Boeing / Wisk':
   demos=hosted_demo('Public-reference aircraft aerodynamics','Blender exterior reconstruction and steady OpenFOAM CFD at 100 mph. Surface Cp and selected native streamlines; preliminary numerical screening.','/assets/videos/midnight-seamless-flow-10s.mp4','/assets/videos/midnight-seamless-flow-poster.png','/AISolutions/midnight-aerodynamics.html').replace('<video controls','<video loop controls')+hosted_demo('Aircraft exhaust plume','External hot-gas flow around an approximate aircraft center section.','/assets/videos/aircraft-tr-plume-pencil-10s.mp4','/assets/videos/aircraft-tr-plume-pencil-poster.png','/AISolutions/aircraft-plume.html')+hosted_demo('Battery cooling','Transient module temperatures with two liquid cold plates in series.','/assets/videos/battery-module-series-10s.mp4','/assets/videos/battery-module-series-poster.png','/AISolutions/battery-cooling.html')
   note+=' The aerodynamics and plume use public Midnight-inspired geometry, not a Wisk aircraft. The aerodynamic field is not fully converged or grid independent.'
   count=3
  else:
   selected=COMPANY_SIMULATIONS.get(company,[])
   demos=''.join(public_demo(by_activity[a]) for a in selected)
   count=len(selected)
   if company=='Blue Origin':
    demos=experience_demo()+demos;count+=1
    note+=' The rocket study is a public-data Falcon 9-inspired concept, with planned CFD; it is not Blue Origin geometry.'
   if company=='Alcyone Therapeutics': note+=' This video demonstrates particle focusing in an idealized tube; it is not a CSF or thermophoresis result.'
  if demos:
   result+=f'<details class="company-demos"><summary><span class="demos-closed">View demos</span><span class="demos-open">Hide demos</span><span class="demo-count">{count} video'+('s' if count!=1 else '')+f'<span class="sr-only"> for {company}</span></span></summary><div class="company-demos-body"><p class="demo-context">{note}</p><div class="company-demo-grid">{demos}</div><a class="text-link all-demos" href="/AISolutions/simulations.html">All analysis &amp; modeling →</a></div></details>'
  result+=related_research(company,papers,link)
  result+='</article>'
 return result

def company_navigation():
 labels={'Boeing / Wisk':'Wisk / Boeing','National Iranian Oil Company':'NIOC','Alcyone Therapeutics':'Alcyone','Iran University of Science & Technology':'IUST','University of Mazandaran':'Mazandaran'}
 return '<nav class="company-jump" aria-label="Jump to experience or education">'+''.join(f'<a href="#{anchor}">{labels.get(name,name)}</a>' for name,anchor,*_ in COMPANIES)+'</nav>'

def overview_company_logos():
 """Individual logo links share the canonical Experience section identifiers."""
 featured={'wisk-experience','amazon-leo-experience','blue-origin-experience','alcyone-experience','idaho-experience','nioc-experience'}
 links=[]
 for company,anchor,logos,_ in COMPANIES:
  if anchor not in featured: continue
  if company=='Boeing / Wisk':
   links.append(f'<a class="company-logo wisk-boeing" data-company-preview href="/AISolutions/experience.html#{anchor}" aria-label="View Wisk and Boeing experience and independent demos"><img src="/assets/company-logos/wisk.svg" alt="Wisk"><span class="company-logo-relationship">Wisk · Boeing subsidiary</span><span class="company-logo-action">View work <span aria-hidden="true">↗</span></span></a>')
   continue
  for file,name in logos:
   slug={'university-idaho.png':'university-idaho'}.get(file,file.rsplit('.',1)[0])
   links.append(f'<a class="company-logo {slug}" data-company-preview href="/AISolutions/experience.html#{anchor}" aria-label="View {e(name)} work and available demos"><img src="/assets/company-logos/{file}" alt="{e(name)}" loading="lazy"><span class="company-logo-action">View work <span aria-hidden="true">↗</span></span></a>')
 return ''.join(links)

def company_dialog():
 return '''<dialog class="company-dialog" id="company-dialog" aria-labelledby="company-dialog-title"><header class="company-dialog-toolbar"><div><p class="eyebrow">Experience &amp; demos</p><h2 id="company-dialog-title">Company experience</h2></div><button class="company-dialog-close" type="button" aria-label="Close company popup">Close <span aria-hidden="true">×</span></button></header><div class="company-dialog-content"><p class="company-dialog-status" role="status">Loading experience…</p><div class="company-dialog-body"></div></div><footer class="company-dialog-footer"><a class="text-link" data-company-source href="/AISolutions/experience.html">Open full Experience page →</a><button class="company-dialog-retry" type="button" hidden>Try again</button></footer></dialog>'''
