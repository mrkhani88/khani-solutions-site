"""Independent public-reference 2D transfer concept; no employer data or raw outputs."""

TITLE = 'Cryogenic propellant transfer | Independent 2D CFD concept'
SUMMARY = ('A generic LOX-like tank moves through coast, settling and one-way propellant transfer. '
           'Native two-phase flow fields are presented alongside separately credited New Glenn mission context.')
URL = '/AISolutions/new-glenn-transfer-first.html'
ASSETS = '/assets/studies/new-glenn-transfer-first'
VIDEO = ASSETS + '/New_Glenn_Transfer_First_LinkedIn.mp4'
POSTER = ASSETS + '/LinkedIn_Cover.png'
DATA = ASSETS + '/public-study-summary.json'


def media(preload='metadata'):
    return (f'<div class="simulation-media new-glenn-media"><video controls playsinline '
            f'preload="{preload}" poster="{POSTER}" width="1080" height="1350" '
            'aria-label="72-second independent 2D propellant transfer concept and credited New Glenn mission context">'
            f'<source src="{VIDEO}" type="video/mp4">Your browser does not support this video. '
            f'<a href="{VIDEO}">Download the film</a>.</video></div>')


def overview_feature():
    return f'''<section class="wrap section new-glenn-overview" aria-labelledby="new-glenn-feature-title">
<div class="new-glenn-feature-copy"><p class="eyebrow">New independent engineering film</p>
<h2 id="new-glenn-feature-title">One tank drains.<br>Another fills.</h2>
<p>A 72-second film connects a coarse 2D propellant-transfer concept to the next questions in settling, pressurant conditioning and fluid-load analysis.</p>
<p class="quiet">New Glenn-inspired context · Generic tank geometry · Independent Khani Solutions work</p>
<div class="actions"><a class="button primary" href="{URL}">Watch the film &amp; read the methods →</a>
<a class="text-link" href="/AISolutions/simulations.html#new-glenn-transfer-first">Find it in Analysis &amp; modeling →</a></div></div>
<a class="new-glenn-feature-poster" href="{URL}" aria-label="Watch the independent propellant-transfer film">
<img src="{POSTER}" alt="Cover of the independent propellant-transfer film" width="1080" height="1350" loading="lazy"></a>
</section>'''


def gallery_card():
    return f'''<article id="new-glenn-transfer-first" class="simulation-card filter-item new-glenn-card" data-category="Aerospace" data-method="cfd" data-analysis-company-ids="independent-work">
<div class="card-copy"><p class="eyebrow">Independent 2D CFD concept</p><h2>Cryogenic propellant transfer</h2>
<p>{SUMMARY}</p><div class="pills"><span>OpenFOAM 2512</span><span>2,118 cells</span><span>Two-phase VOF</span></div>
<p class="analysis-status">600-second coast · 40-second settling · 0.9235% donor gas carryover by volume</p>
<p class="study-note">Generic geometry inherited from an earlier Falcon 9 reference visualization, not New Glenn tank CAD. Isothermal flow; no quantified collapse factor, structural stress or buckling margin.</p></div>
{media('none')}<div class="card-bottom"><a class="text-link" href="{URL}">Methods, observations &amp; limitations →</a>
<a class="text-link" href="{VIDEO}" download>Download the film ↓</a><small>72 seconds · Native flow fields / credited mission context</small></div></article>'''


