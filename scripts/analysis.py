"""Analysis presentation and verified software/experience associations.

Employer marks identify related career experience, not ownership of independent
portfolio demonstrations. Company identifiers come from the Experience source.
"""
from html import escape as e
import re
from experience import COMPANIES, COMPANY_SIMULATIONS
from research import MEDIA

COMPANY_BY_NAME = {name:(anchor,logos) for name,anchor,logos,_ in COMPANIES}
TOOLS = {
 'OpenFOAM': ('openfoam.png','https://www.openfoam.com/'),
 'ANSYS Fluent': ('ansys.svg','https://www.ansys.com/products/fluids/ansys-fluent'),
 'Thermal Desktop': ('ansys.svg','https://www.ansys.com/products/thermal/thermal-desktop'),
 'FreeCAD': ('freecad.svg','https://www.freecad.org/'),
 'Siemens NX / FEMAP': ('siemens.svg','https://www.sw.siemens.com/'),
 'Python': ('python.svg','https://www.python.org/'),
 'Gmsh': (None,'https://gmsh.info/'),
 'Elmer': (None,'https://www.elmerfem.org/'),
}

def company_links(names):
 html = ''
 for name in names:
  if name == 'Khani Solutions':
   html += '<a class="analysis-company" href="/" aria-label="Khani Solutions overview"><img src="/assets/khani-solutions-logo.png" alt="Khani Solutions" width="32" height="32"><span>Khani Solutions</span></a>'
   continue
  anchor, logos = COMPANY_BY_NAME[name]
  for file,label in logos:
   html += f'<a class="analysis-company" data-company-preview href="/AISolutions/experience.html#{anchor}" aria-label="View {e(label)} work and available demos" title="View {e(label)} work"><img src="/assets/company-logos/{file}" alt="{e(label)}" loading="lazy"><span class="sr-only">{e(label)}</span></a>'
 return html

def related_context(names):
 return '<div class="analysis-context"><span>Related experience</span>'+company_links(names)+'</div>' if names else ''

def company_ids(names):
 return ' '.join(dict.fromkeys(COMPANY_BY_NAME[name][0] for name in names))

def tool_badges(names):
 html = '<div class="analysis-tools" aria-label="Software used">'
 for name in names:
  logo, url = TOOLS[name]
  art = f'<img src="/assets/tool-logos/{logo}" alt="" loading="lazy">' if logo else ''
  html += f'<a href="{url}" target="_blank" rel="noopener noreferrer">{art}<span>{e(name)}</span><span class="sr-only"> software website</span></a>'
 return html+'</div>'

def keywords(tags):
 return '<p class="analysis-keywords">'+' · '.join(e(t) for t in tags)+'</p>'

def related_to_activity(activity):
 return [name for name, records in COMPANY_SIMULATIONS.items() if activity in records]

def study_card(html, kind):
 names = ['Boeing / Wisk']
 html = html.replace('data-category="Thermal"', f'data-category="Thermal" data-method="cfd" data-analysis-company-ids="{company_ids(names)}"')
 if kind == 'plume':
  html = html.replace('Thermal-runaway exhaust plume around a grounded aircraft','Aircraft exhaust plume')
  tools = ['FreeCAD','Gmsh','OpenFOAM']; tags = ['External flow','Buoyancy','Heat transfer']
  note = 'Independent demonstration · Approximate aircraft geometry and assumed release conditions.'
 else:
  html = html.replace('Battery cooling with two heat exchangers in series','Battery cooling in series')
  tools = ['FreeCAD','Elmer']; tags = ['Conjugate heat transfer','Liquid cooling','Transient response']
  note = 'Independent demonstration · Screening model with assumed materials and operating conditions.'
 html = re.sub(r'<div class="pills">.*?</div>',tool_badges(tools)+keywords(tags),html,count=1,flags=re.S)
 html = re.sub(r'<p class="study-note">.*?</p>',f'<p class="study-note">{note}</p>'+related_context(names),html,count=1,flags=re.S)
 return html

