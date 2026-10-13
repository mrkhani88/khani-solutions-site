"""Public CAD foundation, separate from completed CFD and employer deliverables."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
TEXT=(ROOT/'scripts/content/rocket-cad-cfd.html').read_text()
TITLE='Public-data rocket CAD and connected CFD'
SUMMARY='An editable Falcon 9-inspired assembly connects exterior aerodynamics, wall heat transfer, multiphase tank pressurization and diffuser hardware through one documented public-data geometry foundation.'
SRC='/assets/videos/falcon9-upright-component-tour.mp4'
POSTER='/assets/videos/falcon9-upright-component-tour-poster.png'
URL='/AISolutions/rocket-cad-cfd.html'
def media(preload='metadata'):
 return f'<div class="simulation-media rocket-media"><video loop controls playsinline preload="{preload}" poster="{POSTER}" aria-label="Upright public-data rocket CAD assembly and named component tour"><source src="{SRC}" type="video/mp4">Your browser does not support this video. <a href="{SRC}">Download the CAD film</a>.</video></div>'
def experience_demo():
 return f'<article class="company-demo rocket-demo"><h4>Public-data rocket CAD &amp; connected CFD plan</h4><p>Editable rocket assembly with solid component close-ups. The case study connects the completed CAD to planned external aerodynamics, cryogenic tank pressurization, diffuser flow and system gas budgets.</p>{media("none")}<a class="text-link" href="{URL}">Full technical case study →</a><p class="quiet">Independent Falcon 9-inspired concept · CAD complete; rocket CFD planned.</p></article>'
def gallery_card():
 return f'<article id="rocket-cad-cfd" class="simulation-card filter-item rocket-demo" data-category="Aerospace" data-method="geometry" data-analysis-company-ids="blue-origin-experience"><div class="card-copy"><p class="eyebrow">CAD / Connected analysis plan</p><h2>{TITLE}</h2><p>{SUMMARY}</p><div class="pills"><span>Blender 5.0.1</span><span>Python</span><span>Public references</span></div><p class="analysis-status">CAD and film complete · Aerodynamic, tank and diffuser CFD planned.</p><p class="study-note">Independent Khani Solutions work. Related to cryogenic methods in the Blue Origin experience section; not Blue Origin hardware or a manufacturer model.</p></div>{media("none")}<div class="card-bottom"><a class="text-link" href="{URL}">Full technical case study →</a><a class="text-link" href="/AISolutions/experience.html#blue-origin-experience">Related experience →</a><a class="text-link" href="{SRC}" download>Download CAD film ↓</a><small>42.4-second geometry tour · No solver fields</small></div></article>'
def study_body(intro):
 return intro('Independent aerospace study','Public-data rocket CAD.<br>A foundation for connected CFD.',SUMMARY)+f'<section class="wrap case-study rocket-case"><p class="study-note">By Mohammadreza Khani, PhD · Khani Solutions · Completed CAD / planned physics</p>{media()}<p class="quiet">A fixed, upright 42.4-second loop: assembly, named solid-component close-ups, and disassembly. Read the build details and connected-analysis plan below.</p>{TEXT}<div class="actions"><a class="button secondary" href="/AISolutions/experience.html#blue-origin-experience">Blue Origin experience &amp; independent demos →</a><a class="text-link" href="/AISolutions/simulations.html#rocket-cad-cfd">All analysis &amp; modeling →</a></div></section>'
