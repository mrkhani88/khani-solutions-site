"""Conceptual manual balancing valve for an aircraft battery coolant branch."""

from case_studies import video

TITLE = 'Designing a battery coolant balancing valve in FreeCAD'
DESCRIPTION = ('From 6.90 L/min to a 2.27 mm estimated needle lift in one of six '
               'parallel coolant branches for an electric-aircraft battery pack.')
GALLERY_ID = 'battery-coolant-balancing-valve'
URL = f'/AISolutions/{GALLERY_ID}.html'
VIDEO = f'/assets/videos/{GALLERY_ID}.mp4'
POSTER = f'/assets/videos/{GALLERY_ID}-poster.jpg'
MEDIA_LABEL = 'FreeCAD walkthrough of a manual balancing valve and its placement in the Module 2 coolant branch'
CDA_URL = '/AISolutions/cda-aircraft-battery-cooling.html'


def gallery_card():
    return f'''<article id="{GALLERY_ID}" class="simulation-card filter-item" data-category="Thermal" data-method="geometry" data-analysis-company-ids="independent-work">
{video(VIDEO, POSTER, MEDIA_LABEL, preload='none', webm=False)}
<div class="card-copy">
<p class="eyebrow">Khani Solutions · Battery thermal design</p>
<h2>Battery coolant balancing valve</h2>
<p>Size a manual needle valve for 6.90 L/min of coolant and see how the 2.27 mm estimated starting lift fits into the installed branch concept.</p>
<div class="pills"><span>FreeCAD</span><span>Valve design</span><span>Liquid cooling</span></div>
<p class="study-note">Conceptual valve sizing · 42.5-second CAD walkthrough.</p>
</div>
<div class="card-bottom"><a class="text-link" href="{URL}">Full walkthrough &amp; design notes →</a></div>
</article>'''


def study_body(intro):
    header = intro('Khani Solutions · <a href="https://khanisolutions.com">khanisolutions.com</a>',
                   TITLE, DESCRIPTION)
    return header + f'''<section class="wrap case-study" aria-label="Video and design notes">
{video(VIDEO, POSTER, MEDIA_LABEL, webm=False)}
<p class="study-note">Conceptual sizing · The calculated lift is a starting estimate for flow testing.</p>
<div class="study-details-body">
<p>I designed this manual balancing valve for one of six parallel coolant branches in an electric-aircraft battery pack concept. The 42.5-second video shows the valve assembly and installation concept on the Module 2 branch, a schematic cutaway of the flow path, and a 15-second FreeCAD build walkthrough.</p>
<p><a href="{CDA_URL}">See the six-branch coolant distribution design</a></p>

<h2>Set the flow requirement</h2>
<p>One branch needs <strong>6.90 L/min</strong> of 60% propylene glycol at <strong>30°C</strong>, with <strong>6.0 kPa</strong> allocated to the valve. Using a specific gravity of 1.043, the target flow coefficient is <strong>Kᵥ = 0.414 × √(1.043 ÷ 0.060) = 1.73 m³/h</strong>.</p>

<h2>Lay out the valve body</h2>
<p>The <strong>Ø14 mm inlet and outlet</strong> match the branch bore. Coolant enters from the bottom and exits through a 90° side outlet. The <strong>Ø36 mm body</strong> leaves <strong>7 mm of nominal wall</strong> around the <strong>Ø22 mm chamber</strong>, before accounting for port intersections and other local features.</p>

<h2>Size the seat and needle</h2>
<p>Using <strong>Q = CᴅA√(2Δp/ρ)</strong>, an assumed discharge coefficient of <strong>0.62</strong>, and <strong>6.0 kPa across the seat</strong>, I calculated a required opening of <strong>54.7 mm²</strong>. A <strong>Ø12 mm seat</strong> and <strong>45° needle cone</strong> turn axial motion into a ring-shaped flow area. Solving for that area gives <strong>2.27 mm of starting lift</strong>.</p>

<h2>Design the stem, handwheel, and stops</h2>
<p>The handwheel moves a <strong>Ø8 mm stem</strong> and needle together. The dry guide sets the <strong>0.50 mm lower stop</strong>, and a collar limits lift to <strong>3.00 mm</strong>. With a proposed <strong>1 mm/rev</strong> adjuster, the starting setting is <strong>1.77 turns above the lower stop</strong>.</p>

<h2>Design the removable bonnet and seals</h2>
<p>The <strong>Ø44 mm bonnet</strong> provides access to the needle and supports the stem seal. An <strong>Ø29 mm face gasket</strong> seals the stationary body joint. A separate <strong>8 × 2.2 mm O-ring envelope</strong> represents the seal around the moving stem.</p>

<h2>Retain the bonnet</h2>
<p>Four <strong>M4 screw envelopes</strong> sit on a <strong>Ø34 mm bolt circle</strong>. The model has <strong>Ø4.4 mm bonnet clearance holes</strong> and <strong>Ø3.3 mm blind tap-drill envelopes</strong> in the body.</p>

<h2>Check the lift estimate</h2>
<p>Reserving <strong>0.5 kPa</strong> for the ports and turn raised the estimated lift from <strong>2.27 to 2.38 mm</strong>, still within the modeled travel. FreeCAD reported <strong>zero invalid shapes across all ten assembly parts</strong>. The next validation step is to measure flow versus lift with PG60 at nominal and cold conditions, then verify leakage and pressure integrity separately.</p>
<p class="analysis-keywords">#FreeCAD #ThermalManagement #ValveDesign #ElectricAircraft</p>
</div>
<div class="actions">
<a class="button secondary" href="{VIDEO}" download>Download the walkthrough ↓</a>
<a class="text-link" href="/AISolutions/simulations.html#{GALLERY_ID}">All analysis &amp; modeling →</a>
</div>
</section>'''