def public_card(sim, link):
 activity,title,cat,slug,suffix,desc,tags=sim
 names=related_to_activity(activity)
 url=f'https://www.linkedin.com/feed/update/urn:li:activity:{activity}/'
 return f'''<article class="simulation-card analysis-post filter-item" id="demo-{activity}" data-category="{e(cat)}" data-method="cfd" data-analysis-company-ids="{company_ids(names)}"><div class="card-copy"><p class="eyebrow">{e(cat)} / Public demonstration</p><h2>{e(title)}</h2><p>{e(desc)}</p>{tool_badges(['OpenFOAM'])}{keywords([t for t in tags if t!='OpenFOAM'])}{related_context(names)}</div><details class="analysis-video" open><summary>Watch video<span aria-hidden="true"> +</span></summary><div class="embed-shell"><iframe src="https://www.linkedin.com/embed/feed/update/urn:li:activity:{activity}?compact=1" data-gallery-src="https://www.linkedin.com/embed/feed/update/urn:li:activity:{activity}?compact=1" title="{e(title)} — public video" loading="lazy" allow="fullscreen" allowfullscreen></iframe></div><noscript><p>Use the LinkedIn link below to watch this video.</p></noscript></details><div class="card-bottom">{link(url,'Watch on LinkedIn')}<small>Independent Khani Solutions post</small></div></article>'''

def context_cards():
 figure = MEDIA['papers']['LkGwnXOMwfcC']
 systems = f'''<article class="simulation-card analysis-summary filter-item" id="system-models" data-method="systems" data-analysis-company-ids="blue-origin-experience wisk-experience"><div class="card-copy"><p class="eyebrow">0D / 1D systems · Experience summary</p><h2>From component models to system behavior</h2><p>Mission gas budgets and transient cryogenic subsystem analysis at Blue Origin; battery cooling architecture, pressure drop, and coolant distribution at Boeing / Wisk.</p>{tool_badges(['Thermal Desktop'])}{keywords(['SINDA/FLUINT','FloCAD','Gas budgets','Cooling circuits'])}<p class="analysis-status">Public system-model demonstration planned.</p>{related_context(['Blue Origin','Boeing / Wisk'])}<p class="quiet">Thermal Desktop, FloCAD, and SINDA/FLUINT relate to the Blue Origin work.</p></div><div class="card-bottom"><a class="text-link" href="/AISolutions/experience.html#blue-origin-experience">Explore system-analysis experience →</a></div></article>'''
 twins = f'''<article class="simulation-card analysis-summary filter-item" id="digital-twins" data-method="twins" data-analysis-company-ids="alcyone-experience idaho-experience"><div class="card-copy"><p class="eyebrow">Digital twins · Published research</p><h2>Patient-specific models for CNS drug delivery</h2><p>MRI-derived anatomy, physiological wall motion, and drug transport connect patient geometry to computational models and experimental comparison.</p>{tool_badges(['OpenFOAM','ANSYS Fluent'])}{keywords(['MRI segmentation','Dynamic mesh','CSF transport'])}{related_context(['Alcyone Therapeutics','University of Idaho'])}<p class="quiet">Software spans these research roles; individual publication methods are documented in the papers.</p></div><a class="analysis-research-image" href="/AISolutions/publications.html#paper-LkGwnXOMwfcC" aria-label="Explore the original figure and human in silico trials paper"><img src="{e(figure["asset"])}" alt="{e(figure["alt"])}" loading="lazy"></a><div class="card-bottom"><a class="text-link" href="/AISolutions/publications.html#paper-LkGwnXOMwfcC">Explore the published research →</a><a class="text-link" href="/AISolutions/experience.html#alcyone-experience">Work &amp; methods →</a></div></article>'''
 return systems+twins

