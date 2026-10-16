"""Independent battery thermal study; stage 01 is a verified 0D model."""
from pathlib import Path

def publish_pages(root):
    root=Path(root)
    for name in ['battery-thermal.html','battery-thermal-cad.html','battery-thermal-stage-02.html']:
        (root/'AISolutions'/name).write_text((root/'scripts/content'/name).read_text())

def battery_thermal_card():
    return '''<article class="simulation-card filter-item" id="battery-thermal" data-category="Thermal" data-method="systems" data-analysis-company-ids="independent-work"><div class="card-copy"><p class="eyebrow">Independent work / Battery thermal modeling</p><h2>Battery thermal modeling, step by step</h2><p>Compare 1 W and 2 W heating, then inspect a separate localized-heating model with temperature maps, CAD views and a downloadable thermal mesh. Later stages will add enclosure and electronics coupling.</p><div class="pills"><span>FreeCAD</span><span>Python</span><span>SciPy</span><span>Open source</span></div><p class="study-note">Stages 01–02 available · 0D comparison and cell-only 2D finite volumes · Assumed inputs · Numerically verified, not experimentally validated.</p></div><a class="analysis-research-image" href="/AISolutions/battery-thermal-stage-02.html" aria-label="Open the independent battery thermal comparison and temperature maps"><img src="/assets/studies/battery-thermal/stage-02/figures/heat_input_comparison.png" alt="Comparison of one-watt and two-watt cell heating with unchanged cooling and timing" loading="lazy" width="1980" height="1260"></a><div class="card-bottom"><a class="text-link" href="/AISolutions/battery-thermal.html">Explore Stage 01 →</a><a class="text-link" href="/AISolutions/battery-thermal-stage-02.html">Compare heat input &amp; maps →</a></div></article>'''
