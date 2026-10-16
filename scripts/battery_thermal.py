"""Independent battery thermal study; stage 01 is a verified 0D model."""
from pathlib import Path

def publish_pages(root):
    root=Path(root)
    for name in ['battery-thermal.html','battery-thermal-cad.html','battery-thermal-stage-02.html','battery-thermal-stage-03.html']:
        (root/'AISolutions'/name).write_text((root/'scripts/content'/name).read_text())

def battery_thermal_card():
    return '''<article class="simulation-card filter-item" id="battery-thermal" data-category="Thermal" data-method="systems" data-analysis-company-ids="independent-work"><div class="card-copy"><p class="eyebrow">Independent work / Battery thermal modeling</p><h2>Battery thermal modeling, step by step</h2><p>Start with one cell, double its heat input, then connect the PCB, chip packages and enclosure. Explore per-component temperature maps, source-isolation cases and heat spreading across the assembly.</p><div class="pills"><span>FreeCAD</span><span>Python</span><span>SciPy</span><span>Open source</span></div><p class="study-note">Stages 01–03 available · 14 coupled components · Layered finite volumes and lumped packages · Assumed inputs · Numerically verified, not experimentally validated.</p></div><a class="analysis-research-image" href="/AISolutions/battery-thermal-stage-03.html" aria-label="Open the coupled PCB and enclosure thermal study"><img src="/assets/studies/battery-thermal/stage-03/figures/component_maps.png" alt="Battery, main PCB, RF PCB, midplate and back-cover temperature maps on one shared color scale" loading="lazy" width="2380" height="850"></a><div class="card-bottom"><a class="text-link" href="/AISolutions/battery-thermal.html">Start with Stage 01 →</a><a class="text-link" href="/AISolutions/battery-thermal-stage-02.html">Compare heat input →</a><a class="text-link" href="/AISolutions/battery-thermal-stage-03.html">Explore PCB &amp; enclosure →</a></div></article>'''