def analysis_filters():
 methods=[('all','All work'),('geometry','CAD & study plans'),('cfd','CFD & thermal'),('systems','0D / 1D systems'),('twins','Digital twins')]
 buttons=''.join(f'<button type="button" data-analysis-method="{key}" aria-pressed="{str(key=="all").lower()}" aria-controls="analysis-grid">{label}</button>' for key,label in methods)
 names=['Boeing / Wisk','Blue Origin','Alcyone Therapeutics','University of Idaho']
 options='<option value="independent-work">Independent work</option>'+''.join(f'<option value="{COMPANY_BY_NAME[name][0]}">{e(name)}</option>' for name in names)
 return f'<div class="analysis-controls"><div class="analysis-method-filter" role="group" aria-label="Modeling method">{buttons}</div><label class="analysis-company-filter">Work context<select data-analysis-company><option value="all">All work contexts</option>{options}</select></label></div>'

def software_section():
 groups=[
  ('OpenFOAM','openfoam.png','https://www.openfoam.com/','CFD · Custom physics · Dynamic mesh','Public demonstrations and custom OpenFOAM physics at Alcyone.',['Alcyone Therapeutics']),
  ('Ansys','ansys.svg','https://www.ansys.com/','Fluent · Thermal Desktop · SINDA/FLUINT · FloCAD','CFD and mission thermal-fluid systems at Blue Origin; Fluent-based biomedical models at Idaho.',['Blue Origin','University of Idaho']),
  ('Siemens','siemens.svg','https://www.sw.siemens.com/','NX · FEMAP · Finite-element analysis','Spacecraft geometry, meshing, and impact-response analysis at Amazon LEO.',['Amazon LEO']),
  ('Geometry & multiphysics','freecad.svg','https://www.freecad.org/','FreeCAD · Gmsh · Elmer','Geometry, meshing, and thermal-fluid solvers in my independent case studies.',['Khani Solutions']),
  ('Modeling & design','dassaultsystemes.svg','https://www.3ds.com/','Abaqus · SolidWorks','Additional finite-element modeling and CAD tools listed in my résumé.',[]),
  ('Automation & computing','python.svg','https://www.python.org/','Python · MATLAB · C++ · HPC','Repeatable model setup, post-processing, and parallel simulation workflows. Python automation at Amazon LEO; HPC at Alcyone.',['Amazon LEO','Alcyone Therapeutics']),
 ]
 cards=''
 for title,logo,url,tags,desc,names in groups:
  cards+=f'<article class="analysis-software"><div class="software-heading"><a href="{url}" target="_blank" rel="noopener noreferrer" aria-label="{e(title)} software website"><img src="/assets/tool-logos/{logo}" alt="{e(title) if title not in ["Geometry & multiphysics","Modeling & design","Automation & computing"] else {"freecad.svg":"FreeCAD","dassaultsystemes.svg":"Dassault Systèmes","python.svg":"Python"}[logo]}" loading="lazy"></a><h3>{e(title)}</h3></div><p class="software-keywords">{e(tags)}</p><p>{e(desc)}</p>{related_context(names)}</article>'
 return f'<section class="wrap analysis-software-section" id="software"><div class="section-heading"><p class="eyebrow">The working toolkit</p><h2>Software &amp; methods.</h2><p>Tools from my project workflows and engineering experience.</p></div><div class="analysis-software-grid">{cards}</div></section>'

def analysis_page(intro, cards):
 return intro('Thermal-fluid engineering','Analysis &amp; modeling.','CFD and heat transfer, 0D/1D system models, and digital twins.','<div class="actions"><a class="button primary" href="#analysis-work">Explore the work ↓</a><a class="text-link" href="#software">Software &amp; methods →</a></div>')+f'<section class="wrap gallery-section" id="analysis-work"><div class="analysis-section-heading"><div><p class="eyebrow">Models in practice</p><h2>Explore the work.</h2></div><p>Public demos, research, and selected experience.</p></div>{analysis_filters()}<p class="analysis-gallery-note">Employer logos link to related experience. Video demonstrations are independent Khani Solutions work.</p><p class="quiet" role="status" data-analysis-status>Public studies, design-stage work and related experience.</p><div class="simulation-grid" id="analysis-grid" data-analysis-grid>{cards}{context_cards()}</div><div class="analysis-empty" data-analysis-empty hidden><h3>No entries match this combination.</h3><p>Try another modeling method or company.</p><button type="button" class="button secondary" data-analysis-reset>Show all work</button></div></section>'+software_section()
