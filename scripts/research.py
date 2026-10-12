"""Shared public research records for Publications and Experience.

Scholar identifiers were checked on 2026-10-11. Disclosure titles and
submission dates come from the supplied resume, not from patent records.
"""
from html import escape as e
from pathlib import Path
import json

MEDIA = json.loads((Path(__file__).parent / 'content/research-media.json').read_text())

def paper_links(paper, link):
 cite, doi, full = paper[4:7]
 source = MEDIA['papers'].get(cite, {})
 doi, full = source.get('doi') or doi, source.get('full_text') or full
 actions = link(scholar_record(cite), 'Scholar record') if cite else ''
 if doi: actions += link(doi, 'Publisher / DOI')
 if full: actions += link(full, 'Read full text')
 if source.get('pdf'): actions += link(source['pdf'], 'Original PDF')
 return actions

def source_figure(source, related=False):
 prefix = 'Related published research · ' if related else ''
 page = source['extraction']['page']
 return f'''<figure class="publication-figure"><a class="figure-preview" href="{e(source['asset'])}" target="_blank" rel="noopener" aria-label="Enlarge {e(source['alt'])}"><img src="{e(source['asset'])}" alt="{e(source['alt'])}" width="{source['width']}" height="{source['height']}" loading="lazy" decoding="async"><span>Enlarge figure ↗</span></a><figcaption><strong>{prefix}{e(source['figure'])}</strong> · {e(source['caption'])}<span class="figure-credit"><a href="{e(source['pdf'])}#page={page}" target="_blank" rel="noopener">Original PDF · page {page} ↗</a><span>{e(source['credit'])}</span></span></figcaption></figure>'''

def publication_figure(cite):
 source = MEDIA['papers'].get(cite)
 return source_figure(source) if source else ''

SCHOLAR = 'https://scholar.google.com/citations?user=ipaKdZ4AAAAJ&hl=en'

def scholar_record(cite):
 return f'https://scholar.google.com/citations?view_op=view_citation&hl=en&user=ipaKdZ4AAAAJ&citation_for_view=ipaKdZ4AAAAJ:{cite}'

def paper_anchor(paper):
 return 'paper-' + (paper[4] or 'premixed-flame')

# Distinguish publication dates from the dates of the underlying research.
RESEARCH_GROUPS = {
 'Alcyone Therapeutics': ['YOwf2qJgpHMC','kNdYIx-mwKoC','5nxA0vEk-isC','LkGwnXOMwfcC'],
 'University of Idaho': ['WF5omc3nYNoC','eQOLeE2rZwMC','YsMSGLbcyi4C','zYLM7Y9cAGgC','IjCSPb-OGe4C','qjMakFHDy7sC','u5HHmVD_uO8C','u-x6o8ySG0sC'],
 'Iran University of Science & Technology': ['2osOgNQ5qMEC','9yKSN-GCB0IC'],
}

# Tuple shape matches the journal records in build_portfolio.py.
DISSERTATION = (2019,
 'Magnetic Resonance Image-based Numerical Modeling of Cerebrospinal Fluid Dynamics: Application to Filtration and Intrathecal Drug Delivery',
 'Mohammadreza Khani', 'University of Idaho · PhD dissertation', 'ufrVoPGSRksC', '',
 'https://verso.uidaho.edu/esploro/outputs/doctoral/MAGNETIC-RESONANCE-IMAGE-BASED-NUMERICAL-MODELING-OF/996638239601851', 'Dissertation')
ABSTRACTS = [
 (2025, 'A novel approach for treatment of rett syndrome and other x-linked disorders through miREX gene regulation combined with FalconTM precision CSF delivery',
  'C. N. Dennys et al., including M. Khani', 'Human Gene Therapy 36 (3–4), E280 · Conference abstract', 'ULOm3_A8WrAC', '', '', 'Conference abstract'),
 (2024, 'The miREX Platform Technology Allows for Highly Efficacious X-Reactivation for Treatment of X-linked Disorders',
  'C. Dennys et al., including M. Khani', 'Molecular Therapy 32 (4), 317–318 · Conference abstract', '3fE2CSJIrl8C', '', '', 'Conference abstract'),
 (2024, 'Leveraging In Silico and In Vitro Modeling for Optimization of Intrathecal AAV9 Delivery to the Brain: Validation in Nonhuman Primates and Translation to Human Rett Syndrome Patient Anatomy',
  'B. Martin et al., including M. Khani', 'Molecular Therapy 32 (4), 746–747 · Conference abstract', 'MXK_kJrjxJIC', '', '', 'Conference abstract'),
]

PATENTS = [
 ('Fluid delivery systems and methods of treatment', 'US Patent App. 17/748,199', 'hqOjcs7Dif8C', 'Alcyone Therapeutics'),
 ('Fluid delivery systems and methods of treatment', 'US Patent App. 17/748,221', 'UebtZRa9Y70C', 'Alcyone Therapeutics'),
 ('Fluid delivery systems and methods of treatment', 'US Patent App. 17/748,246', 'Se3iqnhoufwC', 'Alcyone Therapeutics'),
 ('Systems, catheters, and methods for treating along the central nervous system', 'US Patent App. 17/583,814', 'roLk4NBRz8UC', 'University of Idaho'),
]
DISCLOSURES = [
 ('Dual-lumen neurapheresis catheter for equal flow at aspiration and return ports.', 'Submitted October 24, 2018 · University of Idaho', 'Martin BA, Khani M'),
 ('Subject-specific prediction and optimization of intrathecal (IT) drug therapy based on medical imaging and computational modeling.', 'Submitted March 2020 · University of Idaho', 'Martin BA, Khani M'),
]

