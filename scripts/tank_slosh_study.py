"""Independent Khani Solutions sloshing-tank AMR study and public media."""

TITLE = 'Adaptive mesh refinement in a sloshing tank'
URL = '/AISolutions/tank-slosh.html'
ASSETS = '/assets/studies/tank-slosh'
VIDEO = ASSETS + '/Slosh_Surface_Tracking.mp4'
PLAYBACK_VIDEO = '/assets/videos/portfolio/slosh-surface-tracking-web.mp4'
POSTER = ASSETS + '/Slosh_AMR_Poster.png'
DATA = ASSETS + '/public-study-summary.json'


def media(preload='metadata'):
    return (f'<div class="simulation-media slosh-media"><video controls playsinline '
            f'preload="{preload}" poster="{POSTER}" width="1080" height="1350" '
            'aria-label="Two-dimensional sloshing-tank interface and native adaptive mesh: full tank above, fixed-scale tracked detail below">'
            f'<source src="{PLAYBACK_VIDEO}" type="video/mp4">Your browser does not support this video. '
            f'<a href="{VIDEO}">Download the film</a>.</video></div>')


def gallery_card():
    return f'''<article id="tank-slosh-amr" class="simulation-card filter-item slosh-card" data-category="Aerospace" data-method="cfd" data-analysis-company-ids="independent-work">
<div class="card-copy"><p class="eyebrow">Khani Solutions · Numerical methods</p><h2>Adaptive mesh refinement in a sloshing tank</h2>
<p>A geometric VOF interface drives native quadtree refinement and coarsening. A fixed-scale detail view follows the computed crest and detached fragment while the full tank remains visible.</p>
<div class="pills"><span>Basilisk</span><span>Geometric VOF</span><span>Levels 6–11</span></div>
<p class="analysis-status">3.90625 mm finest cells · 365 native states · 0–18.2 s computed prefix</p>
<p class="study-note">Independent two-dimensional method demonstration. The retained prefix passed numerical/output checks; the longer run ended at a pressure-projection guard.</p></div>
{media('none')}<div class="card-bottom"><a class="text-link" href="{URL}">AMR rules, numerical checks &amp; scope →</a>
<a class="text-link" href="{VIDEO}" download>Download the film ↓</a><small>18.25 seconds · Native interface and mesh</small></div></article>'''


