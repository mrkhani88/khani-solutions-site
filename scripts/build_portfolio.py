# -*- coding: utf-8 -*-
from pathlib import Path
from html import escape as e, unescape
import json
import re
from experience import company_experience, company_navigation, overview_company_logos, company_dialog
from scholar import scholar_section
from research import paper_anchor, scholar_record, intellectual_property, publication_figure, paper_links, DISSERTATION, ABSTRACTS
from analysis import analysis_page, public_card, study_card
from battery_thermal import battery_thermal_card, publish_pages as publish_battery_thermal_pages
from midnight_sweep import sweep_viewer, SWEEP_TEXT
from midnight_wake import wake_study
from case_studies import PLUME_TEXT, PLUME_SUMMARY, BATTERY_SUMMARY, BATTERY_CONTEXT, BATTERY_END, MIDNIGHT_TEXT, MIDNIGHT_SUMMARY, MIDNIGHT_POST_URL, midnight_card, plume_card, battery_card, study_page, video
from rocket_study import gallery_card as rocket_card, study_body as rocket_body
from lunar_tank import gallery_card as lunar_card, study_body as lunar_body
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'AISolutions'
publish_battery_thermal_pages(ROOT)
SCHOLAR='https://scholar.google.com/citations?user=ipaKdZ4AAAAJ&hl=en'
LINKEDIN='https://www.linkedin.com/in/mohammadreza-khani-phd/'
nav=[('index.html','Overview'),('automation.html','AI & automation'),('simulations.html','Analysis & modeling'),('publications.html','Publications'),('experience.html','Experience'),('contact.html','Contact')]
# Small decorative icons supplement the visible labels; they never replace them.
ICONS={
 'home':'<path d="m3 10 9-7 9 7v10a1 1 0 0 1-1 1h-5v-7H9v7H4a1 1 0 0 1-1-1z"/>',
 'play':'<circle cx="12" cy="12" r="9"/><path d="m10 8 6 4-6 4z"/>',
 'briefcase':'<rect x="3" y="7" width="18" height="14" rx="2"/><path d="M8 7V3h8v4M3 12a20 20 0 0 0 18 0M10 12h4v3h-4z"/>',
 'projects':'<rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/>',
 'paper':'<path d="M14 2H5a1 1 0 0 0-1 1v18a1 1 0 0 0 1 1h14a1 1 0 0 0 1-1V8zM14 2v6h6M8 12h8M8 16h8"/>',
 'book':'<path d="M12 5v16M3 3c4-1 7 0 9 2 2-2 5-3 9-2v16c-4-1-7 0-9 2-2-2-5-3-9-2z"/>',
 'scholar':'<path d="m2 9 10-5 10 5-10 5zM6 11v6c4 3 8 3 12 0v-6M22 9v8"/>',
 'link':'<path d="m10 13 4-4M8 16l-1 1a4 4 0 0 1-6-6l5-5a4 4 0 0 1 6 0M16 8l1-1a4 4 0 0 1 6 6l-5 5a4 4 0 0 1-6 0" transform="translate(0 -1)"/>',
 'mail':'<rect x="3" y="5" width="18" height="14" rx="2"/><path d="m3 6 9 7 9-7"/>',
 'phone':'<path d="m6 3 4 4-2 3c2 3 3 4 6 6l3-2 4 4-2 3C10 23 1 14 3 5z"/>',
 'up':'<path d="M12 21V3m-7 7 7-7 7 7"/>',
 'skip':'<path d="m4 5 11 7-11 7zM19 5v14"/>',
 'rocket':'<path d="M10 15c-1-4 3-10 11-12 0 8-6 12-10 12M10 9H5l-3 5h7M15 14v5l-5 3v-7M7 17l-4 4"/><circle cx="16" cy="8" r="2"/>',
 'waves':'<path d="M2 6c4-5 7 5 11 0s7 0 9 0M2 12c4-5 7 5 11 0s7 0 9 0M2 18c4-5 7 5 11 0s7 0 9 0"/>',
 'particles':'<circle cx="5" cy="6" r="2"/><circle cx="18" cy="5" r="2"/><circle cx="12" cy="13" r="3"/><circle cx="4" cy="20" r="2"/><circle cx="20" cy="19" r="2"/><path d="m7 8 3 3m4-1 3-3M6 18l4-3m5 0 3 2"/>',
 'thermal':'<path d="M9 14V5a3 3 0 0 1 6 0v9a5 5 0 1 1-6 0M12 8v10"/><circle cx="12" cy="18" r="1"/>',
 'code':'<path d="m8 6-6 6 6 6m8-12 6 6-6 6M14 3l-4 18"/>',
 # Brain icon: Lucide (ISC), see assets/icons/lucide-LICENSE.txt.
 'automation':'<path d="M12 18V5" /><path d="M15 13a4.17 4.17 0 0 1-3-4 4.17 4.17 0 0 1-3 4" /><path d="M17.598 6.5A3 3 0 1 0 12 5a3 3 0 1 0-5.598 1.5" /><path d="M17.997 5.125a4 4 0 0 1 2.526 5.77" /><path d="M18 18a4 4 0 0 0 2-7.464" /><path d="M19.967 17.483A4 4 0 1 1 12 18a4 4 0 1 1-7.967-.517" /><path d="M6 18a4 4 0 0 1-2-7.464" /><path d="M6.003 5.125a4 4 0 0 0-2.526 5.77" />',
}
def action_icon(name):
 return f'<svg class="action-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">{ICONS[name]}</svg>'
