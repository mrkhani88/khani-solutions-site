"""Published native transient-wake results, shared by the case study and demos."""
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
ASSETS = '/assets/studies/midnight-wake'


def wake_viewer():
    return f'''<div class="midnight-wake-media">
<video controls playsinline muted preload="metadata" poster="{ASSETS}/Branded_Poster.png" aria-label="Transient aircraft wake at fixed twenty degree angle of attack, with local lift loading, instantaneous streamlines, vortex surfaces and time-resolved force plots"><source src="{ASSETS}/Midnight_Transient_Wake_20deg_Branded.mp4" type="video/mp4">Your browser does not support this video. <a href="{ASSETS}/Midnight_Transient_Wake_20deg_Branded.mp4">Download the wake video</a>.</video>
<p>Fixed 20° · 100 mph · 75 native snapshots · 7.5-second slowed playback. The aircraft and camera stay stationary; the flow evolves in physical time.</p>
<div class="sweep-links"><a href="{ASSETS}/Midnight_Transient_Wake_20deg_Branded.mp4" download>Download branded wake video ↓</a><a href="/AISolutions/midnight-aerodynamics.html#transient-wake-results">Results &amp; technical interpretation →</a></div></div>'''


def wake_study():
    review = json.loads((ROOT / 'assets/studies/midnight-wake/Result_Review.json').read_text())
    stats = review['weighted_force_statistics']
    rows = []
    for name, key in [('Lift', 'lift_N'), ('Drag', 'drag_N'), ('Side force', 'Fy_N')]:
        s = stats[key]
        rows.append(f'<tr><th scope="row">{name}</th><td>{s["mean"]/1000:+.3f}</td><td>{s["fluctuation_rms"]/1000:.3f}</td><td>{s["minimum"]/1000:+.3f} to {s["maximum"]/1000:+.3f}</td></tr>')
    force_table = '<div class="sweep-data-scroll"><table><caption>Full-aircraft forces over 0.500005–1.999991 s; time-weighted statistics</caption><thead><tr><th scope="col">Quantity</th><th scope="col">Mean / kN</th><th scope="col">Fluctuation RMS / kN</th><th scope="col">Min–max / kN</th></tr></thead><tbody>' + ''.join(rows) + '</tbody></table></div>'
    gamma_rows = []
    for label, s in zip(['X = 6 m, left', 'X = 6 m, right', 'X = 10 m, left', 'X = 10 m, right'], review['circulation_statistics_m2_s']):
        gamma_rows.append(f'<tr><th scope="row">{label}</th><td>{s["mean"]:+.2f}</td><td>{s["fluctuation_rms"]:.2f}</td><td>{s["minimum"]:+.2f} to {s["maximum"]:+.2f}</td></tr>')
    gamma_table = '<div class="sweep-data-scroll"><table><caption>Fixed-loop circulation over 75 snapshots, 0.502–1.982 s</caption><thead><tr><th scope="col">Loop station</th><th scope="col">Mean Γ / m² s⁻¹</th><th scope="col">Fluctuation RMS / m² s⁻¹</th><th scope="col">Min–max / m² s⁻¹</th></tr></thead><tbody>' + ''.join(gamma_rows) + '</tbody></table></div>'
    text = (ROOT / 'scripts/content/midnight-wake.html').read_text()
    return text.replace('WAKE_VIEWER', wake_viewer()).replace('WAKE_FORCE_TABLE', force_table).replace('WAKE_GAMMA_TABLE', gamma_table)


def wake_demo():
    return '<article class="company-demo midnight-wake-demo"><h4>Transient wake: persistence and load fluctuations</h4><p>A full-aircraft, fixed-20° URANS follow-up to the steady angle sweep. Inspect physical-time wake evolution and the corresponding loads.</p>' + wake_viewer() + '<p class="quiet">Independent public-reference reconstruction; unpowered and exploratory. No grid/time-step independence or validated shedding frequency.</p></article>'