def study_body(intro):
    return intro('Khani Solutions · Independent numerical-method study',
                 'Adaptive mesh refinement<br>in a sloshing tank.',
                 'Geometric interface tracking, distance-based quadtree adaptation, and a fixed-scale view of the evolving liquid surface.') + f'''
<section class="wrap case-study slosh-study">
<p class="study-note">By Mohammadreza Khani, PhD · Khani Solutions · Assumed tank geometry and operating conditions</p>
<div class="slosh-lead"><div>{media()}<p class="slosh-video-caption">Upper panel: full tank. Lower panel: a constant 1.20 m × 0.652 m physical window tracking the crest and then a detached fragment. Both panels show the same saved native state.</p></div>
<div class="slosh-at-a-glance"><p class="eyebrow">The retained calculation</p><h2>Resolution follows the interface.</h2>
<dl class="slosh-metrics"><div><dt>3.90625 mm</dt><dd>Finest cell width, from an 8 m computational box at level 11.</dd></div>
<div><dt>Levels 6–11</dt><dd>Native two-dimensional quadtree leaves, with a 125 mm background cell width.</dd></div>
<div><dt>365 states</dt><dd>Saved every 0.05 s over 0–18.2 s; shown once each at 20 frames/s.</dd></div></dl>
<p class="slosh-status"><strong>Retained numerical prefix.</strong> The longer calculation failed its physical pressure-projection guard after this interval. Full-run acceptance remains false; experimental and mesh-convergence validation remain open.</p>
<div class="actions"><a class="button primary" href="{VIDEO}" download>Download the film ↓</a><a class="text-link" href="{DATA}" download>Public method summary (JSON) ↓</a></div></div></div>

<nav class="slosh-jump" aria-label="Study sections"><a href="#slosh-interface">Interface reconstruction</a><a href="#slosh-adaptation">Refinement rules</a><a href="#slosh-transfer">Mesh transfer &amp; flux repair</a><a href="#slosh-reading">Reading the film</a><a href="#slosh-scope">Numerical checks &amp; scope</a></nav>

<article id="slosh-interface" class="slosh-article"><p class="eyebrow">01 · Geometric interface</p><h2>The computed volume fraction defines the refinement target.</h2>
<p>Basilisk solves the two-phase flow using geometric volume-of-fluid (VOF) transport. In mixed cells, the interface is reconstructed with piecewise-linear interface calculation (PLIC). Pure-liquid/pure-gas face jumps are also included so that an interface aligned with a cell face remains part of the distance calculation.</p>
<p>At each adaptation pass, the interface segments are copied into a bounding-volume hierarchy (BVH) for distance queries. The segment geometry and the BVH remain fixed during that pass. Refinement therefore follows the current numerical interface rather than a prescribed wave shape or a change in display resolution.</p>
</article>

<article id="slosh-adaptation" class="slosh-article"><p class="eyebrow">02 · Native quadtree AMR</p><h2>Four interface bands set the required local level.</h2>
<p>The smallest requested width is <var>h</var> = 8 m / 2<sup>11</sup> = 3.90625 mm. A cell’s proximity is its centre-to-interface distance reduced by half its diagonal, with a lower bound of zero. This whole-cell allowance refines cells whose corners can enter the target band.</p>
<div class="slosh-table-scroll"><table class="slosh-table"><caption>Distance thresholds in the refinement pass</caption><thead><tr><th scope="col">Whole-cell proximity</th><th scope="col">Distance</th><th scope="col">Target level</th><th scope="col">Cell width</th></tr></thead><tbody>
<tr><td>Below 3<var>h</var></td><td>11.71875 mm</td><td>11</td><td>3.90625 mm</td></tr>
<tr><td>Below 10<var>h</var></td><td>39.0625 mm</td><td>10</td><td>7.8125 mm</td></tr>
<tr><td>Below 30<var>h</var></td><td>117.1875 mm</td><td>9</td><td>15.625 mm</td></tr>
<tr><td>Below 80<var>h</var></td><td>312.5 mm</td><td>8</td><td>31.25 mm</td></tr>
</tbody></table></div>
<p>The background minimum is level 6. A separate wall rule keeps the fixed wall and a five-<var>h</var> buffer at the finest level. Coarsening uses interface-distance bands expanded by a factor of 1.5, retaining fine cells until the interface has moved farther away. This hysteresis reduces repeated refinement and coarsening near a band boundary.</p>
<p>Adaptation is evaluated every four solver iterations. Because the time step varies, these passes do not occur at a fixed physical-time interval.</p>
</article>

<article id="slosh-transfer" class="slosh-article"><p class="eyebrow">03 · Numerical continuity</p><h2>A mesh change also requires a consistent transported state.</h2>
<p>Refinement and coarsening operate on the native solver fields. Liquid area, domain area, and phase sensible energy are checked across adaptation. Conservative phase-weighted thermal transfer and the native momentum refinement callbacks carry the solution to the new grid.</p>
<p>The remapped face flux is repaired with an auxiliary projection before transport continues. Its divergence guard is 2 × 10<sup>−10</sup> s<sup>−1</sup>. The auxiliary potential is a numerical flux correction; physical pressure is obtained through the separate flow pressure solve.</p>
<p>The run uses a VOF Courant limit of 0.4 and a maximum time step of 0.01 s. Local cell size therefore affects both spatial resolution and the admissible transport step.</p>
</article>

<article id="slosh-reading" class="slosh-article"><p class="eyebrow">04 · Reading the film</p><h2>Mesh-change colours compare successive saved native grids.</h2>
<div class="slosh-colour-key"><p><span class="slosh-swatch slosh-refined" aria-hidden="true"></span><strong>Amber:</strong> current cells that are refined descendants of a previously coarser native leaf.</p><p><span class="slosh-swatch slosh-coarsened" aria-hidden="true"></span><strong>Purple:</strong> current parent cells whose areas were fully tiled by finer leaves in the preceding saved grid.</p></div>
<p>The comparison interval is the 0.05 s between saved states. Several adaptation passes may occur within it, so these highlighted cells are not individual adaptation-event counts. The first state has no preceding grid for comparison.</p>
<p>The detail camera changes position while its physical width and height stay fixed. The renderer uses the same native timestamp for the full-tank and detail panels, with no temporal interpolation, repeated states, or synthetic mesh subdivision. The encoded duration is 18.25 s because 365 frames are shown at 20 frames/s; the last physical timestamp is 18.2 s.</p>
</article>

<article id="slosh-scope" class="slosh-article"><p class="eyebrow">05 · Evidence and interpretation</p><h2>The film presents a checked prefix of an incomplete calculation.</h2>
<p>The delivery audit checks the 365-state sequence, synchronized panels, native-time playback, constant physical crop, encoded-file integrity, and full video decode. The numerical-prefix audit includes the per-step history and native-field checks at five representative saved states. These checks support the provenance of the shown output; they do not establish experimental agreement or mesh-converged fragmentation.</p>
<details class="slosh-details"><summary>Model assumptions</summary><div>
<p>The assumed tank section is 7 m wide and 4.5 m high. A fixed Cartesian full-cell wall representation and impermeable slip conditions are used. Liquid properties approximate LOX; gas properties approximate helium. Initial liquid and gas temperatures are 90 K and 120 K, with a maintained 95 K wall.</p>
<p>A prescribed accelerating-tank frame uses a vertical acceleration of −0.5 m/s² and lateral forcing with amplitude 0.035 m/s² and period 16 s, ramped up over the first 4 s. The initial free-surface slope is 0.14 and the initial velocity is zero.</p>
<p>Sensible-energy transport is solved without thermal feedback on the incompressible flow. Gas equation-of-state effects, phase change, absolute ullage pressurization, and structural response are outside this model. Two-dimensional interface fragments are qualitative computed features rather than validated three-dimensional droplet predictions.</p>
</div></details>
<p>The attempted 100 s run did not complete. The retained 0–18.2 s prefix is separately scoped and numerically/output verified. The pressure-projection failure after that prefix remains part of the study record.</p>
<p><strong>Khani Solutions workflow:</strong> AI assists workflow scripting, post-processing, and technical communication. Basilisk performs the numerical flow calculation; engineering review determines how its output can be interpreted.</p>
<div class="actions"><a class="button secondary" href="{DATA}" download>Download the public method summary ↓</a><a class="text-link" href="/AISolutions/simulations.html#tank-slosh-amr">All analysis &amp; modeling →</a></div>
</article>
</section>'''