def decorate_actions(html):
 def decorate(match):
  tag,attrs,content=match.groups()
  if '<svg' in content or '<img' in content or 'skip-link' in attrs:
   return match.group(0)
  label=unescape(re.sub('<[^>]+>','',content)).strip()
  href=re.search(r'href="([^"]+)"',attrs)
  href=unescape(href.group(1)) if href else ''
  name=None
  if tag=='button':
   category=re.search(r'data-filter="([^"]+)"',attrs)
   if category:
    name={'All':'projects','Aerospace':'rocket','Free surface':'waves','Particle transport':'particles','Thermal':'thermal'}[category.group(1)]
   elif 'type="submit"' in attrs: name='mail'
   elif label=='Skip intro': name='skip'
  elif href.startswith('mailto:'): name='mail'
  elif href.startswith('tel:'): name='phone'
  elif 'scholar.google.com' in href: name='scholar'
  elif 'doi.org' in href: name='link'
  elif label.startswith('Read full text'): name='book'
  elif 'solver' in label.lower() or 'workflow' in label.lower(): name='code'
  elif 'thermal analysis' in label.lower(): name='thermal'
  else:
   name={'index.html':'home','simulations.html':'waves','automation.html':'automation','publications.html':'paper','experience.html':'briefcase','contact.html':'mail','#projects':'projects','#career':'briefcase','#main':'up'}.get(href)
  if not name: return match.group(0)
  if 'class="' in attrs: attrs=attrs.replace('class="','class="icon-action ',1)
  else: attrs+=' class="icon-action"'
  return f'<{tag}{attrs}>{action_icon(name)}<span class="action-label">{content}</span></{tag}>'
 return re.sub(r'<(a|button)(\s[^>]*)>(.*?)</\1>',decorate,html,flags=re.S)
def link(url,label,cls='text-link',arrow=True):
 icon=''
 if 'linkedin.com/' in url:
  cls += ' linkedin-link'
  icon='<svg class="linkedin-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" width="20" height="20" aria-hidden="true" focusable="false"><path fill="currentColor" d="M0 1.146C0 .513.526 0 1.175 0h13.65C15.474 0 16 .513 16 1.146v13.708c0 .633-.526 1.146-1.175 1.146H1.175C.526 16 0 15.487 0 14.854V1.146zm4.943 12.248V6.169H2.542v7.225h2.401zM3.743 5.182c.837 0 1.358-.554 1.358-1.248-.015-.709-.521-1.248-1.342-1.248-.822 0-1.359.539-1.359 1.248 0 .694.521 1.248 1.327 1.248h.016zm4.908 8.212V9.359c0-.216.016-.432.08-.586.173-.431.568-.878 1.232-.878.869 0 1.216.662 1.216 1.633v3.866h2.401V9.25c0-2.22-1.184-3.252-2.763-3.252-1.274 0-1.845.7-2.166 1.193V6.169H6.25c.03.678 0 7.225 0 7.225h2.401z"/></svg>'
 outward=' <span aria-hidden="true">↗</span>' if arrow else ''
 return f'<a class="{cls}" href="{e(url,quote=True)}" target="_blank" rel="noopener noreferrer">{icon}{e(label)}{outward}</a>'
def page(file,title,description,body):
 n=''.join(f'<a href="{f}"'+(' aria-current="page"' if f==file else '')+f'>{label}</a>' for f,label in nav)
 theme_color='#fbf7ee' if file=='index.html' else '#081126'
 stylesheet_version='20261015-text-brand' if file=='index.html' else '20261013-rocket-study'
 html=f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(title)} | Khani Solutions</title><meta name="description" content="{e(description,quote=True)}">
