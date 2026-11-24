"""Independent FreeCAD reference study of two EV battery cooling layouts."""

from case_studies import video

TITLE = 'AI-assisted CAD drafting for high-voltage EV battery cooling'
DESCRIPTION = ('A FreeCAD walkthrough of a Rivian R1T-style flat cold plate and '
               'a Tesla Model S P85-style scalloped cooling ribbon, from blank sketches to assembly.')
URL = '/AISolutions/ev-battery-cooling-freecad.html'
VIDEO = '/assets/videos/ev-battery-cooling-freecad.mp4'
POSTER = '/assets/videos/ev-battery-cooling-freecad-poster.jpg'
MEDIA_LABEL = 'FreeCAD walkthrough of the Rivian-style flat plate and Tesla-style scalloped cooling ribbon'
GALLERY_ID = 'ev-battery-cooling-freecad'


def gallery_card():
    return f'''<article id="{GALLERY_ID}" class="simulation-card filter-item" data-category="Thermal" data-method="geometry" data-analysis-company-ids="independent-work">
{video(VIDEO, POSTER, MEDIA_LABEL, preload='none', webm=False)}
<div class="card-copy">
<p class="eyebrow">Khani Solutions · Battery thermal design</p>
<h2>EV battery cooling in FreeCAD</h2>
<p>A Rivian R1T-style plate cools through the cell ends, while a Tesla Model S P85-style scalloped ribbon runs along the cell sidewalls. Watch both designs take shape from blank sketches.</p>
<div class="pills"><span>FreeCAD</span><span>AI-assisted drafting</span><span>Liquid cooling</span></div>
<p class="study-note">Independent reference geometry based on public sources.</p>
</div>
<div class="card-bottom"><a class="text-link" href="{URL}">Full walkthrough &amp; technical notes →</a></div>
</article>'''


def study_body(intro):
    header = intro('Khani Solutions · Mohammadreza Khani, PhD', TITLE,
                   'Rivian R1T vs. Tesla Model S P85')
    return header + f'''<section class="wrap case-study" aria-label="Video and engineering notes">
{video(VIDEO, POSTER, MEDIA_LABEL, webm=False)}
<p class="study-note">Silent FreeCAD walkthrough · Independent reconstruction using public references and illustrative dimensions.</p>
<div class="study-details-body">
<p>Where should you pull heat out of a cylindrical battery cell? In this FreeCAD walkthrough, I worked through two approaches from a blank sketch. The Rivian-style plate collects heat through the <strong>cell ends</strong>. The Tesla-style ribbon collects it through the <strong>cell sidewalls</strong>.</p>

<h2>Rivian R1T Quad · 141 kWh in FEV’s benchmark</h2>
<p>One flat liquid cold plate sits between two cell stacks, so both faces of the plate collect heat. This gives both stacks a shared cooling surface and preserves a thin module layout. Rivian’s patent shows counterflow passages and fins placed selectively downstream to improve temperature uniformity as the coolant warms. The manufacturing challenges are keeping both contact faces flat, sealing the plate, and maintaining good thermal contact across the stacks.
<a href="https://benchmarking.fev.com/img/cms/TechNuggets/2024-08-13_TechNuggets_Rivian_R1T_Grey.pdf#page=5">FEV battery specifications</a> · <a href="https://benchmarking.fev.com/img/cms/TechNuggets/2024-08-13_TechNuggets_Rivian_R1T_Grey.pdf#page=4">FEV module layout</a> · <a href="https://patents.google.com/patent/US20200153062A1/en">Rivian patent</a></p>

<h2>Tesla Model S P85 · 85 kWh original rating</h2>
<p>A flattened coolant ribbon winds between staggered rows of 18650 cells. The scallops follow the cylindrical cans, increasing the sidewall contact area while fitting into the gaps between rows. The challenge is holding that fit across many cells while bending the tube without constricting its internal passages. The module loops receive coolant in parallel, so the manifolds must distribute flow evenly.
<a href="https://www.tesla.com/sites/default/files/2012_model_s_specifications_and_features.pdf">Tesla specifications</a> · <a href="https://www.govinfo.gov/content/pkg/FR-2021-10-05/pdf/2021-21416.pdf#page=2">NHTSA cooling-system description</a> · <a href="https://patents.google.com/patent/US20080311468A1/en">Tesla ribbon patent application</a></p>

<h2>The thermal and hydraulic tradeoff</h2>
<p>A wider flow area can lower coolant velocity in the flat plate, while shallow passages, ports, turns, and fins can still contribute significant pressure loss. In the ribbon, small passages and long runs can raise pressure drop. Parallel module feeds split the pack flow among the branches. At a given flow rate, lower pressure drop reduces hydraulic pump power. To compare cooling performance, I’d match the heat load, coolant, and inlet temperature, then measure <strong>peak cell temperature and cell-to-cell temperature spread at equal pump power</strong>. This video shows the CAD build and geometry checks.
<a href="https://www.energy.gov/documents/doe-hdbk-1012-92vol3">DOE fluid-flow handbook</a></p>

<h2>How AI assisted the build</h2>
<p>I used AI to interpret public drawings, establish reference dimensions, plan the feature order, and check the fit and coolant connections. The video shows the actual FreeCAD operations from clean sheet to assembly, including the Rivian channel pocket and hollow ports, the Tesla ribbon’s four passages cut one at a time, the repeated <strong>R9.25 mm scallops</strong>, and the two staggered rows patterned from a single <strong>Ø18 mm cell</strong>.</p>
<p class="analysis-keywords">#FreeCAD #BatteryThermalManagement #EVEngineering #AIAssistedDesign</p>
</div>
<div class="actions">
<a class="button secondary" href="{VIDEO}" download>Download the walkthrough ↓</a>
<a class="text-link" href="/AISolutions/simulations.html#{GALLERY_ID}">All analysis &amp; modeling →</a>
</div>
</section>'''
