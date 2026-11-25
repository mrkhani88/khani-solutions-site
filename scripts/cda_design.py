"""Conceptual aircraft battery coolant distribution in FreeCAD."""

from case_studies import video

TITLE = 'From a 6 kW heat load to a FreeCAD cooling loop for an electric aircraft battery pack'
DESCRIPTION = ('A 60-second FreeCAD walkthrough of coolant distribution for six battery modules, '
               'from the heat-load calculation and tubing layout to component screening.')
GALLERY_ID = 'cda-aircraft-battery-cooling'
URL = f'/AISolutions/{GALLERY_ID}.html'
VIDEO = f'/assets/videos/{GALLERY_ID}.mp4'
POSTER = f'/assets/videos/{GALLERY_ID}-poster.jpg'
MEDIA_LABEL = 'FreeCAD walkthrough of a six-module aircraft battery cooling distribution assembly'


def gallery_card():
    return f'''<article id="{GALLERY_ID}" class="simulation-card filter-item" data-category="Thermal" data-method="geometry" data-analysis-company-ids="independent-work">
{video(VIDEO, POSTER, MEDIA_LABEL, preload='none', webm=False)}
<div class="card-copy">
<p class="eyebrow">Khani Solutions · Battery thermal design</p>
<h2>Aircraft battery cooling distribution</h2>
<p>Watch a 6 kW design basis turn into a six-branch FreeCAD coolant loop with routed tubing, a candidate pump, balancing valves, and instrumentation.</p>
<div class="pills"><span>FreeCAD</span><span>Hydraulic sizing</span><span>Liquid cooling</span></div>
<p class="study-note">Conceptual circulation layout · 60-second CAD walkthrough.</p>
</div>
<div class="card-bottom"><a class="text-link" href="{URL}">Full walkthrough &amp; design notes →</a></div>
</article>'''


def study_body(intro):
    header = intro('Khani Solutions · <a href="https://khanisolutions.com">khanisolutions.com</a>',
                   TITLE, DESCRIPTION)
    return header + f'''<section class="wrap case-study" aria-label="Video and design notes">
{video(VIDEO, POSTER, MEDIA_LABEL, webm=False)}
<p class="study-note">Conceptual circulation layout · Sustained operation at 6 kW requires a separate heat sink.</p>
<div class="study-details-body">
<p>In this 60-second walkthrough, I show how I sized and laid out a liquid cooling distribution assembly for six battery modules. The study combines hand calculations, prior cold-plate CFD, catalog screening, and AI-assisted design work in FreeCAD.</p>

<h2>Define the heat load and flow path</h2>
<p>Each module was sized for 960 W of battery heat and 40 W of DC/DC converter losses. That gives <strong>6 × 1,000 W = 6 kW</strong>. The layout uses six parallel branches, with the top and bottom cold plates in series within each module.</p>

<h2>Size the coolant flow</h2>
<p>I used 60% propylene glycol by volume, consistent with the prior cold-plate study. With a 30°C inlet, a 35°C return limit, and a specific heat of 3.383 kJ/(kg·K), the energy balance gives <strong>ṁ = 6 ÷ (3.383 × 5) = 0.355 kg/s minimum</strong>. I carried forward the cold-plate study’s nominal flow of <strong>41.4 L/min total</strong>, or <strong>6.90 L/min per branch</strong>.</p>
<p><a href="https://ingredi.com/content/pdfs/DOWFROST_Manual.pdf">Dow engineering guide</a></p>

<h2>Route the tubing and budget pressure loss</h2>
<p>I drew the centerlines around the existing pack ports in FreeCAD and sized the main lines, bank headers, and module branches to <strong>25, 18, and 14 mm ID</strong>. Darcy–Weisbach, fitting allowances, and the prior plate-pair CFD estimate of <strong>10.93 kPa</strong> gave <strong>44.7 kPa</strong> along one complete flow path. A 20% allowance brought the pump screening duty to <strong>53.6 kPa at 41.4 L/min</strong>.</p>
<p><a href="https://www.energy.gov/ehss/articles/doe-hdbk-10123-92">DOE fluid-flow handbook</a></p>

<h2>Screen the pump and expansion vessel</h2>
<p>The <strong>Pierburg CWA400 PWM (7.07223.10.0)</strong> was a candidate because it offers variable-speed control and its published curve shows headroom at the target flow. That curve uses 50/50 water/glycol at 80°C and 12.5 V, so the PG60 duty still needs verification. For the vessel, 10 L of coolant expanding from 0°C to 60°C gave <strong>0.376 L</strong> of expansion. I placed a <strong>Reflex S 2 (8707700)</strong> envelope at pump suction as a 2 L packaging reference. Its published glycol guidance goes up to 50%.</p>
<p><a href="https://www.tecomotive.de/download/datasheets/CWA400_PWM_EN.pdf">Pump curve</a> · <a href="https://reflex-winkelmann.com/ee/tooted/8707700">Vessel data</a></p>

<h2>Add balancing, instrumentation, and service access</h2>
<p>The catalog shortlist included <strong>IMI TA STAD DN15</strong> valves to trim branch flow, <strong>Swagelok SS-65TS16</strong> ball valves for isolation, and a <strong>Spirax Sarco Fig 36HP</strong> Y-strainer to protect the plate passages. <strong>WIKA A-10</strong> transmitters monitor pressure, an <strong>ifm SM8000</strong> meters total flow, and two <strong>Bosch Motorsport NTC M12</strong> probes track supply and return temperature. The layout also reserves space for <strong>Gates Green Stripe</strong> hose, fill, bleed, drain, and relief connections.</p>
<p><a href="https://assets.imi-hydronic.com/Documents/Catalogues/English_International/PDF_low/STAD_PN25_EN_low.pdf">Balancing valve</a> · <a href="https://www.ifm.com/my/en/product/SM8000">Flowmeter</a> · <a href="https://www.bosch-motorsport.com/products/sensors/temperature/temperature-sensor-ntc-m12/">Temperature probes</a></p>

<p>The video shows the actual FreeCAD drafting, from centerlines and tube sweeps to component placement. I imported supplier STEP geometry for the Bosch probes and used editable envelopes for the pump, vessel, and service hardware.</p>
<p class="analysis-keywords">#ThermalManagement #ElectricAircraft #FreeCAD #BatteryEngineering</p>
</div>
<div class="actions">
<a class="button secondary" href="{VIDEO}" download>Download the walkthrough ↓</a>
<a class="text-link" href="/AISolutions/simulations.html#{GALLERY_ID}">All analysis &amp; modeling →</a>
</div>
</section>'''
