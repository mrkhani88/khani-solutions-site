"""Independent LOX mission-window study; associated only with Blue Origin methods."""
from pathlib import Path

ASSETS = '/assets/studies/lunar-tank'
URL = '/AISolutions/lunar-tank-cfd.html'
TITLE = 'Propellant in motion: a cryogenic tank through a lunar mission'
SUMMARY = 'Ground filling, engine cutoff, slosh, settling and restart: native 2D OpenFOAM liquid fields inside transparent 3D CAD, with fixed-scale plots and a schematic mission map.'


def media(preload='metadata'):
    return f'<div class="lunar-tank-media"><video controls playsinline preload="{preload}" poster="{ASSETS}/Poster.jpg" aria-label="Generic LOX tank through thirty-five mission windows, with liquid inventory, separate zero-dimensional ullage pressure, outlet liquid fraction and axial load plots"><source src="{ASSETS}/Propellant_In_Motion.mp4" type="video/mp4">Your browser does not support this video. <a href="{ASSETS}/Propellant_In_Motion.mp4">Download the film</a>.</video></div>'


def experience_demo():
    return f'<article class="company-demo"><h4>Propellant in motion: filling, settling &amp; restart</h4><p>{SUMMARY}</p>{media("none")}<a class="text-link" href="{URL}">Video, numerical results &amp; technical case study →</a><p class="quiet">Independent generic LOX study · Coarse 2D VOF + separate 0D pressure · Public references and assumed inputs.</p></article>'


def gallery_card():
    return f'<article id="lunar-tank-cfd" class="simulation-card filter-item" data-category="Aerospace" data-method="cfd" data-analysis-company-ids="blue-origin-experience"><div class="card-copy"><p class="eyebrow">Multiphase CFD / Cryogenic systems</p><h2>{TITLE}</h2><p>{SUMMARY}</p><div class="pills"><span>OpenFOAM 2512</span><span>Blender CAD</span><span>Python</span></div><p class="analysis-status">35 completed analysis windows · Exploratory screening model.</p><p class="study-note">Independent Khani Solutions work. Related only to the cryogenic methods in the Blue Origin experience section; not employer hardware or results.</p></div>{media("none")}<div class="card-bottom"><a class="text-link" href="{URL}">Full technical case study →</a><a class="text-link" href="/AISolutions/experience.html#blue-origin-experience">Blue Origin experience →</a><small>108-second silent film · 2D fields in 3D CAD</small></div></article>'


def study_body(intro):
    text = (Path(__file__).parent / 'content/lunar-tank.html').read_text()
    return intro('Khani Solutions · Independent cryogenic CFD study', 'Propellant in motion.<br>From ground fill to lunar restart.', SUMMARY) + f'<section class="wrap case-study lunar-tank-study"><p class="study-note">By Mohammadreza Khani, PhD · Public references and assumed inputs · Not Blue Origin hardware, a Blue Moon MK2 reconstruction or employer project results.</p>{media()}<p class="quiet">108 seconds · Silent · 1080 × 1350. Short analysis windows and coast intervals are compressed for presentation.</p><div class="actions"><a class="button secondary" href="{ASSETS}/Propellant_In_Motion.mp4" download>Download full film ↓</a><a class="text-link" href="{ASSETS}/Propellant_In_Motion_60s.mp4" download>60-second social cut (1.8×) ↓</a><a class="text-link" href="#model-scope">Read the model scope →</a></div>{text}<div class="actions"><a class="button secondary" href="/AISolutions/experience.html#blue-origin-experience">Blue Origin experience &amp; independent demos →</a><a class="text-link" href="/AISolutions/rocket-cad-cfd.html">Earlier public-data rocket CAD foundation →</a></div></section>'
