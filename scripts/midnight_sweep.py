"""Shared angle-sweep viewer for the study, gallery and Wisk methods demos."""
from pathlib import Path
import json, csv

ROOT = Path(__file__).resolve().parents[1]
ASSETS = '/assets/studies/midnight-sweep'
def SWEEP_TEXT():
    with (ROOT / 'assets/studies/midnight-sweep/Angle_Sweep.csv').open() as f:
        cases = list(csv.DictReader(f))
    rows = ''.join(f'<tr><td>{c["alpha_deg"]}°</td><td>{float(c["lift_N"])/1000:+.3f}</td><td>{float(c["drag_N"])/1000:.3f}</td><td>{float(c["Cl_mean"]):.4f}</td><td>{float(c["Cd_mean"]):.4f}</td><td>Not met</td></tr>' for c in cases)
    table = '<table><thead><tr><th>AoA</th><th>Lift / kN</th><th>Drag / kN</th><th>CL</th><th>CD</th><th>Full convergence targets</th></tr></thead><tbody>' + rows + '</tbody></table>'
    return (ROOT / 'scripts/content/midnight-angle-sweep.html').read_text().replace('SWEEP_RESULTS_TABLE', table)
SWEEP_POST_URL = ''  # Set only after the new post is published and verified.

def sweep_viewer():
    timeline = json.loads((ROOT / 'assets/studies/midnight-sweep/Loop_Timeline.json').read_text())['case_indices']
    buttons = ''.join(f'<button type="button" data-sweep-case="{i}" aria-pressed="{str(i==0).lower()}">{2*i}°</button>' for i in range(11))
    post = f'<a href="{SWEEP_POST_URL}" target="_blank" rel="noopener noreferrer">Discuss the angle sweep on LinkedIn ↗</a>' if SWEEP_POST_URL else ''
    return f'''<div class="midnight-sweep" data-midnight-sweep data-timeline='{json.dumps(timeline)}' data-assets="{ASSETS}">
<video controls loop playsinline muted preload="metadata" poster="{ASSETS}/Lift_Poster.png" src="{ASSETS}/Midnight_0_to_20_Lift_3s.mp4" aria-label="Independent aircraft CFD angle sweep, zero to twenty degrees and back to zero"></video>
<div class="sweep-controls" role="group" aria-label="Surface force coloring"><button type="button" data-sweep-mode="Lift" aria-pressed="true">Lift coloring</button><button type="button" data-sweep-mode="Drag" aria-pressed="false">Drag coloring</button><span class="sweep-control-break"></span><button type="button" data-sweep-cut="3" aria-pressed="true">3 s loop</button><button type="button" data-sweep-cut="11" aria-pressed="false">11 s inspection</button></div>
<div class="sweep-controls sweep-angles" role="group" aria-label="Select angle of attack">{buttons}<output data-sweep-active aria-live="polite">0° · increasing</output></div>
<p class="sweep-help">Select an angle to pause and inspect. Use the video’s play control to resume the 0° → 20° → 0° loop. All eleven calculated angles remain on the plots; the highlighted point follows the displayed field. Use fullscreen for detailed plots on small screens.</p>
<p class="sweep-status" role="status" data-sweep-status hidden></p>
<p class="sweep-qualified">Independent public-reference Archer Midnight approximation, presented with the Wisk methods demos. All eleven cases missed full convergence targets. This is an unpowered, symmetric screening study, not Wisk/Boeing/Archer engineering data or a validated stall envelope.</p>
<div class="sweep-links"><a data-sweep-download href="{ASSETS}/Midnight_0_to_20_Lift_3s.mp4" download>Download selected video ↓</a><a href="{ASSETS}/Angle_Sweep.csv" download>All-angle force data ↓</a><a href="{ASSETS}/midnight-sweep-blender.zip" download>Editable Blender scene (72 MB ZIP) ↓</a><a href="/AISolutions/midnight-aerodynamics.html#angle-sweep-methods">Methods &amp; interpretation →</a>{post}</div></div>'''

def sweep_demo():
    return '<article class="company-demo midnight-sweep-demo"><h4>Aircraft angle-of-attack sweep: 0°–20°</h4><p>Inspect native flow paths and local lift/drag contributions while comparing every sampled angle.</p>' + sweep_viewer() + '</article>'