<link rel="canonical" href="https://khanisolutions.com/{'' if file=='index.html' else 'AISolutions/'+file}">
<meta property="og:title" content="{e(title,quote=True)} | Khani Solutions"><meta property="og:description" content="{e(description,quote=True)}"><meta property="og:type" content="website"><meta property="og:image" content="https://khanisolutions.com/assets/reza-khani-founder.jpeg">
<meta name="theme-color" content="{theme_color}"><link rel="icon" href="../assets/khani-solutions-logo.svg" type="image/svg+xml"><link rel="stylesheet" href="portfolio.css?v={stylesheet_version}"><script src="portfolio.js?v=20261012-midnight-study" defer></script><script src="/AISolutions/scholar.js?v=20261012-midnight-study" defer></script></head>
<body><a class="skip-link" href="#main">Skip to content</a><header class="site-header"><div class="header-inner"><a class="brand" href="index.html"><img src="../assets/khani-solutions-logo.svg" width="46" height="46" alt=""><span>Khani Solutions<small>Mohammadreza Khani, PhD</small></span></a><button class="nav-toggle" aria-expanded="false" aria-controls="site-nav" type="button">Menu <img src="../assets/icon-list.svg" alt="" width="18" height="18"></button><nav id="site-nav" aria-label="Main navigation">{n}</nav></div></header>
<main id="main" tabindex="-1">{body}</main><footer><div class="footer-inner"><div><strong>Khani Solutions</strong><p>CFD · Thermal fluids · Biomedical engineering</p><small>© 2026 Mohammadreza Khani</small></div><div class="footer-links">{link(LINKEDIN,'Connect & follow on LinkedIn')}{link(SCHOLAR,'Google Scholar')}<a href="mailto:mkhani.phd@gmail.com">Email me ↗</a><a href="#main">Back to top ↑</a></div></div></footer></body></html>'''
 if file == 'midnight-aerodynamics.html':
  html = html.replace('https://khanisolutions.com/assets/reza-khani-founder.jpeg', 'https://khanisolutions.com/assets/studies/midnight-wake/Branded_Poster.png')
 if file == 'rocket-cad-cfd.html':
  html = html.replace('https://khanisolutions.com/assets/reza-khani-founder.jpeg', 'https://khanisolutions.com/assets/videos/falcon9-upright-component-tour-poster.png')
 if file == 'lunar-tank-cfd.html':
  html = html.replace('https://khanisolutions.com/assets/reza-khani-founder.jpeg', 'https://khanisolutions.com/assets/studies/lunar-tank/Poster.jpg')
 if file in ['lunar-tank-cfd.html', 'experience.html', 'simulations.html']:
  html = html.replace('</head>', '<link rel="stylesheet" href="/AISolutions/lunar-tank.css?v=20261016-r7"></head>')
 if file in ['index.html', 'simulations.html']:
  html = html.replace('</body>', company_dialog() + '</body>')
 html=decorate_actions(html)
 if file in ['index.html', 'simulations.html', 'experience.html', 'midnight-aerodynamics.html']:
  html=html.replace('</head>', '<link rel="stylesheet" href="/AISolutions/midnight-wake.css?v=20261016-wake-r1"></head>')
 html=html.replace('</head>', '<link rel="stylesheet" href="/AISolutions/midnight-sweep.css?v=20261014-angle-loop-r2"><script src="/AISolutions/midnight-sweep.js?v=20261014-angle-loop-r2" defer></script></head>')
 if file == 'automation.html':
  html = html.replace('</head>', '<link rel="stylesheet" href="/AISolutions/automation.css?v=20261015-airfoil-auto-color"><script type="module" src="/AISolutions/airfoil-flow.js?v=20261015-airfoil-auto-color"></script></head>')
  html = html.replace('https://khanisolutions.com/assets/reza-khani-founder.jpeg', 'https://khanisolutions.com/assets/automation/lewiston-map.jpg')
 # Absolute site paths allow Overview to render at the root and legacy URL.
 for route, _ in nav:
  destination = '/' if route == 'index.html' else '/AISolutions/' + route
  html = html.replace('href="' + route + '"', 'href="' + destination + '"')
 html = html.replace('../assets/', '/assets/').replace('href="portfolio.css?', 'href="/AISolutions/portfolio.css?').replace('src="portfolio.js?', 'src="/AISolutions/portfolio.js?')
 html = html.replace('src="/assets/khani-solutions-logo.svg"', 'src="/assets/khani-solutions-logo.png"')
 if file == 'index.html':
  animation_head = '<link rel="preload" as="image" href="/assets/khani-solutions-logo.png" fetchpriority="high"><link rel="stylesheet" href="/AISolutions/logo-intro.css?v=20261008-1"><script src="/AISolutions/logo-intro.js?v=20261009-1" defer></script>'
  html = html.replace('</head>', animation_head + '</head>')
  html = html.replace('<body>', '<body>' + decorate_actions((ROOT/'scripts/templates/logo-intro.html').read_text()))
 html = html.replace('<body>', f'<body class="page-{Path(file).stem}">')
 (OUT/file).write_text(html)
 if file == 'index.html':
  (ROOT/'index.html').write_text(html)
def intro(kicker,title,description,actions=''):
 return f'<section class="page-intro"><div class="wrap"><p class="eyebrow">{kicker}</p><h1>{title}</h1><p class="lead">{description}</p>{actions}</div></section>'
def pills(items): return '<div class="pills">'+''.join(f'<span>{e(x)}</span>' for x in items)+'</div>'
# The descriptions below are paraphrases of the supplied resume and identified public posts.
sims=[
('7339877315046273027','Dynamic mesh wave simulation','Free surface','openfoam-cfd-dynamicmesh','Vwoh','A moving mesh follows wave propagation and the evolving free surface. Motion settings and absorption zones help control deformation and reflected waves.',['OpenFOAM','Dynamic mesh','Wave motion']),
('7384687421818519552','Nonlinear waves in cryogenic tanks','Aerospace','cfd-openfoam-cryogenics','zvdE','A Stokes V wave model explores nonlinear free-surface motion in cryogenic propellant tanks, with interface tracking and damping at the boundaries.',['VOF multiphase','Stokes V','Cryogenics']),
('7381071965295538176','Cryogenic tank slosh and ullage response','Aerospace','cfd-cryogenics-lh2','BsUO','A three-dimensional tank model examines liquid slosh under six-degree-of-freedom motion and its interaction with ullage pressure and thermal behavior.',['OpenFOAM','6-DOF motion','LH₂ / LOX']),
('7364440285642227713','Transient compressible flow','Aerospace','cfd-openfoam-aerospaceengineering','wSo5','A throttle bottle simulation resolves pressure waves, shock reflections, recirculation, and flow separation inside an aerospace flow configuration.',['Compressible flow','Pressure waves','Transient CFD']),
('7345902436043145216','Particle focusing through geometry','Particle transport','cfd-openfoam-particlefocusing','t0GT','A converging and diverging tube explores how carrier-flow geometry changes particle trajectories and concentrates an aerosol stream.',['Lagrangian particles','OpenFOAM','Aerosol flow']),
('7335087470562222080','Electronics cooling and conjugate heat transfer','Thermal','cfd-openfoam-thermalmodeling','80gV','A CPU and heatsink model couples spatially varying heat generation with airflow to examine thermal hot spots and cooling design.',['Conjugate heat transfer','Electronics cooling','HPC'])]
battery_study_details = '<details class="study-details"><summary>Model details, results &amp; engineering considerations</summary><div class="study-details-body"><p>I built this conjugate heat transfer study using FreeCAD for the geometry and Elmer for the flow and thermal calculations.</p><p>The model represents 30 pouch cells as a single anisotropic thermal block, measuring 352 × 188 × 169 mm, inside a 2 mm titanium casing. Two aluminum cold plates sit on opposite faces, separated from the casing by 0.5 mm thermal interface layers. Each plate contains a five-pass serpentine channel. Coolant passes through the first plate, crosses to the second, and then exits.</p><p>The battery conductivity was assumed to be 20 W/m·K in-plane and 1 W/m·K through-plane. That difference matters: a cold plate can remain relatively cool while the module interior heats up because heat cannot reach the cooled faces quickly enough.</p><p>The simulation used:</p><ul><li>300 W of uniform module heat generation.</li><li>1 L/min water at 25°C, with all regions initially at 25°C.</li><li>Approximately 2.08 million tetrahedral elements.</li><li>A steady incompressible flow calculation followed by transient conduction and coolant advection, using 30-second steps over one hour.</li></ul><p>At one hour, the calculated module peak reached 63.5°C, while the coolant reached 26.4°C after the first plate and 27.8°C at the outlet. The coolant was removing approximately 195 W at that instant; the remaining heat was still accumulating in the assembly. This was a transient result, not thermal equilibrium.</p><p>Practical design concerns include warmer coolant entering the second plate, pressure losses through both serpentine circuits, insufficient pump flow, channel blockage, and thermal interface gaps or uneven compression. The interfaces here were perfectly bonded; those defects were not simulated.</p><p>This is an illustrative screening study. The flow regime is transitional, although modeled as laminar. A mass-conserving flux reconstruction changed the calculated velocity field by about 22%, so flow refinement, turbulence sensitivity, mesh/time-step studies, and experimental comparison are needed before using these temperatures for design decisions.</p><p>The video compresses one simulated hour into 10 seconds.</p></div></details>'
battery_text = BATTERY_CONTEXT + battery_study_details.split('<div class="study-details-body">', 1)[1].rsplit('</div></details>', 1)[0] + BATTERY_END
simcards = battery_thermal_card() + midnight_card() + study_card(plume_card(), 'plume') + study_card(battery_card(battery_text), 'battery')
midnight_media = video('/assets/videos/midnight-seamless-flow-10s.mp4','/assets/videos/midnight-seamless-flow-poster.png','Public-reference aircraft CFD: Cp and selected native streamlines').replace('<video controls','<video loop controls')
page('midnight-aerodynamics.html','Aircraft aerodynamics: angle sweep & transient wake','Khani Solutions independent aircraft CFD: 0–20 degree angle sweep, full-domain transient wake at 20 degrees, circulation and aerodynamic load histories, native video and OpenFOAM methods.',intro('Independent engineering case study','From public aircraft views to an evolving wake.',MIDNIGHT_SUMMARY)+f'<section class="wrap case-study midnight-study"><p class="study-note">By Mohammadreza Khani, PhD · Khani Solutions · Independent public-source study; not employer or manufacturer analysis.</p><nav class="wake-jump" aria-label="Case study sections"><a href="#transient-wake">Transient wake</a><a href="#transient-wake-results">Wake results</a><a href="#angle-sweep-methods">0°–20° steady sweep</a><a href="#transient-wake-evidence">Data &amp; settings</a></nav>{wake_study()}<h2>Earlier study: 0°–20° steady angle sweep</h2>{sweep_viewer()}<article class="midnight-technical sweep-methods">{SWEEP_TEXT()}</article><details class="study-details"><summary>Earlier 0° pressure-coefficient study — CAD reconstruction, two original grids and technical archive</summary><div class="study-details-body">{midnight_media}<p>{link(MIDNIGHT_POST_URL,"Earlier Cp study on LinkedIn")}</p><p class="quiet">Historical baseline: surface Cp at 0°, with a ten-second camera loop. Its mesh, numerics and force values differ from the later 0–20° study above.</p>{MIDNIGHT_TEXT}</div></details><div class="actions"><a class="button secondary" href="/AISolutions/experience.html#wisk-experience">Wisk / Boeing experience &amp; independent demos →</a><a class="text-link" href="/AISolutions/simulations.html">All analysis &amp; modeling →</a></div></section>')
page('aircraft-plume.html','Thermal-runaway exhaust plume','External hot-gas plume case study: reconstructed aircraft center section, Gmsh mesh, OpenFOAM settings, checks, results and engineering limitations.',study_page(intro,'Thermal-runaway exhaust plume.',PLUME_SUMMARY,video('/assets/videos/aircraft-tr-plume-pencil-10s.mp4','/assets/videos/aircraft-tr-plume-pencil-poster.png','Pencil aircraft overlay, external gas temperature and instantaneous streamlines'),PLUME_TEXT,'/AISolutions/battery-cooling.html','Battery cooling case study'))
page('battery-cooling.html','Battery cooling in a series circuit','Independent FreeCAD and Elmer battery cooling case study with geometry, materials, mesh, transient results and engineering considerations.',study_page(intro,'Battery cooling in a series circuit.',BATTERY_SUMMARY,video('/assets/videos/battery-module-series-10s.mp4','/assets/videos/battery-module-series-poster.png','Battery module temperature and series coolant circuit'),battery_text,'/AISolutions/aircraft-plume.html','External exhaust plume case study'))

page('rocket-cad-cfd.html','Public-data rocket CAD and connected CFD','Independent Blender rocket CAD and verified component-tour film, with a technical plan for aerodynamic CFD, tank pressurization, diffuser flow and system coupling.',rocket_body(intro))
page('lunar-tank-cfd.html','Propellant in motion: lunar tank CFD','Independent Khani Solutions LOX study: 35 coarse 2D OpenFOAM mission windows in transparent 3D CAD, separate 0D ullage pressure, settling and restart results, assumptions and public references.',lunar_body(intro))
simcards = lunar_card() + simcards
simcards += rocket_card()
simcards += ''.join(public_card(sim, link) for sim in sims)
page('simulations.html','Analysis & modeling','Thermal-fluid analysis, CFD, system-level 0D/1D modeling, digital twins, and engineering software by Mohammadreza Khani.',analysis_page(intro, simcards))
# Citation identifiers were read from the author's live Scholar profile.
papers=[
(2025,'A 3D non-human primate digital model for pharmacokinetic prediction of intra-cerebrospinal fluid drug neuraxial dispersion','M. Khani, L. R. Sass, O. Arters, K. Meyer, B. A. Martin','Fluids and Barriers of the CNS','YOwf2qJgpHMC','https://doi.org/10.1186/s12987-025-00723-z','https://pmc.ncbi.nlm.nih.gov/articles/PMC12584216/','Drug delivery'),
(2025,'Computational and biological modeling of IGF1R inhibition for multifocal medulloblastoma','A. G. Almer et al., including M. Khani','Communications Medicine','kNdYIx-mwKoC','https://doi.org/10.1038/s43856-025-00925-4','https://www.nature.com/articles/s43856-025-00925-4','Drug delivery'),
(2025,'An In Vitro Platform for Pharmacokinetic Quantification and Optimization of Cerebrospinal Fluid Filtration and Drug Circulation','L. R. Sass, M. Khani, M. C. Giordano, A. R. McCabe, S. P. Lad, B. A. Martin','Journal of Medical Devices','5nxA0vEk-isC','https://doi.org/10.1115/1.4066862','https://pmc.ncbi.nlm.nih.gov/articles/PMC12529578/','CSF dynamics'),
(2022,'Human in silico trials for parametric computational fluid dynamics investigation of cerebrospinal fluid drug delivery: impact of injection location, injection protocol, and physiology','M. Khani, G. K. R. Burla, L. R. Sass, O. N. Arters, T. Xing, H. Wu, B. A. Martin','Fluids and Barriers of the CNS','LkGwnXOMwfcC','https://doi.org/10.1186/s12987-022-00304-4','','Drug delivery'),
(2020,'Intrathecal catheter implantation decreases cerebrospinal fluid dynamics in cynomolgus monkeys','M. Khani et al.','PLOS ONE','WF5omc3nYNoC','https://doi.org/10.1371/journal.pone.0244090','https://pmc.ncbi.nlm.nih.gov/articles/PMC7773283/','CSF dynamics'),
(2020,'In vitro and numerical simulation of blood removal from cerebrospinal fluid: comparison of lumbar drain to Neurapheresis therapy','M. Khani, L. R. Sass, M. K. Sharp, A. R. McCabe, L. M. Zitella Verbick, S. P. Lad, B. A. Martin','Fluids and Barriers of the CNS','eQOLeE2rZwMC','https://doi.org/10.1186/s12987-020-00185-5','','CSF dynamics'),
(2020,'Non-invasive MRI quantification of cerebrospinal fluid dynamics in amyotrophic lateral sclerosis patients','L. R. Sass, M. Khani et al.','Fluids and Barriers of the CNS','YsMSGLbcyi4C','https://doi.org/10.1186/s12987-019-0164-3','https://pmc.ncbi.nlm.nih.gov/articles/PMC6971921/','CSF dynamics'),
(2020,'Impact of Neurapheresis system on intrathecal cerebrospinal fluid dynamics: a computational fluid dynamics study','M. Khani et al.','Journal of Biomechanical Engineering','zYLM7Y9cAGgC','','','CSF dynamics'),
(2019,'Characterization of intrathecal cerebrospinal fluid geometry and dynamics in cynomolgus monkeys (macaca fascicularis) by magnetic resonance imaging','M. Khani et al.','PLOS ONE','IjCSPb-OGe4C','https://doi.org/10.1371/journal.pone.0212239','','CSF dynamics'),
(2018,'Anthropomorphic model of intrathecal cerebrospinal fluid dynamics within the spinal subarachnoid space: spinal cord nerve roots increase steady-streaming','M. Khani, L. R. Sass, T. Xing, M. Keith Sharp, O. Balédent, B. A. Martin','Journal of Biomechanical Engineering','qjMakFHDy7sC','','','CSF dynamics'),
(2017,'Nonuniform moving boundary method for computational fluid dynamics simulation of intrathecal cerebrospinal flow distribution in a cynomolgus monkey','M. Khani, T. Xing, C. Gibbs, J. N. Oshinski, G. R. Stewart, J. R. Zeller, B. A. Martin','Journal of Biomechanical Engineering','u5HHmVD_uO8C','','','CSF dynamics'),
(2017,'A 3D subject-specific model of the spinal subarachnoid space with anatomically realistic ventral and dorsal spinal cord nerve rootlets','L. R. Sass, M. Khani, G. C. Natividad, R. S. Tubbs, O. Baledent, B. A. Martin','Fluids and Barriers of the CNS','u-x6o8ySG0sC','','','CSF dynamics'),
(2017,'Three-dimensional simulation of a novel rotary-piston engine in the motoring mode','M. Khani, G. Esmaeelzade','Propulsion and Power Research','9yKSN-GCB0IC','https://doi.org/10.1016/j.jppr.2017.07.005','https://www.sciencedirect.com/science/article/pii/S2212540X17300421','Propulsion')]
papers.append((2017,'Theoretical analysis of the conical premixed flame response to upstream velocity disturbances considering flame speed development effects','G. Esmaeelzade, M. Khani, R. Riazi, M. H. Sabour','Propulsion and Power Research','2osOgNQ5qMEC','https://doi.org/10.1016/j.jppr.2017.02.001','https://www.sciencedirect.com/science/article/pii/S2212540X1730007X','Propulsion'))
def publication_rows(records):
 rows = ''
 for paper in sorted(records, key=lambda p: p[0], reverse=True):
  year,title,authors,journal,cite,doi,full,topic = paper
  figure = publication_figure(cite)
  cls = 'paper illustrated-paper' if figure else 'paper text-paper'
  year_label = f'<span class="paper-year">{year}</span>'
  rows += f'<article class="{cls} filter-item" id="{paper_anchor(paper)}" data-category="{e(topic)}">{figure}<div class="paper-copy"><p class="eyebrow">{year_label} · {e(topic)}</p><h3>{e(title)}</h3><p class="authors">{e(authors)}</p><p class="journal">{e(journal)}</p><div class="paper-links">{paper_links(paper, link)}</div></div></article>'
 return rows
paperrows = ''.join(f'<section class="publication-group" data-publication-group id="{anchor}"><div class="section-heading"><p class="eyebrow">{e(label)}</p><h2>{e(heading)}</h2></div><div class="paper-list">{publication_rows(records)}</div></section>' for anchor,label,heading,records in [
 ('journal-articles',f'{len(papers)} journal articles','Peer-reviewed research.',papers),
 ('dissertation','Doctoral research','PhD dissertation.',[DISSERTATION]),
 ('conference-abstracts','3 conference abstracts','Conference contributions.',ABSTRACTS)])
patents='<section class="wrap section publication-ip" id="intellectual-property"><div class="section-heading"><p class="eyebrow">Intellectual property</p><h2>Patent applications &amp; invention disclosures.</h2></div><p class="quiet">Four co-invented, published US patent applications. Drawings are extracted from the original application PDFs, with the publication and application numbers shown for each record.</p>'+intellectual_property(link, showcase=True)+'</section>'
page('publications.html','Publications','Research, illustrated patent applications, invention disclosures, journal articles, and original publication PDFs by Mohammadreza Khani.',intro('Research & publications','From models to published research.','My research focuses on cerebrospinal fluid dynamics, intrathecal drug delivery, patient-specific modeling, and propulsion.',f'<div class="actions">{link(SCHOLAR,"Google Scholar","button scholar-cta",arrow=False)}<a class="button secondary" href="#intellectual-property">Patents &amp; inventions</a><a class="button secondary" href="#journal-articles">Published papers</a><a class="button secondary" href="#scholar-insights">Citation insights</a></div>')+patents+scholar_section(link)+f'<section class="wrap publication-library"><div class="publication-toolbar"><p>{len(papers)} journal articles · 1 dissertation · 3 conference abstracts</p><label class="search-label">Search papers &amp; abstracts<input type="search" data-search placeholder="Search a title, author, or topic"></label></div><p class="quiet">Selected figures come from the original PDFs. Open a figure to inspect it at full size, or follow the publisher, full-text, and Scholar links. Conference abstracts are listed separately.</p><p class="sr-only" role="status" data-search-status></p>{paperrows}<p data-empty hidden>No publications match your search.</p></section>')
roles=[
('Mar 2026 — Present','Boeing / Wisk','Senior Fluid & Thermal Analysis Engineer','Mountain View, California',[
('Battery thermal management','Lead thermal-fluid analysis across battery cells, modules, packs, propulsion, and aircraft systems. Combine hand calculations, 0D/1D system models, and 3D CFD/FEA to evaluate heat generation, coolant distribution, pressure drop, and cooling architecture.'),
('Hardware and safety','Analyze cold plates, heat exchangers, pumps, valves, venting paths, and thermal runaway behavior. Define test requirements and instrumentation plans, correlate simulations with hardware data, and investigate thermal bottlenecks.')]),
('Oct 2025 — Mar 2026','Amazon LEO','Mechanical Engineer III','Seattle, Washington',[
('Spacecraft impact analysis','Led meshing and finite-element modeling of Kuiper spacecraft hardware to evaluate micrometeoroid and orbital debris impact response using Siemens NX/FEMAP.'),
('Automation and verification','Built Python workflows for geometry cleanup, simulation setup, and post-processing. Worked with design and systems teams to define boundary conditions and document model fidelity and structural risks.')]),
('Aug 2024 — Oct 2025','Blue Origin','Fluid & Thermal System Analysis Engineer III','Seattle, Washington',[
('Cryogenic tank pressurization','Modeled LH₂ and LOX tank multiphase flow and conjugate heat transfer in ANSYS Fluent, resolving stratification, ullage condensation, and gas collapse during pressurization. Evaluated diffuser geometry and its effect on ullage response.'),
('Mission thermal-fluid systems','Developed mission gas budgets and transient subsystem analyses in Thermal Desktop, FloCAD, and SINDA/FLUINT. Investigated tank chilldown, insulation, line heat leaks, fuel transfer, and venting.')]),
('Sep 2022 — Aug 2024','Alcyone Therapeutics','Principal Engineer','Boston, Massachusetts',[
('CNS digital twins','Led patient-specific modeling from MRI segmentation of the brain, spinal cord, and nerve roots through meshing and CFD. Integrated cardiac and respiratory wall motion, dynamic mesh, Lagrangian tracking, and multiphase transport for ASO/AAV delivery.'),
('Partner studies and HPC','Directed simulation collaborations with Biogen, Ultragenyx, and Minnetronix on infusion protocols and catheter design. Configured AMD Threadripper PRO and Intel Xeon systems for parallel CFD and in-house computing.')]),
('Dec 2020 — Sep 2022','Alcyone Therapeutics','Senior Engineer','Boston, Massachusetts',[
('Custom OpenFOAM physics','Developed a thermophoretic force model for size-dependent nanoparticle separation across 30–300 nm particles. Used the model to optimize heater geometry and thermal fields for an air-quality sensor.'),
('Experimental comparison','Verified and validated CSF transport models with 3D-printed flow phantoms and tracer dispersion experiments. Compared spatial and temporal concentration predictions with measured data.')]),
('Nov 2019 — Dec 2020','University of Idaho','Postdoctoral Fellow','Moscow, Idaho',[
('MRI-based drug delivery','Developed high-fidelity drug-delivery models in ANSYS Fluent using MRI-derived anatomy, craniospinal compliance, dynamic mesh, injection locations, dispersion, and clearance.')]),
('May 2012 — Jan 2016','National Iranian Oil Company','Mechanical Engineer','Sari, Iran',[
('Mechanical systems and field work','Maintained and repaired pumps, valves, piping, safety valves, and motor-operated valves. Supported preventive maintenance, welding, fabrication, and troubleshooting.'),
('Tank overhaul projects','Defined scope and materials, coordinated technicians and cross-functional teams, and worked with quality and safety groups on inspection findings, surface preparation, coating, and tank modifications.')])]
rolehtml=company_experience(roles,sims,papers,link)
projects=[
('01','MRI to CFD drug-delivery models','Biomedical simulation','Built workflows that connect anatomical segmentation, meshing, physiological flow conditions, and solute transport. Studied how infusion location, protocol, anatomy, and posture affect intrathecal distribution.',['MRI segmentation','Dynamic mesh','ASO / AAV'], 'publications.html','Explore the research'),
('02','Cryogenic pressurization and propellant systems','Aerospace thermal fluids','Combined detailed tank CFD with mission-level system analysis to study condensation, ullage response, gas consumption, thermal stratification, and diffuser performance.',['ANSYS Fluent','Thermal Desktop','SINDA/FLUINT'],'simulations.html','View public simulations'),
('03','Battery cooling architecture','Thermal engineering','Develop multi-fidelity tools to compare coolant networks, pressure drop, cold-plate performance, heat-exchanger sizing, pumping power, and thermal safety across battery systems.',['0D / 1D / 3D','CFD / FEA','Test correlation'],'contact.html','Discuss thermal analysis'),
('04','Nanoparticle thermophoresis solver','Custom CFD development','Added thermophoretic physics to OpenFOAM to resolve particle-size-dependent motion under thermal gradients and support heater design for a microfluidic sensing device.',['OpenFOAM','C++','Particle transport'],'contact.html','Discuss solver development'),
('05','Rotary-piston engine simulation','Propulsion research','Used dynamic mesh to represent semi-sinusoidal chamber motion and study internal flow, motoring cycles, and wall thermal fields. Extended modeling to species transport and fuel spray dynamics.',['Dynamic mesh','ANSYS Fluent','Spray modeling'],'publications.html','Read the engine paper'),
('06','Simulation workflow automation and HPC','Engineering software','Build repeatable geometry, meshing, solver, and post-processing workflows. Configure parallel computing systems to support large CFD studies and frequent engineering iteration.',['Python','HPC','Workflow automation'],'contact.html','Discuss a workflow')]
projecthtml=''.join(f'<article class="card project-card" id="project-{num}"><p class="eyebrow">{num} / {cat}</p><h3>{title}</h3><p>{desc}</p>{pills(tags)}<a class="text-link" href="{url}">{label} <span aria-hidden="true">→</span></a></article>' for num,title,cat,desc,tags,url,label in projects)
page('experience.html','Experience','Professional experience, education, research publications, patent applications, and invention disclosures in aerospace, biomedical CFD, and thermal-fluid engineering.',intro('Career & education','Experience.','The roles, education, research, and simulation methods behind my portfolio.')+f'<section class="wrap experience-content" id="career">{company_navigation()}<p class="experience-hint">Explore related demos, publications, and intellectual property within each company or university.</p>{rolehtml}<details class="experience-extra" id="projects"><summary>Additional technical focus</summary><div class="two-grid">{projecthtml}</div></details></section>')
page('contact.html','Contact','Contact Mohammadreza Khani at Khani Solutions for CFD, thermal-fluid engineering, and simulation projects.',intro('Get in touch','Let’s talk engineering.','Reach out about CFD, thermal-fluid analysis, research collaboration, or engineering software.')+f'''<section class="wrap contact-grid"><article class="contact-person"><img src="../assets/reza-khani-founder-square-original.svg" alt="Mohammadreza Khani" width="886" height="886"><h2>Mohammadreza Khani, PhD</h2><p>Mechanical engineer · Founder of Khani Solutions</p><div class="contact-links"><a href="mailto:mkhani.phd@gmail.com">mkhani.phd@gmail.com</a><a href="tel:+12085960782">(208) 596-0782</a><p>Lewiston, Idaho · USA</p>{link(LINKEDIN,'Connect & follow on LinkedIn')}</div></article><form class="contact-form"><p class="eyebrow">Start a conversation</p><h2>What are you working on?</h2><label>Name<input name="name" autocomplete="name" required></label><label>Email<input name="email" type="email" autocomplete="email" required></label><label>Organization <span class="quiet">(optional)</span><input name="organization" autocomplete="organization"></label><label>Topic<select name="topic"><option>CFD simulation</option><option>Thermal-fluid analysis</option><option>Biomedical modeling</option><option>Engineering software</option><option>AI & engineering automation</option><option>Research collaboration</option><option>Other</option></select></label><label>Message<textarea name="message" rows="5" required></textarea></label><button class="button primary" type="submit">Prepare email ↗</button><p class="quiet">This opens your email app with the details filled in. Send the message from your email app, or email me directly.</p><p role="status" class="quiet" data-form-status></p></form></section>''')
homecards=''.join(f'<a class="overview-card" href="{file}"><img class="entry-icon" src="../assets/icon-{("waves","file-text","gear")[i]}.svg" alt="" width="40" height="40"><div class="entry-copy"><span class="eyebrow sr-only">0{i+1} / {k}</span><h3>{title}</h3><p>{desc}</p><span class="text-link">{action} →</span></div></a>' for i,(file,k,title,desc,action) in enumerate([
('simulations.html','Explore','Analysis & modeling','Explore thermal-fluid studies, CFD, system-level models, digital twins, and the tools behind the work.','Explore analysis'),('publications.html','Read','Research & publications','Browse journal articles on drug delivery, CSF dynamics, biomedical models, and propulsion.','Browse publications'),('experience.html','Explore','Experience','Follow my engineering work across Boeing / Wisk, Amazon LEO, Blue Origin, Alcyone, and academia.','View experience')]))
page('index.html','Mohammadreza Khani — Engineering portfolio','The engineering portfolio of Mohammadreza Khani, PhD: thermal-fluid analysis, modeling, digital twins, publications, and detailed project experience.',f'''<section class="home-hero"><div class="home-hero-inner wrap"><div class="hero-copy"><h1 class="hero-wordmark">Khani Solutions</h1><p class="hero-tagline">Complex physics. <span>Practical engineering.</span></p><p class="lead">I’m a mechanical engineer working across aerospace, thermal systems, and biomedical fluid dynamics. I use CFD, system modeling, and engineering software to understand how things flow, heat up, and perform.</p><div class="actions"><a class="button primary simulation-cta" href="simulations.html">Analysis &amp; modeling</a><a class="button secondary experience-cta" href="experience.html">Experience</a>{link(LINKEDIN,'LinkedIn','button linkedin-cta',arrow=False)}{link(SCHOLAR,'Google Scholar','button secondary scholar-cta',arrow=False)}</div><div class="hero-meta"><span>Based in Lewiston, Idaho</span><span>PhD · University of Idaho</span></div></div><figure class="hero-portrait"><div class="hero-photo"><img src="../assets/reza-khani-founder-original.jpg" alt="Mohammadreza Khani" width="2085" height="3783" fetchpriority="high"></div><figcaption class="portrait-caption"><strong>Mohammadreza Khani</strong><span>Thermal and fluid analysis · CFD · Digital twins</span></figcaption></figure></div></section><section class="career-strip wrap" aria-label="Experience across industry and research"><p class="eyebrow">Collaboration & experience</p><p class="company-strip-hint">Select a logo to explore my work and related demos.</p><div class="company-row">{overview_company_logos()}</div></section><section class="wrap section portfolio-entries"><div class="section-heading"><p class="eyebrow">Explore my work</p><h2 class="sr-only">The work behind the models.</h2></div><div class="three-grid">{homecards}</div></section><section class="wrap about-section"><div><p class="eyebrow">My approach</p><h2>From physical systems<br>to useful predictions.</h2></div><div><p>I work across detailed 3D simulations, reduced-order system models, and experimental comparison. My projects include cryogenic tank pressurization, battery cooling architecture, spacecraft impact analysis, and patient-specific CNS drug-delivery models.</p><p>Through Khani Solutions, I bring engineering analysis and software development together to make complex simulation workflows repeatable and useful.</p><a class="text-link" href="contact.html">Get in touch →</a></div></section>''')
page('automation.html','AI & engineering automation','Websites, paperwork automation, scheduling and connected tools for local businesses, by Mohammadreza Khani, PhD, based in Lewiston, Idaho.',(ROOT/'scripts/templates/automation.html').read_text())
print(f'Built 10 pages, 3 hosted simulations and 1 CAD foundation, {len(sims)} LinkedIn CFD posts, {len(papers)} journal articles, {len(roles)} roles, {len(projects)} projects.')