def intellectual_property(link, company=None, showcase=False):
 records = [p for p in PATENTS if company is None or p[3] == company]
 disclosures = DISCLOSURES if company in [None, 'University of Idaho'] else []
 html = '<div class="ip-showcase">' if showcase else '<div class="research-list ip-list">'
 for title, num, cite, owner in records:
  source = MEDIA['patents'][cite]
  visual = source_figure(source) if showcase else ''
  cls, heading = ('ip-card', 'h3') if showcase else ('research-item', 'h4')
  actions = link(source['record'], 'Published patent record') + link(source['pdf'], 'Original patent PDF')
  html += f'<article class="{cls}" id="application-{cite}">{visual}<div class="ip-copy"><p class="eyebrow">Published patent application · 2022</p><p class="publication-code">{e(source["number"])}</p><{heading}>{e(title)}</{heading}><p class="research-meta">{e(num)}</p><p class="research-meta">Co-inventor with Bryn Martin and collaborators.</p><div class="paper-links">{actions}</div></div></article>'
 html += '</div>'
 if showcase and disclosures:
  html += '<div class="disclosure-heading"><p class="eyebrow">From research to invention</p><h3>Submitted invention disclosures.</h3><p class="quiet">Titles and submission dates are recorded in my résumé. The images below come from related published research; public disclosure documents and record numbers are not available.</p></div><div class="ip-showcase disclosure-showcase">'
 elif disclosures:
  html += '<div class="research-list ip-list">'
 for i, (title, date, authors) in enumerate(disclosures, 1):
  cite = ['zYLM7Y9cAGgC', 'LkGwnXOMwfcC'][i-1]
  source = MEDIA['papers'][cite]
  visual = source_figure(source, related=True) if showcase else ''
  cls, heading = ('ip-card', 'h4') if showcase else ('research-item', 'h4')
  actions = f'<a class="text-link" href="/AISolutions/publications.html#paper-{cite}">Related published paper →</a>' if showcase else ''
  html += f'<article class="{cls}" id="disclosure-{i}">{visual}<div class="ip-copy"><p class="eyebrow">Submitted invention disclosure</p><{heading}>{e(title)}</{heading}><p class="research-meta">{e(authors)}</p><p class="research-meta">{e(date)}</p><div class="paper-links">{actions}</div></div></article>'
 return html + ('</div>' if disclosures else '')

def research_item(paper, link):
 year, title, authors, journal, cite, doi, full, topic = paper
 actions = paper_links(paper, link)
 return f'<article class="research-item"><p class="eyebrow">{year} · {e(topic)}</p><h4>{e(title)}</h4><p class="research-meta">{e(authors)}</p><p class="research-meta">{e(journal)}</p><div class="paper-links">{actions}<a class="text-link" href="/AISolutions/publications.html#{paper_anchor(paper)}">Publication details →</a></div></article>'

def research_disclosure(label, count, context, contents, company):
 return f'<details class="company-research-group"><summary><span class="research-closed">View {label}</span><span class="research-open">Hide {label}</span><span class="demo-count">{count}<span class="sr-only"> for {e(company)}</span></span></summary><div class="company-research-body"><p class="demo-context">{e(context)}</p>{contents}</div></details>'

def related_research(company, papers, link):
 if company not in RESEARCH_GROUPS: return ''
 by_cite = {p[4]: p for p in papers}
 selected = [by_cite[c] for c in RESEARCH_GROUPS[company]]
 context = {
  'Alcyone Therapeutics': 'Drug-delivery and CSF research connected to this work, including later publications. Publication years can follow the period when the research was carried out.',
  'University of Idaho': 'Publications from my doctoral and postdoctoral research in MRI-based CSF modeling, moving boundaries, anatomy, filtration, and intrathecal drug delivery.',
  'Iran University of Science & Technology': 'My master’s combustion research led to the premixed-flame paper published in 2017. The rotary-piston engine study is included as related propulsion research.',
 }[company]
 extras = [DISSERTATION] if company == 'University of Idaho' else []
 html = research_disclosure('publications', f'{len(selected)} papers' + (' + dissertation' if extras else ''), context,
  '<div class="research-list">' + ''.join(research_item(p, link) for p in extras + selected) + '</div><a class="text-link company-research" href="/AISolutions/publications.html">All publications →</a>', company)
 if company == 'Alcyone Therapeutics':
  html += research_disclosure('conference abstracts', '3 abstracts', 'Conference abstracts listed separately from full journal articles; linked to their original Scholar records.',
   '<div class="research-list">' + ''.join(research_item(p, link) for p in ABSTRACTS) + '</div>', company)
 if company in ['Alcyone Therapeutics', 'University of Idaho']:
  count = '3 applications' if company == 'Alcyone Therapeutics' else '1 application + 2 disclosures'
  label = 'patent applications' if company == 'Alcyone Therapeutics' else 'patents &amp; disclosures'
  context = 'Co-invented fluid-delivery patent applications, with public records linked below.' if company == 'Alcyone Therapeutics' else 'Co-invented catheter patent application and submitted invention disclosures. Disclosure titles and submission dates are listed in my résumé.'
  html += research_disclosure(label, count, context,
   intellectual_property(link, company), company)
 return html