def study_body(intro):
    return intro('Independent New Glenn-inspired concept', 'Cryogenic propellant transfer.',
                 'One tank drains. Another fills. A coarse 2D flow study helps frame the next engineering questions.') + f'''
<section class="wrap case-study new-glenn-study">
<p class="study-note">By Mohammadreza Khani, PhD · Khani Solutions · Independent public-reference work; not a Blue Origin design, employer deliverable or flight prediction.</p>
<div class="new-glenn-lead">{media()}<aside class="new-glenn-at-a-glance" aria-labelledby="new-glenn-observations">
<p class="eyebrow">Observed in this coarse case</p><h2 id="new-glenn-observations">What the calculation shows</h2>
<dl class="new-glenn-metrics"><div><dt>600 s</dt><dd>Prescribed free-fall coast window; detached interior gas pockets developed.</dd></div>
<div><dt>40 s</dt><dd>Settling window, ramping to 0.15 m/s² before transfer.</dd></div>
<div><dt>0.9235%</dt><dd>Transfer-averaged gas carryover at the donor boundary, by mixture volume.</dd></div>
<div><dt>78.6 kPa</dt><dd>Maximum <strong>saved shell-boundary pressure span</strong> in the generic ascent phase; not absolute ullage pressure or structural stress.</dd></div></dl>
<p class="quiet">The 72-second film compresses illustrative mission windows. The solver fields and inventory integrals are separate from the interpolated presentation.</p>
<a class="text-link" href="{DATA}" download>Download the public study summary (JSON) ↓</a></aside></div>

<nav class="new-glenn-jump" aria-label="Study sections"><a href="#transfer-model">Flow model</a><a href="#transfer-observations">Transfer observations</a><a href="#transfer-next-analyses">Next analyses</a><a href="#transfer-context">Mission context &amp; credits</a></nav>

<article id="transfer-model" class="new-glenn-article"><p class="eyebrow">Method and assumptions</p><h2>A generic planar tank, carried continuously through the scenario.</h2>
<p>The calculation uses native OpenFOAM 2512 <code>interFoam</code> on 2,118 cells: a planar section with one cell through its 0.1 m thickness and empty front/back boundaries. The inherited section was previously used in a Falcon 9 reference visualization. It is <strong>not New Glenn tank CAD</strong>, and the dimensional presentation does not make it a three-dimensional CFD calculation.</p>
<p>The fluids are a LOX-like liquid and a constant-density helium-like gas surrogate. The model is incompressible, isothermal and laminar, with surface tension. Prescribed tank-frame acceleration and boundary fluxes represent ground fill, ascent drawdown, cutoff, coast, settling, transfer and an assumed return sequence. The liquid–gas interface is not reset between phases.</p>
<p>A separate receiver tank uses interval-averaged mixture and liquid forcing measured at the donor outlet. This is one-way boundary coupling. Transfer piping, pumps and two-way pressure interaction are not resolved.</p>
<p>The donor tank’s numerical-control history tightened the time controls during the run. Actual measured maximum Courant number was about 0.832, below the retained fatal guard of 0.85 but above the initial target of 0.35. A tighter-control replay is a separate scenario execution, not a bitwise recreation of the archived trajectory.</p></article>

<article id="transfer-observations" class="new-glenn-article"><p class="eyebrow">Results and numerical limits</p><h2>Settling changed the outlet conditions, but gas carryover remained.</h2>
<p>During approximately 600 seconds of coast, the coarse VOF field developed several detached interior gas pockets and wall-wetting liquid. These are non-equilibrium coarse-grid observations, not a prediction of equilibrium bubble shape or a resolved three-dimensional interfacial area.</p>
<p>After approximately 40 seconds of settling, the donor’s transfer-averaged gas carryover was <strong>0.923489% of the mixture volume</strong> at its transfer boundary. That observation motivates comparisons of settling duration, outlet placement and acquisition geometry.</p>
<p>The receiver liquid gain and donor liquid loss differ by <strong>0.062117% of the donor-delivered liquid</strong>. This measured one-way boundary-coupling difference remains reported alongside the separate tank-wise conservation checks; it is not assumed to be zero.</p>
<p>Numerical inventory, boundedness and guard checks were assessed. Mesh and time-step convergence, experimental comparison and flight validation have not been established. The numerical observations are screening inputs for further work.</p></article>

<article id="transfer-next-analyses" class="new-glenn-article"><p class="eyebrow">What this model can inform next</p><h2>Pressurant and structural questions need additional physics.</h2>
<div class="new-glenn-next-grid"><section><h3>Pressurant collapse factor</h3>
<p>A mass-based collapse factor compares actual required pressurant mass with an ideal reference requirement for a matched pressure and expulsion schedule. <strong>This run produces no numerical collapse factor.</strong></p>
<p>It supplies ullage-volume history, interface motion and planar interface-length/wall-wetting proxies. A calculation of actual pressurant demand needs coupled energy and compressible-ullage modeling, gas and wall temperatures, heat transfer and any applicable propellant-vapor or autogenous phase-change physics.</p></section>
<section><h3>Fluid-load cases for structural work</h3>
<p>The maximum saved shell-boundary pressure span is <strong>78.645811 kPa at 110 s</strong> in the generic ascent phase. It is maximum minus minimum shell-boundary fluid pressure and is invariant to a uniform reference offset. Saved extrema sample approximately every two seconds.</p>
<p>The film’s pressure map is relative to each frame’s minimum on a fixed 0–80 kPa scale. The imposed pressure datum does not establish thermodynamic ullage pressure or actual external pressure.</p>
<p>These relative pressure histories can help frame later load cases. Stress, strength and buckling require a separate structural model with suitable geometry, materials, wall thickness, supports, imperfections and load mapping. None is calculated here.</p></section></div></article>

<article id="transfer-context" class="new-glenn-article"><p class="eyebrow">Independent study and third-party media</p><h2>Keep the mission context separate from the assumed tank scenario.</h2>
<p>The launch clips show <strong>NG-2 / ESCAPADE, November 13, 2025</strong>. The mission-profile diagram and postlanding recovery photo provide separate <strong>NG-3 context from April 2026</strong>. They are not footage of this modeled transfer, and the recovery image is not touchdown footage.</p>
<p>New Glenn booster recovery is distinct from upper-stage orbital delivery. The combined whole-tank orbital-transfer and Earth-return sequence in this generic scenario is hypothetical. The official mission-profile diagram shows planned targets rather than validation of achieved orbit or the modeled scenario.</p>
<p>Launch footage: <strong>Blue Origin, distributed through NASA Goddard Scientific Visualization Studio</strong>. Mission diagram and recovery imagery: <strong>Blue Origin</strong>. Original programmatically composed instrumental music accompanies this edit. Third-party media remain subject to their owners’ terms; attribution does not establish unrestricted commercial reuse or imply endorsement.</p>
<ul class="new-glenn-sources"><li><a href="https://svs.gsfc.nasa.gov/14926/" target="_blank" rel="noopener noreferrer">NASA Goddard SVS: NG-2 / ESCAPADE launch media and Blue Origin credit ↗</a></li>
<li><a href="https://www.blueorigin.com/missions/ng-3" target="_blank" rel="noopener noreferrer">Blue Origin: NG-3 mission context ↗</a></li>
<li><a href="https://www.blueorigin.com/gallery/by/new-glenn" target="_blank" rel="noopener noreferrer">Blue Origin: New Glenn image gallery ↗</a></li>
<li><a href="https://ntrs.nasa.gov/citations/20100026018" target="_blank" rel="noopener noreferrer">NASA NTRS: pressurization reference ↗</a></li>
<li><a href="https://ntrs.nasa.gov/citations/20240006787" target="_blank" rel="noopener noreferrer">NASA NTRS: cryogenic-fluid reference ↗</a></li>
<li><a href="https://ntrs.nasa.gov/citations/20230008395" target="_blank" rel="noopener noreferrer">NASA NTRS: cryogenic-fluid reference ↗</a></li></ul></article>
<div class="actions"><a class="button secondary" href="{VIDEO}" download>Download the 72-second film ↓</a><a class="text-link" href="{DATA}" download>Public summary &amp; provenance (JSON) ↓</a><a class="text-link" href="/AISolutions/simulations.html">All analysis &amp; modeling →</a></div>
</section>'''
